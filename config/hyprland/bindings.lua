local dsp = hl.dsp
local universal = { submap_universal = true }
local directions = { h = "l", j = "d", k = "u", l = "r" }
local command_key = "ALT + SHIFT + semicolon"

for key, direction in pairs(directions) do
    hl.bind("ALT + " .. key, dsp.focus({ direction = direction }), universal)
end
for i = 1, 9 do
    hl.bind("ALT + " .. i, dsp.focus({ workspace = tostring(i) }), universal)
end
hl.bind("ALT + q", dsp.window.close(), universal)
hl.bind(command_key, function()
    hl.dispatch(dsp.submap(hl.get_current_submap() == "Command" and "reset" or "Command"))
end, universal)

local function mode(name, bindings)
    hl.define_submap(name, function()
        hl.bind("Escape", dsp.submap("reset"))
        hl.bind("Return", dsp.submap("reset"))
        bindings()
    end)
end

mode("Command", function()
    hl.bind("m", dsp.submap("Move"))
    hl.bind("r", dsp.submap("Adjust"))
    hl.bind("a", dsp.submap("Admin"))
    hl.bind("SHIFT + slash", function()
        hl.dispatch(dsp.submap("reset"))
        hl.exec_cmd('xdg-open "${XDG_CONFIG_HOME:-$HOME/.config}/hypr/help.html"')
    end)
end)

mode("Move", function()
    for key, direction in pairs(directions) do
        hl.bind(key, dsp.window.move({ direction = direction }))
        hl.bind("SHIFT + " .. key, function()
            -- Let Hyprland resolve the adjacent output in logical display coordinates.
            local target = hl.get_monitor(direction)
            if target and not target.focused then
                hl.dispatch(dsp.workspace.move({ monitor = target }))
            end
        end)
    end
    for i = 1, 9 do
        hl.bind(tostring(i), dsp.window.move({ workspace = tostring(i), follow = true }))
    end
end)

local layouts = { "dwindle", "scrolling", "master", "monocle" }
local function cycle_layout()
    local ws = hl.get_active_workspace()
    if not ws or ws.special then return end
    local next_layout = layouts[1]
    for i, layout in ipairs(layouts) do
        if ws.tiled_layout == layout then
            next_layout = layouts[i % #layouts + 1]
            break
        end
    end
    hl.workspace_rule({ workspace = ws.addressable_name, layout = next_layout })
end

mode("Adjust", function()
    local steps = { h = {-25, 0}, j = {0, 25}, k = {0, -25}, l = {25, 0} }
    for key, step in pairs(steps) do
        hl.bind(key, dsp.window.resize({ x = step[1], y = step[2], relative = true }), { repeating = true })
    end
    hl.bind("t", dsp.window.float({ action = "off" }))
    hl.bind("w", dsp.window.float())
    hl.bind("f", dsp.window.fullscreen())
    hl.bind("space", cycle_layout)
end)

mode("Admin", function()
    hl.bind("r", function()
        hl.dispatch(dsp.submap("reset"))
        hl.dispatch(dsp.reload_config())
    end)
    hl.bind("d", function()
        hl.dispatch(dsp.submap("reset"))
        hl.dispatch(dsp.force_renderer_reload())
    end)
end)
