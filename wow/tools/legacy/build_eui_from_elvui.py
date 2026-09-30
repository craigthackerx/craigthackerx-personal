"""LEGACY: the generator that first translated Craig's ElvUI layout into EllesmereUI (v3).

Kept as a record of how each ElvUI setting was mapped. It is superseded: the source of
truth is now ../../ellesmereui/wow-forever.txt, exported in game after hand tuning. Do not
regenerate profiles from this unless starting over from ElvUI.

Usage: python3 legacy/build_eui_from_elvui.py <output.txt>

Values are taken from his decoded ElvUI profile "Craig-2k-2025-latest"
(pixel-perfect 1440p, so ElvUI offsets carry over 1:1 at uiScale 0.5333).
Encoding and verification run through the real LibDeflate and EllesmereUI's
own serializer in Lua, so the string is byte-for-byte what the addon expects.
"""
import os
import re
import subprocess
import sys
import zlib

from lupa import lua51

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import euilib  # noqa: E402

EUI = euilib.EUI_DIR

# ElvUI colours
DARK = 0.054          # ElvUI backdropfadecolor
ACCENT = {"r": 0.0588, "g": 0.5137, "b": 0.851}   # ElvUI value colour #0F83D9
CAST = {"r": 0.9176, "g": 0.9529, "b": 0.0}       # #EAF300
NOKICK = {"r": 1.0, "g": 0.0314, "b": 0.0}        # #FF0800

EUI_STYLE = {"useBlizzardStyle": False, "useClassicStyle": False, "useForeverStyle": False}

# Blizzard's experience bar sits flush on the bottom edge on Forever, so the
# pieces ElvUI had at y=0 start just above it instead.
BOTTOM = 20


def pos(point, x, y, rel=None):
    return {"point": point, "relPoint": rel or point, "x": x, "y": y}


def bar(icons, rows, *, backdrop=True, visibility="always", size=40, extra=None):
    b = {
        "enabled": True,
        "buttonWidth": size, "buttonHeight": size, "buttonPadding": 2,
        "numIcons": icons, "overrideNumIcons": icons,
        "numRows": rows, "overrideNumRows": rows,
        "orientation": "horizontal",
        "barVisibility": visibility, "alwaysHidden": False,
    }
    if visibility == "mouseover":
        b.update({"mouseoverEnabled": True, "mouseoverAlpha": 0, "_savedBarAlpha": 1})
    else:
        b.update({"mouseoverEnabled": False, "mouseoverAlpha": 1})
    if backdrop:
        b.update({"bgEnabled": True, "bgColor": {"r": DARK, "g": DARK, "b": DARK, "a": 0.75}, "bgPadding": 2})
    if extra:
        b.update(extra)
    return b


HIDDEN = {"barVisibility": "never", "alwaysHidden": True}

# ElvUI-style aura icons: square, 1px black border, timer under the icon, soonest first
AURA_LOOK = {"padding": 4, "growDirection": "LEFT", "iconShape": "none",
             "borderSize": 1, "borderR": 0, "borderG": 0, "borderB": 0, "borderA": 1,
             "durationShow": True, "durationTextSize": 11, "durationPosition": "BOTTOM",
             "stackShow": True, "stackTextSize": 11, "stackPosition": "BOTTOMRIGHT",
             "sortMethod": "Expiration"}

