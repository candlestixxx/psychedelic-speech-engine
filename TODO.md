# TODO

## Done
- [x] Core pipeline (`app.py`)
- [x] Batch generator (`auto_run.py`) with 4:3 genre mix
- [x] BPM detection + time-stretch to target
- [x] Beat-synced Mandelbrot rendering
- [x] CUDA support (Pascal float32 fallback)
- [x] Time-range extraction (`--start`/`--end`)

## Next
- [ ] Beat-accurate zoom (use detected onset times instead of BPM-periodic pulse)
- [ ] Audio-reactive color (map amplitude to palette/rotation)
- [ ] DeepSeek retries / rate-limit handling
- [ ] Suno generation retry-on-captcha
- [ ] Web UI (Phase 3)
- [ ] Optional lyric/vocal mode
