"""Batch driver: process a list of speakers from a CSV manifest.

CSV columns (header required):
  url          - YouTube URL (required)
  speaker_name - name for the title card (e.g. "Dr. Albert Hofmann")
  credit_line  - source attribution line (e.g. "High Times interview 1994")
  speaker      - target diarization ID, or "auto" (pick the most-talking speaker)
  style        - psytrance sub-style override (fullon/darkpsy/hitech/random)

Example links.csv:
  url,speaker_name,credit_line,speaker,style
  https://youtu.be/...,Dr. Albert Hofmann,High Times interview 1994,,random

Usage:
  python batch_links.py links.csv --count 4 --visual acid
"""
import argparse
import csv
import os
import re
import sys
import time

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from dotenv import load_dotenv
load_dotenv()

import app as engine
import auto_run as ar
import bpm_tools
from render_beat import render_beat_video, find_base_images
import silhouette


def slugify(text):
    s = re.sub(r"[^A-Za-z0-9]+", "_", (text or "").strip()).strip("_").lower()
    return s or "speaker"


def process_speaker(row, out_root, args, idx, total):
    url = (row.get("url") or "").strip()
    if not url:
        print(f"[{idx}/{total}] SKIP (no url)")
        return
    name = (row.get("speaker_name") or "").strip() or "speaker"
    credit_line = (row.get("credit_line") or "").strip()
    target = (row.get("speaker") or "").strip() or "auto"
    style = (row.get("style") or "").strip() or args.style

    ws = os.path.join(out_root, f"{slugify(name)}_{int(time.time())}")
    os.makedirs(ws, exist_ok=True)
    print(f"\n{'=' * 70}\n[{idx}/{total}] SPEAKER: {name}\n  url={url}\n  speaker={target}\n{'=' * 70}")

    try:
        sil = None  # silhouette ghost disabled (art already contains the speaker)
        base_images = find_base_images(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"))
        audio = engine.download_audio(url, ws, args.start, args.end)
        result = engine.transcribe_and_diarize(audio)
        stats = engine.speaker_stats(result)
        print("  Speaker breakdown:")
        for spk in sorted(stats, key=lambda s: -stats[s]["secs"]):
            print(f"    {spk}: {stats[spk]['secs']:.0f}s / {stats[spk]['count']} segments")
        if target == "auto":
            target = engine.dominant_speaker(result)
            print(f"  auto-selected dominant speaker: {target}")
        if target is None:
            raise RuntimeError("No speakers detected")

        srt_file, raw_text = engine.build_srt_and_text(result, target, ws)
        if not raw_text.strip():
            raise RuntimeError(f"No speech text for speaker {target}")

        polished = engine.polish_script(raw_text, args.prompt_style)
        line_audios = engine.synthesize_lines(polished, args.voice)
        if not line_audios:
            raise RuntimeError("No speech lines were synthesized.")

        plan = ar.build_track_plan(args.count, style, args.bpm_min, args.bpm_max, args.others_per_4)
        print(f"  Track plan ({len(plan)} tracks):")
        for i, spec in enumerate(plan, 1):
            print(f"    {i:2d}. [{spec['kind']}] {spec['genre']} ~{spec['bpm']:.0f} BPM")

        tracks = []
        for i, spec in enumerate(plan, 1):
            try:
                fn = ar.generate_suno_track(spec)
                tracks.append((spec, fn))
                print(f"    [{i}/{len(plan)}] {spec['title']} -> {fn}")
            except Exception as e:
                print(f"    [{i}/{len(plan)}] FAILED: {e}")
            time.sleep(1)

        for j, (spec, music_file) in enumerate(tracks, 1):
            out_name = os.path.join(
                ws, f"{slugify(name)}_{j:02d}_{spec['genre']}_{int(round(spec['bpm']))}bpm.mp4"
            )
            try:
                norm_file = music_file
                bpm = spec["bpm"]
                if args.no_stretch:
                    bpm = bpm_tools.detect_bpm(music_file, hint=spec["bpm"])
                else:
                    norm_file = os.path.join(ws, f"norm_{spec['title']}.mp3")
                    detected, _ = bpm_tools.normalize_bpm(music_file, norm_file, spec["bpm"])
                    print(f"    render {j}: detected {detected:.1f} -> {bpm:.0f} BPM")
                speech_wav, speech_srt = engine.save_rhythmic_speech(line_audios, bpm, os.path.join(ws, f"rhythmic_{j}.wav"),
                                                        engine.media_duration(norm_file))
                render_beat_video(speech_wav, norm_file, speech_srt, out_name, bpm=bpm,
                                  delay=args.delay, size=args.size,
                                  credit_name=name, credit_sub=credit_line,
                                  channel_name="PsySpeech Engine",
                                  genre_label=f"{spec['genre']} {int(round(spec['bpm']))} BPM",
                                  visual=args.visual, silhouette=sil, base_images=base_images,
                                  base_seed=j)
                print(f"    -> {out_name}")
                if args.upload:
                    import youtube_upload
                    youtube_upload.upload_track(out_name, name, spec["genre"], spec["bpm"],
                                                credit_line, args.privacy)
            except Exception as e:
                print(f"    RENDER FAILED: {e}")

        print(f"  DONE {name}: {len(tracks)} track(s)")
    except Exception as e:
        print(f"  ERROR for {name}: {e}  (continuing)")


def main():
    p = argparse.ArgumentParser(description="Batch-process a CSV list of speakers.")
    p.add_argument("manifest", help="Path to links.csv (columns: url, speaker_name, credit_line, speaker, style)")
    p.add_argument("--output", default="batch_output", help="Output root folder")
    p.add_argument("--count", type=int, default=4, help="Psytrance tracks per speaker")
    p.add_argument("--style", choices=["fullon", "darkpsy", "hitech", "random"], default="random")
    p.add_argument("--bpm-min", type=float, default=144.0)
    p.add_argument("--bpm-max", type=float, default=170.0)
    p.add_argument("--others-per-4", type=int, default=3)
    p.add_argument("--start", default=None)
    p.add_argument("--end", default=None)
    p.add_argument("--delay", type=float, default=0.0)
    p.add_argument("--no-stretch", action="store_true")
    p.add_argument("--size", default="1920x1080")
    p.add_argument("--voice", default="am_onyx", help="Kokoro TTS voice ID (am_* = male, af_* = female)")
    p.add_argument("--prompt-style", default="rhythmic spoken-word stanzas")
    p.add_argument("--visual", choices=["default", "acid", "mirror", "kaleido", "layered"], default="default")
    p.add_argument("--upload", action="store_true", help="Upload rendered videos to the authorized YouTube channel")
    p.add_argument("--privacy", choices=["private", "unlisted", "public"], default="unlisted")
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)
    with open(args.manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} speaker(s) from {args.manifest}")
    for i, row in enumerate(rows, 1):
        process_speaker(row, args.output, args, i, len(rows))
    print("\n=== Batch complete ===")


if __name__ == "__main__":
    main()
