# Changelog

## [1.4.0] - 2026-09-01
### Added
- **Male TTS voice by default** (`am_onyx`; `am_*` = male, `af_*` = female).
- **Verbatim key-quote extraction**: DeepSeek now pulls the speaker's most
  quotable moments word-for-word (removing only fillers), one thought per line,
  instead of rewriting into stanzas.
- **Beat-synced rhythmic speech**: each line is synthesized separately and its
  start is snapped to a beat at the track's BPM (`synthesize_lines`,
  `build_rhythmic_speech`, `save_rhythmic_speech` in `app.py`).
- **Beat-flash visuals**: a brightness pulse on every kick (`eq` filter) plus a
  stronger zoom pulse (punch 0.08 → 0.10).
- **Automatic YouTube cookies from Firefox** (`--cookies-from-browser firefox`),
  removing the manual cookies.txt re-export step.

## [1.3.0] - 2026-09-01
### Added
- **Visual styles** (`render_beat.py --visual`): `default`, `acid` (hue
  cycling), `mirror`, `kaleido`, and `layered`.
- **Layered psychedelic mode**: a randomized base layer (cellular automaton /
  animated gradient / Sierpinski / Game-of-Life / soft fractal) **or the
  user's art images in `assets/`**, with the sharp Mandelbrot composited on
  top via a screen glow blend; both layers pulse to the track BPM, and base
  images are cycled per track so every video differs.
- **Speaker credits**: title card + persistent source line + periodic name
  watermark (`--credit-name` / `--credit-sub`).
- **Speaker silhouette**: auto rembg cutout from the YouTube thumbnail,
  ghosted into the video (`silhouette.py`).
- `diarize_probe.py`: identify speakers with zero music cost.
- `batch_links.py` + `links.csv`: multi-speaker batch driver with automatic
  dominant-speaker selection.
- `app.py` helpers: `transcribe_and_diarize`, `speaker_stats`,
  `dominant_speaker`, `build_srt_and_text`.
- YouTube download hardening: `cookies.txt` + deno JS runtime + `web` client +
  `--remote-components ejs:github`.
- `requirements.txt`: `rembg`, `Pillow`.

### Fixed
- CUDA out-of-memory on the GTX 1080 Ti (whisper `batch_size` 16 → 4).
- `ffmpeg`/`ffprobe` missing from PATH (WinGet Links shims; stale winget path).
- yt-dlp 403 / "only images" bot wall (authenticated cookies + deno).
- `scale`/`crop` used `WxH` instead of `W:H` in the image base filter.

## [1.2.0] - 2026-08-31
### Added
- **Dynamic Prompt Styles**: `--prompt-style` instructs the DeepSeek LLM on the
  narrative flavor of the output stanzas (e.g. 'Alan Watts philosophical').
- **Psychedelic Subtitles**: `--subtitle-style` overrides the FFmpeg `force_style`
  rendering filter (font, size, color).

## [1.1.0] - 2026-08-19
### Added
- `auto_run.py` psytrance batch generator: `--bpm-min/--bpm-max`, `--count`,
  `--style`, `--others-per-4`, `--start/--end`, `--size`, `--no-stretch`.
- `styles.py` genre library: 3 psytrance sub-styles + 8 additional genres,
  with a shared signature tag set for a consistent "own sound".
- `bpm_tools.py`: numpy/ffmpeg BPM detection + `atempo` time-stretch to target.
- `render_beat.py`: beat-synced Mandelbrot renderer (kick-triggered zoom pulse).
- Time-range extraction via yt-dlp `--download-sections`.
- `requirements.txt` and `.env.example` (were previously missing).
- Separate Suno API setup (Node app on port 3010, decoupled from other pipelines).
- **Workspace Isolation**: `app.py`/`auto_run.py` execute inside timestamped
  `workspace_run_*/` directories, preventing file collisions during batch runs.
- **Configurable TTS voice**: `--voice` argument (Kokoro voice ID, default `af_heart`).

### Fixed
- DeepSeek model name (`deepseek-chat` instead of the invalid `deepseek-v4-flash`).
- whisperx 3.8.6 API (`whisperx.diarize.DiarizationPipeline`, `token=` arg).
- Pascal-GPU compute type (`float32` instead of `float16`).
- Windows console UTF-8 output.
- Windows-safe FFmpeg subtitles path.
- Removed orphaned `speechbrain` package that broke whisperx model loading.

## [1.0.0] - 2024-05-28
### Added
- `app.py` end-to-end rendering (yt-dlp → WhisperX → DeepSeek → Kokoro → FFmpeg).
- `auto_run.py` Suno batch orchestration.
- CPU fallback for PyTorch.
