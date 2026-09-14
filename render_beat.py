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


def _write_credits_ass(name, sub_line, duration_sec, path, channel_name="PsySpeech Engine", genre_label=None):
    """ASS overlay: movie-style intro (channel -> name -> description) + persistent lower-third."""
    end = _ass_time(duration_sec)
    name = (name or "").replace("\\", "").replace("{", "(").replace("}", ")")
    sub_line = (sub_line or "").replace("\\", "").replace("{", "(").replace("}", ")")
    channel = (channel_name or "").replace("\\", "").replace("{", "(").replace("}", ")")
    lower = name
    if genre_label:
        lower += f"  ·  {genre_label}"
    lower = lower.replace("\\", "").replace("{", "(").replace("}", ")")

    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Channel, Arial, 52, &H00FFFFFF, &H000000FF, &H00000000, &H78000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 3, 0, 5, 40, 40, 40, 1
Style: Title, Arial, 92, &H00FFFFFF, &H000000FF, &H00000000, &H78000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 3, 0, 5, 40, 40, 40, 1
Style: Sub, Arial, 34, &H00FFFFFF, &H000000FF, &H00000000, &H78000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 5, 40, 40, 40, 1
Style: Credit, Arial, 24, &H90FFFFFF, &H000000FF, &H00000000, &H78000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 2, 0, 2, 40, 40, 30, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0, 0:00:00.00, 0:00:03.00, Channel, , 0, 0, 0, , {{\\fad(300,300)}}{channel}
Dialogue: 0, 0:00:03.00, 0:00:06.00, Title, , 0, 0, 0, , {{\\fad(250,250)}}{name}
Dialogue: 0, 0:00:06.00, 0:00:09.00, Sub, , 0, 0, 0, , {{\\fad(250,250)}}{sub_line}
Dialogue: 0, 0:00:09.00, {end}, Credit, , 0, 0, 0, , {lower}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(ass)
    return path


def _random_base_source(size, fps, rng):
    """Return a lavfi source string for a randomized trippy background layer."""
    seed = rng.randint(0, 2 ** 31)
    kind = rng.randrange(8)
    if kind in (0, 1):
        rule = rng.choice([110, 30, 45, 73, 90, 150, 184])
        return f"cellauto=size={size}:rate={fps}:rule={rule}:seed={seed}"
    if kind == 2:
        gtype = rng.choice(["radial", "circular", "spiral", "square", "linear"])
        return f"gradients=size={size}:rate={fps}:type={gtype}:seed={seed}"
    if kind == 3:
        return f"sierpinski=size={size}:rate={fps}:type=1:jump={rng.choice([1, 2, 5])}:seed={seed}"
    # kinds 4..7: MilkDrop-like flowing plasma (dominant), animated via time T
    return (f"nullsrc=size={size}:rate={fps},"
            f"geq=r='128+127*sin(X/{rng.randint(24, 40)}+T*{rng.uniform(1.8, 2.8)})*cos(Y/{rng.randint(36, 60)}-T*{rng.uniform(1.2, 2.0)})'"
            f":g='128+127*sin(Y/{rng.randint(20, 34)}-T*{rng.uniform(2.2, 3.2)})*sin((X+Y)/{rng.randint(48, 80)}+T*{rng.uniform(0.9, 1.6)})'"
            f":b='128+127*cos((X-Y)/{rng.randint(32, 52)}+T*{rng.uniform(1.6, 2.6)})*sin(X/{rng.randint(40, 70)}+T*{rng.uniform(0.8, 1.4)})'")


def _random_geo_source(size, fps, rng):
    """Return a geometric procedural layer (shapes/patterns), distinct from base."""
    seed = rng.randint(0, 2 ** 31)
    kind = rng.randrange(4)
    if kind == 0:
        return f"cellauto=size={size}:rate={fps}:rule={rng.choice([30, 45, 73, 90, 150, 184])}:seed={seed}"
    if kind == 1:
        return f"sierpinski=size={size}:rate={fps}:type=1:jump={rng.choice([1, 2, 5])}:seed={seed}"
    if kind == 2:
        color = rng.choice(["0xFF00FF", "0x00FFFF", "0x00FF00", "0xFF0000", "0xFFFF00"])
        return f"life=size={size}:rate={fps}:ratio=0.08:seed={seed}:life_color={color}:death_color=0x000000"
    return f"gradients=size={size}:rate={fps}:type={rng.choice(['radial', 'circular', 'spiral', 'square'])}:seed={seed}"


