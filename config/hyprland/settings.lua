-- Settings shared by the native Wayland desktop configuration.

hl.monitor({
    output = "",
    mode = "preferred",
    position = "auto",
    scale = "auto",
})

hl.config({
    general = {
        gaps_in = 1, -- Per tile edge: 2 logical pixels between neighbors.
        gaps_out = 5,
        border_size = 2,
        resize_on_border = false,
        allow_tearing = false,
        layout = "dwindle",
        col = { active_border = "rgb(8dbcff)", inactive_border = "rgb(a1a1a1)" },
        snap = {
            enabled = false,
        },
    },
    decoration = {
        rounding = 0,
        active_opacity = 1.0,
        inactive_opacity = 1.0,
        shadow = {
            enabled = false,
        },
        blur = {
            enabled = false,
        },
    },
    animations = {
        enabled = true,
    },
    scrolling = { direction = "right", fullscreen_on_one_column = false },
    dwindle = {
        preserve_split = true,
    },
    cursor = { no_warps = true },
    input = {
        kb_layout = "us",
        kb_options = "caps:escape",
        follow_mouse = 0,
        sensitivity = 0,
        touchpad = {
            natural_scroll = true,
        },
    },
    binds = {
        movefocus_cycles_fullscreen = true,
    },
})

hl.gesture({ fingers = 3, direction = "vertical", action = "workspace" })
hl.gesture({ fingers = 3, direction = "horizontal", action = "scroll_move" })

hl.animation({ leaf = "global", enabled = false })
hl.animation({ leaf = "workspaces", enabled = true, speed = 5, bezier = "default", style = "slidevert" })

-- Numbered workspaces are addressable on demand. Empty ones disappear when
-- left, so each output's bar shows occupied workspaces and its visible one.
hl.on("hyprland.start", function()
    -- Waybar is deliberately optional: this configuration never installs it.
    hl.exec_cmd("command -v waybar >/dev/null && exec waybar")
    -- UWSM runs XDG autostart entries. A plain Hyprland session does not.
    hl.exec_cmd([[if [ -f "${XDG_CONFIG_HOME:-$HOME/.config}/autostart/solaar.desktop" ] &&
        command -v solaar >/dev/null && ! (command -v uwsm >/dev/null && uwsm check is-active compositor-only); then
        exec solaar -w hide
    fi]])
end)
