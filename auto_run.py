import argparse
import os
import random
import sys
import time

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import requests
from dotenv import load_dotenv

load_dotenv()

import app as engine
import bpm_tools
import styles
from render_beat import render_beat_video, find_base_images
import silhouette

SUNO_API_URL = os.environ.get("SUNO_API_URL", "http://localhost:3010/api/custom_generate")
SUNO_TIMEOUT = int(os.environ.get("SUNO_TIMEOUT", "600"))


def _cap_tags(tags, limit=200):
    """Truncate a Suno style string to `limit` chars at a comma boundary."""
    tags = tags.strip()
    if len(tags) <= limit:
        return tags
    cut = tags[:limit].rfind(",")
    return tags[:cut].rstrip() if cut > 0 else tags[:limit].rstrip()


def build_track_spec(kind, genre_key=None, style_key=None, bpm_min=144.0, bpm_max=170.0):
    """Build one track spec: {kind, genre, bpm (target), tags, title}."""
    if kind == "psytrance":
        if not style_key or style_key == "random":
            style_key = random.choice(list(styles.PSYTRANCE_STYLES.keys()))
        st = styles.PSYTRANCE_STYLES[style_key]
        lo = max(bpm_min, st["bpm"][0])
        hi = min(bpm_max, st["bpm"][1])
        if hi < lo:
            hi = lo
        bpm = random.uniform(lo, hi)
        tags = _cap_tags(f"{styles.SIGNATURE_TAGS}, {st['tags']}, {int(round(bpm))} BPM")
        title = f"psy_{style_key}_{int(round(bpm))}bpm"
        return {"kind": "psytrance", "genre": style_key, "bpm": bpm, "tags": tags, "title": title}

    g = styles.OTHER_GENRES[genre_key]
    bpm = random.uniform(g["bpm"][0], g["bpm"][1])
    tags = _cap_tags(f"{styles.SIGNATURE_TAGS}, {g['tags']}, {int(round(bpm))} BPM")
    title = f"{genre_key}_{int(round(bpm))}bpm"
    return {"kind": "other", "genre": genre_key, "bpm": bpm, "tags": tags, "title": title}


def build_track_plan(count, style, bpm_min, bpm_max, others_per_4):
    """4 psytrance -> N other-genre tracks, repeating. Others are distinct per cycle."""
    plan = []
    other_keys = list(styles.OTHER_GENRES.keys())
    for i in range(count):
        plan.append(build_track_spec("psytrance", style_key=style,
                                     bpm_min=bpm_min, bpm_max=bpm_max))
        if (i + 1) % 4 == 0:
            k = min(others_per_4, len(other_keys))
            for g in random.sample(other_keys, k):
                plan.append(build_track_spec("other", genre_key=g))
    return plan


def generate_suno_track(spec):
    """Generate one instrumental track via the Suno API and download its mp3."""
    payload = {
        "prompt": "",
        "tags": spec["tags"],
        "title": spec["title"],
        "make_instrumental": True,
        "wait_audio": True,
        "negative_tags": styles.NEGATIVE_TAGS,
    }
    try:
        resp = requests.post(SUNO_API_URL, json=payload,
                             headers={"Content-Type": "application/json"},
                             timeout=SUNO_TIMEOUT)
    except requests.ConnectionError:
        raise RuntimeError(
            f"Cannot reach Suno API at {SUNO_API_URL}. Is it running? "
            "(Start suno-api with a valid SUNO_COOKIE, then set SUNO_API_URL in .env.)"
        )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"Suno API error: {data['error']}")
    if not isinstance(data, list):
        data = [data]
    for track in data:
        url = track.get("audio_url")
        if url:
            # Suno now serves m4a via media_urls; keep the real extension.
            ext = os.path.splitext(url.split("?")[0])[1] or ".mp3"
            filename = f"suno_{spec['title']}_{int(time.time())}{ext}"
            with open(filename, "wb") as f:
                f.write(requests.get(url, timeout=SUNO_TIMEOUT).content)
            return filename
    raise RuntimeError("Suno returned no audio_url")


def extract_speech_once(url, speaker, start, end, workspace_dir, voice, prompt_style):
    """Run the expensive speech pipeline exactly once; reused for all tracks."""
    print("\n=== [SPEECH] Extracting voice (once, reused for all tracks) ===")
    audio_wav = engine.download_audio(url, workspace_dir, start, end)
    srt_file, raw_text = engine.extract_speech_and_srt(audio_wav, speaker, workspace_dir)
    polished = engine.polish_script(raw_text, prompt_style)
    speech_wav = engine.synthesize_audio(polished, workspace_dir, voice)
    return speech_wav, srt_file