def _mandelbrot_source(size, fps, rng, end_pts=None):
    """Randomized Mandelbrot: a different region, zoom depth and colour scheme per video."""
    anchors = [
        (-0.743643887, -0.131825904),  # seahorse valley
        (-0.75, 0.10),                 # spiral
        (-0.16, 1.04),                 # elephant valley
        (-0.1011, 0.9563),
        (-0.7269, 0.1889),
        (-0.8, 0.156),
        (-0.6, 0.6),
        (-1.0, 0.0),
    ]
    cx, cy = rng.choice(anchors)
    cx += rng.uniform(-0.06, 0.06)
    cy += rng.uniform(-0.06, 0.06)
    start_scale = rng.uniform(1.5, 4.5)
    end_scale = rng.uniform(0.03, 0.5)
    maxiter = rng.randint(80, 400)
    outer = rng.choice(["0x000000", "0x000020", "0x100030", "0x200040", "0x000030"])
    inner = rng.choice(["0xFFFFFF", "0x00FFFF", "0xFF00FF", "0xFFFF00", "0x00FF00", "0xFF5500", "0x8800FF"])
    s = (f"mandelbrot=size={size}:rate={fps}:start_x={cx:.10f}:start_y={cy:.10f}"
         f":start_scale={start_scale:.4f}:end_scale={end_scale:.4f}:maxiter={maxiter}"
         f":outer={outer}:inner={inner}")
    if end_pts is not None:
        s += f":end_pts={end_pts}"
    return s


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
                      delay=0.0, size="1920x1080", fps=30, punch=0.10,
                      credit_name=None, credit_sub=None, visual="default",
                      base_seed=None, silhouette=None, base_images=None,
                      channel_name="PsySpeech Engine", genre_label=None):
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
    rng = random.Random(base_seed)

    sub_filters = f"subtitles='{subt}'"
    if credit_name:
        credits_ass = os.path.abspath(output) + ".credits.ass"
        _write_credits_ass(credit_name, credit_sub, dur, credits_ass,
                           channel_name=channel_name, genre_label=genre_label)
        sub_filters += f",subtitles='{_escape_subtitles(credits_ass)}'"

    inputs = [
        "-f", "lavfi", "-i",
        _mandelbrot_source(size, fps, rng, end_pts),
    ]
    n_video = 1
    base_is_image = False
    if visual == "layered":
        imgs = [p for p in (base_images or []) if os.path.exists(p)]
        if imgs:
            pick = imgs[base_seed % len(imgs)] if base_seed is not None else rng.choice(imgs)
            inputs += ["-loop", "1", "-i", pick]
            base_is_image = True
        else:
            inputs += ["-f", "lavfi", "-i", _random_base_source(size, fps, rng)]
        inputs += ["-f", "lavfi", "-i", _random_geo_source(size, fps, rng)]
        n_video = 3

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
        # Three DISTINCT stacked layers, each with its own beat-synced movement:
        #  base (MilkDrop plasma / art) -> kaleidoscope geometric -> Mandelbrot on top
        z_slow = f"(1+0.35*on/{end_pts})"
        z_base = f"(1+0.35*on/{end_pts})*(1+0.06*pow(max(0,sin(2*PI*on/{period:.4f})),6))"
        z_img = f"(1+0.4*on/{end_pts})*(1+0.06*pow(max(0,sin(2*PI*on/{period:.4f})),6))"
        z_geo = f"(1+0.4*on/{end_pts})*(1+0.08*pow(max(0,cos(2*PI*on/{period:.4f})),8))"
        if base_is_image:
            base_filter = (
                f"[1:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=yuv420p,"
                f"rotate=a='0.04*t':ow=iw:oh=ih,"
                f"zoompan=z='{z_img}':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
                f":d=1:s={size}:fps={fps},hue=h='6*t':s=1.9,eq=brightness=0.6:saturation=1.6[base]"
            )
        else:
            base_filter = (
                f"[1:v]hue=h='6*t':s=2.1,rotate=a='0.04*t':ow=iw:oh=ih,"
                f"zoompan=z='{z_base}':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
                f":d=1:s={size}:fps={fps},eq=brightness=0.6:saturation=1.8[base]"
            )
        geo_filter = (
            f"[2:v]split=2[ga][gb];"
            f"[ga]crop=iw/2:ih:0:0[gl];"
            f"[gb]crop=iw/2:ih:0:0,hflip[gr];"
            f"[gl][gr]hstack,hue=h='-5*t':s=1.9,"
            f"zoompan=z='{z_geo}':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
            f":d=1:s={size}:fps={fps},eq=contrast=1.3:brightness=0.4:saturation=1.7,format=rgba,colorchannelmixer=aa=0.55[geo]"
        )
        fg_filter = (
            f"[0:v]zoompan=z='{zexpr}':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
            f":d=1:s={size}:fps={fps},hue=h='-4*t':s=1.5,eq=contrast=1.4:saturation=1.6:brightness=0.05,format=rgba,colorchannelmixer=aa=0.6[fg]"
        )
        vf_parts += [
            fg_filter,
            base_filter,
            geo_filter,
            f"[base][geo]overlay=0:0[bg2]",
            f"[bg2][fg]blend=all_mode=screen,format=yuv420p,eq=brightness='1+0.2*pow(max(0,cos(2*PI*n/{period:.4f})),6)':saturation=1.2[VIS]",
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
        vf_parts.append(f"[{src}]format=yuv420p,eq=brightness='1+0.18*pow(max(0,cos(2*PI*n/{period:.4f})),6)':saturation=1.15[VIS]")

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
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{dur:.3f}",
        "-metadata", f"title={credit_name or os.path.basename(output)}",
        "-metadata", f"comment={credit_sub or ''}",
        output,
    ]
    subprocess.run(cmd, check=True)
