"""Assign each gap in gaps.csv to a root cause, using what the Pi journals showed (see ../pi/README.md).

Only needs gaps.csv, so it runs without the per-video reads. Writes plots/root_cause.png and
root_cause.json, and prints a markdown table.

Rules, applied in order to every gap:
- known events from the journals and byu-vcl#202 (DNS outage, OT-2 power loss / unclean reboot)
- starts 40-60 s after hh:00 or hh:30 and lasts >= 10 min: the Pi lost its address at a DHCP
  renewal after a bogus ARP conflict. Both Pis boot at 05:00/13:00/21:00, get a 1 h lease, and
  renew at hh:00:4x / hh:30:4x. All three such gaps the journals cover match this, to the second.
- other gaps >= 10 min: unknown (mostly before the journals start on 09-15 / 09-20)
- the rest: scheduled reboot or a short gap, as in analyze.py
"""
import csv
import json
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLOR = {"OT-2": "#2a78d6", "powder doser": "#eb6834"}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
})

RENEWAL = "address dropped at DHCP renewal"
DNS = "campus DNS outage (09-24)"
POWER = "power loss / unclean reboot"
UNKNOWN = "other stall >= 10 min"
REBOOT = "scheduled reboots"
SHORT = "short gaps < 10 min"
CAUSES = [RENEWAL, DNS, POWER, UNKNOWN, REBOOT, SHORT]

# (device or None for both, start, end, cause); a gap is matched by its start time
KNOWN = [
    (None, "2026-09-24 11:55", "2026-09-24 21:02", DNS),
    ("OT-2", "2026-09-23 12:30", "2026-09-23 12:40", POWER),
    ("OT-2", "2026-09-25 13:05", "2026-09-25 13:15", POWER),
]


def classify(r):
    s = datetime.fromisoformat(r["start_local"])
    dur = int(r["duration_s"])
    for dev, a, b, c in KNOWN:
        if dev in (None, r["device"]) and datetime.fromisoformat(a) <= s <= datetime.fromisoformat(b):
            return c
    if dur >= 600 and 40 <= (s.minute % 30) * 60 + s.second <= 60:
        return RENEWAL
    if dur >= 600:
        return UNKNOWN
    if r["cause"].startswith("scheduled"):
        return REBOOT
    return SHORT


def main():
    rows = list(csv.DictReader(open("gaps.csv")))
    summary = json.load(open("summary.json"))
    out = {}
    for r in rows:
        d = out.setdefault(r["device"], {c: {"s": 0, "n": 0} for c in CAUSES})
        c = classify(r)
        d[c]["s"] += int(r["duration_s"])
        d[c]["n"] += 1
    for dev, d in out.items():
        win = summary[dev]["window_s"]
        up = summary[dev]["unique_s"]
        d["_uptime"] = up / win
        d["_uptime_without_renewal_drops"] = (up + d[RENEWAL]["s"]) / win
    json.dump(out, open("root_cause.json", "w"), indent=1)

    print("| cause | " + " | ".join(out) + " |\n|---|" + "---|" * len(out))
    for c in CAUSES:
        print(f"| {c} | " + " | ".join(f"{d[c]['s'] / 3600:.1f} h ({d[c]['n']})" for d in out.values()) + " |")
    print("| uptime | " + " | ".join(f"{d['_uptime']:.2%}" for d in out.values()) + " |")
    print("| uptime without renewal drops | "
          + " | ".join(f"{d['_uptime_without_renewal_drops']:.2%}" for d in out.values()) + " |")

    fig, ax = plt.subplots(figsize=(10, 3.4))
    yk = np.arange(len(CAUSES))
    h = 0.38
    for i, (dev, d) in enumerate(out.items()):
        vals = [d[c]["s"] / 3600 for c in CAUSES]
        ax.barh(yk + (i - 0.5) * (h + 0.02), vals, h, color=COLOR[dev], label=dev)
        for y, v, c in zip(yk, vals, CAUSES):
            ax.annotate(f"{v:.1f} h ({d[c]['n']})", (v, y + (i - 0.5) * (h + 0.02)),
                        xytext=(4, 0), textcoords="offset points", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(yk)
    ax.set_yticklabels(CAUSES)
    ax.invert_yaxis()
    ax.set_xlabel("hours lost (number of gaps)")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, ax.get_xlim()[1] * 1.2)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("Downtime by root cause", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig("plots/root_cause.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
