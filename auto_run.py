import os
import time
import requests
import argparse
import subprocess
from dotenv import load_dotenv

load_dotenv()

SUNO_API_URL = "http://localhost:3000/api/custom_generate"

def generate_suno_tracks(prompt_tags: str, title: str = "Goa Psytrance Track") -> list:
    """Generates music via local Suno API and returns ALL generated track files."""
    print(" [1/5] Requesting music generation from local Suno Docker API...")

    payload = {
        "prompt": "",
        "tags": prompt_tags,
        "title": title,
        "make_instrumental": True,
        "wait_audio": True
    }

    try:
        response = requests.post(SUNO_API_URL, json=payload, headers={"Content-Type": "application/json"}, timeout=120)
        response.raise_for_status()
        data = response.json()

        # In case the API doesn't return a list, make it one
        if not isinstance(data, list):
            data = [data]

        downloaded_files = []
        # Loop over all variations returned by Suno
        for idx, track in enumerate(data):
            audio_url = track.get("audio_url")
            if audio_url:
                filename = f"suno_var_{idx + 1}_{int(time.time())}.mp3"
                print(f" [2/5] Variation {idx + 1} ready! Downloading track from {audio_url}...")
                with open(filename, "wb") as f:
                    f.write(requests.get(audio_url).content)
                downloaded_files.append(filename)

        if not downloaded_files:
             raise ValueError("Suno API did not return any valid audio_urls.")

        return downloaded_files

    except Exception as e:
        print(f"❌ Failed to generate audio via local Suno API: {e}")
        raise

def run_pipeline(youtube_url: str, music_path: str, speaker: str, output: str, video_filter: str, voice: str, prompt_style: str, subtitle_style: str):
    """Triggers the core app.py execution pipeline."""
    print(f"⚡ [3/5] Starting speech extraction, re-voicing, and video rendering for {output}...")

    cmd = [
        "python", "app.py",
        "--url", youtube_url,
        "--music", music_path,
        "--speaker", speaker,
        "--output", output,
        "--video-filter", video_filter,
        "--voice", voice,
        "--prompt-style", prompt_style,
        "--subtitle-style", subtitle_style
    ]
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(description="Fully Automated Psychedelic Video Generator")
    parser.add_argument("--url", required=True, help="YouTube speech URL")
    parser.add_argument("--speaker", default="SPEAKER_01", help="Target speaker ID")
    parser.add_argument("--output", default="final_master.mp4", help="Output MP4 filename")
    parser.add_argument(
        "--tags",
        default="psytrance, Goa trance, Ajja style, 145 bpm, rolling bassline, acid squelches, hypnotic tribal percussion, continuous groove, instrumental",
        help="Suno style tags"
    )
    parser.add_argument("--video-filter", default="mandelbrot=size=1920x1080:rate=30", help="FFmpeg video filter string")
    parser.add_argument("--voice", default="af_heart", help="Kokoro TTS voice ID")
    parser.add_argument("--prompt-style", default="rhythmic spoken-word stanzas", help="Thematic instruction for the DeepSeek LLM (e.g. 'Alan Watts philosophical')")
    parser.add_argument("--subtitle-style", default="FontName=Arial,FontSize=24,PrimaryColour=&H00FFFF,Bold=1", help="FFmpeg force_style subtitle config")

    args = parser.parse_args()

    try:
        # 1. Generate music and gets all variations
        music_files = generate_suno_tracks(args.tags)

        # 2. Process each variation into its own video
        for idx, music_file in enumerate(music_files):
            output_filename = f"variation_{idx + 1}_{args.output}"
            print(f"\n▶️ Rendering variation {idx + 1} to {output_filename} using {music_file}...")

            try:
                run_pipeline(args.url, music_file, args.speaker, output_filename, args.video_filter, args.voice, args.prompt_style, args.subtitle_style)
            except Exception as e:
                print(f"❌ Failed to render variation {idx + 1} ({output_filename}): {e}")
                print(f"⚠️ Proceeding to the next variation...")
                continue # Catch rendering errors to ensure the script continues to the next variation.

        print(f"\n🎉 Batch workflow complete!")

    except Exception as e:
        print(f"Error during execution: {e}")
        exit(1)

if __name__ == "__main__":
    main()
