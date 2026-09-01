"""Beat-synced psychedelic video renderer.

Single-fractal modes: a Mandelbrot source gets a slow ambient zoom plus a
kick-synced pulse (zoompan with a sharp cosine^8 bump at the BPM).

Layered mode: a randomized abstract base layer (cellular automaton / animated
gradient / Sierpinski / Game-of-Life / soft fractal) is colour-cycled, blurred
and gently pulse-zoomed, then the sharp Mandelbrot is composited over it with a
"screen" glow blend -- a multi-layer psychedelic picture unique to each video.

Credits: a fading title card (speaker name) over the first seconds, a persistent
source line, and a periodic semi-transparent name watermark inside the art.

Silhouette: if a transparent PNG of the speaker is provided, it is ghosted
(50% opacity) over the centre periodically, so the psychedelic art bleeds
through the speaker's shape.
"""
import os
import random
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
    """ASS overlay: fading title, persistent credit line, periodic name tag."""
    end = _ass_time(duration_sec)
    name = (name or "").replace("\\", "").replace("{", "(").replace("}", ")")
    sub_line = (sub_line or "").replace("\\", "").replace("{", "(").replace("}", ")")

    tag_events = ""
    if name:
        t = 15.0
        while t < duration_sec - 4:
            tag_events += (
                f"Dialogue: 0, {_ass_time(t)}, {_ass_time(t + 3)}, Tag, , 0, 0, 0, , "
                f"{{\\fad(400,400)}}{name}\n"
            )
            t += 20.0

    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title, Arial, 96, &H00FFFFFF, &H000000FF, &H00000000, &H78000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 3, 0, 5, 40, 40, 40, 1
Style: Credit, Arial, 26, &H00FFFFFF, &H000000FF, &H00000000, &H78000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 2, 40, 40, 30, 1
Style: Tag, Arial, 40, &H50FFFFFF, &H000000FF, &H00000000, &H78000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 8, 40, 40, 40, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0, 0:00:00.00, 0:00:05.50, Title, , 0, 0, 0, , {{\\fad(250,250)}}{name}
Dialogue: 0, 0:00:00.00, {end}, Credit, , 0, 0, 0, , {sub_line}
{tag_events}"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(ass)
    return path


def _random_base_source(size, fps, rng):
    """Return a lavfi source string for a randomized trippy background layer."""
    seed = rng.randint(0, 2 ** 31)
    kind = rng.randrange(6)
    if kind in (0, 1):
        rule = rng.choice([110, 30, 45, 73, 90, 150, 184])
        return f"cellauto=size={size}:rate={fps}:rule={rule}:seed={seed}"
    if kind == 2:
        gtype = rng.choice(["radial", "circular", "spiral", "square", "linear"])
        return f"gradients=size={size}:rate={fps}:type={gtype}:seed={seed}"
    if kind == 3:
        return f"sierpinski=size={size}:rate={fps}:type=1:jump={rng.choice([1, 2, 5])}:seed={seed}"
    if kind == 4:
        color = rng.choice(["0xFF00FF", "0x00FFFF", "0x00FF00", "0xFF0000", "0xFFFF00"])
        return f"life=size={size}:rate={fps}:ratio=0.06:seed={seed}:life_color={color}:death_color=0x000000"
    return f"mandelbrot=size={size}:rate={fps}:start_scale=2.5:end_scale=0.15:maxiter=150"


def find_base_images(directory):
    """Return psychedelic base-art image paths in a directory.

    Excludes the auto thumbnail/silhouette files so only your art examples are
    picked up as base layers.
    """
    if not os.path.isdir(directory):
        return []
    exts = (".png", ".jpg", ".jpeg", ".webp")
    out = []
    for fn in sorted(os.listdir(directory)):
        low = fn.lower()
        if "silhouette" in low or "thumb" in low:
            continue
        if low.endswith(exts):
            out.append(os.path.join(directory, fn))
    return out


