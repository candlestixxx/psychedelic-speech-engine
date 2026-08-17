# TODO

## Immediate Tasks
- [x] Implement core pipeline `app.py`.
- [x] Implement batch pipeline `auto_run.py`.
- [x] Support multiple music generation variations via Suno API response handling.
- [x] Handle PyTorch CPU fallback gracefully.
- [ ] Add explicit error handling/retries for DeepSeek API timeouts.
- [ ] Incorporate custom FFmpeg filter arguments as a runtime configuration.

## Minor Fixes
- [ ] Suppress warnings originating from WhisperX when `int8` quantization isn't fully supported on older CPUs.