# Changelog

## [1.1.0] - 2024-05-28
### Added
- Implemented **Workspace Isolation**: `app.py` now executes entirely within isolated `workspace_run_<timestamp>/` directories. This prevents concurrent batch-processing runs from overwriting intermediate files (e.g., `downloaded_audio.wav`, `.srt` files).
- Implemented **Configurable TTS Voices**: Added the `--voice` argument to allow overriding the default `af_heart` voice profile.

## [1.0.1] - 2024-05-28
### Added
- Added `--video-filter` CLI argument to both `app.py` and `auto_run.py` to allow overriding the default Mandelbrot FFmpeg background filter.
### Fixed
- Added a 3-attempt exponential backoff retry loop for the DeepSeek API to prevent random timeout crashes.
- Suppressed PyTorch/NumPy initialization and CPU quantization warnings from `whisperx` that cluttered the execution console.

## [1.0.0] - 2024-05-28
### Added
- Created `app.py` for end-to-end video rendering from YouTube using `yt-dlp`, WhisperX, DeepSeek, Kokoro TTS, and FFmpeg.
- Implemented CPU fallback logic for PyTorch dependencies to ensure cross-platform compatibility without strict CUDA requirements.
- Added `auto_run.py` to batch-process generated variations from the local Suno Docker API container.
- Established documentation standards, ignoring cache files (`__pycache__`).
- Documented core architecture, roadmap, and project metadata in compliance with session guidelines.