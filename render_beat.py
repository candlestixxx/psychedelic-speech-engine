"""Beat-synced Mandelbrot video renderer.

The fractal gets a slow ambient zoom (mandelbrot source) plus a kick-synced
pulse (zoompan with a sharp cosine^8 bump at the track's BPM frequency).
Speech is mixed on top of the full-length music; the video runs the length of
the music track.

Optional visual styles (applied between the zoom pulse and the text overlays
so subtitles/credits stay clean and readable):

  default  - raw Mandelbrot + beat pulse
  acid     - + continuous hue cycling (saturation-boosted colour rotation)
  mirror   - + left/right kaleidoscope mirroring
  kaleido  - mirror + hue cycling

Optional credits: a fading title card over the first seconds (e.g. the
speaker's name) plus a persistent source-credit line, burned in via libass and
also written into the file's metadata.
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


def _ass_time(seconds):
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, c = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def _write_credits_ass(name, sub_line, duration_sec, path):
    """Write a minimal ASS overlay: centered title fade + bottom credit line."""
    end = _ass_time(duration_sec)
    name = (name or "").replace("\\", "").replace("{", "(").replace("}", ")")
    sub_line = (sub_line or "").replace("\\", "").replace("{", "(").replace("}", ")")

    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title, Arial, 96, &H00FFFFFF, &H000000FF, &H00000000, &H78000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 3, 0, 5, 40, 40, 40, 1
Style: Credit, Arial, 26, &H00FFFFFF, &H000000FF, &H00000000, &H78000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 2, 40, 40, 30, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0, 0:00:00.00, 0:00:05.50, Title, , 0, 0, 0, , {{\\fad(250,250)}}{name}
Dialogue: 0, 0:00:00.00, {end}, Credit, , 0, 0, 0, , {sub_line}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(ass)
    return path


def render_beat_video(speech_wav, music_file, srt_file, output, bpm,
                      delay=0.0, size="1920x1080", fps=30, punch=0.08,
                      credit_name=None, credit_sub=None, visual="default"):
    """Render the Mandelbrot fractal with a kick-synced zoom pulse.

    `punch` controls the zoom pulse depth (0.08 = 8% pulse).
    `visual` selects an optional effect layer (default/acid/mirror/kaleido).
    `credit_name` / `credit_sub` optionally burn an attribution overlay in.
    """
    dur = _duration(music_file)
    period = fps * 60.0 / max(1.0, bpm)  # frames per beat
    zexpr = f"1+{punch}*pow(max(0,cos(2*PI*on/{period:.4f})),8)"
    subt = _escape_subtitles(srt_file)
    end_pts = int(dur * fps)  # make the slow mandelbrot zoom span the whole track

    sub_filters = f"subtitles='{subt}'"
    if credit_name:
        credits_ass = os.path.abspath(output) + ".credits.ass"
        _write_credits_ass(credit_name, credit_sub, dur, credits_ass)
        sub_filters += f",subtitles='{_escape_subtitles(credits_ass)}'"

    # Build the video filter graph as labelled segments joined by ';'.
    vf_parts = [
        f"[0:v]zoompan=z='{zexpr}':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
        f":d=1:s={size}:fps={fps}[zp]"
    ]
    src = "zp"
    if visual == "acid":
        vf_parts.append(f"[{src}]hue=h='6*t':s=1.4[vz]")
        src = "vz"
    elif visual in ("mirror", "kaleido"):
        vf_parts.append(
            f"[{src}]split=2[va][vb];"
            f"[va]crop=iw/2:ih:0:0[vl];"
            f"[vb]crop=iw/2:ih:0:0,hflip[vr];"
            f"[vl][vr]hstack[vz]"
        )
        src = "vz"
        if visual == "kaleido":
            vf_parts.append(f"[{src}]hue=h='6*t':s=1.4[vz2]")
            src = "vz2"
    vf_parts.append(f"[{src}]{sub_filters}[v]")
    vf = ";".join(vf_parts)

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
        "-metadata", f"title={credit_name or os.path.basename(output)}",
        "-metadata", f"comment={credit_sub or ''}",
        output,
    ]
    subprocess.run(cmd, check=True)
