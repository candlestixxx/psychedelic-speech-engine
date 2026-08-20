# MEMORY

## Architecture (v1.1.0)

- `app.py` — single-track speech→video pipeline (WhisperX → DeepSeek → Kokoro → FFmpeg).
- `auto_run.py` — batch generator: builds a 4:3 psytrance:other-genre plan,
  generates music via the Suno API, extracts speech ONCE, then renders one
  beat-synced video per track.
- `styles.py` — genre/style tag library (3 psytrance + 8 others + signature).
- `bpm_tools.py` — BPM detection (numpy/ffmpeg autocorrelation) + `atempo` stretch.
- `render_beat.py` — Mandelbrot + kick-synced zoom pulse + subtitles + audio mix.

## Data flow

- State passes via files (`.wav` / `.srt` / `.mp3` / `.mp4`), not in-memory buffers.
- The expensive speech pipeline (transcribe/diarize/polish/TTS) runs once per
  run and is reused across all music tracks.

## Environment

- Python 3.11 venv; torch 2.8.0+cu126 (GTX 1080 Ti, Pascal → float32 compute).
- Suno API: separate `suno-api` Node app on port 3010 (`SUNO_COOKIE` required).
- DeepSeek (`DEEPSEEK_API_KEY`) + HuggingFace (`HF_TOKEN`) in `.env`.

## Development preferences

- Robust CLI args; per-track error handling (batch continues on failure).
- Never commit `.env` or generated media (gitignored).