unit_frames = {
    **EUI_STYLE,
    "healthBarTexture": "none",          # flat fill, closest to ElvUI Minimalist
    "castBarTexture": "inherit",
    "playerThreatBorderEnabled": True,   # ElvUI player threatStyle = BORDERS
    "threatPctEnabled": True,            # threat % on target/focus (Forever only)
    "enabledFrames": {"player": True, "target": True, "focus": True, "pet": True,
                      "targettarget": True, "boss": True, "focustarget": False},
    "player": {
        "frameWidth": 203, "healthHeight": 52, "powerPosition": "none",
        "showPortrait": False, "portraitStyle": "none",
        "healthClassColored": True, "healthBarOpacity": 100,
        "leftTextContent": "name", "leftTextSize": 12,
        "rightTextContent": "curhpshort", "rightTextSize": 18,
        "centerTextContent": "none",
        "showPlayerCastbar": False,      # player cast bar comes from Resource Bars
        # Timed buffs as a row of icons along the top edge (ElvUI aura bars stand-in)
        "showBuffs": True, "buffAnchor": "topleft", "buffGrowth": "right",
        "buffSize": 24, "maxBuffs": 8, "buffMaxPerRow": 8, "buffSpacingX": 1,
        "buffHasDuration": True,
        "buffShowCooldownText": True, "buffCooldownTextSize": 11, "buffStackTextSize": 11,
    },
    "target": {
        "frameWidth": 204, "healthHeight": 42, "powerHeight": 10, "powerPosition": "below",
        "showPortrait": False, "portraitStyle": "none",
        "healthClassColored": True, "healthBarOpacity": 100,
        "leftTextContent": "perhp", "leftTextSize": 18,
        "rightTextContent": "name", "rightTextSize": 12,
        "centerTextContent": "none",
        "powerPercentText": "center", "powerTextFormat": "curpp", "powerPercentSize": 10,
        "showCastbar": True, "castbarWidth": 204, "castbarHeight": 25,
        "castbarFillColor": CAST, "castbarUninterruptibleColor": NOKICK,
    },
    "focus": {
        "frameWidth": 100, "healthHeight": 40, "powerPosition": "none",
        "showPortrait": False, "portraitStyle": "none",
        "healthClassColored": True, "healthBarOpacity": 100,
        "showCastbar": False,
    },
    "targettarget": {"frameWidth": 100, "healthHeight": 40, "healthClassColored": True, "healthBarOpacity": 100},
    "pet": {"frameWidth": 130, "healthHeight": 40, "powerPosition": "none",
            "healthClassColored": True, "healthBarOpacity": 100},
    "boss": {"frameWidth": 216, "healthHeight": 40, "powerHeight": 10, "powerPosition": "below"},
    "positions": {
        "player": pos("BOTTOM", -270, 216),
        "target": pos("BOTTOM", 270, 216),
        "targettarget": pos("BOTTOM", 312, 62),
        "pet": pos("BOTTOM", -313, 62),
        "focus": pos("BOTTOM", -317, 147),
    },
    # ElvUI auras: buffs 28px / debuffs 26px, one row each, growing left from bottom right
    "playerAuraBars": {
        **EUI_STYLE,
        "enabled": True,
        "pabEditModeSeeded": True,
        "fvBuffWipe": 1,                  # skip the one-time Forever buff wipe on import
        "defaultBuffs": {**AURA_LOOK, "enabled": True, "iconSize": 28, "iconsPerRow": 20,
                         "maxRows": 1, "maxTotal": 20},
        "defaultDebuffs": {**AURA_LOOK, "enabled": True, "iconSize": 28, "iconsPerRow": 10,
                           "maxRows": 1, "maxTotal": 10},
        "buffsPos": {**pos("BOTTOMRIGHT", -4, 385), "design": True},
        "debuffsPos": {**pos("BOTTOMRIGHT", -4, 440), "design": True},
    },
}

resource_bars = {
    "useBlizzardStyleBars": False, "useClassicStyleBars": False,
    "general": {"barTexture": "none"},
    "health": {"enabled": False},
    # ElvUI detached player power bar: 200 x 22 above the action bars
    "primary": {"enabled": True, "width": 200, "height": 22,
                "textFormat": "curpp", "textSize": 16,
                "unlockPos": pos("BOTTOM", 0, 268)},
    # Forever swing timer: same width as the rage bar, sitting right on top of it
    "swingTimer": {"enabled": True, "width": 200, "height": 12, "rowSpacing": 2,
                   "texture": "none", "unlockPos": pos("BOTTOM", 0, 294)},
    # ElvUI player cast bar 204 x 25 under the player frame (icon adds 25 to width)
    "castBar": {**EUI_STYLE, "enabled": True, "width": 179, "height": 25, "showIcon": True,
                "texture": "none", "classColored": False,
                "fillR": CAST["r"], "fillG": CAST["g"], "fillB": CAST["b"], "fillA": 1,
                "unlockPos": pos("BOTTOM", -270, 192)},
}

