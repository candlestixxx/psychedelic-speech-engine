# MEMORY

## Architecture (v1.4.0)

- `app.py` — core speech→video engine. Exposes reusable functions:
  `download_audio` (yt-dlp, Firefox cookies), `transcribe_and_diarize`
  (WhisperX + pyannote), `speaker_stats`, `dominant_speaker`,
  `build_srt_and_text`, `extract_speech_and_srt`, `polish_script` (DeepSeek,
  verbatim key quotes), `synthesize_audio`, `synthesize_lines`,
  `build_rhythmic_speech`, `save_rhythmic_speech`.
- `auto_run.py` — single-speaker batch: 4:3 psytrance:other-genre plan, Suno
  music gen, speech extracted ONCE, then one beat-synced video per track.
- `batch_links.py` — multi-speaker driver: reads `links.csv`
  (url, speaker_name, credit_line, speaker, style), auto-picks the dominant
  speaker per video, runs the full pipeline per speaker, per-track error
  handling, per-speaker output folder.
- `diarize_probe.py` — identify speakers in a video with zero music cost:
  prints each speaker's total time, segment count, and sample lines.
- `styles.py` — genre library (3 psytrance + 8 other genres + signature tags +
  negative tags).
- `bpm_tools.py` — BPM detection (numpy/ffmpeg autocorrelation) + `atempo` stretch.
- `render_beat.py` — the visual renderer (see Visual system below), plus
  `find_base_images()` helper.
- `silhouette.py` — fetch the YouTube thumbnail → rembg background removal →
  transparent PNG of the speaker.
- `youtube_auth.py` — one-time OAuth2 flow → saves `youtube_token.json`
  (refresh token, gitignored).
- `youtube_upload.py` — uploads an MP4 via `youtube.videos().insert`;
  `upload_track()` builds the standard title/description/tags.

## Data flow

- State passes via files (`.wav` / `.srt` / `.mp3` / `.mp4` / `.png`), never
  in-memory buffers. The expensive speech pipeline runs once per run and is
  reused across all music tracks.

## Visual system (`render_beat.py`)

- Single-fractal modes (`--visual`): `default`, `acid` (hue cycling),
  `mirror` (left/right symmetry), `kaleido` (mirror + hue).
- `layered` mode: a base layer (see below) is hue-cycled + blurred + gently
  pulse-zoomed, then the sharp Mandelbrot is composited over it with a `screen`
  glow blend. Both layers move to the track BPM.
- **Beat-flash**: an `eq` brightness pulse on every kick (sharp `cos^n`), plus a
  stronger Mandelbrot zoom pulse (`punch=0.10`) for visible beat sync.
- Base layer is **randomized per video** from procedural generators (cellauto
  cellular automaton, animated `gradients` radial/circular/spiral/square,
  Sierpinski triangle, neon Game-of-Life, soft fractal) **or** the user's
  psychedelic art images in `assets/` (excludes `*silhouette*` / `*thumb*`).
  When art images exist they win; images are cycled per track via `base_seed`.
- Credits (burned in via libass): large title card (0–5.5 s), persistent
  bottom source line, and a semi-transparent name watermark every ~20 s.
  Set with `--credit-name` / `--credit-sub`.

## Speech pipeline

- Default voice is **`am_onyx`** (male); `am_*` = male, `af_*` = female.
- `polish_script` extracts the speaker's **key quotes verbatim** (one thought
  per line), not a rewrite.
- Rhythmic sync: each line is synthesized separately
  (`synthesize_lines`) and placed so its start lands on a beat
  (`build_rhythmic_speech`) at the track's BPM — speech hits the rhythm.
- Silhouette: an optional transparent PNG of the speaker is ghosted (50%
  opacity) center-frame every ~25 s for 5 s. Auto-generated from the thumbnail
  via rembg, or can be dropped in manually.

## Environment

- Python 3.11 venv managed by **uv** (no pip inside it — install with
  `uv pip install --python .venv/Scripts/python.exe <pkg>`).
  torch 2.8.0+cu126, whisperx 3.8.6, pyannote-audio 4.0.7, kokoro 0.9.4,
  rembg 2.0.81, Pillow, google-api-python-client, google-auth-oauthlib.
- GPU: GTX 1080 Ti (Pascal, sm_61) → `float32` compute. Whisper `batch_size=4`
  (16 OOMs the 11 GB card).
- Suno API: separate `../suno-api` Node app on **port 3010**. Cookie is set and
  verified (account `resurrectingbeats`, ~9980 monthly credits left). Restart with
  `cd ../suno-api && npx next dev -p 3010`. 1 generation = 2 songs = 10 credits;
  `auto_run` keeps only the first `audio_url`.
- **Critical suno-api patch (LOCAL only, not pushed upstream)**: `src/lib/SunoApi.ts`
  was fixed to read `media_urls` (m4a) because Suno now returns
  `audio_url: ".../api/forbidden"`. Commit `642e49a` in the suno-api repo. If
  `../suno-api` is re-cloned, re-apply: add `extractAudioUrl()` (prefer m4a from
  `media_urls`) and use it in both `get()` and `generateSongs()` (replacing
  `audio_url: audio.audio_url`).
- YouTube download (yt-dlp) uses **`--cookies-from-browser firefox`** (reads
  Firefox cookies live — no manual re-export), the **deno** JS runtime, the
  `web` player client, and `--remote-components ejs:github`. Keep YouTube
  logged in in Firefox. Falls back to `cookies.txt` if Firefox is absent.
- `ffmpeg`/`ffprobe`/`deno` are shimmed into `WinGet\Links` (on PATH):
  ffmpeg 9.0.1 (Gyan), deno 2.9.6. The winget PATH entry was stale
  (`ffmpeg-9.0-full_build` vs the real `ffmpeg-9.0.1-full_build`).
- `.env` keys: `DEEPSEEK_API_KEY`, `HF_TOKEN` (gated pyannote models),
  `GEMINI_API_KEY` (unused), `SUNO_API_URL=http://localhost:3010/api/custom_generate`,
  `SUNO_TIMEOUT=600`.

## Speaker identification

- Diarization returns anonymous `SPEAKER_XX` labels only — the real name is
  always supplied manually (`--credit-name` / `links.csv`).
- `dominant_speaker()` picks whoever talks the most (usually the subject).
- Reference (Hofmann video `jN6rYHAZ30c`): `SPEAKER_01` = Albert Hofmann
  (381 s), `SPEAKER_02` = Peter Gorman (interviewer, 108 s), `SPEAKER_00` =
  Laura Huxley (7 s phone call). Description: "Peter Gorman interviews Albert
  Hofmann for High Times (1994)."

## Never commit (gitignored)

- `.env`, `cookies.txt`, `youtube_token.json`, `assets/`, `*.mp3`/`*.mp4`/`*.wav`/`*.srt`,
  `workspace_run_*/`, `probe.log`, `probe_*/`, `batch_output/`, `*.credits.ass`.

## Development preferences

- Per-track / per-speaker error handling; the batch continues on failure.
- Procedural/generated visuals only; the only external assets are the user's
  own art in `assets/`.
