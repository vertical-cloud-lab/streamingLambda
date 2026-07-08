# PR #234: Added ability to download yt videos

- **URL:** https://github.com/AccelerationConsortium/ac-dev-lab/pull/234
- **Author:** @Jonathan-Woo
- **State:** closed (merged)
- **Created:** 2025-05-01T15:47:19Z  **Closed:** 2025-05-01T23:21:04Z
- **Comments archived:** 7 issue comments
- **Review comments:** 0; **Reviews:** 1; **Files changed:** src/ac_training_lab/video_editing/yt_utils.py

---

## Original description

Reusing `get_latest_video_id` from HF and using [yt-dlp](https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file). Included the platform independent yt-dlp binary.

```
(base) ➜  video_editing git:(yt-download) ✗ python yt_utils.py 
Download successful!
[youtube] Extracting URL: https://www.youtube.com/live/ktj2CUfRv0w
[youtube] ktj2CUfRv0w: Downloading webpage
[youtube] ktj2CUfRv0w: Downloading tv client config
[youtube] ktj2CUfRv0w: Downloading player aa3fc80b-main
[youtube] ktj2CUfRv0w: Downloading tv player API JSON
[youtube] ktj2CUfRv0w: Downloading ios player API JSON
[youtube] ktj2CUfRv0w: Downloading m3u8 information
[info] ktj2CUfRv0w: Downloading 1 format(s): 135+251
[download] Destination: Opentrons OT-2 Livestream @ AC Training Lab [ktj2CUfRv0w].f135.m
p4

[download]   0.0% of   37.48MiB at  Unknown B/s ETA Unknown
[download]   0.0% of   37.48MiB at    2.27MiB/s ETA 00:16  
[download]   0.0% of   37.48MiB at    3.80MiB/s ETA 00:09
[download]   0.0% of   37.48MiB at    5.85MiB/s ETA 00:06
[download]   0.1% of   37.48MiB at    8.48MiB/s ETA 00:04
[download]   0.2% of   37.48MiB at    9.36MiB/s ETA 00:04
[download]   0.3% of   37.48MiB at   13.49MiB/s ETA 00:02
[download]   0.7% of   37.48MiB at   16.77MiB/s ETA 00:02
[download]   1.3% of   37.48MiB at   18.58MiB/s ETA 00:01
[download]   2.7% of   37.48MiB at   25.10MiB/s ETA 00:01
[download]   5.3% of   37.48MiB at   28.00MiB/s ETA 00:01
[download]  10.7% of   37.48MiB at   28.33MiB/s ETA 00:01
[download]  21.3% of   37.48MiB at   29.79MiB/s ETA 00:00
[download]  26.1% of   37.48MiB at   30.31MiB/s ETA 00:00
[download]  26.1% of   37.48MiB at  484.95KiB/s ETA 00:58
[download]  26.1% of   37.48MiB at    1.10MiB/s ETA 00:25
[download]  26.1% of   37.48MiB at    2.16MiB/s ETA 00:12
[download]  26.1% of   37.48MiB at    3.97MiB/s ETA 00:06
[download]  26.2% of   37.48MiB at    6.86MiB/s ETA 00:04
[download]  26.3% of   37.48MiB at   10.06MiB/s ETA 00:02
[download]  26.4% of   37.48MiB at   12.78MiB/s ETA 00:02
[download]  26.8% of   37.48MiB at   10.92MiB/s ETA 00:02
[download]  27.4% of   37.48MiB at   14.77MiB/s ETA 00:01
[download]  28.8% of   37.48MiB at   20.38MiB/s ETA 00:01
[download]  31.4% of   37.48MiB at   22.68MiB/s ETA 00:01
[download]  36.8% of   37.48MiB at   26.23MiB/s ETA 00:00
[download]  47.4% of   37.48MiB at   27.91MiB/s ETA 00:00
[download]  51.8% of   37.48MiB at   29.36MiB/s ETA 00:00
[download]  51.8% of   37.48MiB at  547.63KiB/s ETA 00:34
[download]  51.8% of   37.48MiB at    1.23MiB/s ETA 00:14
[download]  51.8% of   37.48MiB at    2.33MiB/s ETA 00:07
[download]  51.8% of   37.48MiB at    4.20MiB/s ETA 00:04
[download]  51.8% of   37.48MiB at    7.01MiB/s ETA 00:02
[download]  51.9% of   37.48MiB at    8.48MiB/s ETA 00:02
[download]  52.1% of   37.48MiB at   13.16MiB/s ETA 00:01
[download]  52.4% of   37.48MiB at   16.02MiB/s ETA 00:01
[download]  53.1% of   37.48MiB at   17.46MiB/s ETA 00:01
[download]  54.4% of   37.48MiB at   14.19MiB/s ETA 00:01
[download]  57.1% of   37.48MiB at   16.70MiB/s ETA 00:00
[download]  62.4% of   37.48MiB at   17.18MiB/s ETA 00:00
[download]  73.1% of   37.48MiB at   20.51MiB/s ETA 00:00
[download]  78.2% of   37.48MiB at   21.39MiB/s ETA 00:00
[download]  78.2% of   37.48MiB at  Unknown B/s ETA Unknown
[download]  78.2% of   37.48MiB at    1.80MiB/s ETA 00:04  
[download]  78.2% of   37.48MiB at    3.19MiB/s ETA 00:02
[download]  78.2% of   37.48MiB at    5.54MiB/s ETA 00:01
[download]  78.3% of   37.48MiB at    9.57MiB/s ETA 00:00
[download]  78.3% of   37.48MiB at    9.02MiB/s ETA 00:00
[download]  78.5% of   37.48MiB at   10.72MiB/s ETA 00:00
[download]  78.8% of   37.48MiB at   13.75MiB/s ETA 00:00
[download]  79.5% of   37.48MiB at   17.75MiB/s ETA 00:00
[download]  80.8% of   37.48MiB at   17.45MiB/s ETA 00:00
[download]  83.5% of   37.48MiB at   19.36MiB/s ETA 00:00
[download]  88.8% of   37.48MiB at   21.09MiB/s ETA 00:00
[download]  99.5% of   37.48MiB at   17.05MiB/s ETA 00:00
[download] 100.0% of   37.48MiB at   17.25MiB/s ETA 00:00
[download] 100% of   37.48MiB in 00:00:01 at 22.16MiB/s  
[download] Destination: Opentrons OT-2 Livestream @ AC Training Lab [ktj2CUf
ebm

[download]   0.0% of    4.73MiB at  Unknown B/s ETA Unknown
[download]   0.1% of    4.73MiB at    2.57MiB/s ETA 00:01  
[download]   0.1% of    4.73MiB at    3.97MiB/s ETA 00:01
[download]   0.3% of    4.73MiB at    6.57MiB/s ETA 00:00
[download]   0.6% of    4.73MiB at    8.14MiB/s ETA 00:00
[download]   1.3% of    4.73MiB at    9.41MiB/s ETA 00:00
[download]   2.6% of    4.73MiB at   11.66MiB/s ETA 00:00
[download]   5.3% of    4.73MiB at   13.81MiB/s ETA 00:00
[download]  10.5% of    4.73MiB at   17.99MiB/s ETA 00:00
[download]  21.1% of    4.73MiB at   21.33MiB/s ETA 00:00
[download]  42.3% of    4.73MiB at   20.64MiB/s ETA 00:00
[download]  84.5% of    4.73MiB at   22.44MiB/s ETA 00:00
[download] 100.0% of    4.73MiB at   22.32MiB/s ETA 00:00
[download] 100% of    4.73MiB in 00:00:00 at 16.17MiB/s  
[Merger] Merging formats into "Opentrons OT-2 Livestream @ AC Training Lab [
.mkv"
Deleting original file Opentrons OT-2 Livestream @ AC Training Lab [ktj2CUfR
4 (pass -k to keep)
Deleting original file Opentrons OT-2 Livestream @ AC Training Lab [ktj2CUfR
bm (pass -k to keep)

Download successful!
[youtube] Extracting URL: https://www.youtube.com/live/ktj2CUfRv0w
[youtube] ktj2CUfRv0w: Downloading webpage
[youtube] ktj2CUfRv0w: Downloading tv client config
[youtube] ktj2CUfRv0w: Downloading tv player API JSON
[youtube] ktj2CUfRv0w: Downloading ios player API JSON
[youtube] ktj2CUfRv0w: Downloading m3u8 information
[info] ktj2CUfRv0w: Downloading 1 format(s): 135+251
[download] Opentrons OT-2 Livestream @ AC Training Lab [ktj2CUfRv0w].mkv has
n downloaded
```

