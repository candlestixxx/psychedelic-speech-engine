# DEPLOYMENT GUIDE

## Prerequisites
1. **Environment Configuration:**
   - Create a `.env` file in the root directory based on `.env.example`.
   - Variables required:
     - `HF_TOKEN` (HuggingFace token for WhisperX/pyannote diarization)
     - `DEEPSEEK_API_KEY` (DeepSeek model authentication)
2. **Local Suno Docker API:**
   - Ensure the external Suno API is running locally via Docker on port 3000.
   - The endpoint `http://localhost:3000/api/custom_generate` must be accessible.

## Option 1: Docker Compose (Recommended 1-Click Deployment)
The easiest way to run the engine is via Docker. This handles all system dependencies (`ffmpeg`, `espeak-ng`) automatically.

1. Ensure Docker and Docker Compose are installed.
2. Run the orchestration command:
   ```bash
   docker-compose up -d --build
   ```
3. Open your browser and navigate to `http://localhost:7860` to access the interactive Web GUI.

*(Note: The `docker-compose.yml` file is pre-configured for NVIDIA GPU passthrough. If you do not have an NVIDIA GPU, it will safely ignore the reservation and execute CPU fallback logic).*

## Option 2: Native Python Execution
If you prefer running natively outside of Docker, you must manually satisfy the system requirements.

1. **System Libraries:** Install `ffmpeg` and `espeak-ng`.
2. **Python Environment:** Use Python 3.10+.
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Engine:**
   - For Web GUI: `python ui.py` (Accessible at `http://localhost:7860`)
   - For CLI Automation: `python auto_run.py --url "YOUTUBE_URL_HERE" --output "my_video.mp4"`