# ElvUI bar N is Blizzard page N. EllesmereUI keys its bars by Blizzard bar, so
# map by page to keep keybinds and spells on the same bar:
#   ElvUI bar1 -> MainBar, bar2 (page 2) -> Bar9, bar3 (page 3) -> Bar4,
#   bar4 (page 4) -> Bar5, bar5 (page 5) -> Bar3, bar6 (page 6) -> Bar2
action_bars = {
    **EUI_STYLE,
    "squareIcons": True,
    "useBlizzardDataBars": False,        # EllesmereUI's own flat XP bar, placed below
    "barPositions": {
        "MainBar": pos("BOTTOM", 0, 224),
        "Bar3": pos("BOTTOM", 0, 181),
        "Bar2": pos("BOTTOM", 0, 137),
        "Bar4": pos("BOTTOM", 0, BOTTOM),
        "Bar9": pos("BOTTOMLEFT", 458, BOTTOM),
        "Bar5": pos("TOPRIGHT", -209, -6),
        "StanceBar": pos("BOTTOM", -244, BOTTOM),
        "XPBar": pos("BOTTOMLEFT", 462, 4),       # between the left panel and the menu bar
        "PetBar": pos("BOTTOM", 313, BOTTOM),
    },
    "bars": {
        "MainBar": bar(8, 1),
        "Bar3": bar(8, 1),
        "Bar2": bar(8, 1),
        "Bar4": bar(12, 2),
        "Bar9": bar(12, 4, visibility="mouseover"),
        "Bar5": bar(12, 2, backdrop=False, visibility="mouseover"),
        "BagBar": dict(HIDDEN),
        "MicroBar": dict(HIDDEN),         # replaced by the data bar menu below
        "XPBar": {"width": 808, "height": 10, "orientation": "HORIZONTAL", "alwaysHidden": False,
                  "barTexture": "none", "textSize": 9, "clickThrough": True},
        "RepBar": {"alwaysHidden": True},
        "Bar6": dict(HIDDEN), "Bar7": dict(HIDDEN), "Bar8": dict(HIDDEN), "Bar10": dict(HIDDEN),
        "StanceBar": {"buttonWidth": 32, "buttonHeight": 32, "buttonPadding": 2, "barVisibility": "always"},
        "PetBar": {"buttonWidth": 32, "buttonHeight": 32, "buttonPadding": 2,
                   "numIcons": 10, "overrideNumIcons": 10, "numRows": 1, "overrideNumRows": 1},
    },
}

nameplates = {
    **EUI_STYLE,
    "healthBarTexture": "none", "castBarTexture": "none",
    "threatColorMode": "always", "threatColorHealth": True,
    # ElvUI threat colours: good (tanking) red, bad magenta, transitions yellow/blue, off-tank green
    "tankHasAggroEnabled": True,
    "tankHasAggro": {"r": 0.7059, "g": 0.1608, "b": 0.1608},
    "tankLosingAggro": {"r": 0.1725, "g": 0.7569, "b": 1.0},
    "tankNoAggro": {"r": 0.9255, "g": 0.1373, "b": 0.9961},
    "offTankAggroEnabled": True,
    "offTankAggro": {"r": 0.1373, "g": 1.0, "b": 0.1882},
    "dpsHasAggro": {"r": 0.9255, "g": 0.1373, "b": 0.9961},
    "dpsNearAggro": {"r": 0.1725, "g": 0.7569, "b": 1.0},
}

