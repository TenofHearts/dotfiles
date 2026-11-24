# Hyprland workspaces over RDP

This [service drop-in](50-workspaces.conf) moves regular workspaces to an RDP client on connect and restores them to the available displays on disconnect. **The physical console stays unlocked.**

## Set up

- Use Hyprland 0.57 with `hyprctl`, Python 3.11+ at `/usr/bin/python3`, and `/usr/bin/hypr-rdp` with native session hooks. Work from a local terminal in the intended session with a physical monitor active.
- The existing `hypr-rdp.service` user unit must be ordered after and part of `graphical-session.target`. The drop-in replaces `ExecStart=/usr/bin/hypr-rdp`; review custom arguments or other overrides before installing.
- Configure authentication, TLS, and the bind address in your private `~/.config/hypr-rdp/config.toml`. Leave `output`, `on_session_start`, and `on_session_end` unset so the drop-in can manage them.

From the repository root, stop the listener, including any separately launched server, before linking:

```sh
systemctl --user stop hypr-rdp.service
./install.sh --only hypr-rdp
python3 scripts/links.py status --only hypr-rdp
```

Continue when all three links report `OK`. If a file conflicts, back it up and move it aside first, then retry. The user manager's `WAYLAND_DISPLAY` and `HYPRLAND_INSTANCE_SIGNATURE` must match this desktop session.

```sh
systemctl --user daemon-reload
systemctl --user is-active graphical-session.target && systemctl --user start hypr-rdp.service
systemctl --user is-active hypr-rdp.service
```

When the service is `active`, unpin any pinned local windows and connect with your RDP client. Disconnect to return the workspaces to the desktop.

## Stop or recover

Use `systemctl --user stop hypr-rdp.service` to stop the listener and restore the desktop. If cleanup was interrupted, keep a physical monitor connected and confirm `pgrep -u "$(id -u)" -x hypr-rdp` finds no process. In the **same running Hyprland session**, run:

```sh
helper="$HOME/.local/libexec/hypr-rdp/workspaces.py"
env -u INVOCATION_ID /usr/bin/python3 "$helper" stop
/usr/bin/python3 "$helper" status
```

If ownership of an output is unclear, leave it alone. If the session is gone, save any remaining work and start a fresh graphical login.

To roll back, stop the service and finish cleanup first. Once status reads `not running`, remove only `${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/hypr-rdp.service.d/50-workspaces.conf` after confirming it is a symlink to [this drop-in](50-workspaces.conf). Run `systemctl --user daemon-reload` before starting the original service.
