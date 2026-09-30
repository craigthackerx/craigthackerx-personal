"""Shared helpers for EllesmereUI profile strings.

EllesmereUI strings are "!EUI_" + LibDeflate:EncodeForPrint(LibDeflate:CompressDeflate(
Serializer.Serialize(payload))). Rather than reimplementing any of that, this module runs
the addon's own Lua serializer (lifted from EllesmereUI_Profiles.lua) and the real
LibDeflate inside Lua 5.1 via lupa, so encode and decode behave exactly as in game.

Dependencies (see fetch_deps.sh): an EllesmereUI checkout and a LibDeflate checkout,
found under $EUI_DEPS (default: <this folder>/.deps) as EllesmereUI/ and LibDeflate/.
"""
import os

from lupa import lua51

HERE = os.path.dirname(os.path.abspath(__file__))
DEPS = os.environ.get("EUI_DEPS", os.path.join(HERE, ".deps"))
EUI_DIR = os.path.join(DEPS, "EllesmereUI")
LIBDEFLATE = os.path.join(DEPS, "LibDeflate", "LibDeflate.lua")
PROFILES_LUA = os.path.join(EUI_DIR, "EllesmereUI_Profiles.lua")

_LUA_HELPERS = r"""
function DecodeEUI(s)
    s = s:gsub("^%s+", ""):gsub("%s+$", "")
    assert(s:sub(1, 5) == "!EUI_", "not an !EUI_ string")
    local d = LibDeflate:DecodeForPrint(s:sub(6)); assert(d, "decode failed")
    local raw = LibDeflate:DecompressDeflate(d); assert(raw, "decompress failed")
    local p = Serializer.Deserialize(raw); assert(type(p) == "table", "deserialize failed")
    assert(p.version == 3, "unsupported payload version " .. tostring(p.version))
    return p
end
function EncodeEUI(p)
    return "!EUI_" .. LibDeflate:EncodeForPrint(LibDeflate:CompressDeflate(Serializer.Serialize(p)))
end
local function isarray(t)
    local n = #t
    if n == 0 then return false end
    for k in pairs(t) do
        if type(k) ~= "number" or k < 1 or k > n or k % 1 ~= 0 then return false end
    end
    return true
end
local function key(k)
    if type(k) == "string" and k:match("^[%a_][%w_]*$") then return k end
    return "[" .. (type(k) == "string" and string.format("%q", k) or tostring(k)) .. "]"
end
function Dump(v, ind)
    ind = ind or ""
    local t = type(v)
    if t == "string" then return string.format("%q", v) end
    if t ~= "table" then return tostring(v) end
    if next(v) == nil then return "{}" end
    local out, ni = {}, ind .. "  "
    if isarray(v) then
        for i = 1, #v do out[#out + 1] = ni .. Dump(v[i], ni) end
    else
        local ks = {}
        for k in pairs(v) do ks[#ks + 1] = k end
        table.sort(ks, function(a, b) return tostring(a) < tostring(b) end)
        for _, k in ipairs(ks) do out[#out + 1] = ni .. key(k) .. " = " .. Dump(v[k], ni) end
    end
    return "{\n" .. table.concat(out, ",\n") .. "\n" .. ind .. "}"
end
"""


def _require(path, what):
    if not os.path.exists(path):
        raise SystemExit(f"{what} not found at {path}. Run fetch_deps.sh or set EUI_DEPS.")


def runtime():
    """A Lua 5.1 runtime with LibDeflate, EllesmereUI's Serializer and the helpers loaded."""
    _require(LIBDEFLATE, "LibDeflate")
    _require(PROFILES_LUA, "EllesmereUI_Profiles.lua")
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    g = lua.globals()
    g.LibDeflate = lua.execute(open(LIBDEFLATE, encoding="utf-8").read())
    src = open(PROFILES_LUA, encoding="utf-8").read()
    start = src.index("local Serializer = {}")
    end = src.index("EllesmereUI._Serializer = Serializer")
    g.Serializer = lua.execute(src[start:end] + "\nreturn Serializer\n")
    lua.execute(_LUA_HELPERS)
    return lua


def profiles_source_lines():
    _require(PROFILES_LUA, "EllesmereUI_Profiles.lua")
    return open(PROFILES_LUA, encoding="utf-8").read().splitlines()


def to_py(v):
    """Convert a Lua table to plain Python (lists for 1..n arrays, dicts otherwise)."""
    if lua51.lua_type(v) == "table":
        keys = list(v.keys())
        if keys and all(isinstance(k, int) for k in keys) and sorted(keys) == list(range(1, len(keys) + 1)):
            return [to_py(v[k]) for k in sorted(keys)]
        return {str(k): to_py(v[k]) for k in keys}
    return v


def read_string(path):
    return open(path, encoding="utf-8").read().strip()


def write_string(path, s):
    """Write a profile string as a single line with no trailing newline."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