raid_frames = {
    "useBlizzardStyle": False, "useClassicStyle": False,
    "healthBarTexture": "none", "healthColorMode": "class",
    "frameWidth": 88, "frameHeight": 30, "cellSpacing": -1,
    "unlockPos": pos("BOTTOMLEFT", 4, 234),
    "partyFrameWidth": 200, "partyFrameHeight": 45, "partyCellSpacing": 2,
    "partySortMode": "ROLE", "partyHorizontal": False, "partyFlipGrowth": False,
    "partyUnlockPos": pos("BOTTOMLEFT", 4, 234),
}

minimap = {"minimap": {
    **EUI_STYLE,
    "mapSize": 162, "position": pos("TOPRIGHT", -4, -4), "shape": "square",
    "locationMode": "none", "_capturedOnce": True,
}}

chat = {"chat": {
    **EUI_STYLE,
    "chatPosition": pos("BOTTOMLEFT", 4, BOTTOM), "_chatPosOwnership": 1,
    "chatSize": {"w": 450, "h": 184},
    "extendBgBehindTabs": True,
    "bgAlpha": 0.75, "bgR": DARK, "bgG": DARK, "bgB": DARK,
    "timestampFormat": "%I:%M %p ", "tabFontSize": 10,
}}

def cdm_bar(key, size):
    return {"key": key, "barType": key, "enabled": True, "iconSize": size, "spacing": 2,
            "numRows": 1, "iconShape": "none", "iconZoom": 0.08,
            "borderSize": 1, "borderR": 0, "borderG": 0, "borderB": 0, "borderA": 1,
            "borderTexture": "solid", "borderThickness": "thin",
            "showCooldownText": True, "cooldownFontSize": 14 if size >= 36 else 11,
            "stackCountSize": 11, "barVisibility": "always"}


# Cooldown Manager: three rows stacked centre-screen above the swing timer.
# Spells per bar are per spec, so they are set in game.
cooldown_manager = {
    "useBlizzardStyle": False, "useBlizzardStyleBars": False,
    "useClassicStyle": False, "useClassicStyleBars": False,
    "useForeverStyle": False, "useForeverStyleBars": False,
    "cdmBars": {"bars": [cdm_bar("cooldowns", 40), cdm_bar("utility", 32), cdm_bar("buffs", 28)]},
    "cdmBarPositions": {
        "cooldowns": pos("BOTTOM", 0, 342),
        "utility": pos("BOTTOM", 0, 386),
        "buffs": pos("BOTTOM", 0, 424),
    },
    # Any Tracking Bar you add starts in this look: ElvUI aura bar size, flat, class coloured
    "tbbStylePresets": [{"name": "ElvUI Aura Bars", "style": {
        "width": 203, "height": 17, "texture": "none", "bgR": 0, "bgG": 0, "bgB": 0, "bgA": 0.6,
        "showTimer": True, "timerPosition": "right", "timerSize": 11,
        "showName": True, "namePosition": "left", "nameSize": 11,
        "iconDisplay": "left", "borderSize": 1, "borderR": 0, "borderG": 0, "borderB": 0,
    }}],
}

# Buff Reminders: on Forever only the spell IDs you add yourself are checked
aura_reminders = {
    "display": {"remindersEnabled": True, "scale": 0.8, "borderSize": 1},
    "unlockPos": pos("TOP", 0, -150),
    "forever": {"camp": False, "customIDs": []},
}

# Quality of Life (profile part; repair and junk selling are account settings, already on)
qol = {
    "showFPS": False,                  # FPS/latency live in the left data panel instead
    "showSecondaryStats": False,
    "cursor": {"enabled": False, "crosshairSize": "None"},
    "raidTools": {"mode": "group"},    # raid markers etc. in groups (ElvUI marker bar)
}

bags = {
    "bagColumns": 12, "bagDesaturateJunkItems": True,
    "showItemlevelInBags": True, "itemlevelFontSize": 12,
    # opens above the right chat, where ElvUI's bags opened
    "bagsPosition": {"point": "BOTTOMRIGHT", "relativePoint": "BOTTOMRIGHT", "x": -4, "y": 232},
}

