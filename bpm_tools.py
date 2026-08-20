"""Lightweight BPM detection + tempo normalization.

No librosa/numba dependency: audio is resampled with ffmpeg, an onset-strength
envelope is built, and autocorrelation finds the dominant beat period. This is
very reliable for steady four-on-the-floor electronic music.
"""
import os
import shutil
import subprocess

import numpy as np

TARGET_SR = 22050
HOP = 512


def _load_mono(path):
    """ffmpeg-resample to mono 22050 Hz and return raw float32 samples."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ar", str(TARGET_SR), "-ac", "1",
         "-f", "f32le", "-"],
        check=True, capture_output=True,
    )
    return np.frombuffer(proc.stdout, dtype=np.float32)


def _onset_envelope(mono):
    n = len(mono) - (len(mono) % HOP)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    frames = mono[:n].reshape(-1, HOP)
    energy = np.sqrt(np.mean(frames ** 2, axis=1))
    onset = np.diff(energy)
    onset[onset < 0] = 0.0
    return onset


def detect_bpm(path, hint=None, min_bpm=60, max_bpm=200):
    """Estimate BPM of an audio file. `hint` biases peak selection toward it."""
    mono = _load_mono(path)
    onset = _onset_envelope(mono)
    if len(onset) < 64:
        return float(hint or 140.0)

    fps = TARGET_SR / HOP  # envelope frames per second
    lag_min = max(1, int(round(fps * 60.0 / max_bpm)))
    lag_max = min(len(onset) - 1, int(round(fps * 60.0 / min_bpm)))
    if lag_max <= lag_min:
        return float(hint or 140.0)

    corr = np.correlate(onset, onset, "full")
    center = len(onset) - 1
    lags = np.arange(lag_min, lag_max + 1)
    scores = corr[center + lags].astype(np.float64)
    # bias-correct toward longer windows
    scores = scores / np.maximum(1.0, (len(onset) - lags).astype(np.float64))

    bpm = 60.0 * fps / lags
    peaks = []
    for i in range(1, len(scores) - 1):
        if scores[i] >= scores[i - 1] and scores[i] >= scores[i + 1]:
            peaks.append(i)
    if not peaks:
        return float(hint or 140.0)

    cand_bpm = bpm[peaks]
    cand_score = scores[peaks]
    order = np.argsort(cand_score)[::-1]
    top = [(float(cand_bpm[i]), float(cand_score[i])) for i in order[:10]]

    if hint is not None:
        best = min(top, key=lambda x: abs(x[0] - hint))
    else:
        best = top[0]
    return best[0]


def _atempo_filter(factor):
    parts = []
    f = factor
    while f > 2.0:
        parts.append("atempo=2.0")
        f /= 2.0
    while f < 0.5:
        parts.append("atempo=0.5")
        f /= 0.5
    parts.append(f"atempo={f:.6f}")
    return ",".join(parts)


def normalize_bpm(in_path, out_path, target_bpm, dry_run=False):
    """Detect BPM and time-stretch `in_path` to `target_bpm`, writing `out_path`.

    Returns (detected_bpm, stretched: bool).
    """
    detected = detect_bpm(in_path, hint=target_bpm)
    factor = target_bpm / detected if detected else 1.0
    if dry_run or abs(factor - 1.0) < 0.01:
        if os.path.abspath(in_path) != os.path.abspath(out_path):
            shutil.copy(in_path, out_path)
        return detected, False

    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", in_path,
         "-filter:a", _atempo_filter(factor), "-vn", out_path],
        check=True,
    )
    return detected, True
