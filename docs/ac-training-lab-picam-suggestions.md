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

## 2. 8-hour chunking is done by a crontab reboot (not `RuntimeMaxSec`)

The intended behavior is for YouTube to store each **8-hour segment as its own
video**. This is achieved the way the picam docs already prescribe under
[Automatic startup](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html#automatic-startup):
a **root crontab** reboots the Pi every 8 hours, and on each boot `device.py`
calls the Lambda `end` (which finalizes/stops the previous broadcast on YouTube,
closing that chunk) followed by `create` (a fresh broadcast for the next chunk):

```cron
# Restart at 5 am, 1 pm, and 9 pm local time (8-hour spacing)
0 5,13,21 * * * /sbin/shutdown -r now
```

Because of this, do **not**:

- add `RuntimeMaxSec=8h` (or similar) to `device.service` — the cron reboot
  already provides the periodic restart, and a second mechanism would create
  off-schedule chunk boundaries; and
- make the Lambda `create` action idempotent / reuse the previous broadcast — that
  would prevent YouTube from finalizing each 8-hour chunk. `create` must always
  start a fresh broadcast, and `device.py` must keep calling `end` before `create`
  on startup.

Keep the plain `device.service` from the README (`Restart=always`,
`RestartSec=10`, `TimeoutStartSec=60`). Two small, optional doc fixes remain:

- `StartLimitInterval` / `StartLimitBurst` are shown under `[Service]` in the
  README but belong in the `[Unit]` section (they are ignored under `[Service]` in
  current systemd).
- `Environment=PYTHONUNBUFFERED=1` — so `journalctl` shows logs live.

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

## 5. Disable Wi-Fi power save (root cause of the Pi dropping off the network)

On 2026-07-06 the Pi went unreachable on the tailnet for hours while the stream
"hung" (it only recovered at the next scheduled cron reboot). The kernel log
showed `brcmfmac: brcmf_cfg80211_set_power_mgmt: power save enabled` — the
well-known Pi Zero 2 W failure where Wi-Fi power saving wedges the connection
until reboot. The hardware watchdog was already active (systemd,
`hardware timeout of 1min`), so a kernel hang would have self-rebooted; the
outage was a network-level drop, consistent with power save.

Applied on the Pi (recommend shipping in the picam setup docs):

```ini
# /etc/NetworkManager/conf.d/wifi-powersave-off.conf
[connection]
# 2 = disable Wi-Fi power saving (Pi Zero 2 W drops off Wi-Fi with it enabled)
wifi.powersave = 2
```

plus a live `iw dev wlan0 set power_save off` (package `iw`) so it takes effect
without a reconnect.

## 6. Persistent journald (so outages can be post-mortemed)

The journal was RAM-only, so all logs from before a reboot were lost — the
2026-07-06 outage could not be fully diagnosed because the 13:00 cron reboot
wiped them. Applied on the Pi:

```ini
# /etc/systemd/journald.conf.d/persistent.conf
[Journal]
Storage=persistent
SystemMaxUse=100M
```

(then `systemd-tmpfiles --create --prefix /var/log/journal` and
`systemctl restart systemd-journald`). `SystemMaxUse=100M` bounds the journal so
it cannot fill the SD card.

## 7. Stall watchdog: restart `device.service` when RTMP output stalls

The remaining failure mode systemd cannot catch: `ffmpeg`/`rpicam-vid` stay
*alive* but no data reaches YouTube (dead RTMP socket, wedged camera pipeline) —
`Restart=always` never fires because nothing exits. A watchdog now runs on the
Pi (recommend upstreaming to the picam setup):

- `/usr/local/bin/stream-watchdog.sh` — every minute, reads `bytes_acked` on the
  established TCP connection to the RTMP server (`ss -tin '( dport = :1935 )'`),
  the ground truth that data is reaching YouTube. Three consecutive checks with
  no progress (or no socket) → `systemctl restart device.service`. A 180 s grace
  period after service start avoids false positives while `end`/`create` run,
  and the counter resets whenever bytes move (a *lower* count than last check
  just means a new socket after a reconnect, which is healthy).
- `stream-watchdog.service` (oneshot) + `stream-watchdog.timer`
  (`OnBootSec=2min`, `OnUnitActiveSec=1min`), enabled.
- Optional dead-man's-switch: if `/etc/default/stream-watchdog` defines
  `HEALTHCHECK_URL` (e.g. a Healthchecks.io or UptimeRobot heartbeat URL), the
  watchdog pings it on every *healthy* check — so an external monitor alerts
  when the whole Pi drops off the network, the one case no on-device logic can
  handle. Currently unset; add a URL to enable alerting.

Validated 2026-07-06 by freezing ffmpeg with `SIGSTOP`: the watchdog logged
3 missed checks, restarted `device.service`, Lambda `end`→`create` returned 200,
and the stream came back on a fresh broadcast (~110 s detection + normal restart
time). A watchdog restart mid-cycle behaves exactly like a boot: it finalizes
the current chunk and opens a new one, so it composes fine with the 8-hour
cron-reboot chunking in (2).

Note on periodic speed tests: avoid full-bandwidth tests (e.g. `speedtest`) on
this Pi — they saturate the Zero 2 W's uplink and compete with the live RTMP
upload, causing the very stalls being monitored for.