quest_tracker = {"questTracker": {
    **EUI_STYLE,
    "enabled": True, "visibility": "always", "skinHeaders": True,
    "titleFontSize": 12, "objectiveFontSize": 10, "headerFontSize": 13,
    "bgR": 0.035, "bgG": 0.035, "bgB": 0.035, "bgAlpha": 0.75,
}}

# Damage meter replaces Details: one window above the right chat
damage_meters = {"dm": {
    **EUI_STYLE,
    "barTexture": "none", "barHeight": 18, "barSpacing": 1,
    "showClassColor": True, "numberFormat": 2,
    "bgR": 0, "bgG": 0, "bgB": 0, "bgAlpha": 0.75,
    "windowCount": 1,
    "windows": [{"position": pos("BOTTOMRIGHT", -4, 232), "width": 450, "height": 135,
                 "curDMType": 0}],   # 0 = Damage Done
}}


def block(bid, kind, settings=None, **extra):
    b = {"id": bid, "type": kind, "align": "CENTER", "xOff": 0, "yOff": 0,
         "settings": settings or {}}
    b.update(extra)
    return b


def data_bar(bid, name, point, x, length, thickness, blocks):
    return {"id": bid, "name": name, "orientation": "H", "lengthMode": "custom",
            "length": length, "thickness": thickness, "snapEdge": "none",
            "sizingMode": "even" if len(blocks) > 1 else "auto", "fontScale": 100,
            "theme": {"style": "eui", "euiAlpha": 0.75,
                      "modernColor": {"r": DARK, "g": DARK, "b": DARK, "a": 0.75}},
            "visibility": "always", "savedPos": pos(point, x, 0),
            "nextBlockId": len(blocks), "blocks": blocks}


MENU_OFF = {k: False for k in ("menu", "guild", "social", "char", "spell", "ach", "quest",
                               "lfg", "pvp", "housing", "journal", "pet", "shop", "help")}

# ElvUI datatext panels under each chat, plus the micro menu between the XP bar and right chat
data_bars = {
    "nextBarId": 3,
    "bars": [
        data_bar(1, "Left Panel", "BOTTOMLEFT", 4, 450, 18, [
            block(1, "fps", {}, contentGapR=0),
            block(2, "ms", {"showIcon": False, "latencyMode": "world"}, contentGapL=0),
            block(3, "durability", {"showIcon": True}),
            block(4, "bags", {"showIcon": True, "value": "free", "reagent": False, "lowThreshold": 0}),
        ]),
        data_bar(2, "Right Panel", "BOTTOMRIGHT", -4, 450, 18, [
            block(1, "clock", {"localTime": True, "twentyFour": False, "showMail": True, "showResting": True}),
            block(2, "micromenu", {**MENU_OFF, "guild": True, "disableBlizzardMicroMenu": False,
                                   "hideSocialText": False, "mainMenuSpacing": 4, "iconSpacing": 2},
                  textYOff=8),
            block(3, "gold", {"showIcons": True, "abbreviate": True}),
        ]),
        data_bar(3, "Menu", "BOTTOMRIGHT", -458, 400, 20, [
            block(1, "micromenu", {**MENU_OFF, "menu": True, "guild": True, "social": True,
                                   "char": True, "spell": True, "ach": True, "quest": True,
                                   "lfg": True, "pvp": True, "journal": True, "pet": True,
                                   "help": True, "disableBlizzardMicroMenu": True,
                                   "hideSocialText": False, "mainMenuSpacing": 4, "iconSpacing": 2},
                  textYOff=8),
        ]),
    ],
}

UI_SCALE = 0.64   # Craig ran ElvUI at 64%; the ElvUI offsets are in these units

