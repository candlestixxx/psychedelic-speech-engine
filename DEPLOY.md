# DEPLOYMENT GUIDE

## Prerequisites

- **Python 3.11** (venv recommended; 3.14 is too new for `whisperx`)
- **FFmpeg** on PATH
- **Node.js 18+** (to run the Suno API locally — Docker is NOT required)
- `espeak-ng` is **not** required — `espeakng-loader` bundles it automatically
  via kokoro/misaki.

## 1. Python environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### CUDA (optional but recommended)

`requirements.txt` installs CPU torch by default. For an NVIDIA GPU, install
the matching CUDA build from the PyTorch index:

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cu126 \
  torch==2.8.0+cu126 torchaudio==2.8.0+cu126 torchvision==0.23.0+cu126
```

> Pascal GPUs (GTX 10-series, compute capability 6.1) auto-select `float32`
> because they lack efficient fp16 compute. Volta+ (sm_70+) uses `float16`.

## 2. Environment variables (`.env`)

Copy `.env.example` to `.env` and fill in:

- `DEEPSEEK_API_KEY` — required for script polishing.
- `HF_TOKEN` — required for diarization. Accept the terms on
  `pyannote/speaker-diarization-community-1` and `pyannote/segmentation-3.0`.
- `SUNO_API_URL` — defaults to `http://localhost:3010/api/custom_generate`.

## 3. Suno API (separate service, port 3010)

```bash
git clone https://github.com/gcui-art/suno-api.git ../suno-api
cd ../suno-api
npm install
```

Create `../suno-api/.env`:

```
SUNO_COOKIE=<your full Suno session cookie>
```

Start it on a free port (3010 keeps it clear of other projects):

```bash
npx next dev -p 3010
```

Get the cookie from suno.com devtools: F12 → Network → refresh → find a request
containing `?__clerk_api_version` → copy the `Cookie` header value.

## 4. Run

```bash
# Batch: 8 psytrance + 6 other-genre tracks
.venv\Scripts\python auto_run.py --url "YOUTUBE_URL" --count 8 --style random

# Single track with your own music file (no Suno)
.venv\Scripts\python app.py --url "YOUTUBE_URL" --music "track.mp3"
```

## Troubleshooting

- **Suno 401/500** → the Suno API has no valid `SUNO_COOKIE` (or it expired).
- **hCaptcha errors** → add a paid `TWOCAPTCHA_KEY` to the Suno API `.env`.
- **`whisperx` import error about `k2_fsa`** → an orphaned `speechbrain`
  package is installed; `pip uninstall speechbrain`.
