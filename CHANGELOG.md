# Changelog

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
