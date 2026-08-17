# MEMORY

## Architectural Observations
- **Modularity:** `app.py` handles the single-video extraction-to-render logic, acting as an atomic action. `auto_run.py` acts as the orchestrator/iterator over `app.py`.
- **API Interfaces:** The Suno API interaction is local (`http://localhost:3000`), meaning the system relies heavily on local environment Docker configurations. DeepSeek is remote, requiring standard API key auth.
- **Data Flow:** The pipeline passes state mostly via files (`.wav` audio, `.srt` subtitles, `.mp4` video) rather than holding all buffers in memory, improving stability over long renders.

## Development Preferences
- Prefer robust native CLI arguments for all configurations.
- Ensure error outputs are captured without abruptly halting batch processes.
- Do not commit cache files, `.env` files, or intermediate generated `.wav`/`.mp3` blobs to the git repository.