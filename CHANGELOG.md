# Changelog

## [1.4.0] - 2024-05-28
### Added
- Implemented **Docker Containerization**: Added a highly optimized `Dockerfile` integrating Python 3.10, `ffmpeg`, and `espeak-ng`.
- Implemented **Docker Compose Orchestration**: Added `docker-compose.yml` configured for native NVIDIA GPU passthrough (CUDA support) while supporting CPU-only fallback logic, binding the Gradio Web UI port for 1-click deployments.

## [1.3.0] - 2024-05-28
### Added
- Implemented **Web GUI**: Created `ui.py` leveraging Gradio to expose all pipeline arguments (TTS voice, LLM prompt styles, Subtitle styles) via an interactive local web application.
- Added `requirements.txt` to lock down core Python dependencies.

### Fixed
- Stabilized FFmpeg subtitle parsing on cross-platform setups by sanitizing absolute path strings (converting backslashes to forward slashes).

## [1.2.0] - 2024-05-28
### Added
- Implemented **Dynamic Prompt Styles**: Added `--prompt-style` parameter to natively instruct the DeepSeek LLM to generate thematic stanzas (e.g., 'Alan Watts philosophical' or 'Aggressive Cyberpunk').
- Implemented **Psychedelic Subtitles**: Added `--subtitle-style` parameter to override the default FFmpeg `force_style` rendering filter, allowing dynamic font, size, and color adjustments.

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