---

## Comments (complete, in chronological order)

### Comment 1 — @sgbaird at 2025-05-01T16:02:55Z

Great! Could you try to address the pre-commit checks and then push again?

---

### Comment 2 — @sgbaird at 2025-05-01T16:17:17Z

See https://ac-training-lab.readthedocs.io/en/latest/contributing.html#create-an-environment

Then you can run `pre-commit run --all-files`

---

### Comment 3 — @sgbaird at 2025-05-01T16:34:45Z

Could you also include a link to yt-dlp somewhere? Easiest is link to within py file. Could also add a readme

---

### Comment 4 — @sgbaird at 2025-05-01T22:59:55Z

Btw, earlier today I updated the HF get latest fn: https://huggingface.co/spaces/AccelerationConsortium/OT-2-LCM/commit/6dcf96c9166f0f4fac848e11bf23703df1ee1b30

Worth updating? I can also just merge. Lmk

---

### Comment 5 — @Jonathan-Woo at 2025-05-01T23:01:59Z

@sgbaird I ended up removing the yt-dlp binary since it was too big (3 mb), the link is added in the docstring though.

---

### Comment 6 — @Jonathan-Woo at 2025-05-01T23:19:38Z

> Btw, earlier today I updated the HF get latest fn: https://huggingface.co/spaces/AccelerationConsortium/OT-2-LCM/commit/6dcf96c9166f0f4fac848e11bf23703df1ee1b30
> 
> Worth updating? I can also just merge. Lmk

yep thanks. Just updated.

---

### Comment 7 — @sgbaird at 2025-05-03T11:22:57Z

Seems there's something wrong with my implementation: https://huggingface.co/spaces/AccelerationConsortium/OT-2-LCM/discussions/5

---


## PR Reviews

### Review — @sgbaird at 2025-05-01T23:20:22Z (APPROVED)

(no body)

---
