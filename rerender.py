"""Re-render the latest Leary video with the NEW visuals using the existing
music + cached speech (no new Suno generation)."""
import os
import random
import sys
import time

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from dotenv import load_dotenv
load_dotenv()

import app as engine
import bpm_tools
from render_beat import render_beat_video, find_base_images

URL = "https://www.youtube.com/watch?v=dpV-RHMgVCA"
MUSIC = "suno_psy_hitech_170bpm_1788475233.mp3"
TARGET_BPM = 170.0
NAME = "Timothy Leary"
SUB = "Merv Griffin Show · 1966 · on LSD"
CHANNEL = "PsySpeech Engine"
GENRE_LABEL = "hitech psytrance 170 BPM"

line_items = engine.load_speech_cache(URL, "orig")
assert line_items, "no cached speech"
print(f"loaded {len(line_items)} cached clips")

# BPM normalize the existing music
norm_file = f"rerender_norm_{int(time.time())}.mp3"
detected, _stretched = bpm_tools.normalize_bpm(MUSIC, norm_file, TARGET_BPM)
print(f"BPM: detected {detected:.1f} -> normalized {TARGET_BPM:.0f}")

# beat-synced rhythmic speech
speech_wav = f"rerender_speech_{int(time.time())}.wav"
speech_srt = speech_wav + ".srt"
engine.save_rhythmic_speech(line_items, TARGET_BPM, speech_wav,
                            engine.media_duration(norm_file))
print(f"rhythmic speech saved: {speech_wav}")

out_name = f"final_rerender_{int(time.time())}.mp4"
base_images = find_base_images("assets")
render_beat_video(
    speech_wav, norm_file, speech_srt, out_name,
    bpm=TARGET_BPM, delay=0.0, size="1920x1080",
    credit_name=NAME, credit_sub=SUB, channel_name=CHANNEL,
    genre_label=GENRE_LABEL,
    visual="layered", silhouette=None, base_images=base_images,
    base_seed=random.randrange(2**31),
)
print(f"rendered: {out_name}")

import youtube_upload
youtube_upload.upload_track(out_name, NAME, "hitech", TARGET_BPM, SUB, "unlisted")
print("DONE")
