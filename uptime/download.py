"""Download low-res renditions of every archived broadcast (through a SOCKS proxy on a campus Pi,
because YouTube bot-blocks the CI runner)."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

OUT = os.environ.get("VIDEO_DIR", "/tmp/videos")
PROXIES = os.environ.get("YTDLP_PROXIES", "socks5://127.0.0.1:1081").split(",")
FMT = {"OT-2": "160", "powder doser": "160"}


def job(item):
    k, dev, vid = item
    dst = f"{OUT}/{vid}.mp4"
    if os.path.exists(dst):
        return vid, "cached"
    r = subprocess.run(["yt-dlp", "-q", "--no-progress", "--proxy", PROXIES[k % len(PROXIES)], "-f", FMT[dev], "-o", dst,
                        f"https://www.youtube.com/watch?v={vid}"], capture_output=True, text=True, timeout=3600)
    return vid, "ok" if r.returncode == 0 else r.stderr.strip().splitlines()[-1:]


def main(broadcasts="broadcasts.json", workers=6):
    os.makedirs(OUT, exist_ok=True)
    b = json.load(open(broadcasts))
    items = []
    for x in b:
        dev = x["snippet"]["title"].split(" stream ")[0]
        if dev in FMT and x["status"]["lifeCycleStatus"] == "complete":
            items.append((x["snippet"]["actualStartTime"], dev, x["id"]))
    items.sort()
    with ThreadPoolExecutor(workers) as ex:
        for vid, st in ex.map(job, [(k, d, v) for k, (_, d, v) in enumerate(items)]):
            print(vid, st, flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:2], *[int(a) for a in sys.argv[2:3]])
