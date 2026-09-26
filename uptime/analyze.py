"""Turn per-video overlay reads (results/*.npz) into uptime numbers, plots and a gap list.

uptime = unique overlay timestamps / seconds in the device's window, where the window runs from
the device's first broadcast start to the end of its last completed broadcast.
"""
import glob
import json
import os
from datetime import datetime, timedelta, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from overlay import DEVICES

TZ = timezone(timedelta(hours=-6))
RES = "results"
OUT = "plots"
COLOR = {"OT-2": "#2a78d6", "powder doser": "#eb6834"}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
})


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def runs(mask_or_sorted):
    """Contiguous runs of consecutive integers -> (starts, ends) inclusive."""
    a = mask_or_sorted
    if len(a) == 0:
        return np.array([], int), np.array([], int)
    brk = np.where(np.diff(a) != 1)[0]
    return a[np.r_[0, brk + 1]], a[np.r_[brk, len(a) - 1]]


def load():
    b = json.load(open("broadcasts.json"))
    stats = {s["id"]: s for s in (json.load(open(f)) for f in glob.glob(f"{RES}/*.json"))}
    out = {}
    for dev in DEVICES:
        bs = sorted([x for x in b if x["snippet"]["title"].split(" stream ")[0] == dev
                     and x["snippet"].get("actualStartTime")], key=lambda x: x["snippet"]["actualStartTime"])
        done = [x for x in bs if x["status"]["lifeCycleStatus"] == "complete"]
        t0 = ts(bs[0]["snippet"]["actualStartTime"])
        t1 = ts(done[-1]["snippet"]["actualEndTime"])
        bint = [(ts(x["snippet"]["actualStartTime"]), ts(x["snippet"].get("actualEndTime") or done[-1]["snippet"]["actualEndTime"]))
                for x in bs]
        labels = [np.load(f"{RES}/{x['id']}.npz")["labels"] for x in done if x["id"] in stats]
        missing = [x["id"] for x in done if x["id"] not in stats]
        lab = np.unique(np.concatenate(labels)) if labels else np.array([], int)
        lab = lab[(lab >= t0) & (lab <= t1)]
        out[dev] = dict(t0=t0, t1=t1, labels=lab, bint=bint, broadcasts=bs, done=done,
                        stats=[stats[x["id"]] for x in done if x["id"] in stats], missing=missing)
    return out


def analyze(d):
    t0, t1, lab = d["t0"], d["t1"], d["labels"]
    n = t1 - t0 + 1
    up = np.zeros(n, bool)
    up[lab - t0] = True
    inb = np.zeros(n, bool)
    for a, b in d["bint"]:
        inb[max(a, t0) - t0:min(b, t1) - t0 + 1] = True
    # videos we could not read: exclude their span from the denominator
    na = np.zeros(n, bool)
    for x in d["done"]:
        if x["id"] in d["missing"]:
            a, b = ts(x["snippet"]["actualStartTime"]), ts(x["snippet"]["actualEndTime"])
            na[a - t0:b - t0 + 1] = True
    na &= ~up
    down = ~up & ~na
    gs, ge = runs(np.where(down)[0])
    gaps = []
    for s, e in zip(gs, ge):
        seg = inb[s:e + 1]
        g = dict(start=int(t0 + s), end=int(t0 + e), dur=int(e - s + 1),
                 in_broadcast=int(seg.sum()), no_broadcast=int((~seg).sum()))
        g["cause"] = cause(g)
        gaps.append(g)
    return dict(n=int(n), na=int(na.sum()), up=int(up.sum()), down=int(down.sum()),
                down_in_broadcast=int((down & inb).sum()), down_no_broadcast=int((down & ~inb).sum()),
                upv=up, nav=na, inb=inb, gaps=gaps)


ROTATIONS = (5, 13, 21)  # local hours of the scheduled reboot / new broadcast


