# Changelog

## [1.0.0] - 2024-05-28
### Added
- Created `app.py` for end-to-end video rendering from YouTube using `yt-dlp`, WhisperX, DeepSeek, Kokoro TTS, and FFmpeg.
- Implemented CPU fallback logic for PyTorch dependencies to ensure cross-platform compatibility without strict CUDA requirements.
- Added `auto_run.py` to batch-process generated variations from the local Suno Docker API container.
- Established documentation standards, ignoring cache files (`__pycache__`).
- Documented core architecture, roadmap, and project metadata in compliance with session guidelines.