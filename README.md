# Psychedelic Speech Engine

A Python pipeline that turns speech and written text into beat-synced
psychedelic music videos: text-to-speech voice-over layered over music,
with audio-reactive visuals rendered via FFmpeg shaders.

## Status

**Paused.** Version 1.6.0. Last feature work landed 2026-09-15
(BPM-synced visual shaders, v1.6.0); the most recent commit is
2026-09-16 (a `.gitignore` tweak). No activity in the ~2 months since.

## What's built

Per the codebase and commit history:

- **TTS voice-over:** `--text-file` mode synthesizes writings and quotes
  as narration. Includes quote files from psychedelic researchers and
  writers (Carhart-Harris, Griffiths, Hofmann, Huxley, Leary, McKenna).
- **Beat-synced visuals:** a 3-layer stack — MilkDrop plasma base,
  kaleidoscope geometric layer, semi-transparent Mandelbrot — each synced
  to detected BPM. Dynamic BPM detection locked to the visual shaders in
  v1.6.0.
- **Rendering:** `render_beat.py` / `app.py` drive FFmpeg shader
  rendering; `rerender.py` re-renders existing work; `silhouette.py`
  and `styles.py` support the visual pipeline.
- **Batching & automation:** `auto_run.py`, `batch_links.py`,
  `diarize_probe.py` for batch runs and speaker diarization probes.
- **YouTube:** `youtube_upload.py` / `youtube_auth.py` for uploading
  finished videos.
- **Deployment:** `Dockerfile` and `docker-compose.yml` exist in-repo.

## What's not verified

- No output videos, demo links, or published results are in the repo, so
  the end-to-end render quality is unverified from here.
- No live service or deployment is documented.
- API keys / credentials needed (see `.env.example`) are not part of
  the repo.

## Quick Start

See `DEPLOY.md` and `.env.example` in the repo for configuration.
Dependencies are listed in `requirements.txt`.

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in required keys
python app.py --help
```

## Links

- Repo: https://github.com/candlestixxx/psychedelic-speech-engine
- Related docs in-repo: `CHANGELOG.md`, `ROADMAP.md`, `TODO.md`,
  `DEPLOY.md`, `HANDOFF.md`, `VISION.md`, `content_sources.md`,
  `speakers.md`
