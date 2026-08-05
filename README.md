# 🌀 Psychedelic Speech-to-Music Video Engine

An automated, high-performance, cost-optimized Python pipeline that converts YouTube speech and interview clips into philosophical, spoken-word music tracks set against audio-reactive Mandelbrot fractal animations.

---

## 💡 Architecture & Tech Stack

- **Audio Extraction:** `yt-dlp` extracts raw audio directly from YouTube URLs without video overhead.
- **Speaker Diarization:** `WhisperX` + `pyannote.audio` transcribes and isolates specific guest speakers (`SPEAKER_01`).
- **Script Polishing:** `DeepSeek API` (`deepseek-v4-flash`) strips filler words and formats speech into rhythmic spoken-word stanzas (~$0.0001 per run).
- **Local Voice Synthesis:** `Kokoro-82M TTS` generates natural, human-like voiceovers locally at zero API cost.
- **Music Integration:** Optimized for **Ajja / Goa Psytrance** instrumental tracks generated via `Suno Pro`.
- **Video Rendering Engine:** `FFmpeg` generates dynamic zooming Mandelbrot visuals, burns in `.srt` subtitles, and mixes multi-track audio into an `.mp4` deliverable.

---

## 🛠️ Prerequisites & System Dependencies

Before running the pipeline, ensure the following core tools are installed on your host system:

- **Python 3.10+** (Python 3.11 recommended)
- **FFmpeg** (Must be accessible in system PATH)
- **espeak-ng** (Required by Kokoro TTS for phoneme processing)

### System Package Installation Commands

#### Ubuntu / Debian Linux
```bash
sudo apt-get update && sudo apt-get install -y espeak-ng ffmpeg git
