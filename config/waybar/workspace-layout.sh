#!/bin/sh
# Encode the connector as a Lua string before passing it to the compositor.
monitor=$(printf %s "$WAYBAR_OUTPUT_NAME" | jq -Rs .) || exit 1
exec hyprctl repl "(function()
    local mon = hl.get_monitor($monitor)
    local ws = mon and (mon.active_special_workspace or mon.active_workspace)
    local layout = ws and ws.tiled_layout or ''
    return (layout:gsub('^%l', string.upper))
end)()"
