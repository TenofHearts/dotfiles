-- Input configuration

hl.config({
    input = {
        kb_options = "caps:escape",
        -- sensitivity = -0.25,
        accel_profile = "flat",
        touchpad = { natural_scroll = true },
    },
    -- Uncomment the section below to enable software cursors; this can help with cursor display or behavior issues
    -- cursor = {
    --     no_hardware_cursors = 1,
    -- },
})

hl.gesture({ fingers = 3, direction = "vertical", action = "workspace" })
hl.gesture({ fingers = 3, direction = "horizontal", action = "scroll_move" })
