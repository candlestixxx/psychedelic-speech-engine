# SESSION HANDOFF

## Summary

- Suno API configured and **verified** (port 3010, 10000 monthly credits,
  account `resurrectingbeats`).
- YouTube download unblocked: `cookies.txt` (extension) + deno + web client;
  ffmpeg/ffprobe/deno fixed on PATH.
- Speaker auto-identification (`diarize_probe.py`, `dominant_speaker()`).
- Visual engine: `layered` psychedelic mode (user art base + Mandelbrot glow),
  plus `acid`/`mirror`/`kaleido`, credits, name watermark, and silhouette ghost.
- `batch_links.py` + `links.csv` for multi-speaker automation.
- All work committed + pushed through commit `2c07717`.

## Status

- ✅ Suno API live on 3010 (restart: `cd ../suno-api && npx next dev -p 3010`).
- ✅ YouTube download works (needs `cookies.txt`; re-export on rotation).
- ✅ Hofmann = `SPEAKER_01` (see MEMORY.md).
- ✅ Visual styles render-tested: default / acid / mirror / kaleido / layered
  + image base + silhouette.

## Next steps

1. Run the smoke test (1 track) then a full batch:
   `batch_links.py links.csv --visual layered`.
2. Watch for Suno hCaptcha → add `TWOCAPTCHA_KEY` to `suno-api/.env`.
3. Re-export `cookies.txt` (one click in the extension) when YouTube rotates.
4. Optional: disable the rembg silhouette ghost (the art already contains the
   silhouette) — one-line change in `render_beat.py` if a pure art+Mandelbrot
   look is preferred.
5. Optional: add a `silhouette` override column to `links.csv` / `--silhouette`
   flag for manual transparent PNGs.

## Key facts

- Venv: `.venv` (uv-managed; use `uv pip install --python .venv/Scripts/python.exe <pkg>`).
- GPU: GTX 1080 Ti → float32; whisper `batch_size=4`.
- Suno: 1 gen = 2 songs = 10 credits; only first `audio_url` is used.
- Speaker names are manual (diarization is anonymous `SPEAKER_XX`).
- `cookies.txt` and `assets/` are gitignored (secrets / local media).
