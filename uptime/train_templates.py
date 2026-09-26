"""Learn the digit templates used by process.py (templates_<device>.pkl).

1. tesseract-label ~750 frames of one 8 h video per device (OT-2: read the 360p rendition and
   use the aligned 144p frames; powder doser: 144p is legible as is) -> templates for the digits seen.
2. self-train the rest: in three more videos read MM:SS with those templates and take HH from
   the broadcast start + video position (these videos drift < 2 s), then refit on everything.

usage: python train_templates.py OT-2 <8h.mp4 144p> <same video 360p> <id> <id> <id>
       python train_templates.py "powder doser" <8h.mp4 144p> - <id> <id> <id>
"""
import json
import pickle
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from multiprocessing import Pool

import numpy as np

from overlay import DEVICES, features, tesseract_label, train

TZ = timezone(timedelta(hours=-6))


def grab(path, crop, step):
    x, y, cw, ch = crop
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-an", "-vf", f"select=not(mod(n\\,{step})),crop={cw}:{ch}:{x}:{y}",
           "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.uint8).reshape(-1, ch, cw)


def main(dev, low_path, ref_path, *ids):
    low = grab(low_path, DEVICES[dev]["crop"], 1141)
    ref = grab(ref_path, (0, 0, 216, 30), 1141) if ref_path != "-" else low
    n = min(len(low), len(ref))
    with Pool(4) as p:
        labs = p.map(tesseract_label, list(ref[:n]), chunksize=20)
    samples = [(low[i], lab) for i, lab in enumerate(labs) if lab]
    T, cnt = train(samples, dev)

    b = {x["id"]: x for x in json.load(open("broadcasts.json"))}
    step = 577
    for vid in ids:
        crops = grab(f"/tmp/videos/{vid}.mp4", DEVICES[dev]["crop"], step)
        d = ((features(crops, dev)[:, :, None, :] - T[None]) ** 2).sum(-1)
        d[:, cnt == 0] = np.inf
        dig, o = d.argmin(2), np.sort(d, 2)
        marg = (o[:, :, 1] - o[:, :, 0]) / (o[:, :, 1] + 1e-6)
        mm, ss = dig[:, 2] * 10 + dig[:, 3], dig[:, 4] * 10 + dig[:, 5]
        st = datetime.fromisoformat(b[vid]["snippet"]["actualStartTime"].replace("Z", "+00:00")).astimezone(TZ)
        approx = st.hour * 3600 + st.minute * 60 + st.second + np.arange(len(crops)) * step / 30.0 - 6
        cands = np.stack([(np.floor(approx / 3600) + k) * 3600 + mm * 60 + ss for k in (-1, 0, 1)])
        t = cands[np.abs(cands - approx).argmin(0), np.arange(len(mm))]
        ok = (marg[:, 2:].min(1) > 0.05) & (mm < 60) & (ss < 60)
        good = ok & (np.abs(t - approx - np.median((t - approx)[ok])) < 120)
        samples += [(crops[i], f"{int(t[i] // 3600) % 24:02d}{mm[i]:02d}{ss[i]:02d}") for i in np.where(good)[0]]
    pickle.dump(train(samples, dev), open(f"templates_{dev.replace(' ', '_')}.pkl", "wb"))


if __name__ == "__main__":
    main(*sys.argv[1:])
