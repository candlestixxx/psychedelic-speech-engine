import argparse
import os
import subprocess
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
    parser.add_argument("--delay", type=float, default=0.0, help="Delay for speech overlay")
    parser.add_argument("--output", default="final_master.mp4", help="Output MP4 filename")
    parser.add_argument("--video-filter", default="mandelbrot=size=1920x1080:rate=30", help="FFmpeg video filter string")
    parser.add_argument("--voice", default="af_heart", help="Kokoro TTS voice ID")
    parser.add_argument("--prompt-style", default="rhythmic spoken-word stanzas", help="Thematic instruction for the DeepSeek LLM (e.g. 'Alan Watts philosophical')")
    parser.add_argument("--subtitle-style", default="FontName=Arial,FontSize=24,PrimaryColour=&H00FFFF,Bold=1", help="FFmpeg force_style subtitle config")
    return parser.parse_args()

def download_audio(url, workspace_dir):
    output_wav = os.path.join(workspace_dir, "downloaded_audio.wav")
    print(f"Downloading audio from {url} to {output_wav}")
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "--output", output_wav,
        url
    ]
    subprocess.run(cmd, check=True)
    return output_wav

def extract_speech_and_srt(audio_file, target_speaker, workspace_dir):
    print("Transcribing and diarizing...")
    import whisperx
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN environment variable is missing.")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"

    model = whisperx.load_model("large-v2", device, compute_type=compute_type)
    audio = whisperx.load_audio(audio_file)
    result = model.transcribe(audio, batch_size=16 if device == "cuda" else 4)

    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

    diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)
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

    srt_filename = os.path.join(workspace_dir, "isolated_speech.srt")
    with open(srt_filename, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return srt_filename, raw_text

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")

def polish_script(raw_text, prompt_style):
    print(f"Polishing script with DeepSeek (Style: {prompt_style})...")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if not deepseek_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is missing.")

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {deepseek_key}",
        "Content-Type": "application/json"
    }

    prompt = f"Clean the following transcript, remove filler words, and format the speech into {prompt_style}. Output ONLY the polished text:\n\n{raw_text}"

    payload = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "You are a poetic assistant."},
            {"role": "user", "content": prompt}
        ]
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
    print(f"Synthesizing audio with Kokoro (Voice: {voice_id})...")
    from kokoro import KPipeline
    import soundfile as sf
    import numpy as np

    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipeline = KPipeline(lang_code='a', device=device)
    generator = pipeline(text, voice=voice_id, speed=1.0, split_pattern=r'\n+')

    audio_chunks = []
    for i, (gs, ps, audio) in enumerate(generator):
        if audio is not None:
            audio_chunks.append(audio)

    if not audio_chunks:
        raise ValueError("No audio synthesized.")

    final_audio = np.concatenate(audio_chunks)
    output_speech_wav = os.path.join(workspace_dir, "synthesized_speech.wav")
    sf.write(output_speech_wav, final_audio, 24000)
    return output_speech_wav

def render_video(speech_file, music_file, srt_file, output_file, delay, video_filter, subtitle_style):
    print(f"Rendering final video to {output_file}...")

    # Command to generate mandelbrot, add delayed speech and music, and burn subtitles
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", video_filter,
        "-i", speech_file,
        "-i", music_file,
        "-filter_complex",
        f"[1:a]adelay={int(delay*1000)}|{int(delay*1000)}[speech]; [speech][2:a]amix=inputs=2:duration=shortest[a]; [0:v]subtitles={srt_file}:force_style='{subtitle_style}'[v]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-shortest",
        output_file
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
        # Step 1: Download audio
        audio_wav = download_audio(args.url, workspace_dir)

        # Step 2: Diarize and Transcribe
        srt_file, raw_text = extract_speech_and_srt(audio_wav, args.speaker, workspace_dir)

        # Step 3: Polish Script via DeepSeek
        polished_text = polish_script(raw_text, args.prompt_style)

        # Step 4: Synthesize TTS
        synthesized_speech = synthesize_audio(polished_text, workspace_dir, args.voice)

        # Step 5: Render Video
        render_video(synthesized_speech, args.music, srt_file, args.output, args.delay, args.video_filter, args.subtitle_style)

    except Exception as e:
        print(f"Error during execution: {e}")
        exit(1)

if __name__ == "__main__":
    main()
