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
from dotenv import load_dotenv

load_dotenv()


def setup_argparse():
    parser = argparse.ArgumentParser(description="Psychedelic Speech-to-Music Video Engine (app.py)")
    parser.add_argument("--url", required=True, help="YouTube speech URL")
    parser.add_argument("--music", required=True, help="Path to background music file")
    parser.add_argument("--speaker", default="SPEAKER_01", help="Target speaker ID")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay for speech overlay (seconds)")
    parser.add_argument("--output", default="final_master.mp4", help="Output MP4 filename")
    return parser.parse_args()


def download_audio(url):
    output_wav = "downloaded_audio.wav"
    print(f"[1/5] Downloading audio from {url} to {output_wav}")
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "--output", output_wav,
        url,
    ]
    subprocess.run(cmd, check=True)
    return output_wav


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


def extract_speech_and_srt(audio_file, target_speaker):
    print("[2/5] Transcribing and diarizing (this can take a while)...")
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

    model = whisperx.load_model("large-v2", device, compute_type=compute_type)
    audio = whisperx.load_audio(audio_file)
    result = model.transcribe(audio, batch_size=16 if device == "cuda" else 4)

    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

    # whisperx 3.8.x: DiarizationPipeline lives in whisperx.diarize and takes `token=`
    diarize_model = DiarizationPipeline(token=hf_token, device=device)
    diarize_segments = diarize_model(audio)
    result = whisperx.assign_word_speakers(diarize_segments, result)

    srt_content = ""
    raw_text = ""
    idx = 1
    for segment in result["segments"]:
        if segment.get("speaker") == target_speaker:
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()

            srt_content += f"{idx}\n{start} --> {end}\n{text}\n\n"
            raw_text += text + " "
            idx += 1

    srt_filename = "isolated_speech.srt"
    with open(srt_filename, "w", encoding="utf-8") as f:
        f.write(srt_content)

    if idx == 1:
        print(f"    WARNING: no speech found for speaker '{target_speaker}'. "
              f"Available speakers will be visible in the full transcript run.")
    return srt_filename, raw_text


def polish_script(raw_text):
    print("[3/5] Polishing script with DeepSeek...")
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
        "Clean the following transcript, remove filler words, and format the speech "
        "into rhythmic spoken-word stanzas. Output ONLY the polished text:\n\n"
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

    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    data = response.json()

    polished_text = data["choices"][0]["message"]["content"]
    return polished_text


def synthesize_audio(text):
    print("[4/5] Synthesizing audio with Kokoro TTS...")
    from kokoro import KPipeline
    import numpy as np
    import soundfile as sf

    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipeline = KPipeline(lang_code='a', device=device)
    generator = pipeline(text, voice='af_heart', speed=1.0, split_pattern=r'\n+')

    audio_chunks = []
    for i, (gs, ps, audio) in enumerate(generator):
        if audio is not None:
            audio_chunks.append(audio)

    if not audio_chunks:
        raise ValueError("No audio synthesized.")

    final_audio = np.concatenate([a.cpu().numpy() if hasattr(a, "cpu") else np.asarray(a)
                                  for a in audio_chunks])
    output_speech_wav = "synthesized_speech.wav"
    sf.write(output_speech_wav, final_audio, 24000)
    return output_speech_wav


def _ffmpeg_subtitle_path(path):
    """Escape a path for use inside ffmpeg's subtitles/ass filter (Windows-safe)."""
    p = os.path.abspath(path).replace("\\", "/")
    p = p.replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")
    return p


def render_video(speech_file, music_file, srt_file, output_file, delay):
    print(f"[5/5] Rendering final video to {output_file}...")

    delay_ms = int(delay * 1000)
    subtitles = _ffmpeg_subtitle_path(srt_file)

    # mandelbrot is an infinite source; -shortest ends output when the (finite) audio ends.
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "mandelbrot=size=1920x1080:rate=30",
        "-i", speech_file,
        "-i", music_file,
        "-filter_complex",
        f"[1:a]adelay={delay_ms}:all=1[speech]; [speech][2:a]amix=inputs=2:duration=shortest[a]; "
        f"[0:v]subtitles='{subtitles}'[v]",
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

    try:
        # Step 1: Download audio
        audio_wav = download_audio(args.url)

        # Step 2: Diarize and transcribe
        srt_file, raw_text = extract_speech_and_srt(audio_wav, args.speaker)

        # Step 3: Polish script via DeepSeek
        polished_text = polish_script(raw_text)

        # Step 4: Synthesize TTS
        synthesized_speech = synthesize_audio(polished_text)

        # Step 5: Render video
        render_video(synthesized_speech, args.music, srt_file, args.output, args.delay)

        print(f"Done! Final video: {args.output}")

    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
