#!/bin/bash
# Exercise the Wi-Fi recovery step of stream-watchdog.sh with stand-ins for
# nmcli, systemctl, logger and sleep, so nothing touches the real Wi-Fi and
# nothing reboots. Needs no root and runs anywhere in about a second.
#
#   ./test-wifi-recovery.sh [path/to/stream-watchdog.sh]

set -u
SRC=${1:-"$(dirname "$0")/stream-watchdog.sh"}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
failures=0

mkdir "$TMP/bin"
# nmcli: "device show" prints $TMP/wifi-state (empty = nmcli failing); "radio" is recorded
cat > "$TMP/bin/nmcli" <<EOF
#!/bin/bash
echo "nmcli \$*" >> "$TMP/calls"
[ "\$1" = radio ] && exit 0
cat "$TMP/wifi-state"
EOF
# systemctl: device.service is neither failed nor active, so the script stops
# right after the Wi-Fi step; "reboot" is recorded
cat > "$TMP/bin/systemctl" <<EOF
#!/bin/bash
[ "\$1" = reboot ] && echo "systemctl reboot" >> "$TMP/calls"
exit 3
EOF
printf '#!/bin/bash\necho "$*" >> %s/log\n' "$TMP" > "$TMP/bin/logger"
printf '#!/bin/bash\nexit 0\n' > "$TMP/bin/sleep"
chmod +x "$TMP/bin/"*

sed -e "s|^WIFI_STATE=[^ ]*|WIFI_STATE=$TMP/wifi|" \
    -e "s|^REBOOT_HIST=.*|REBOOT_HIST=$TMP/reboots|" \
    -e "s|^STATE=.*|STATE=$TMP/state|" \
    -e "s|^HIST=.*|HIST=$TMP/restarts|" \
    -e "s|/etc/default/stream-watchdog|$TMP/default|g" \
    "$SRC" > "$TMP/wd.sh"
for want in "^WIFI_STATE=$TMP/wifi " "^REBOOT_HIST=$TMP/reboots\$" "^STATE=$TMP/state\$"; do
    grep -q -- "$want" "$TMP/wd.sh" || { echo "could not rewrite $SRC ($want)" >&2; exit 2; }
done

up_s() { awk '{printf "%d", $1}' /proc/uptime; }

# run [nmcli state] [contents of the Wi-Fi state file, or "none"]
run() {
    printf '%s' "$1" > "$TMP/wifi-state"
    if [ "$2" = none ]; then rm -f "$TMP/wifi"; else echo "$2" > "$TMP/wifi"; fi
    rm -f "$TMP/calls" "$TMP/log"
    PATH="$TMP/bin:$PATH" bash "$TMP/wd.sh" > /dev/null 2>&1
}

check() {  # check <description> <command...>
    local desc=$1; shift
    if "$@"; then echo "PASS  $desc"; else echo "FAIL  $desc"; failures=$((failures + 1)); fi
}
# shellcheck disable=SC2317  # called through check
called() { grep -q -- "$1" "$TMP/calls" 2>/dev/null; }

run "100 (connected)" "123 1"
check "connected: state file cleared, no action" \
    bash -c "[ ! -e '$TMP/wifi' ] && ! grep -qE 'radio|reboot' '$TMP/calls'"

run "" none
check "nmcli gives no answer: step skipped" \
    bash -c "[ ! -e '$TMP/wifi' ] && ! grep -qE 'radio|reboot' '$TMP/calls'"

run "30 (disconnected)" none
check "just went down: outage start recorded, no action" \
    bash -c "read -r s r < '$TMP/wifi' && [ \$(( \$(awk '{printf \"%d\", \$1}' /proc/uptime) - s )) -le 2 ] && [ \"\$r\" = 0 ] && ! grep -qE 'radio|reboot' '$TMP/calls'"

run "30 (disconnected)" "$(( $(up_s) - 300 )) 0"
check "down 5 min: still waiting" bash -c "! grep -qE 'radio|reboot' '$TMP/calls'"

run "70 (connecting (getting IP configuration))" "$(( $(up_s) - 660 )) 0"
check "down 11 min: radio off, then on" \
    bash -c "grep -n 'radio wifi' '$TMP/calls' | tr '\n' ' ' | grep -q 'radio wifi off.*radio wifi on'"
check "down 11 min: logged, reset remembered" \
    bash -c "grep -q 'turning Wi-Fi off and on' '$TMP/log' && read -r s r < '$TMP/wifi' && [ \"\$r\" = 1 ]"

run "30 (disconnected)" "$(( $(up_s) - 900 )) 1"
check "down 15 min after a reset: no second reset, no reboot yet" bash -c "! grep -qE 'radio|reboot' '$TMP/calls'"

rm -f "$TMP/reboots"
run "30 (disconnected)" "$(( $(up_s) - 1260 )) 1"
check "down 21 min: reboot" called "systemctl reboot"
check "down 21 min: reboot counted" bash -c "[ \$(grep -c . '$TMP/reboots') = 1 ]"

now=$(date +%s); printf '%s\n%s\n%s\n' "$((now - 100))" "$((now - 200))" "$((now - 300))" > "$TMP/reboots"
run "30 (disconnected)" "$(( $(up_s) - 1260 )) 1"
check "3 reboots in 24 h already: holds off" bash -c "! grep -q reboot '$TMP/calls' && grep -q 'reboot budget exhausted' '$TMP/log'"

printf '%s\n' "$((now - 90000))" "$((now - 100))" > "$TMP/reboots"
run "30 (disconnected)" "$(( $(up_s) - 1260 )) 1"
check "reboots older than 24 h don't count" called "systemctl reboot"

echo
[ "$failures" = 0 ] && echo "all passed" || echo "$failures failed"
exit "$failures"
