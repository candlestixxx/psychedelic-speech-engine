import argparse
import os
import subprocess
import sys

# Force UTF-8 output so transcripts (em-dashes, curly quotes, phonemes, etc.)
# never crash the Windows console with UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import requests
import torch
import json
import time
import warnings
from dotenv import load_dotenv

# Suppress PyTorch/NumPy and quantization warnings from whisperx
warnings.filterwarnings("ignore")

load_dotenv()


def setup_argparse():
    parser = argparse.ArgumentParser(description="Psychedelic Speech-to-Music Video Engine (app.py)")
    parser.add_argument("--url", required=True, help="YouTube speech URL")
    parser.add_argument("--music", required=True, help="Path to background music file")
    parser.add_argument("--speaker", default="SPEAKER_01", help="Target speaker ID")
    parser.add_argument("--start", default=None, help="Optional: extract only from this timestamp (e.g. 01:23:45 or 83)")
    parser.add_argument("--end", default=None, help="Optional: extract only up to this timestamp (e.g. 01:30:00)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay for speech overlay (seconds)")
    parser.add_argument("--output", default="final_master.mp4", help="Output MP4 filename")
    parser.add_argument("--video-filter", default="mandelbrot=size=1920x1080:rate=30", help="FFmpeg video filter string")
    parser.add_argument("--voice", default="am_onyx", help="Kokoro TTS voice ID (am_* = male, af_* = female)")
    parser.add_argument("--prompt-style", default="rhythmic spoken-word stanzas", help="Thematic instruction for the DeepSeek LLM (e.g. 'Alan Watts philosophical')")
    parser.add_argument("--subtitle-style", default="FontName=Arial,FontSize=24,PrimaryColour=&H00FFFF,Bold=1", help="FFmpeg force_style subtitle config")
    return parser.parse_args()


def _firefox_available():
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if base and os.path.exists(os.path.join(base, "Mozilla Firefox", "firefox.exe")):
            return True
    return False


def download_audio(url, workspace_dir, start=None, end=None):
    output_wav = os.path.join(workspace_dir, "downloaded_audio.wav")
    section = None
    if start or end:
        s = start or "0:00"
        e = end or "inf"
        section = f"*{s}-{e}"
    msg = f"[1/5] Downloading audio from {url} to {output_wav}"
    if section:
        msg += f" (section {section})"
    print(msg)
    cmd = [
        "yt-dlp",
        "--remote-components", "ejs:github",
        "--extractor-args", "youtube:player_client=web",
        "--extract-audio",
        "--audio-format", "wav",
        "--output", output_wav,
    ]
    # YouTube bot-walls unauthenticated IPs. Prefer Firefox (yt-dlp reads its
    # cookies live, so no manual re-export); fall back to a cookies.txt export.
    cookies_args = []
    if _firefox_available():
        cookies_args = ["--cookies-from-browser", "firefox"]
    else:
        cookies_file = os.environ.get("YT_COOKIES_FILE") or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "cookies.txt"
        )
        if os.path.exists(cookies_file):
            cookies_args = ["--cookies", cookies_file]
    if cookies_args:
        cmd = ["yt-dlp"] + cookies_args + cmd[1:]
    if section:
        cmd += ["--download-sections", section]
    cmd.append(url)
    subprocess.run(cmd, check=True)
    return output_wav


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


