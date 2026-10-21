"""Read the ffmpeg drawtext timestamp overlay ("%Y-%m-%d_%H-%M-%S") from low-res YouTube renditions.

Each device's overlay sits at a fixed place, so the six time digits are cut out at fixed
cells and classified by nearest mean template. Templates are learned once from frames
labelled by tesseract (see train()).
"""
import re
import subprocess

import numpy as np

# DejaVuSans advance offsets (px at size 64) for "YYYY-MM-DD_HH-MM-SS"
ADV = [0.0, 40.72, 81.44, 122.16, 162.88, 185.97, 226.69, 267.41, 290.5, 331.22, 371.94,
       403.94, 444.66, 485.38, 508.47, 549.19, 589.91, 613.0, 653.72, 694.44]
TIME_CHARS = [11, 12, 14, 15, 17, 18]

# per device: youtube format, frame size, crop (x, y, w, h) holding the label, text x0/scale, digit rows
DEVICES = {
    "OT-2": dict(fmt="160", w=256, h=144, crop=(0, 0, 84, 12), x0=2.1, s=0.1112, y0=1, y1=10),
    "powder doser": dict(fmt="160", w=144, h=256, crop=(0, 0, 144, 16), x0=3.0, s=0.196, y0=2, y1=15),
}


def cells(dev):
    d = DEVICES[dev]
    out = []
    for i in TIME_CHARS:
        a = int(round(d["x0"] + ADV[i] * d["s"]))
        b = int(round(d["x0"] + ADV[i + 1] * d["s"]))
        out.append((a, b))
    w = max(b - a for a, b in out)
    return [(a, a + w) for a, _ in out], d["y0"], d["y1"]


def features(crops, dev):
    """crops: (N, h, w) uint8 -> (N, 6, F) normalised digit cells."""
    cs, y0, y1 = cells(dev)
    f = np.stack([crops[:, y0:y1, a:b].reshape(len(crops), -1) for a, b in cs], 1).astype(np.float32)
    f -= f.mean(2, keepdims=True)
    f /= f.std(2, keepdims=True) + 8.0
    return f


def frames(path, dev, extra=()):
    """Yield batches of cropped grayscale frames (N, h, w) from a video file (all frames decoded)."""
    x, y, w, h = DEVICES[dev]["crop"]
    cmd = ["ffmpeg", "-v", "error", "-threads", "1", *extra, "-i", path, "-an", "-fps_mode", "passthrough",
           "-vf", f"crop={w}:{h}:{x}:{y}", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = w * h * 4096
    while True:
        buf = p.stdout.read(n)
        if not buf:
            break
        a = np.frombuffer(buf, np.uint8)
        yield a[: len(a) // (w * h) * w * h].reshape(-1, h, w)
    p.wait()


LABEL_RE = re.compile(r"(\d{4})-(\d\d)-(\d\d)_?(\d\d)-(\d\d)-(\d\d)")


def tesseract_label(crop):
    import cv2
    import pytesseract
    c = 255 - cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    try:
        s = pytesseract.image_to_string(c, config="--psm 7 -c tessedit_char_whitelist=0123456789-_", timeout=3)
    except RuntimeError:
        return None
    m = LABEL_RE.search(s.replace(" ", ""))
    if not m:
        return None
    hh, mm, ss = (int(v) for v in m.groups()[3:])
    if hh > 23 or mm > 59 or ss > 59:
        return None
    return f"{hh:02d}{mm:02d}{ss:02d}"


def train(samples, dev):
    """samples: list of (crop, 'HHMMSS'). Returns templates (6, 10, F) and per-class counts."""
    crops = np.stack([c for c, _ in samples])
    f = features(crops, dev)
    T = np.zeros((6, 10, f.shape[2]), np.float32)
    cnt = np.zeros((6, 10), int)
    for k, (_, lab) in enumerate(samples):
        for i, ch in enumerate(lab):
            T[i, int(ch)] += f[k, i]
            cnt[i, int(ch)] += 1
    T /= np.maximum(cnt, 1)[..., None]
    return T, cnt


def classify(crops, dev, T, cnt):
    """Returns (N,) int seconds-of-day (-1 if unreadable) and (N,) worst-digit margin."""
    f = features(crops, dev)
    d = ((f[:, :, None, :] - T[None]) ** 2).sum(-1)  # N,6,10
    d[:, cnt == 0] = np.inf
    o = np.sort(d, 2)
    dig = d.argmin(2)
    margin = (o[:, :, 1] - o[:, :, 0]) / (o[:, :, 1] + 1e-6)
    hh = dig[:, 0] * 10 + dig[:, 1]
    mm = dig[:, 2] * 10 + dig[:, 3]
    ss = dig[:, 4] * 10 + dig[:, 5]
    sec = hh * 3600 + mm * 60 + ss
    bad = (hh > 23) | (mm > 59) | (ss > 59)
    sec[bad] = -1
    return sec, margin.min(1)
