"""Check how a profile string's layout survives EllesmereUI's import merge.

Usage: python3 eui_verify_layout.py <string-file> [--client forever|retail]

Runs the addon's real layout code (the first part of EllesmereUI_Profiles.lua:
BuildImportKeyToFolder, FilterLayoutToFolders, MergeImportedLayout) against a base
profile that carries the fresh-install anchors a new Forever install seeds, with every
module ticked in the import dialog, and prints which anchors the new profile ends up
with. "dropped" means the position stored in the profile string applies.
Also reports whether the string reads as the other client (EllesmereUI then skips its
Cooldown Manager spell layouts).
"""
import argparse

import euilib

SETUP = r"""
EllesmereUI = { IS_FOREVER = %s, _unlockRegisteredElements = {
    EDM_Win1 = { folder = "EllesmereUIDamageMeters" },
    EDB_1 = { folder = "EllesmereUIDataBars" }, EDB_2 = { folder = "EllesmereUIDataBars" },
    EDB_3 = { folder = "EllesmereUIDataBars" } } }
local EDGES = { SCREEN_LEFT = 1, SCREEN_RIGHT = 1, SCREEN_TOP = 1, SCREEN_BOTTOM = 1 }
function EllesmereUI.IsScreenEdgeKey(k) return EDGES[k] ~= nil end
"""

CHECK = r"""
function CheckLayout(p)
    local d = p.data
    local function EA(t, side, ox, oy, ek, es, eo)
        local r = { target = t, side = side, offsetX = ox, offsetY = oy }
        if ek then r.edge = { key = ek, side = es, offset = eo } end
        return r
    end
    -- fresh Forever install seed (EllesmereUI_ForeverLayout.lua)
    local base = { anchors = {
        ECHAT_MainChat = EA("SCREEN_LEFT", "RIGHT", 63.33, 0, "SCREEN_BOTTOM", "TOP", 108.17),
        EBS_Minimap    = EA("SCREEN_RIGHT", "LEFT", -23.33, 0, "SCREEN_TOP", "BOTTOM", -62.5),
        EDM_Win1       = EA("SCREEN_RIGHT", "LEFT", -10, 0, "SCREEN_BOTTOM", "TOP", 62),
        MainBar        = EA("SCREEN_BOTTOM", "TOP", 0, 34),
        player         = EA("SCREEN_BOTTOM", "TOP", -317, 171),
        target         = EA("SCREEN_BOTTOM", "TOP", 317, 171),
        targettarget   = EA("target", "TOP", 40, 6),
        pet            = EA("player", "BOTTOM", 0, -8),
    }, widthMatch = {}, heightMatch = {}, phantomBounds = {} }
    local sel = {}
    for f in pairs(d.addons) do sel[f] = true end
    local ul = d.unlockLayout or {}
    local meta = d.unlockLayoutMeta and d.unlockLayoutMeta.keyToFolder or {}
    local k2f = EllesmereUI.BuildImportKeyToFolder(ul, meta)
    local merged = EllesmereUI.MergeImportedLayout(base, EllesmereUI.FilterLayoutToFolders(ul, sel, k2f), sel)
    local out = {}
    local seen = {}
    for k in pairs(base.anchors) do seen[k] = true end
    for k in pairs(merged.anchors) do seen[k] = true end
    for k in pairs(seen) do
        local a = merged.anchors[k]
        local s
        if not a then s = "dropped (profile position applies)"
        else
            s = a.target .. " x=" .. tostring(a.offsetX)
            if a.edge then s = s .. " + " .. a.edge.key .. " " .. tostring(a.edge.offset) end
        end
        out[#out + 1] = "  anchor " .. k .. ": " .. s
    end
    for _, kind in ipairs({ "widthMatch", "heightMatch" }) do
        for k, v in pairs(merged[kind] or {}) do out[#out + 1] = "  " .. kind .. " " .. k .. " -> " .. v end
    end
    table.sort(out)
    return table.concat(out, "\n")
end
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--client", choices=["forever", "retail"], default="forever",
                    help="which game to simulate the import on (default forever)")
    args = ap.parse_args()
    lua = euilib.runtime()
    src = euilib.profiles_source_lines()
    lua.execute(SETUP % ("true" if args.client == "forever" else "false"))
    lua.execute("\n".join(src[:src.index("--  Profile DB helpers") - 1]))
    start = next(i for i, line in enumerate(src) if line.startswith("function EllesmereUI.PayloadFromOtherClient"))
    lua.execute("\n".join(src[start:start + 4]))
    lua.execute(CHECK)
    g = lua.globals()
    p = g.DecodeEUI(euilib.read_string(args.file))
    other = g.EllesmereUI.PayloadFromOtherClient(p)
    print(f"{args.file} imported on {args.client}: reads as other client = {other}")
    print(g.CheckLayout(p))


if __name__ == "__main__":
    main()
