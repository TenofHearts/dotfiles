# Workspace hooks for `hypr-rdp.service`

This optional [drop-in](50-workspaces.conf) hands your Hyprland workspaces to an RDP client on connect and returns them on disconnect. It uses your existing `hypr-rdp.service`; linking the profile does not start the listener or change login enablement.

## Before linking

Use Hyprland 0.57, `/usr/bin/hypr-rdp` with native session hooks, Python 3.11+, and an active systemd graphical session. Run the commands below as the desktop user in the intended Hyprland instance, with at least one active physical monitor. The drop-in expects a base unit ordered after and part of `graphical-session.target`, with **exactly `ExecStart=/usr/bin/hypr-rdp`**. It replaces that line to pass the two native session hooks; review any custom arguments or other drop-ins first.

Authentication, TLS and the bind address still come from `~/.config/hypr-rdp/config.toml`. Keep credentials in private files, out of the unit, command lines and diagnostic output. Native CLI hooks replace `on_session_start` and `on_session_end`; they are not chained. Preflight refuses existing hook commands or a configured `output`. Only remove those settings yourself after deciding to use the managed headless output and these hooks.

## Install and start

Stop the existing service before linking, so the next startup captures the desktop **before** the RDP output appears. Stop any separately launched server through its original launcher. From the checkout:

```sh
systemctl --user stop hypr-rdp.service
./install.sh --only hypr-rdp --dry-run
./install.sh --only hypr-rdp
python3 scripts/links.py status --only hypr-rdp
```

Expect three `OK` links: `workspaces.py` and `hypr_ipc.py` in `~/.local/libexec/hypr-rdp/`, plus `${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/hypr-rdp.service.d/50-workspaces.conf`. The installer skips conflicts; review and back them up before retrying. The service does not depend on the dotfiles' Hyprland bindings.

```sh
systemctl --user daemon-reload
systemctl --user is-active graphical-session.target   # must be active
systemctl --user start hypr-rdp.service
systemctl --user is-active hypr-rdp.service
/usr/bin/python3 "$HOME/.local/libexec/hypr-rdp/workspaces.py" status
```

The service should report `active`. The user manager's `WAYLAND_DISPLAY` and `HYPRLAND_INSTANCE_SIGNATURE` must refer to the same running compositor. If they are missing or mismatched on a single-session account, run `systemctl --user import-environment WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE` from the intended Hyprland terminal, then retry.

## What gets restored

- **Listener startup:** `prepare` records workspace homes, visible workspaces and focus. `ready` waits up to five seconds for the managed `hypr-rdp` output, repairs startup hotplug moves and parks the output on an empty `rdp-idle` workspace (a suffixed name if taken). Reserve this placeholder for the listener.
- **Connect:** The native start hook snapshots the current layout, parks physical displays on placeholders, moves their regular workspaces to RDP and shows the previously focused display's workspace. Visible special workspaces are hidden locally; they are not transferred. If a local window is pinned, the hook refuses the handoff instead of leaving that window visible on a placeholder. Unpin it and reconnect.
- **Disconnect:** The end hook returns regular workspaces to their recorded displays and restores available views, visible special workspaces and focus where possible. New workspaces on RDP, and workspaces whose original monitor is missing, go to the previously focused physical display or the first remaining one. This is workspace-level restoration: deliberate window moves, app launches and closes are not undone.

Hyprland may discard empty, nonpersistent workspaces once they are no longer visible. The helper can recreate a saved visible view; it cannot restore every discarded workspace or return workspaces to an unplugged display.

Move mode's `Shift+H/J/K/L` skips `hypr-rdp` when moving a whole workspace. Placeholders are ordinary workspaces: window moves, dragging and application launches are not restricted. They do not lock the physical console.

To check focus, start with a local test window focused, then start the service without connecting. Confirm typing still reaches the same window. Connect and check the remote view; disconnect and check the previous local view and focus. Repeat on a non-primary display if available.

## Stop, recover or remove

Use `systemctl --user stop hypr-rdp.service` to stop the listener, including while the base unit is retrying. On a graceful stop, `before-stop` snapshots the idle layout before the server can remove its output. Post-stop cleanup uses the saved session state and only removes an identified, owned headless output. A crash can bypass the pre-stop snapshot. The helper's `status` is read-only. Preflight refuses to start over another server, leftover state or an existing RDP output.

If cleanup was interrupted, stop the service and confirm `pgrep -u "$(id -u)" -x hypr-rdp` returns no PID. In the **same still-running Hyprland instance**, run `env -u INVOCATION_ID /usr/bin/python3 "$HOME/.local/libexec/hypr-rdp/workspaces.py" stop` to retry cleanup outside a service invocation, then check `status`. If ownership cannot be proven, leave the output alone. If no physical display remains, reconnect one before retrying. If the compositor is gone, save any remaining work and start a fresh graphical login. Use `systemctl --user reset-failed hypr-rdp.service` before starting again if systemd's start limit was reached.

To roll back the service integration, **stop `hypr-rdp.service` and finish cleanup first**. From the same checkout, remove only this drop-in link:

```sh
dropin="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/hypr-rdp.service.d/50-workspaces.conf"
if test -L "$dropin" && test "$(readlink -f -- "$dropin")" = "$(pwd -P)/platform/cachyos/hypr-rdp/50-workspaces.conf"; then
    unlink "$dropin" && systemctl --user daemon-reload
fi
```

The two helpers are inert without the drop-in. Start `hypr-rdp.service` to resume its original behavior when desired; no enable/disable step is needed. A Hyprland configuration reload invalidates the helper's monitor reference. If that happens, stop the service normally so the native server releases its own output before recovery.