def main():
    p = argparse.ArgumentParser(description="Psychedelic Speech Engine - batch music video generator")
    p.add_argument("--url", required=True, help="YouTube speech URL")
    p.add_argument("--speaker", default="SPEAKER_01", help="Target speaker ID")
    p.add_argument("--output", default="final_master", help="Output filename prefix (no extension)")
    p.add_argument("--count", type=int, default=4, help="Number of PSYTRANCE tracks")
    p.add_argument("--style", choices=["fullon", "darkpsy", "hitech", "random"], default="random",
                   help="Psytrance sub-style (random picks per track)")
    p.add_argument("--bpm-min", type=float, default=144.0, help="Psytrance BPM lower bound")
    p.add_argument("--bpm-max", type=float, default=170.0, help="Psytrance BPM upper bound")
    p.add_argument("--others-per-4", type=int, default=3,
                   help="Other-genre tracks generated per every 4 psytrance tracks")
    p.add_argument("--start", default=None, help="Extract YouTube audio from this timestamp")
    p.add_argument("--end", default=None, help="Extract YouTube audio up to this timestamp")
    p.add_argument("--delay", type=float, default=0.0, help="Delay before speech starts (seconds)")
    p.add_argument("--no-stretch", action="store_true", help="Skip BPM time-stretch normalization")
    p.add_argument("--size", default="1920x1080", help="Video size (e.g. 1280x720 for faster renders)")
    p.add_argument("--voice", default="af_heart", help="Kokoro TTS voice ID")
    p.add_argument("--prompt-style", default="rhythmic spoken-word stanzas", help="Thematic instruction for the DeepSeek LLM (e.g. 'Alan Watts philosophical')")
    p.add_argument("--credit-name", default=None, help="Speaker name to show in a fading title card (e.g. 'Dr. Albert Hofmann')")
    p.add_argument("--credit-sub", default=None, help="Persistent source/credit line (e.g. 'Interview excerpt - AI re-voicing')")
    p.add_argument("--visual", choices=["default", "acid", "mirror", "kaleido", "layered"], default="default",
                   help="Visual style layer (acid = hue cycling, mirror/kaleido = kaleidoscope, layered = psychedelic base + Mandelbrot)")
    p.add_argument("--upload", action="store_true", help="Upload rendered videos to the authorized YouTube channel")
    p.add_argument("--privacy", choices=["private", "unlisted", "public"], default="unlisted")
    args = p.parse_args()

    # Create isolated workspace directory for this execution
    workspace_dir = f"workspace_run_{int(time.time())}"
    os.makedirs(workspace_dir, exist_ok=True)
    print(f"📁 Created isolated workspace: {workspace_dir}")

    if args.bpm_max < args.bpm_min:
        args.bpm_min, args.bpm_max = args.bpm_max, args.bpm_min

    plan = build_track_plan(args.count, args.style, args.bpm_min, args.bpm_max, args.others_per_4)

    print("\n=== Track plan ===")
    for i, spec in enumerate(plan, 1):
        print(f"  {i:2d}. [{spec['kind']:9s}] {spec['genre']:22s} target {spec['bpm']:.0f} BPM")
    print(f"Total tracks: {len(plan)}")

    # Extract speech FIRST: the YouTube download is cookie-sensitive, so do it
    # immediately (before Suno's slow generation) to avoid cookie rotation.
    try:
        speech_wav, srt_file = extract_speech_once(args.url, args.speaker, args.start, args.end, workspace_dir, args.voice, args.prompt_style)
    except Exception as e:
        print(f"Speech extraction failed: {e}")
        sys.exit(1)

    sil = silhouette.fetch_silhouette(args.url, workspace_dir)
    base_images = find_base_images(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"))

    print("\n=== [MUSIC] Generating tracks via Suno ===")
    tracks = []
    for i, spec in enumerate(plan, 1):
        print(f"[{i}/{len(plan)}] {spec['title']} ...")
        try:
            fn = generate_suno_track(spec)
            tracks.append((spec, fn))
            print(f"        -> {fn}")
        except Exception as e:
            print(f"        FAILED: {e}  (continuing)")
        time.sleep(1)

    if not tracks:
        print("No tracks were generated. Aborting.")
        sys.exit(1)

    print("\n=== [RENDER] Normalizing BPM + rendering beat-synced videos ===")
    for idx, (spec, music_file) in enumerate(tracks, 1):
        out_name = f"{args.output}_{idx:02d}_{spec['genre']}_{int(round(spec['bpm']))}bpm.mp4"
        try:
            norm_file = music_file
            bpm = spec["bpm"]
            if args.no_stretch:
                bpm = bpm_tools.detect_bpm(music_file, hint=spec["bpm"])
                print(f"[{idx}/{len(tracks)}] {spec['title']}: using detected {bpm:.1f} BPM (no stretch)")
            else:
                norm_file = f"norm_{spec['title']}.mp3"
                detected, _stretched = bpm_tools.normalize_bpm(music_file, norm_file, spec["bpm"])
                print(f"[{idx}/{len(tracks)}] {spec['title']}: detected {detected:.1f} -> stretched to {bpm:.0f} BPM")
            render_beat_video(speech_wav, norm_file, srt_file, out_name, bpm=bpm,
                              delay=args.delay, size=args.size,
                              credit_name=args.credit_name, credit_sub=args.credit_sub,
                              visual=args.visual, silhouette=sil, base_images=base_images,
                              base_seed=idx)
            print(f"        -> {out_name}")
            if args.upload:
                import youtube_upload
                youtube_upload.upload_track(out_name, args.credit_name or "Speaker", spec["genre"],
                                            spec["bpm"], args.credit_sub or "", args.privacy)
        except Exception as e:
            print(f"        RENDER FAILED: {e}")

    print("\n=== Done ===")
    print(f"Rendered {len(tracks)} video(s). Files are named: {args.output}_*")


if __name__ == "__main__":
    main()
