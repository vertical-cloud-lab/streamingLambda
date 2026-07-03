# Suggested changes for the ac-training-lab picam device

These are recommendations for the `src/ac_training_lab/picam/` directory in
[AccelerationConsortium/ac-training-lab](https://github.com/AccelerationConsortium/ac-training-lab),
collected while debugging the office cam / YouTube streaming pipeline. They are
tracked here so they can be turned into a proper PR **in that repo** later. None
of them are changes to this (streamingLambda) repository.

Context: the Pi (`rpi-zero2w-stream-cam`) already runs the `device.py` from
ac-training-lab PR #539 (branch `copilot/sub-pr-538`) unchanged. Per-device
config (resolution, frame rate, flips, workflow name, privacy, etc.) lives in the
Pi's `my_secrets.py` and should stay there — do **not** hardcode it into `device.py`.

## 1. Run exactly one systemd service (avoid the camera race)

The single camera can only be held by one process. When two units
(`device.service` and a second `picam-stream.service`) both launch `device.py`
at boot, they race for the camera: one wins and streams, the loser's
`rpicam-vid` dies instantly, its `ffmpeg` then misdetects the empty `pipe:0` as
an `lrc` subtitle stream and thrashes in a restart loop (high CPU, repeated
`create`/`end` Lambda calls, throwaway YouTube broadcasts).

Recommendation: document/ship a **single** canonical service and make it explicit
that only one unit may run `device.py`.

## 2. Harden the documented `device.service`

The service block currently in `README.md` is missing a few options that the
working Pi unit has and benefits from:

- `Restart=always`, `RestartSec=20` (already documented, keep)
- `RuntimeMaxSec=8h` — periodically restart the whole pipeline so it recovers
  from long-run drift / stale broadcasts.
- `KillSignal=SIGINT` + `TimeoutStopSec=45` — `device.py` catches
  `KeyboardInterrupt` and cleanly terminates `rpicam-vid` and `ffmpeg`. Without
  SIGINT, `systemctl stop/restart` sends SIGTERM and can leave orphaned camera
  processes holding the device.
- `Environment=PYTHONUNBUFFERED=1` — so `journalctl` shows logs live.

Also, `StartLimitInterval` / `StartLimitBurst` are shown under `[Service]` in the
README but belong in the `[Unit]` section (they are ignored under `[Service]` in
current systemd).

## 3. Optional: make the ffmpeg input format explicit in `device.py`

`start_stream()` reads video with `-i pipe:0` and lets ffmpeg auto-probe the
format. Passing `-f h264` immediately before `-i pipe:0` tells ffmpeg the pipe is
raw H.264, which prevents the `lrc`/subtitle misdetection seen at startup when the
camera briefly produces no data. This is a small defensive change; the root cause
of the misdetection is the two-service race in (1).

## 4. Note: transient playlist-add 409 comes from the Lambda, not `device.py`

On `create`, YouTube occasionally returns `HttpError 409 SERVICE_UNAVAILABLE`
when the freshly-created broadcast is added to its playlist. The broadcast is
created and streams fine; only the playlist-add fails. This retry/backoff belongs
in this repo's `chalicelib/ytb_api_utils.py` (`create_broadcast_and_bind_stream`),
not in ac-training-lab.
