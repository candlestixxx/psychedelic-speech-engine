"""Auto-generate a transparent silhouette of a speaker from their YouTube video.

Downloads the video thumbnail and runs rembg (AI background removal) to produce
a transparent PNG of the person, which the renderer can layer into the video.
"""
import os
import re
import subprocess


def extract_video_id(url):
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def fetch_silhouette(url, out_dir, min_bytes=4000):
    """Return a path to a transparent PNG of the speaker, or None if it fails."""
    vid = extract_video_id(url)
    if not vid:
        print("    [silhouette] could not parse video id, skipping")
        return None

    out = os.path.join(out_dir, "speaker_silhouette.png")
    if os.path.exists(out):
        return out

    for quality in ("hqdefault", "mqdefault"):
        thumb = os.path.join(out_dir, f"thumb_{quality}.jpg")
        src = f"https://img.youtube.com/vi/{vid}/{quality}.jpg"
        subprocess.run(["curl", "-s", "-L", "-o", thumb, src], check=False)
        if not (os.path.exists(thumb) and os.path.getsize(thumb) > min_bytes):
            continue
        try:
            from rembg import remove
            from PIL import Image
            img = Image.open(thumb).convert("RGBA")
            remove(img).save(out)
            print(f"    [silhouette] generated from {quality} thumbnail -> {out}")
            return out
        except Exception as e:
            print(f"    [silhouette] failed ({e}); trying next thumbnail")

    print("    [silhouette] no usable thumbnail, skipping")
    return None
