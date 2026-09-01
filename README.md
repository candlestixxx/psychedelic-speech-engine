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
3. **Key-quote extraction** — the `DeepSeek` API pulls the speaker's most
   quotable moments **verbatim** (removing only fillers), one thought per line.
4. **Voice re-synthesis** — `Kokoro-82M` TTS re-voices each line in a male
   voice (`am_onyx`), then places each line **on a beat** (rhythmic sync).
5. **Music generation** — a self-hosted **Suno API** generates instrumental
   tracks from a genre/style library (see below).
6. **Beat-synced render** — `FFmpeg` renders a multi-layer psychedelic scene:
   a base layer (procedural fractal/automaton or your art in `assets/`) plus
   the Mandelbrot glowing on top, all pulsing to the track's BPM. Subtitles,
   speaker credits, and an optional speaker silhouette are burned in, and the
   re-voiced speech is mixed over the full-length track.

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

## 🎨 Visual styles, credits & silhouette

`render_beat.py` supports `--visual` modes:
- `default` — plain Mandelbrot + beat pulse.
- `acid` — hue-cycling Mandelbrot.
- `mirror` / `kaleido` — kaleidoscopic mirroring (and hue).
- `layered` — a psychedelic base layer + the Mandelbrot glowing on top (screen
  blend). The base is randomized per video from procedural generators, **or**
  uses your art images placed in `assets/` (cycled per track).

Speaker attribution is burned in automatically: a title card with the speaker's
name (first ~5 s), a persistent source line at the bottom, and a periodic name
watermark inside the art. `silhouette.py` auto-generates a transparent speaker
cutout from the YouTube thumbnail (via `rembg`) and ghosts it into the video.

## 🔍 Multi-speaker batch

Drop a list of speakers into `links.csv`:
```csv
url,speaker_name,credit_line,speaker,style
https://www.youtube.com/watch?v=...,Dr. Albert Hofmann,High Times interview 1994 (Peter Gorman) · AI re-voicing,,random
```
Then run:
```bash
.venv\Scripts\python batch_links.py links.csv --count 4 --visual layered
```
Leave `speaker` blank to auto-pick whoever talks the most. To identify speakers
without spending Suno credits:
```bash
.venv\Scripts\python diarize_probe.py --url "URL" --start 0:00 --end 10:00
```

---

## 🛠️ Prerequisites

- **Python 3.11** (3.10 works; 3.14 is too new for `whisperx`)
- **FFmpeg** on PATH (used for BPM/resample + rendering)
- **Node.js 18+** (to run the Suno API locally — no Docker required)
- **deno** — yt-dlp's JS runtime (required to solve YouTube's player challenge)
- **Git**
- **Firefox** — log into YouTube there once; the pipeline reads its cookies
  live (`--cookies-from-browser firefox`), so no manual re-export.
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
| `--voice` | `am_onyx` | Kokoro TTS voice ID (`am_*` male, `af_*` female) |
| `--prompt-style` | rhythmic spoken-word stanzas | DeepSeek narrative flavor |
| `--credit-name` | (none) | speaker name for the title card |
| `--credit-sub` | (none) | persistent source/credit line |
| `--visual` | `default` | `default` / `acid` / `mirror` / `kaleido` / `layered` |

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
- **First silhouette run downloads the `rembg` model (~1 GB)** — one-time, cached.
- **YouTube rotates cookies** — if downloads start returning 403 / "only images",
  re-export `cookies.txt` with the extension.
- **Suno BPM is approximate** — `auto_run.py` detects and stretches each track
  to its target, so output always lands in range.
- **Suno CAPTCHA** — if generation fails with hCaptcha errors, add a paid
  `TWOCAPTCHA_KEY` to the Suno API `.env`.
- **Render time** — the 1080p Mandelbrot is CPU-rendered (a few minutes per
  track). Use `--size 1280x720` for faster previews.
- **Separation from other pipelines** — the Suno API runs on port 3010 in its
  own folder; this repo never touches other projects (e.g. Hymnmania).