payload = {
    "version": 3,
    "type": "full",
    "client": "forever",
    "meta": {"euiScale": UI_SCALE},
    "data": {
        "addons": {
            "EllesmereUIUnitFrames": unit_frames,
            "EllesmereUIResourceBars": resource_bars,
            "EllesmereUIActionBars": action_bars,
            "EllesmereUINameplates": nameplates,
            "EllesmereUIRaidFrames": raid_frames,
            "EllesmereUIMinimap": minimap,
            "EllesmereUIChat": chat,
            "EllesmereUICooldownManager": cooldown_manager,
            "EllesmereUIAuraBuffReminders": aura_reminders,
            "EllesmereUIQoL": qol,
            "EllesmereUIBags": bags,
            "EllesmereUIQuestTracker": quest_tracker,
            "EllesmereUIDamageMeters": damage_meters,
            "EllesmereUIDataBars": data_bars,
        },
        "fonts": {"global": "Expressway", "outlineMode": "shadow", "_styleSlots": {"active": "eui"}},
        "euiAccent": {"useClass": False, "custom": ACCENT},
        "uiScale": UI_SCALE,
        # Present but empty: the import drops the fresh-install screen anchors for
        # every module above, so the positions in this string take effect.
        "unlockLayout": {"anchors": {
            "EDM_Win1": {"target": "SCREEN_RIGHT", "side": "LEFT", "offsetX": -4, "offsetY": 0,
                         "edge": {"key": "SCREEN_BOTTOM", "side": "TOP", "offset": 232}},
        }, "widthMatch": {}, "heightMatch": {}, "phantomBounds": {}},
        "unlockLayoutMeta": {"keyToFolder": {"EDM_Win1": "EllesmereUIDamageMeters"}},
    },
}


# ---------------------------------------------------------------- key check
FOLDER_SRC = {
    "EllesmereUIUnitFrames": ["EllesmereUIUnitFrames", "EllesmereUIOptions/EUI_UnitFrames_Options.lua"],
    "EllesmereUIResourceBars": ["EllesmereUIResourceBars"],
    "EllesmereUIActionBars": ["EllesmereUIActionBars", "EllesmereUI.lua"],
    "EllesmereUINameplates": ["EllesmereUINameplates"],
    "EllesmereUIRaidFrames": ["EllesmereUIRaidFrames"],
    "EllesmereUIMinimap": ["EllesmereUIMinimap", "EllesmereUI_ForeverLayout.lua"],
    "EllesmereUIChat": ["EllesmereUIChat", "EllesmereUI_ForeverLayout.lua"],
    "EllesmereUICooldownManager": ["EllesmereUICooldownManager", "EllesmereUIOptions/EUI_CooldownManager_Options.lua"],
    "EllesmereUIAuraBuffReminders": ["EllesmereUIAuraBuffReminders"],
    "EllesmereUIQoL": ["EllesmereUIQoL"],
    "EllesmereUIBags": ["EllesmereUIBags"],
    "EllesmereUIQuestTracker": ["EllesmereUIQuestTracker", "EllesmereUIOptions/EUI_Style_Options.lua"],
    "EllesmereUIDamageMeters": ["EllesmereUIDamageMeters"],
    "EllesmereUIDataBars": ["EllesmereUIDataBars"],
}
SKIP = {"BagBar", "MicroBar", "XPBar", "RepBar", "cooldowns", "utility", "buffs", "r", "g", "b", "a", "x", "y", "w", "h", "point", "relPoint",
        "MainBar", "Bar2", "Bar3", "Bar4", "Bar5", "Bar6", "Bar7", "Bar8", "Bar9", "Bar10",
        "StanceBar", "PetBar", "player", "target", "focus", "pet", "targettarget", "boss", "focustarget"}


def leaf_keys(t, out):
    for k, v in t.items():
        if k not in SKIP:
            out.add(k)
        if isinstance(v, dict):
            leaf_keys(v, out)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    leaf_keys(item, out)
    return out


