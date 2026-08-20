# 🌀 Psychedelic Speech Engine

An automated pipeline that converts YouTube speech and interview clips into
spoken-word music videos set against **beat-synced Mandelbrot fractal
animations**, scored with AI-generated **psytrance** (and a rotating cast of
other electronic genres).

The system re-synthesizes the speaker's voice with local TTS — so the output
audio waveform is 100% freshly generated and won't trip Content ID — polishes
the script with an LLM, and generates a batch of instrumental tracks whose BPM
is detected and normalized to an exact target.

---

## ⚙️ How it works

1. **Audio extraction** — `yt-dlp` downloads the source audio (optionally only
   a `--start`/`--end` time range of the video).
2. **Transcription + diarization** — `WhisperX` + `pyannote.audio` transcribe
   the audio and isolate the target speaker (`SPEAKER_01`).
3. **Script polishing** — the `DeepSeek` API strips filler words and formats
   the speech into rhythmic spoken-word stanzas.
4. **Voice re-synthesis** — `Kokoro-82M` TTS re-voices the script locally.
5. **Music generation** — a self-hosted **Suno API** generates instrumental
   tracks from a genre/style library (see below).
6. **Beat-synced render** — `FFmpeg` renders the Mandelbrot fractal with a
   kick-triggered zoom pulse at the track's BPM, burns in subtitles, and mixes
   the re-voiced speech over the full-length track.

---

## 🎵 The "own sound" batch generator

`auto_run.py` is a batch music-video generator:

- **Primary genre — psytrance** (144–170 BPM), three sub-styles:
  - `fullon` (144–148) — Goa/full-on, rolling bass, acid squelches
  - `darkpsy` (148–160) — dark/forest, fast rolling bass
  - `hitech` (160–170) — rapid-fire, glitchy, intense
- **Every 4 psytrance tracks also generate 3 tracks** drawn randomly and
  distinctly from 8 additional genres: Tech House, Hard Techno, Drum & Bass,
  Dubstep, Hardstyle, Japanese Hardcore (J-Core), J-Techno-Synthpop, and
  Detroit House & Techno.
- Every track carries a **signature tag set** ("hypnotic spiritual journey,
  deep meditative groove…") so the channel keeps a consistent identity rather
  than copying any single artist.
- **BPM is detected then time-stretched** (`atempo`) to the exact target, so
  every track lands precisely in range (Suno's BPM is only approximate).

---

## 🛠️ Prerequisites

- **Python 3.11** (3.10 works; 3.14 is too new for `whisperx`)
- **FFmpeg** on PATH (used for BPM/resample + rendering)
- **Node.js 18+** (to run the Suno API locally — no Docker required)
- **Git**
- A CUDA GPU is optional; everything falls back to CPU. On Pascal cards
  (GTX 10-series) the pipeline auto-selects `float32` instead of `float16`.

---

## 🚀 Setup

### 1. Clone
```bash
git clone https://github.com/candlestixxx/psychedelic-speech-engine.git
cd psychedelic-speech-engine
```

### 2. Python environment
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
```
`requirements.txt` pins the exact set `whisperx 3.8.6` supports
(torch 2.8.0 + pyannote-audio 4.0.7). For a CUDA GPU, install the matching
CUDA build of torch/torchaudio/torchvision from the PyTorch index (cu126).

### 3. Configure `.env`
```bash
cp .env.example .env
```
| Key | Required? | Purpose |
|---|---|---|
| `DEEPSEEK_API_KEY` | yes | script polishing (DeepSeek) |
| `HF_TOKEN` | yes | speaker diarization (gated pyannote model) |
| `SUNO_API_URL` | yes (batch mode) | Suno API endpoint (default `http://localhost:3010/api/custom_generate`) |
| `GEMINI_API_KEY` | no | saved for future use; not used by this pipeline |

`HF_TOKEN` also requires accepting the terms on:
- https://huggingface.co/pyannote/speaker-diarization-community-1
- https://huggingface.co/pyannote/segmentation-3.0

### 4. Run the Suno API (separate service, port 3010)
```bash
git clone https://github.com/gcui-art/suno-api.git ../suno-api
cd ../suno-api
npm install
```
Create `../suno-api/.env` with your Suno session cookie:
```
SUNO_COOKIE=<full Cookie header from suno.com>
```
Start it on a free port:
```bash
npx next dev -p 3010
```
The cookie comes from browser devtools at suno.com (F12 → Network → find a
request containing `?__clerk_api_version` → copy the `Cookie` header).

---

## ▶️ Usage

### Batch generator (music + videos)
```bash
.venv\Scripts\python auto_run.py --url "YOUTUBE_URL" --count 8 --style random
```

| Flag | Default | Description |
|---|---|---|
| `--url` | (required) | YouTube speech URL |
| `--speaker` | `SPEAKER_01` | target speaker ID |
| `--count` | `4` | number of psytrance tracks |
| `--style` | `random` | `fullon` / `darkpsy` / `hitech` / `random` |
| `--bpm-min` / `--bpm-max` | `144` / `170` | psytrance BPM window |
| `--others-per-4` | `3` | other-genre tracks per 4 psytrance tracks |
| `--start` / `--end` | (none) | extract only a time range of the source |
| `--delay` | `0` | seconds before the speech starts |
| `--size` | `1920x1080` | video size (`1280x720` renders faster) |
| `--no-stretch` | off | skip BPM normalization |
| `--output` | `final_master` | output filename prefix |

Example — 4 darkpsy + 3 other-genre tracks, from a 10-minute slice:
```bash
.venv\Scripts\python auto_run.py --url "URL" --count 4 --style darkpsy \
  --start "00:05:00" --end "00:15:00" --size 1280x720
```

### Single track (your own music file, no Suno)
```bash
.venv\Scripts\python app.py --url "URL" --music "track.mp3" --speaker SPEAKER_01 \
  --start "00:01:00" --end "00:05:00" --output out.mp4
```

---

## 📝 Notes & caveats

- **First run downloads `large-v2` (~3 GB)** plus the diarization model into the
  HuggingFace cache (one-time).
- **Suno BPM is approximate** — `auto_run.py` detects and stretches each track
  to its target, so output always lands in range.
- **Suno CAPTCHA** — if generation fails with hCaptcha errors, add a paid
  `TWOCAPTCHA_KEY` to the Suno API `.env`.
- **Render time** — the 1080p Mandelbrot is CPU-rendered (a few minutes per
  track). Use `--size 1280x720` for faster previews.
- **Separation from other pipelines** — the Suno API runs on port 3010 in its
  own folder; this repo never touches other projects (e.g. Hymnmania).
