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
        enabled = false,
    },
    dwindle = {
        preserve_split = true,
    },
    cursor = { no_warps = true },
    input = {
        kb_layout = "us",
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

-- Numbered workspaces are addressable on demand. Empty ones disappear when
-- left, so each output's bar shows occupied workspaces and its visible one.
hl.on("hyprland.start", function()
    -- Waybar is deliberately optional: this configuration never installs it.
    hl.exec_cmd("command -v waybar >/dev/null && exec waybar")
end)
