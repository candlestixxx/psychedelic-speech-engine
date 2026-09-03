# ROADMAP

## Phase 1: Core Engine Automation (Current)
- Establish the baseline workflow (Extract $\rightarrow$ Transcribe $\rightarrow$ Polish $\rightarrow$ Synthesize $\rightarrow$ Render).
- Enable batch-processing of multiple music tracks.
- Native CPU execution fallbacks.
- Fully isolate execution runtimes to prevent file collisions.

## Phase 2: Visual Enhancements
- Expand FFmpeg filters to include audio-reactive shaders beyond Mandelbrot.
- Dynamically detect BPM of Suno-generated tracks and adjust video pulse rates accordingly.

## Phase 3: GUI and Deployment
- Containerize the entire engine via Docker for seamless 1-click deployments alongside the Suno API.