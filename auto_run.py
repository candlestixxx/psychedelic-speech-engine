import os
import sys

# Force UTF-8 output (Windows console safety).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import time
import requests
import argparse
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Configurable: lets you point at a different Suno API docker/port without editing code.
SUNO_API_URL = os.environ.get("SUNO_API_URL", "http://localhost:3000/api/custom_generate")
SUNO_TIMEOUT = int(os.environ.get("SUNO_TIMEOUT", "300"))


def generate_suno_tracks(prompt_tags: str, title: str = "Goa Psytrance Track") -> list:
    """Generates music via the local Suno API and returns ALL generated track files."""
    print(f" [1/5] Requesting music generation from Suno API ({SUNO_API_URL})...")

    payload = {
        "prompt": "",
        "tags": prompt_tags,
        "title": title,
        "make_instrumental": True,
        "wait_audio": True,
    }

    try:
        response = requests.post(
            SUNO_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=SUNO_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            data = [data]

        downloaded_files = []
        for idx, track in enumerate(data):
            audio_url = track.get("audio_url")
            if audio_url:
                filename = f"suno_var_{idx + 1}_{int(time.time())}.mp3"
                print(f" [2/5] Variation {idx + 1} ready! Downloading track from {audio_url}...")
                with open(filename, "wb") as f:
                    f.write(requests.get(audio_url, timeout=SUNO_TIMEOUT).content)
                downloaded_files.append(filename)

        if not downloaded_files:
            raise ValueError("Suno API did not return any valid audio_urls.")

        return downloaded_files

    except requests.ConnectionError as e:
        print(f"❌ Could not reach the Suno API at {SUNO_API_URL}. "
              f"Is the Docker container running? (error: {e})")
        raise
    except Exception as e:
        print(f"❌ Failed to generate audio via Suno API: {e}")
        raise


def run_pipeline(youtube_url: str, music_path: str, speaker: str, output: str):
    """Triggers the core app.py execution pipeline."""
    print(f"⚡ [3/5] Starting speech extraction, re-voicing, and video rendering for {output}...")

    cmd = [
        sys.executable, "app.py",
        "--url", youtube_url,
        "--music", music_path,
        "--speaker", speaker,
        "--output", output,
    ]
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description="Fully Automated Psychedelic Video Generator")
    parser.add_argument("--url", required=True, help="YouTube speech URL")
    parser.add_argument("--speaker", default="SPEAKER_01", help="Target speaker ID")
    parser.add_argument("--output", default="final_master.mp4", help="Output MP4 filename")
    parser.add_argument(
        "--tags",
        default="psytrance, Goa trance, Ajja style, 145 bpm, rolling bassline, acid squelches, "
                "hypnotic tribal percussion, continuous groove, instrumental",
        help="Suno style tags",
    )

    args = parser.parse_args()

    try:
        # 1. Generate music and get all variations
        music_files = generate_suno_tracks(args.tags)

        # 2. Process each variation into its own video
        for idx, music_file in enumerate(music_files):
            output_filename = f"variation_{idx + 1}_{args.output}"
            print(f"\n▶️ Rendering variation {idx + 1} to {output_filename} using {music_file}...")

            try:
                run_pipeline(args.url, music_file, args.speaker, output_filename)
            except Exception as e:
                print(f"❌ Failed to render variation {idx + 1} ({output_filename}): {e}")
                print(f"⚠️ Proceeding to the next variation...")
                continue

        print(f"\n🎉 Batch workflow complete!")

    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
