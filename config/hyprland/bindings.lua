local dsp = hl.dsp
-- App shortcuts belong to Normal mode unless explicitly requested in every mode.
local universal = { submap_universal = true }
local directions = { h = "l", j = "d", k = "u", l = "r" }
local command_key = "ALT + SHIFT + semicolon"

local function horizontal_focus(direction, cycle)
    return function()
        -- Match the workspace targeted by Hyprland's layout dispatcher.
        local ws = hl.get_active_special_workspace() or hl.get_active_workspace()
        if ws and ws.tiled_layout == "monocle" then
            hl.dispatch(dsp.layout(cycle))
        else
            hl.dispatch(dsp.focus({ direction = direction }))
        end
    end
end
hl.bind("ALT + h", horizontal_focus(directions.h, "cycleprev"), universal)
hl.bind("ALT + l", horizontal_focus(directions.l, "cyclenext"), universal)
hl.bind("ALT + j", dsp.focus({ direction = directions.j }), universal)
hl.bind("ALT + k", dsp.focus({ direction = directions.k }), universal)
for i = 1, 9 do
    hl.bind("ALT + " .. i, dsp.focus({ workspace = tostring(i) }), universal)
end
-- Replace the CachyOS cycle binding before opening Noctalia's switcher.
hl.unbind("ALT + Tab")
hl.bind("ALT + Tab", dsp.exec_cmd("noctalia msg window-switcher hold workspace"), universal)
hl.bind("ALT + SHIFT + Tab", dsp.exec_cmd("noctalia msg window-switcher hold workspace reverse"), universal)
hl.bind("ALT + m", dsp.window.close(), universal)
hl.bind("ALT + q", dsp.window.kill(), universal)
hl.bind("ALT + space", dsp.exec_cmd("noctalia msg panel-toggle launcher"))
hl.bind("ALT + SHIFT + s", dsp.exec_cmd("shotori gui"), universal)
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

local resize_presets = { 0.25, 0.33, 0.50, 1.0 }
local function next_span(current, sign, snap)
    if not snap then return current + sign * 0.05 end
    for i = 1, #resize_presets do
        local target = resize_presets[sign > 0 and i or #resize_presets + 1 - i]
        if (target - current) * sign > 0.005 then return target end
    end
end

local function resize_step(dx, dy, snap)
    local w = hl.get_active_window()
    if not w or (w.fullscreen or 0) ~= 0 then return end
    local layout = w.layout
    if not layout or layout.name ~= "scrolling" then
        if not snap then hl.dispatch(dsp.window.resize({ x = dx, y = dy, relative = true })) end
        return
    end

    local col = layout.column
    if not col then return end
    if dx ~= 0 then
        -- Resizing the column directly lets the viewport pan past its right edge.
        local target = next_span(col.width, dx > 0 and 1 or -1, snap)
        if target then hl.dispatch(dsp.layout(("colresize %.6f"):format(target))) end
    elseif #col.windows > 1 then
        -- Use tiled client heights (logical px), excluding borders, gaps and bars.
        local total = 0
        for _, row in ipairs(col.windows) do total = total + row.size.y end
        if total == 0 then return end
        local height = w.size.y
        local target = next_span(height / total, dy > 0 and 1 or -1, snap)
        if target then
            hl.dispatch(dsp.window.resize({ x = 0, y = math.floor(target * total - height + 0.5), relative = true }))
        end
    end
end

mode("Adjust", function()
    local steps = { h = {-25, 0}, j = {0, 25}, k = {0, -25}, l = {25, 0} }
    for key, step in pairs(steps) do
        hl.bind(key, function() resize_step(step[1], step[2], false) end, { repeating = true })
        hl.bind("SHIFT + " .. key, function() resize_step(step[1], step[2], true) end)
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