def render_beat_video(speech_wav, music_file, srt_file, output, bpm,
                      delay=0.0, size="1920x1080", fps=30, punch=0.08,
                      credit_name=None, credit_sub=None, visual="default",
                      base_seed=None, silhouette=None, base_images=None):
    """Render the psychedelic video for one track.

    `visual` in {default, acid, mirror, kaleido, layered}.
    `base_seed` fixes the layered background choice (None = random per video).
    `silhouette` is an optional transparent PNG of the speaker to ghost in.
    """
    dur = _duration(music_file)
    period = fps * 60.0 / max(1.0, bpm)  # frames per beat
    zexpr = f"1+{punch}*pow(max(0,cos(2*PI*on/{period:.4f})),8)"
    subt = _escape_subtitles(srt_file)
    end_pts = int(dur * fps)
    w, h = (int(v) for v in size.split("x"))

    sub_filters = f"subtitles='{subt}'"
    if credit_name:
        credits_ass = os.path.abspath(output) + ".credits.ass"
        _write_credits_ass(credit_name, credit_sub, dur, credits_ass)
        sub_filters += f",subtitles='{_escape_subtitles(credits_ass)}'"

    inputs = [
        "-f", "lavfi", "-i",
        f"mandelbrot=size={size}:rate={fps}:start_scale=3.0:end_scale=0.4"
        f":maxiter=200:end_pts={end_pts}",
    ]
    n_video = 1
    base_is_image = False
    if visual == "layered":
        rng = random.Random(base_seed)
        imgs = [p for p in (base_images or []) if os.path.exists(p)]
        if imgs:
            pick = imgs[base_seed % len(imgs)] if base_seed is not None else rng.choice(imgs)
            inputs += ["-loop", "1", "-i", pick]
            base_is_image = True
        else:
            inputs += ["-f", "lavfi", "-i", _random_base_source(size, fps, rng)]
        n_video = 2

    speech_idx = n_video
    music_idx = n_video + 1
    inputs += ["-i", speech_wav, "-i", music_file]

    sil_idx = None
    if silhouette and os.path.exists(silhouette):
        sil_idx = music_idx + 1
        inputs += ["-loop", "1", "-i", silhouette]

    # Build the visual composite, ending in a single labelled stream "VIS".
    vf_parts = []
    if visual == "layered":
        z_bg = f"1+0.04*pow(max(0,cos(2*PI*on/{period:.4f})),8)"
        if base_is_image:
            z_img = f"(1+0.4*on/{end_pts})*(1+0.05*pow(max(0,cos(2*PI*on/{period:.4f})),8))"
            base_filter = (
                f"[1:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=yuv420p,"
                f"zoompan=z='{z_img}':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
                f":d=1:s={size}:fps={fps},hue=h='6*t':s=1.3[bg]"
            )
        else:
            base_filter = (
                f"[1:v]hue=h='6*t':s=1.6,gblur=sigma=12,zoompan=z='{z_bg}'"
                f":x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':d=1:s={size}:fps={fps}[bg]"
            )
        vf_parts += [
            f"[0:v]zoompan=z='{zexpr}':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
            f":d=1:s={size}:fps={fps},hue=h='-4*t':s=1.4[fg]",
            base_filter,
            f"[bg][fg]blend=all_mode=screen,format=yuv420p[VIS]",
        ]
    else:
        vf_parts.append(
            f"[0:v]zoompan=z='{zexpr}':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
            f":d=1:s={size}:fps={fps}[zp]"
        )
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
        vf_parts.append(f"[{src}]format=yuv420p[VIS]")

    final_label = "VIS"
    if sil_idx is not None:
        cut_h = int(h * 0.55)
        vf_parts.append(
            f"[{sil_idx}:v]scale=-2:{cut_h},format=rgba,colorchannelmixer=aa=0.5[cut];"
            f"[VIS][cut]overlay=x='(W-w)/2':y='(H-h)/2':enable='lt(mod(t,25),5)'[VIS2]"
        )
        final_label = "VIS2"

    vf_parts.append(f"[{final_label}]{sub_filters}[v]")
    vf = ";".join(vf_parts)

    af = (
        f"[{speech_idx}:a]adelay={int(delay * 1000)}:all=1[sp];"
        f"[sp][{music_idx}:a]amix=inputs=2:duration=longest[a]"
    )

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", f"{vf};{af}",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{dur:.3f}",
        "-metadata", f"title={credit_name or os.path.basename(output)}",
        "-metadata", f"comment={credit_sub or ''}",
        output,
    ]
    subprocess.run(cmd, check=True)