def transcribe_and_diarize(audio_file, model_name="large-v2"):
    """Run WhisperX transcription + pyannote diarization.

    Returns the result whose `segments` each carry a 'speaker' label.
    """
    print("[diarize] Transcribing and diarizing (this can take a while)...")
    import whisperx
    from whisperx.diarize import DiarizationPipeline

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise ValueError(
            "HF_TOKEN is required for speaker diarization. The pyannote model is gated on "
            "HuggingFace. Create a token at https://huggingface.co/settings/tokens and accept "
            "the terms at https://huggingface.co/pyannote/speaker-diarization-community-1 "
            "(and https://huggingface.co/pyannote/segmentation-3.0). Then put HF_TOKEN in your .env file."
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        major, _ = torch.cuda.get_device_capability(0)
        # Pascal GPUs (sm_60/61, e.g. GTX 1080 Ti) have no efficient fp16 compute;
        # ctranslate2 rejects float16 there, so use float32. Volta+ (sm_70+) uses fp16.
        compute_type = "float16" if major >= 7 else "float32"
    else:
        compute_type = "int8"
    print(f"    device={device}, compute_type={compute_type}")

    model = whisperx.load_model(model_name, device, compute_type=compute_type)
    audio = whisperx.load_audio(audio_file)
    result = model.transcribe(audio, batch_size=4)

    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

    # whisperx 3.8.x: DiarizationPipeline lives in whisperx.diarize and takes `token=`
    diarize_model = DiarizationPipeline(token=hf_token, device=device)
    result = whisperx.assign_word_speakers(diarize_model(audio), result)
    return result


def speaker_stats(result):
    """Return {speaker_id: {'secs': float, 'count': int}} from a diarized result."""
    from collections import defaultdict
    stats = defaultdict(lambda: {"secs": 0.0, "count": 0})
    for seg in result.get("segments", []):
        spk = seg.get("speaker", "UNKNOWN")
        stats[spk]["secs"] += seg["end"] - seg["start"]
        stats[spk]["count"] += 1
    return dict(stats)


def dominant_speaker(result):
    """Pick the speaker who talks the most (usually the subject, not the interviewer)."""
    stats = speaker_stats(result)
    if not stats:
        return None
    return max(stats, key=lambda s: stats[s]["secs"])


def build_srt_and_text(result, target_speaker, workspace_dir):
    """Build an SRT + raw text from a diarized result for one speaker."""
    srt_content = ""
    raw_text = ""
    idx = 1
    for segment in result.get("segments", []):
        if segment.get("speaker") == target_speaker:
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()
            srt_content += f"{idx}\n{start} --> {end}\n{text}\n\n"
            raw_text += text + " "
            idx += 1

    srt_filename = os.path.join(workspace_dir, "isolated_speech.srt")
    with open(srt_filename, "w", encoding="utf-8") as f:
        f.write(srt_content)

    if idx == 1:
        print(f"    WARNING: no speech found for speaker '{target_speaker}'. "
              f"Available speakers will be visible in the full transcript run.")
    return srt_filename, raw_text


def extract_speech_and_srt(audio_file, target_speaker, workspace_dir):
    result = transcribe_and_diarize(audio_file)
    return build_srt_and_text(result, target_speaker, workspace_dir)


def polish_script(raw_text, prompt_style):
    print(f"[3/5] Polishing script with DeepSeek (Style: {prompt_style})...")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if not deepseek_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is missing.")

    model_name = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {deepseek_key}",
        "Content-Type": "application/json",
    }

    prompt = (
        "You are editing a spoken-word piece. From the transcript below, extract the "
        "most profound, quotable moments — the speaker's KEY points — VERBATIM. Keep "
        "their exact words; only remove filler (um, uh, you know, stutters). Break the "
        "result into short standalone lines (one complete thought per line), separated "
        "by newlines. Do NOT paraphrase, summarize, or add any words. "
        f"Tone/narrative flavor: {prompt_style}. Output ONLY the quotes, one per line:\n\n"
        f"{raw_text}"
    )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a poetic assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise ValueError("DeepSeek API failed after maximum retries.")


def synthesize_audio(text, workspace_dir, voice_id):
    print(f"[4/5] Synthesizing audio with Kokoro TTS (Voice: {voice_id})...")
    from kokoro import KPipeline
    import numpy as np
    import soundfile as sf

    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipeline = KPipeline(lang_code='a', device=device)
    generator = pipeline(text, voice=voice_id, speed=1.0, split_pattern=r'\n+')

    audio_chunks = []
    for i, (gs, ps, audio) in enumerate(generator):
        if audio is not None:
            audio_chunks.append(audio)

    if not audio_chunks:
        raise ValueError("No audio synthesized.")

    final_audio = np.concatenate([a.cpu().numpy() if hasattr(a, "cpu") else np.asarray(a)
                                  for a in audio_chunks])
    output_speech_wav = os.path.join(workspace_dir, "synthesized_speech.wav")
    sf.write(output_speech_wav, final_audio, 24000)
    return output_speech_wav


