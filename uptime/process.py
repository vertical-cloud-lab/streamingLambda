"""Read the timestamp overlay on every frame of every downloaded video.

Per video, writes results/<id>.npz with
  labels: unique overlay timestamps (unix seconds) that survive a weighted
          longest-increasing-subsequence filter (drops misreads, which break monotonicity)
  dwell:  seconds of video showing each label (~1 = healthy, >>1 = frozen picture)
Decoding skips B-frames (DECODE=noref, ~3x faster, still ~5 frames per video second); a jump of
2+ seconds between adjacent decoded frames is counted as "ambiguous" and such videos are re-read
with every frame decoded (DECODE=full).
and a stats row in results/<id>.json.
"""
import json
import os
import pickle
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta, timezone

import numpy as np

from overlay import DEVICES, classify, frames

VIDEO_DIR = os.environ.get("VIDEO_DIR", "/tmp/videos")
RES = os.environ.get("RESULTS_DIR", "results")
DECODE = os.environ.get("DECODE", "noref")
TZ = timezone(timedelta(hours=-6))  # overlay is Pi localtime (America/Denver, MDT during the whole period)
TEMPLATES = {}


def weighted_lis(vals, w):
    """Indices of the max-weight strictly increasing subsequence (Fenwick tree, O(n log n))."""
    u, r = np.unique(vals, return_inverse=True)
    m = len(u)
    tree_v = np.zeros(m + 1)
    tree_i = np.full(m + 1, -1)
    best = np.zeros(len(vals))
    prev = np.full(len(vals), -1)
    for k, (x, wt) in enumerate(zip(r, w)):
        # query max over ranks < x
        i, bv, bi = x, 0.0, -1
        while i > 0:
            if tree_v[i] > bv:
                bv, bi = tree_v[i], tree_i[i]
            i -= i & -i
        best[k], prev[k] = bv + wt, bi
        i = x + 1
        while i <= m:
            if best[k] > tree_v[i]:
                tree_v[i], tree_i[i] = best[k], k
            i += i & -i
    k = int(best.argmax())
    out = []
    while k >= 0:
        out.append(k)
        k = prev[k]
    return np.array(out[::-1], int)


def run(item):
    vid, dev, start_utc = item
    path = f"{VIDEO_DIR}/{vid}.mp4"
    T, cnt = TEMPLATES[dev]
    t0 = time.time()
    secs, margins = [], []
    extra = ("-skip_frame", "noref") if DECODE == "noref" else ()
    for batch in frames(path, dev, extra):
        s, m = classify(batch, dev, T, cnt)
        secs.append(s)
        margins.append(m)
    sec = np.concatenate(secs)
    margin = np.concatenate(margins)
    n = len(sec)
    ok = sec >= 0
    # day assignment: overlay is local time; broadcasts are < 13 h
    start = datetime.fromisoformat(start_utc.replace("Z", "+00:00")).astimezone(TZ)
    day0 = int(datetime(start.year, start.month, start.day, tzinfo=TZ).timestamp())
    s0 = start.hour * 3600 + start.minute * 60 + start.second
    ab = np.where(sec >= s0 - 3600, day0 + sec, day0 + 86400 + sec)
    ab[~ok] = -1
    # run-length encode readable frames
    idx = np.where(ok)[0]
    a = ab[idx]
    brk = np.r_[True, (a[1:] != a[:-1]) | (np.diff(idx) != 1)]
    rs = np.where(brk)[0]
    rl = np.diff(np.r_[rs, len(a)])
    rv = a[rs]
    keep = weighted_lis(rv, rl) if len(rv) else np.array([], int)
    # sum dwell over (possibly split) runs of the same kept label
    kv, kl = rv[keep], rl[keep]
    labels, inv = np.unique(kv, return_inverse=True)
    video_s = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    path], capture_output=True, text=True).stdout.strip() or 0)
    fs = video_s / max(n, 1)  # seconds of video per decoded frame
    dwell = np.round(np.bincount(inv, weights=kl) * fs, 2) if len(kv) else np.array([])
    # jumps of 2+ s between adjacent decoded frames: skipped B-frames may have held other labels
    ke = rs[keep] + rl[keep] - 1  # last readable-frame position of each kept run
    adj = idx[rs[keep][1:]] - idx[ke[:-1]] == 1
    ambiguous = int(((np.diff(kv) >= 2) & adj).sum()) if len(kv) > 1 else 0
    np.savez_compressed(f"{RES}/{vid}.npz", labels=labels, dwell=dwell)
    stats = dict(id=vid, device=dev, start=start_utc, decode=DECODE, frames=int(n), video_s=round(video_s, 2),
                 ambiguous=ambiguous,
                 unreadable=int((~ok).sum()), runs=int(len(rv)), runs_dropped=int(len(rv) - len(keep)),
                 frames_dropped=int(rl.sum() - kl.sum()), unique=int(len(labels)),
                 first=int(labels[0]) if len(labels) else None, last=int(labels[-1]) if len(labels) else None,
                 low_margin=int((margin[ok] < 0.05).sum()), secs=round(time.time() - t0, 1))
    json.dump(stats, open(f"{RES}/{vid}.json", "w"))
    return stats


def init():
    for dev in DEVICES:
        TEMPLATES[dev] = pickle.load(open(f"templates_{dev.replace(' ', '_')}.pkl", "rb"))


def main(workers=3, ids=None):
    os.makedirs(RES, exist_ok=True)
    b = json.load(open("broadcasts.json"))
    todo = []
    for x in sorted(b, key=lambda x: x["snippet"].get("actualStartTime") or ""):
        dev = x["snippet"]["title"].split(" stream ")[0]
        vid = x["id"]
        if ids is not None:
            if vid in ids:
                todo.append((vid, dev, x["snippet"]["actualStartTime"]))
        elif dev in DEVICES and os.path.exists(f"{VIDEO_DIR}/{vid}.mp4") and not os.path.exists(f"{RES}/{vid}.json"):
            todo.append((vid, dev, x["snippet"]["actualStartTime"]))
    with ProcessPoolExecutor(workers, initializer=init) as ex:
        for st in ex.map(run, todo):
            print(json.dumps(st), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2:] or None)
