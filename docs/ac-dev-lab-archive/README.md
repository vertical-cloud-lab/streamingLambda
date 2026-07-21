# ac-dev-lab download/process/re-upload discussion archive

Complete comment archives (fetched via the GitHub API on 2026-07-08, including
comments hidden in the web UI by GitHub's pagination) from the
AccelerationConsortium/ac-dev-lab issues and PRs that trace the design of the
YouTube livestream **download → post-process → re-upload** pipeline. Archived
to give agents working in this repo the full context without re-fetching.

| File | Item | State | What it covers |
|---|---|---|---|
| `issue-212-*.md` | [#212](https://github.com/AccelerationConsortium/ac-dev-lab/issues/212) | closed | First exploration of downloading self-owned videos; settled on yt-dlp over youtube-dl |
| `pr-234-*.md` | [#234](https://github.com/AccelerationConsortium/ac-dev-lab/pull/234) | merged | `yt_utils.py`: yt-dlp download of the latest video (public videos, no auth) |
| `issue-223-*.md` | [#223](https://github.com/AccelerationConsortium/ac-dev-lab/issues/223) | open | The processing pipeline: auto-editor stale-section detection, ffmpeg speed-up overlay, 16x speedup, title convention, yt-dlp cookie problems on HF Spaces |
| `issue-231-*.md` | [#231](https://github.com/AccelerationConsortium/ac-dev-lab/issues/231) | open | 8-hr restart mechanism history (origin of this streamingLambda repo): Lambda holds token.pickle, crontab reboot `0 5,13,21`, one-time stream keys |
| `issue-341-*.md` | [#341](https://github.com/AccelerationConsortium/ac-dev-lab/issues/341) | closed | Kickoff for Playwright-based downloads of private videos |
| `pr-343-*.md` | [#343](https://github.com/AccelerationConsortium/ac-dev-lab/pull/343) | merged | **The adopted downloader**: YouTube Data API discovery + Playwright Studio download with TOTP login |

## Key findings

### Download (the hard part — YouTube has no API to download video content)

- **yt-dlp** (PR #234) works fine for public/unlisted videos with no auth, and
  is the preferred tool on headless/ephemeral machines. For **private** videos
  it needs browser cookies, which expire within hours
  ([yt-dlp#8227](https://github.com/yt-dlp/yt-dlp/issues/8227)) — a dead end
  for unattended automation on HF Spaces (issue #223).
- **Playwright + YouTube Studio** (PR #343, the merged approach in
  `src/ac_training_lab/video_editing/download.py`): a dedicated Google account
  (`achardwarestreams.downloader@...`) is a **channel editor** (viewer role has
  the download button disabled). The script:
  1. lists playlists/videos via the YouTube Data API and filters out
     already-downloaded/processed ones,
  2. logs into Google with email + password + **pyotp TOTP** (2FA re-enabled
     deliberately: Google blocks password-only logins from ephemeral machines
     with "couldn't verify this account belongs to you", but accepts
     password+TOTP),
  3. navigates to `studio.youtube.com/video/{video_id}/edit` and clicks the
     ⋮ menu → Download.
- Playwright **headless fails** (Google bot detection) — a virtual framebuffer
  (xvfb) is required. On the BALAM cluster it runs inside an **apptainer**
  container (system deps not installable), and only login nodes have internet.
- HF Spaces cannot run Playwright at all (no GUI browser env; Docker attempt
  stalled) — reproducer: `huggingface.co/spaces/AccelerationConsortium/playwright-reproducer`.
- Alternative acknowledged in the threads: make videos public/unlisted so
  yt-dlp works without auth (sgbaird encourages public/unlisted "in part for
  this reason").

### Processing (issue #223)

- **auto-editor** pipeline by @Jonathan-Woo:
  1. `auto-editor --edit motion:threshold=…` produces v1 timestamps of stale
     (no-motion) sections,
  2. ffmpeg burns a speed-up indicator overlay (e.g. `16x`) on stale sections,
  3. auto-editor speeds up stale sections (`--silent-speed`), keeping motion at 1x.
- Tuning knobs: `threshold` (fraction of changed pixels to count as motion) and
  `margin` (padding around kept sections). False positives are a concern, so
  stale sections are sped up rather than deleted (a huge `--silent-speed`
  effectively deletes).
- Title convention so originals and processed videos can be matched via the
  Data API: keep the original title/ID and append **`[processed, 16x]`**.
- Later development moved to
  [AccelerationConsortium/youtube-livestream-processor](https://github.com/AccelerationConsortium/youtube-livestream-processor).

### Upload / orchestration

- Uploads and playlist management use the YouTube Data API with the channel
  owner's **token.pickle** (same credential this repo's Lambda uses from S3).
- Issue #231 documents why broadcasts are chunked by reboot (`0 5,13,21 * * *`
  crontab) with the Lambda doing `end` → `create` — YouTube autostart is
  unreliable if a broadcast is created while data is already flowing.