def synthesize_lines(text, voice_id):
    """Synthesize each line separately; returns a list of float32 mono arrays."""
    from kokoro import KPipeline
    import numpy as np

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipeline = KPipeline(lang_code='a', device=device)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    audios = []
    for line in lines:
        chunks = []
        for _gs, _ps, audio in pipeline(line, voice=voice_id, speed=1.0, split_pattern=r'\n+'):
            if audio is not None:
                chunks.append(audio)
        if chunks:
            audios.append(np.concatenate(
                [a.cpu().numpy() if hasattr(a, "cpu") else np.asarray(a) for a in chunks]
            ))
    return audios


def build_rhythmic_speech(line_audios, bpm, sr=24000, gap_frac=0.25):
    """Place each line so its start lands on a beat; returns one float32 array."""
    import numpy as np
    beat_samples = int(sr * 60.0 / max(1.0, bpm))
    gap = int(beat_samples * gap_frac)
    placements = []
    t = gap
    for a in line_audios:
        start = int(np.ceil(t / beat_samples) * beat_samples)
        placements.append((start, a))
        t = start + len(a) + gap
    total = max(placements[-1][0] + len(placements[-1][1]) + gap, sr)
    out = np.zeros(total, dtype=np.float32)
    for start, a in placements:
        out[start:start + len(a)] += a
    return out


def save_rhythmic_speech(line_audios, bpm, out_path, sr=24000):
    import soundfile as sf
    arr = build_rhythmic_speech(line_audios, bpm, sr=sr)
    sf.write(out_path, arr, sr)
    return out_path


def _ffmpeg_subtitle_path(path):
    """Escape a path for use inside ffmpeg's subtitles/ass filter (Windows-safe)."""
    p = os.path.abspath(path).replace("\\", "/")
    p = p.replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")
    return p


def render_video(speech_file, music_file, srt_file, output_file, delay, video_filter, subtitle_style):
    print(f"[5/5] Rendering final video to {output_file}...")

    delay_ms = int(delay * 1000)
    subtitles = _ffmpeg_subtitle_path(srt_file)

    # mandelbrot is an infinite source; -shortest ends output when the (finite) audio ends.
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", video_filter,
        "-i", speech_file,
        "-i", music_file,
        "-filter_complex",
        f"[1:a]adelay={delay_ms}:all=1[speech]; [speech][2:a]amix=inputs=2:duration=shortest[a]; "
        f"[0:v]subtitles='{subtitles}':force_style='{subtitle_style}'[v]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-shortest",
        output_file,
    ]

    subprocess.run(cmd, check=True)
    print("Rendering complete!")


def main():
    args = setup_argparse()

    # Create isolated workspace directory for this execution
    workspace_dir = f"workspace_run_{int(time.time())}"
    os.makedirs(workspace_dir, exist_ok=True)
    print(f"📁 Created isolated workspace: {workspace_dir}")

    try:
        # Step 1: Download audio (optionally a time range of the video)
        audio_wav = download_audio(args.url, workspace_dir, args.start, args.end)

        # Step 2: Diarize and transcribe
        srt_file, raw_text = extract_speech_and_srt(audio_wav, args.speaker, workspace_dir)

        # Step 3: Polish script via DeepSeek
        polished_text = polish_script(raw_text, args.prompt_style)

        # Step 4: Synthesize TTS
        synthesized_speech = synthesize_audio(polished_text, workspace_dir, args.voice)

        # Step 5: Render video
        render_video(synthesized_speech, args.music, srt_file, args.output, args.delay, args.video_filter, args.subtitle_style)

        print(f"Done! Final video: {args.output}")

    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
