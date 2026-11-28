-- Workspace rules wiki https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/
-- Add your workspace rules here. Increment the workspace number as you go. Do not have duplicate workspaces.
local valid_layouts = { dwindle = true, scrolling = true, master = true, monocle = true }
local state_home = os.getenv("XDG_STATE_HOME")
if not state_home or state_home:sub(1, 1) ~= "/" then
    state_home = os.getenv("HOME") .. "/.local/state"
end
local layout_state_dir = state_home .. "/hypr"
local layout_state_path = layout_state_dir .. "/workspace-layouts.lua"
local workspace_layouts = {}
local layout_state_dir_ready = false

local function shell_quote(value)
    return "'" .. value:gsub("'", "'\\''") .. "'"
end

local function ensure_layout_state_dir()
    if layout_state_dir_ready then return true end
    local ok = os.execute("mkdir -p -- " .. shell_quote(layout_state_dir))
    layout_state_dir_ready = ok == true or ok == 0
    return layout_state_dir_ready
end

local function read_layout_state()
    local file = io.open(layout_state_path, "r")
    if not file then return end
    local source = file:read("*a")
    file:close()
    local chunk = load(source, "@" .. layout_state_path, "t", {})
    if not chunk then return end
    local ok, saved = pcall(chunk)
    if not ok or type(saved) ~= "table" then return end
    for workspace, layout in pairs(saved) do
        if type(workspace) == "string" and valid_layouts[layout] then
            workspace_layouts[workspace] = layout
        end
    end
end

local function write_layout_state()
    if not ensure_layout_state_dir() then return end
    local temporary = layout_state_path .. ".tmp"
    local file = io.open(temporary, "w")
    if not file then return end
    file:write("return {\n")
    for workspace, layout in pairs(workspace_layouts) do
        file:write(string.format("  [%q] = %q,\n", workspace, layout))
    end
    file:write("}\n")
    file:close()
    os.rename(temporary, layout_state_path)
end

read_layout_state()
ensure_layout_state_dir()

hl.workspace_rule({ workspace = "name:gaming", monitor = PRIMARY_MONITOR, default = true })
hl.workspace_rule({ workspace = "1", monitor = MONITOR1, default = true })
hl.workspace_rule({ workspace = "2", monitor = MONITOR1, default = true })
hl.workspace_rule({ workspace = "3", monitor = MONITOR1, default = true })
-- hl.workspace_rule({ workspace = "4", monitor = MONITOR2, default = true })
-- hl.workspace_rule({ workspace = "5", monitor = MONITOR2, default = true })
-- hl.workspace_rule({ workspace = "6", monitor = MONITOR2, default = true })

for workspace, layout in pairs(workspace_layouts) do
    hl.workspace_rule({ workspace = workspace, layout = layout })
end

WORKSPACE_LAYOUT_STATE = {
    set = function(workspace, layout)
        if type(workspace) ~= "string" or not valid_layouts[layout] then return end
        workspace_layouts[workspace] = layout
        write_layout_state()
    end,
}

hl.config({ scrolling = { direction = "right", column_width = 1.0, fullscreen_on_one_column = false } })
