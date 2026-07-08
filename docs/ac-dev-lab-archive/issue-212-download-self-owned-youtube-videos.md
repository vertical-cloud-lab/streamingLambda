# Issue #212: Download self-owned YouTube videos

- **URL:** https://github.com/AccelerationConsortium/ac-dev-lab/issues/212
- **Author:** @sgbaird
- **State:** closed
- **Created:** 2025-03-27T16:47:25Z  **Closed:** 2025-05-01T23:21:05Z
- **Comments archived:** 2 issue comments

---

## Original description

In creator dashboard, there's a way to download it via GUI. Some possibilities: 

- use browser cookies: https://stackoverflow.com/a/55272225
- use youtube-dl: https://github.com/ytdl-org/youtube-dl

Terms of service: https://www.youtube.com/t/terms

Cc @Jonathan-Woo 

---

## Comments (complete, in chronological order)

### Comment 1 — @sgbaird at 2025-04-08T14:18:33Z

@Neil-YL if you end up getting stuck on the new picam device.py script, could you give this one a try? Ideally, it would be great to have the full restart + download workflow tested to show that we can store and retrieve 24/7 streams.

---

### Comment 2 — @Jonathan-Woo at 2025-05-01T15:49:48Z

Switched to using yt-dlp instead of youtube-dl because it's more actively maintained.

---
