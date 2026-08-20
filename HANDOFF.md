# SESSION HANDOFF

## Summary

- Built the psytrance batch generator (`auto_run.py` + `styles.py` +
  `bpm_tools.py` + `render_beat.py`).
- Stood up a separate Suno API (Node app on port 3010) decoupled from other
  pipelines (e.g. Hymnmania).
- Verified BPM detection, time-stretch, beat-synced rendering, and CUDA paths.
- Merged all fixes into `main`.

## Next steps

1. Paste the Suno cookie into `suno-api/.env` (`SUNO_COOKIE=`) to enable real
   music generation.
2. Run `auto_run.py --url "..." --count 8` for a full batch.
3. Watch for Suno hCaptcha — add `TWOCAPTCHA_KEY` if generation fails.

## Key facts

- Suno API runs on port **3010** (`npx next dev -p 3010` in `../suno-api`).
- Project venv at `.venv` (Python 3.11), torch 2.8.0+cu126 (GTX 1080 Ti).
- `HF_TOKEN` + `DEEPSEEK_API_KEY` are in the project `.env` (gitignored).
