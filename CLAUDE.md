# CLAUDE.md

## Tailscale → Raspberry Pi (streaming camera) connection

**You are already on the tailnet.** The `claude.yml` workflow joins the runner via the
official [Tailscale GitHub Action](https://tailscale.com/kb/1276/tailscale-github-action)
(OAuth client, `tag:stream-cam-test`) before you start. Run `tailscale status` to confirm —
do **not** install Tailscale, mint auth keys via the API, or run `tailscale up` unless
status genuinely shows you disconnected. Access to the Pi is
[Tailscale SSH](https://tailscale.com/kb/1193/tailscale-ssh) (authorized by
[tailnet ACLs](https://tailscale.com/kb/1018/acls), not SSH keys):
`ssh "$RPI_STREAM_CAM_USERNAME@$RPI_STREAM_CAM_HOSTNAME"` — always use the env vars, and
never print the hostname, Lambda URL, bucket names, RTMP/stream keys, or heartbeat ping URLs
in comments, commits, or logs. If SSH is refused, the fix is an ACL/tag change only the
tailnet admin can make — report it and stop rather than working around it.

**sudo on the Pi is password-gated** (no passwordless sudo; polkit rejects non-interactive
`systemctl`). Feed the password over stdin so it never hits a process list or log:
`ssh … "sudo -S -p '' <cmd>" <<< "$RPI_STREAM_CAM_PASSWORD"`. Run AWS CLI work from the
**runner** (it has the AWS env vars) — don't route AWS calls through the Pi. Conversely,
YouTube blocks datacenter IPs, so video downloads must run **on the Pi** (residential IP),
rate-capped (`--limit-rate`) so they don't starve the live RTMP upload. Never run
full-bandwidth speed tests on the Pi for the same reason.

**Things that look like bugs but are intentional** (see
`docs/ac-training-lab-picam-suggestions.md` and the
[picam docs](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html#automatic-startup)):
the Pi reboots at 05:00/13:00/21:00 America/Denver by root crontab so YouTube stores each
8-hour chunk as its own video — an unreachable Pi near those times is likely mid-reboot, and
a Pi that dropped off the network often self-recovers at the next one, so check the clock
before declaring an outage. Do **not** re-implement chunking with `RuntimeMaxSec`, make the
Lambda `create` idempotent, or add a second systemd unit: `device.service` is the **only**
unit that may run `device.py` (a second one races for the camera and thrashes). A
`stream-watchdog` timer already restarts `device.service` on RTMP stalls with a 6/day budget
(config in `/etc/default/stream-watchdog`, mode 600) and pings Healthchecks.io when healthy —
check its journal (`journalctl -t stream-watchdog`) before adding new monitoring.

**Every `device.service` restart creates a new YouTube broadcast** (`end` → `create`), so
restart it only when necessary and verify afterwards: service `active`, single
`rpicam-vid` + `ffmpeg` pair, RTMP socket `ESTABLISHED` with `bytes_acked` advancing.
Prefer read-only inspection; confirm end-to-end (Lambda `create` → 200, stream live) before
reporting success, and report failures as failures. Changes to `device.py`/systemd/cron live
on the Pi and upstream in ac-training-lab — record them in
`docs/ac-training-lab-picam-suggestions.md`, not as code in this repo.
