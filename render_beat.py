"""Beat-synced Mandelbrot video renderer.

The fractal gets a slow ambient zoom (mandelbrot source) plus a kick-synced
pulse (zoompan with a sharp cosine^8 bump at the track's BPM frequency).
Speech is mixed on top of the full-length music; the video runs the length of
the music track.
"""
import os
import subprocess


def _escape_subtitles(path):
    p = os.path.abspath(path).replace("\\", "/")
    return p.replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")


def _duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        text=True,
    ).strip()
    return float(out)


def render_beat_video(speech_wav, music_file, srt_file, output, bpm,
                      delay=0.0, size="1920x1080", fps=30, punch=0.08):
    """Render the Mandelbrot fractal with a kick-synced zoom pulse.

    `punch` controls the zoom pulse depth (0.08 = 8% pulse).
    """
    dur = _duration(music_file)
    period = fps * 60.0 / max(1.0, bpm)  # frames per beat
    zexpr = f"1+{punch}*pow(max(0,cos(2*PI*on/{period:.4f})),8)"
    subt = _escape_subtitles(srt_file)
    end_pts = int(dur * fps)  # make the slow mandelbrot zoom span the whole track

    vf = (
        f"[0:v]zoompan=z='{zexpr}':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
        f":d=1:s={size}:fps={fps},subtitles='{subt}'[v]"
    )
    af = (
        f"[1:a]adelay={int(delay * 1000)}:all=1[sp];"
        f"[sp][2:a]amix=inputs=2:duration=longest[a]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i",
        f"mandelbrot=size={size}:rate={fps}:start_scale=3.0:end_scale=0.4"
        f":maxiter=200:end_pts={end_pts}",
        "-i", speech_wav,
        "-i", music_file,
        "-filter_complex", f"{vf};{af}",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{dur:.3f}",
        output,
    ]
    subprocess.run(cmd, check=True)