def cause(g):
    """Rough bucket for a gap: scheduled rotation, blip, no broadcast at all, or stream dead while live."""
    ls, le = local(g["start"]), local(g["end"])
    for h in ROTATIONS:
        for day in {ls.date(), le.date()}:
            r = datetime(day.year, day.month, day.day, h, tzinfo=TZ).timestamp()
            if g["start"] - 60 <= r <= g["end"] + 1 and g["dur"] <= 600:
                return "scheduled reboot/rotation"
    if g["dur"] < 10:
        return "blip < 10 s"
    if g["no_broadcast"] > g["in_broadcast"]:
        return "no broadcast"
    return "broadcast live but no frames"


CAUSES = ["scheduled reboot/rotation", "blip < 10 s", "broadcast live but no frames", "no broadcast"]


def local(t):
    return datetime.fromtimestamp(t, TZ)


def fmt_dur(s):
    if s < 120:
        return f"{s} s"
    if s < 7200:
        return f"{s / 60:.0f} min"
    return f"{s / 3600:.1f} h"


def broadcast_coverage():
    """Upper bound for every device, from the API alone: share of its window inside some broadcast."""
    b = json.load(open("broadcasts.json"))
    v = json.load(open("videos.json"))
    out = {}
    for dev in sorted({x["snippet"]["title"].split(" stream ")[0] for x in b}):
        bs = [x for x in b if x["snippet"]["title"].split(" stream ")[0] == dev and x["snippet"].get("actualStartTime")]
        if not bs:
            continue
        iv = sorted((ts(x["snippet"]["actualStartTime"]), ts(x["snippet"]["actualEndTime"])) for x in bs
                    if x["snippet"].get("actualEndTime"))
        if not iv:
            continue
        t0, t1 = iv[0][0], max(e for _, e in iv)
        cov, cur_s, cur_e = 0, *iv[0]
        for s, e in iv[1:]:
            if s > cur_e:
                cov += cur_e - cur_s
                cur_s, cur_e = s, e
            else:
                cur_e = max(cur_e, e)
        cov += cur_e - cur_s
        out[dev] = dict(first=local(t0).strftime("%Y-%m-%d %H:%M"), last=local(t1).strftime("%Y-%m-%d %H:%M"),
                        broadcasts=len(bs), privacy=sorted({x["status"]["privacyStatus"] for x in bs}),
                        window_h=round((t1 - t0) / 3600, 1), broadcast_h=round(cov / 3600, 1),
                        coverage=round(cov / (t1 - t0), 4))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    data = load()
    A = {dev: analyze(d) for dev, d in data.items()}
    summary = {}
    for dev, a in A.items():
        d = data[dev]
        denom = a["n"] - a["na"]
        big = sorted(a["gaps"], key=lambda g: -g["dur"])
        buckets = {"<10 s": (0, 10), "10 s-2 min": (10, 120), "2-30 min": (120, 1800), "30 min-2 h": (1800, 7200), ">2 h": (7200, 1e12)}
        summary[dev] = dict(
            window_start=local(d["t0"]).isoformat(), window_end=local(d["t1"]).isoformat(),
            window_s=a["n"], not_analyzed_s=a["na"], unique_s=a["up"], uptime=a["up"] / denom,
            down_s=a["down"], down_in_broadcast_s=a["down_in_broadcast"], down_no_broadcast_s=a["down_no_broadcast"],
            broadcasts=len(d["broadcasts"]), videos_read=len(d["stats"]), videos_missing=d["missing"],
            ambiguous_jumps=sum(s.get("ambiguous", 0) for s in d["stats"]),
            misreads_dropped=sum(s["runs_dropped"] for s in d["stats"]),
            unreadable_frames=sum(s["unreadable"] for s in d["stats"]),
            frames=sum(s["frames"] for s in d["stats"]),
            gaps=len(a["gaps"]),
            causes={c: dict(n=sum(g["cause"] == c for g in a["gaps"]), s=sum(g["dur"] for g in a["gaps"] if g["cause"] == c))
                    for c in CAUSES},
            gap_buckets={k: dict(n=sum(lo <= g["dur"] < hi for g in a["gaps"]),
                                 s=sum(g["dur"] for g in a["gaps"] if lo <= g["dur"] < hi)) for k, (lo, hi) in buckets.items()},
            largest_gaps=[dict(start=local(g["start"]).strftime("%Y-%m-%d %H:%M:%S"), dur=fmt_dur(g["dur"]),
                               dur_s=g["dur"], no_broadcast_s=g["no_broadcast"], cause=g["cause"]) for g in big[:15]],
        )
    # downtime shared by both cameras (same wall-clock second) -> common cause (network, YouTube, power)
    devs = list(A)
    if len(devs) == 2:
        lo = max(data[x]["t0"] for x in devs)
        hi = min(data[x]["t1"] for x in devs)
        dn = [((~A[x]["upv"]) & ~A[x]["nav"])[lo - data[x]["t0"]:hi - data[x]["t0"] + 1] for x in devs]
        ok = [(~A[x]["nav"])[lo - data[x]["t0"]:hi - data[x]["t0"] + 1] for x in devs]
        both_ok = ok[0] & ok[1]
        summary["shared_downtime"] = dict(
            both_down_s=int((dn[0] & dn[1] & both_ok).sum()),
            **{f"{x}_down_s": int((dn[i] & both_ok).sum()) for i, x in enumerate(devs)})
    summary["broadcast_coverage_all_devices"] = broadcast_coverage()
    json.dump(summary, open("summary.json", "w"), indent=1)
    with open("gaps.csv", "w") as f:
        f.write("device,start_local,end_local,duration_s,no_broadcast_s,in_broadcast_s,cause\n")
        for dev, a in A.items():
            for g in a["gaps"]:
                f.write(f"{dev},{local(g['start']):%Y-%m-%d %H:%M:%S},{local(g['end']):%Y-%m-%d %H:%M:%S},"
                        f"{g['dur']},{g['no_broadcast']},{g['in_broadcast']},{g['cause']}\n")

    # ---- daily uptime -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 3.8))
    daily = {}
    for dev, a in A.items():
        t0 = data[dev]["t0"]
        tt = t0 + np.arange(a["n"])
        day = np.array([local(t).date() for t in tt[::3600]])  # hourly resolution for the date map
        dd = np.repeat(day, 3600)[:a["n"]]
        days = sorted(set(day))
        vals = []
        for dy in days:
            m = (dd == dy) & ~a["nav"]
            vals.append(a["upv"][m].mean() if m.sum() > 3600 else np.nan)
        daily[dev] = (days, np.array(vals))
        x = [datetime(dy.year, dy.month, dy.day, 12) for dy in days]
        ax.plot(x, 100 * np.array(vals), color=COLOR[dev], lw=2, marker="o", ms=3.5, label=dev)
        ax.annotate(f"{dev}", (x[-1], 100 * vals[-1]), xytext=(6, 0), textcoords="offset points",
                    color=INK2, va="center", fontsize=9)
    ax.set_ylabel("uptime per day (%)")
    lo = np.nanmin([np.nanmin(v) for _, v in daily.values()])
    ax.set_ylim(max(0, np.floor(lo * 10) * 10 - 5), 100.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.legend(frameon=False, loc="lower left")
    ax.set_title("Daily uptime from unique overlay timestamps (MDT days)", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(f"{OUT}/daily_uptime.png", dpi=150)
    plt.close(fig)

    # ---- day x hour heatmap per device (sequential blue) ------------------------------------------
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("b", ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#104281"])
    cmap.set_bad("#d9d8d4")
    fig, axs = plt.subplots(1, len(A), figsize=(11, 7.5), sharey=True)
    for ax, (dev, a) in zip(axs, A.items()):
        t0 = data[dev]["t0"]
        l0 = local(t0)
        start = int(datetime(l0.year, l0.month, l0.day, tzinfo=TZ).timestamp())
        l1 = local(data[dev]["t1"])
        ndays = (datetime(l1.year, l1.month, l1.day, tzinfo=TZ) - datetime(l0.year, l0.month, l0.day, tzinfo=TZ)).days + 1
        grid = np.full((ndays, 24), np.nan)
        off = t0 - start
        full = np.full(ndays * 86400, -1, np.int8)
        seg = np.where(a["nav"], -1, a["upv"].astype(np.int8))
        full[off:off + a["n"]] = seg
        h = full.reshape(ndays, 24, 3600)
        valid = (h >= 0).sum(2)
        with np.errstate(invalid="ignore"):
            grid = np.where(valid > 600, (h == 0).sum(2) / np.maximum(valid, 1), np.nan)
        im = ax.imshow(100 * grid, aspect="auto", cmap=cmap, vmin=0, vmax=100, interpolation="nearest",
                       extent=(0, 24, ndays, 0))
        ax.set_title(dev, loc="left", fontsize=11)
        ax.set_xticks([0, 5, 13, 21, 24])
        ax.set_xlabel("hour of day (MDT)")
        ax.grid(False)
        yt = list(range(0, ndays, 7))
        ax.set_yticks([y + 0.5 for y in yt])
        ax.set_yticklabels([(l0 + timedelta(days=y)).strftime("%b %d") for y in yt])
    cb = fig.colorbar(im, ax=axs, shrink=0.6, pad=0.02)
    cb.set_label("downtime in the hour (%)")
    cb.outline.set_visible(False)
    fig.suptitle("Downtime by hour of day (white = fully up; gray = outside window / video not readable)", x=0.06, ha="left", fontsize=11)
    fig.savefig(f"{OUT}/hourly_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # ---- where the downtime went: gap-duration buckets ----------------------------------------------
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    keys = list(next(iter(summary.values()))["gap_buckets"])
    xk = np.arange(len(keys))
    w = 0.38
    for i, dev in enumerate(A):
        gb = summary[dev]["gap_buckets"]
        axs[0].bar(xk + (i - 0.5) * (w + 0.02), [gb[k]["s"] / 3600 for k in keys], w, color=COLOR[dev], label=dev)
        axs[1].bar(xk + (i - 0.5) * (w + 0.02), [gb[k]["n"] for k in keys], w, color=COLOR[dev], label=dev)
    for ax, t in zip(axs, ["downtime (hours) by gap length", "number of gaps by gap length"]):
        ax.set_xticks(xk)
        ax.set_xticklabels(keys)
        ax.set_title(t, loc="left", fontsize=11)
        ax.grid(axis="x", visible=False)
    axs[1].set_yscale("log")
    axs[0].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(f"{OUT}/gap_buckets.png", dpi=150)
    plt.close(fig)

    # ---- downtime by cause ------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 3.2))
    yk = np.arange(len(CAUSES))
    h = 0.38
    for i, dev in enumerate(A):
        vals = [summary[dev]["causes"][c]["s"] / 3600 for c in CAUSES]
        ax.barh(yk + (i - 0.5) * (h + 0.02), vals, h, color=COLOR[dev], label=dev)
        for y, v, c in zip(yk, vals, CAUSES):
            ax.annotate(f"{v:.1f} h ({summary[dev]['causes'][c]['n']} gaps)", (v, y + (i - 0.5) * (h + 0.02)),
                        xytext=(4, 0), textcoords="offset points", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(yk)
    ax.set_yticklabels(CAUSES)
    ax.invert_yaxis()
    ax.set_xlabel("hours lost")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, ax.get_xlim()[1] * 1.25)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("Where the downtime went", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(f"{OUT}/downtime_by_cause.png", dpi=150)
    plt.close(fig)

    # ---- downtime vs local time of day ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 3.4))
    for dev, a in A.items():
        t0 = data[dev]["t0"]
        tt = t0 + np.arange(a["n"])
        mod = ((tt - 6 * 3600) % 86400) // 60  # local minute of day
        ok = ~a["nav"]
        tot = np.bincount(mod[ok], minlength=1440)
        dn = np.bincount(mod[ok & ~a["upv"]], minlength=1440)
        ax.plot(np.arange(1440) / 60, 100 * dn / np.maximum(tot, 1), color=COLOR[dev], lw=1.2, label=dev)
    ax.set_xticks(range(0, 25, 1))
    ax.set_xlim(0, 24)
    ax.set_xlabel("time of day (MDT)")
    ax.set_ylabel("% of days down")
    ax.legend(frameon=False)
    ax.set_title("Share of days each minute was lost (reboots at 05:00, 13:00, 21:00)", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(f"{OUT}/downtime_by_minute.png", dpi=150)
    plt.close(fig)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("largest_gaps",)} for k, v in summary.items()}, indent=1, default=str))


if __name__ == "__main__":
    main()