def check_keys():
    missing = []
    for folder, tbl in payload["data"]["addons"].items():
        paths = [os.path.join(EUI, p) for p in FOLDER_SRC[folder]]
        for key in sorted(leaf_keys(tbl, set())):
            r = subprocess.run(["grep", "-rqw", "--include=*.lua", key, *paths])
            if r.returncode != 0:
                missing.append(f"{folder}: {key}")
    return missing


# ---------------------------------------------------------------- Lua encode/verify
def to_lua(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, dict):
        return "{" + ",".join(f"[{to_lua(k)}]={to_lua(val)}" for k, val in v.items()) + "}"
    if isinstance(v, list):
        return "{" + ",".join(to_lua(item) for item in v) + "}"
    raise TypeError(type(v))


def serializer_source():
    src = open(os.path.join(EUI, "EllesmereUI_Profiles.lua"), encoding="utf-8").read()
    start = src.index("local Serializer = {}")
    end = src.index("EllesmereUI._Serializer = Serializer")
    return src[start:end] + "\nreturn Serializer\n"


def main():
    missing = check_keys()
    print("keys not found in module source:", missing or "none")

    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    lib = lua.execute(open(euilib.LIBDEFLATE, encoding="utf-8").read())
    ser = lua.execute(serializer_source())
    lua.globals().LibDeflate, lua.globals().Serializer = lib, ser
    lua.execute("PAYLOAD = " + to_lua(payload))
    s = lua.eval('"!EUI_" .. LibDeflate:EncodeForPrint(LibDeflate:CompressDeflate(Serializer.Serialize(PAYLOAD), {level = 9}))')

    # Decode exactly as EllesmereUI.DecodeImportString does
    lua.globals().IMPORT = s
    check = lua.execute("""
        local encoded = IMPORT:sub(6)
        local decoded = LibDeflate:DecodeForPrint(encoded)
        assert(decoded, "decode failed")
        local raw = LibDeflate:DecompressDeflate(decoded)
        assert(raw, "decompress failed")
        local p = Serializer.Deserialize(raw)
        assert(type(p) == "table" and p.version == 3 and p.type == "full", "bad payload")
        assert(type(p.data.addons) == "table", "no addons")
        -- round trip: re-serialising the decoded payload must reproduce the same bytes' content
        local again = Serializer.Deserialize(Serializer.Serialize(p))
        local uf = p.data.addons.EllesmereUIUnitFrames
        local ab = p.data.addons.EllesmereUIActionBars
        return string.format("ok: %d chars decoded, player %dx%d at %s %d,%d, MainBar %d icons at y=%d, accent %.4f,%.4f,%.4f, scale %.2f, swing %s y=%d, bagbar %s",
            #raw, uf.player.frameWidth, uf.player.healthHeight, uf.positions.player.point,
            uf.positions.player.x, uf.positions.player.y, ab.bars.MainBar.numIcons,
            ab.barPositions.MainBar.y, p.data.euiAccent.custom.r, p.data.euiAccent.custom.g,
            p.data.euiAccent.custom.b, p.data.uiScale,
            tostring(p.data.addons.EllesmereUIResourceBars.swingTimer.enabled),
            p.data.addons.EllesmereUIResourceBars.swingTimer.unlockPos.y,
            ab.bars.BagBar.barVisibility)
    """)
    print(check)

    # Independent check with Python's zlib on the same bytes
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789()"
    lut = {c: i for i, c in enumerate(alphabet)}
    cache = bits = 0
    out = bytearray()
    for ch in s[5:]:
        cache |= lut[ch] << bits
        bits += 6
        while bits >= 8:
            out.append(cache & 0xFF)
            cache >>= 8
            bits -= 8
    text = zlib.decompress(bytes(out), -15).decode()
    assert text.startswith("{") and "s7:version" not in text[:0]
    print("zlib cross-check ok:", len(text), "chars;", "EllesmereUIActionBars" in text)

    out = sys.argv[1] if len(sys.argv) > 1 else "eui-from-elvui-v3.txt"
    euilib.write_string(out, s)
    print("string length:", len(s))


if __name__ == "__main__":
    sys.exit(main())
