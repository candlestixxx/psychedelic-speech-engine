"""Identify speakers in a YouTube video without generating any music.

Downloads a (optionally time-bounded) slice of the audio, transcribes with
WhisperX, diarizes with pyannote, and prints every speaker's total speaking
time, segment count, and sample lines — so you can figure out which
`SPEAKER_XX` is your target before running a full (paid) batch.

Usage:
    python diarize_probe.py --url "https://..." [--start 0:00] [--end 10:00]
"""
import argparse
import os
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import torch
from dotenv import load_dotenv

load_dotenv()

import app as engine


def main():
    p = argparse.ArgumentParser(description="Identify speakers in a YouTube video (no music gen).")
    p.add_argument("--url", required=True)
    p.add_argument("--start", default=None)
    p.add_argument("--end", default=None)
    p.add_argument("--model", default="large-v2")
    args = p.parse_args()

    workspace = f"probe_{int(__import__('time').time())}"
    os.makedirs(workspace, exist_ok=True)

    print("=== [1/3] Downloading audio slice ===")
    wav = engine.download_audio(args.url, workspace, args.start, args.end)

    print("=== [2/3] Transcribe + diarize ===")
    import whisperx
    from whisperx.diarize import DiarizationPipeline

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise SystemExit("HF_TOKEN is missing (needed for pyannote diarization).")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        major, _ = torch.cuda.get_device_capability(0)
        compute_type = "float16" if major >= 7 else "float32"
    else:
        compute_type = "int8"
    print(f"    device={device}, compute_type={compute_type}")

    model = whisperx.load_model(args.model, device, compute_type=compute_type)
    audio = whisperx.load_audio(wav)
    result = model.transcribe(audio, batch_size=4)
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
    diarize = DiarizationPipeline(token=hf_token, device=device)
    result = whisperx.assign_word_speakers(diarize(audio), result)

    print("\n=== [3/3] Speaker summary ===")
    from collections import defaultdict
    stats = defaultdict(lambda: {"secs": 0.0, "count": 0, "samples": []})
    for seg in result["segments"]:
        spk = seg.get("speaker", "UNKNOWN")
        stats[spk]["secs"] += seg["end"] - seg["start"]
        stats[spk]["count"] += 1
        if len(stats[spk]["samples"]) < 3:
            stats[spk]["samples"].append(seg["text"].strip())

    for spk in sorted(stats, key=lambda s: -stats[s]["secs"]):
        st = stats[spk]
        print(f"\n--- {spk}: {st['secs']:.0f}s across {st['count']} segments ---")
        for s in st["samples"]:
            print(f"    \"{s[:140]}\"")


if __name__ == "__main__":
    main()
