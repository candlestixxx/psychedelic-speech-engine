# DEPLOYMENT GUIDE

## Prerequisites
1. **System Libraries:**
   - Install `ffmpeg`. Must be accessible in system PATH.
   - Install `espeak-ng` (required by Kokoro TTS).
2. **Environment Configuration:**
   - Create a `.env` file in the root directory based on `.env.example` (or configure via GitHub Actions).
   - Variables required:
     - `HF_TOKEN` (HuggingFace token for WhisperX/pyannote diarization)
     - `DEEPSEEK_API_KEY` (DeepSeek model authentication)

## Python Environment Setup
1. Use Python 3.10 or 3.11.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Ensure PyTorch is configured for CUDA if you have a compatible GPU, though CPU execution is supported as a fallback).*

## Local Suno Docker API
1. Ensure the Suno API is running locally via Docker on port 3000.
2. The endpoint `http://localhost:3000/api/custom_generate` must be accessible.

## Running the Engine
Run the fully automated pipeline:
```bash
python auto_run.py --url "YOUTUBE_URL_HERE" --output "my_video.mp4"
```