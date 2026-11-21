-- Hyprland resolves a symlinked entry point to the checkout. Search the live
-- profile first so sibling modules (including machine-only files) still work.
local config_home = os.getenv("XDG_CONFIG_HOME")
if not config_home or config_home:sub(1, 1) ~= "/" then config_home = os.getenv("HOME") .. "/.config" end
local local_path = config_home .. "/hypr/?.lua"
package.path = local_path .. ";" .. package.path

local function require_local(name)
    if package.searchpath(name, local_path) then require(name) end
end

require("config.animations")
require_local("config.autostart")
require("config.colors")
require("config.decorations")
require("config.variables")
require_local("config.environment")
require("config.inputs")
require("config.binds")
require("config.misc")
require("config.monitors")
require("config.windowrules")
require("config.workspaces")
require("bindings")
require_local("config.local")
