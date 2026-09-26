# Livestream Pi fixes for the long outages (issue #9)

| Pi | camera | tailnet name |
|---|---|---|
| Pi Zero 2 W | powder doser (`picam-d1pr`) | `rpi-zero2w-stream-cam-d1pr` (`RPI_STREAM_CAM_HOSTNAME`) |
| Pi Zero 2 W | OT-2 (`picam-ot2`) | `rpi-2w-stream-cam-ex3f` |

## Root cause of the long stalls

The Pi journals (kept since 09-15 on the powder doser and 09-20 on the OT-2) show the same sequence
every time. [`journal-evidence.log`](journal-evidence.log) has the lines.

1. **A bogus ARP "conflict".** Something on the campus Wi-Fi sends an ARP packet claiming the Pi's own
   IP address from MAC `00:00:00:00:00:00`. NetworkManager's IPv4 address conflict detection (ACD,
   RFC 5227, on by default: `ipv4.dad-timeout` = 200 ms) logs
   `conflict detected for IP address 10.60.9.67 with host 00:00:00:00:00:00`.
   On 09-25 this hit both Pis within 5 s (23:00:21 and 23:00:26). That means it comes from the network,
   not from either Pi.
2. **At a later DHCP renewal, NetworkManager drops the address.** The renewal returns the *same*
   address. NetworkManager flags the conflict again, and within a second removes the address and the
   default route (`RTM_DELROUTE ... gw=10.60.0.1`). Wi-Fi stays associated, but the Pi has no IPv4.
   Renewals happen every 30 min after boot. Both Pis boot at 05:00/13:00/21:00, so renewals fall at
   about hh:00:44 / hh:30:44. That is why the stalls in the uptime analysis start at hh:30:44–50.
3. **The stream dies, then systemd gives up on it.** About 4 min later, the RTMP watchdog sees no
   progress and restarts `device.service`. `device.py` calls the Lambda first and exits on
   `Temporary failure in name resolution`. systemd restarts it 10 s later, twice. The third failure is
   within `StartLimitBurst=3`/hour, so systemd marks the unit `failed`.
4. **The network comes back about 53 min later, but the stream doesn't.** At DHCP rebinding time
   (T2 = 87.5 % of the 1 h lease), NetworkManager gives up on the lease and reconnects. It gets the same
   address and is online again within a second. The old watchdog ignored a `failed` unit, so nothing
   started the stream until the next scheduled reboot, up to 8 h later.

| outage | Pi | address dropped | network back | stream back |
|---|---|---|---|---|
| 09-16 | powder doser (and OT-2, same second in the video) | 12:30:45 | 13:00 reboot | 13:01 |
| 09-19 | powder doser | 22:30:45 | 23:24:01 | 05:01 next day |
| 09-25 | powder doser | 23:30:45 | 00:24:00 | 03:07, when the new watchdog was installed |
| 09-25 | OT-2 | 23:55:41 | 00:49:06 | **00:49:40**, from the new watchdog |

In the whole 57-day record, gaps of at least 10 min that start 40–60 s after hh:00/hh:30 add up to
**21.2 h (OT-2) and 21.6 h (powder doser)**, about half of all downtime. That's the
"address dropped at DHCP renewal" bar in [`../uptime/plots/root_cause.png`](../uptime/plots/root_cause.png)
(from [`../uptime/root_cause.py`](../uptime/root_cause.py)).

## Fixes

1. **[`no-ipv4-acd.conf`](no-ipv4-acd.conf) → `/etc/NetworkManager/conf.d/`** sets `ipv4.dad-timeout=0`,
   which turns ACD off. NetworkManager then ignores the bogus ARP packets and keeps its address. This
   removes the trigger. It takes effect the next time the Wi-Fi connects, which is the next scheduled
   reboot. The trade-off is that a real duplicate address on the network would no longer be detected.
   The DHCP server assigns the addresses, so that shouldn't happen.
2. **[`stream-watchdog.sh`](stream-watchdog.sh) → `/usr/local/bin/`** is the version from
   [byu-vcl#202](https://github.com/vertical-cloud-lab/byu-vcl/pull/202#issuecomment-5839981016). It also
   restarts `device.service` once it has been `failed` for 10 min and `a.rtmp.youtube.com:1935` accepts
   a connection. It uses the same budget of 6 watchdog restarts per day. This bounds every network outage
   (this one, DNS, and others) to *outage + about 1–10 min*, instead of *until the next reboot*. The unit
   files and [`test-stream-watchdog.sh`](test-stream-watchdog.sh) (a self-test against a throwaway unit)
   are copied unchanged from byu-vcl `8e14d4c`.

| Pi | watchdog | ACD off |
|---|---|---|
| powder doser | installed 2026-09-26 03:06 MDT. Self-test passed on the Pi. It started the stream at 03:06:52 | installed 2026-09-26 03:07 MDT; `NetworkManager --print-config` shows it; active from the 05:00 reboot |
| OT-2 | installed 2026-09-25 15:56 MDT (byu-vcl#202) | **not yet**: this repo has no sudo password for that Pi |

To install on the OT-2 Pi (or any other), from this directory:

```sh
scp no-ipv4-acd.conf <user>@rpi-2w-stream-cam-ex3f:/tmp/
ssh <user>@rpi-2w-stream-cam-ex3f 'sudo install -m 644 /tmp/no-ipv4-acd.conf /etc/NetworkManager/conf.d/ && sudo nmcli general reload conf'
```

To check that ACD is off after a reboot: `journalctl -b -u NetworkManager | grep "acd pending"` should
print nothing. Before the change, every boot logged `new lease, address=..., acd pending`.

To undo on the powder doser:
`sudo rm /etc/NetworkManager/conf.d/no-ipv4-acd.conf` and
`sudo install -m 755 /var/backups/stream-watchdog.sh.2026-09-26 /usr/local/bin/stream-watchdog.sh`.

## Open questions

- **What sends the `00:00:00:00:00:00` ARP?** It's most likely the campus wireless controller or
  switch, probing or proxying ARP for client addresses. BYU OIT would know. The next occurrence could
  be captured with `sudo tcpdump -eni wlan0 arp and ether src 00:00:00:00:00:00`.
- **`device.py` exits when its first Lambda call fails.** A retry loop there (in ac-training-lab)
  would stop a short DNS outage from using up the start limit at all.
- **OT-2 09-23 12:34.** The Pi rebooted without a clean shutdown, so power was probably lost, and
  `device.service` never started in that boot. The stream came back at a manual reboot at 13:16. The
  09-25 13:10 gap was the power loss described in byu-vcl#202.
