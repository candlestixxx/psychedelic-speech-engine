# SESSION HANDOFF

## Summary

- Suno API configured, patched (`media_urls` m4a fix), and **verified** (port
  3010, account `resurrectingbeats`).
- YouTube download automatic via **Firefox cookies** (`--cookies-from-browser
  firefox`) + deno + web client; ffmpeg/ffprobe/deno fixed on PATH.
- Speaker auto-identification (`diarize_probe.py`, `dominant_speaker()`).
- Visual engine: `layered` mode (user art base + Mandelbrot glow + **beat
  flash**) plus `acid`/`mirror`/`kaleido`, credits, name watermark, silhouette.
- **Male voice** default (`am_onyx`) + **verbatim key quotes** + **rhythmic
  beat-synced speech** (lines snap to beats at the track BPM).
- YouTube upload (OAuth2) wired into `auto_run.py` / `batch_links.py`
  (`--upload`); verified posting to channel "PsySpeech Engine".
- `batch_links.py` + `links.csv` for multi-speaker automation.
- **First video is live (unlisted)**: https://youtu.be/_yt0ZOWksZQ
- All work committed + pushed through `e49c22f`.

## Status

- ✅ Suno live on 3010 (restart: `cd ../suno-api && npx next dev -p 3010`).
  ⚠️ Keep the local `extractAudioUrl` patch if re-cloning suno-api (see MEMORY).
- ✅ YouTube download automatic (Firefox cookies; keep YouTube logged in in Firefox).
- ✅ Hofmann = `SPEAKER_01` (see MEMORY.md).
- ✅ YouTube upload authorized (`youtube_token.json`), channel verified.

## Next steps

1. Review the test video, then run a full batch:
   `batch_links.py links.csv --count 8 --visual layered --upload --privacy unlisted`.
2. Watch Suno hCaptcha → add `TWOCAPTCHA_KEY` to `suno-api/.env`.
3. Optionally: silhouette override column in `links.csv`, or disable the
   silhouette ghost for a pure art+Mandelbrot look.

## Key facts

- Venv: `.venv` (uv-managed; `uv pip install --python .venv/Scripts/python.exe <pkg>`).
- GPU: GTX 1080 Ti → float32; whisper `batch_size=4`.
- Suno: 1 gen = 2 songs = 20 credits; only first `audio_url` used. ~9940 left.
- Voice default `am_onyx`; speaker names are manual (`SPEAKER_XX` is anonymous).
- `cookies.txt`, `youtube_token.json`, `assets/`, `.env` are gitignored.
- YouTube API quota: ~6 uploads/day default (1600 units each) — request a
  quota increase for bulk posting.
