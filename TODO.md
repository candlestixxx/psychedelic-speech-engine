# TODO

## Done
- [x] Core pipeline (`app.py`)
- [x] Batch generator (`auto_run.py`) with 4:3 genre mix
- [x] BPM detection + time-stretch to target
- [x] Beat-synced Mandelbrot rendering
- [x] CUDA support (Pascal float32 fallback; whisper batch_size=4)
- [x] Time-range extraction (`--start`/`--end`)
- [x] Suno API configured + verified (port 3010, 10000 credits)
- [x] Suno media_urls patch (audio_url was "forbidden")
- [x] YouTube download unblocked (Firefox cookies auto-read + deno + web client)
- [x] Speaker auto-identification (`diarize_probe.py`, `dominant_speaker`)
- [x] Visual styles (`default`/`acid`/`mirror`/`kaleido`/`layered`)
- [x] Layered mode with user art base + Mandelbrot glow, per-track cycling
- [x] Beat-flash visuals (eq brightness pulse on kick) + stronger zoom pulse
- [x] Speaker credits (title card + source line + name watermark)
- [x] Speaker silhouette from thumbnail (rembg)
- [x] Multi-speaker batch driver (`batch_links.py` + `links.csv`)
- [x] YouTube OAuth2 upload (`youtube_auth.py`, `youtube_upload.py`, `--upload`)
- [x] Male voice default (`am_onyx`)
- [x] Verbatim key-quote extraction (DeepSeek)
- [x] Rhythmic beat-synced speech (`synthesize_lines` + `build_rhythmic_speech`)
- [x] End-to-end smoke test posted to YouTube (unlisted)

## Next
- [ ] Beat-accurate zoom (use detected onset times instead of BPM-periodic pulse)
- [ ] Audio-reactive color (map amplitude to palette/rotation)
- [ ] DeepSeek retries / rate-limit handling
- [ ] Suno generation retry-on-captcha (TWOCAPTCHA_KEY)
- [ ] Web UI (Phase 3)
- [ ] Optional lyric/vocal mode
- [ ] Manual silhouette override (`--silhouette` / `links.csv` column)
- [ ] Disable rembg silhouette ghost when the art already contains the silhouette
