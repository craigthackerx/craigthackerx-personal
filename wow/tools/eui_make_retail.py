"""Build the retail EllesmereUI profile from the WoW Forever one.

Usage: python3 eui_make_retail.py ../ellesmereui/wow-forever.txt ../ellesmereui/retail.txt

The layout and look are shared, so retail is derived from Forever rather than kept by
hand. The transform:
  * stamps the string as retail (drops payload.client), so EllesmereUI treats it as
    same-client on retail
  * drops Forever-only data: Cooldown Manager spell layouts (they would land on the
    wrong retail spec), the swing timer, threat % text, the Forever buff wipe flag,
    Forever Buff Reminders, and threat meter size links
  * adds the retail-only modules in the same flat dark style: Mythic+ Tools, Friends
    list and Dragon Riding

Re-run it whenever wow-forever.txt changes, then check the result with eui_decode.py
and eui_verify_layout.py --client retail.
"""
import argparse

import euilib

TRANSFORM = r"""
function MakeRetail(p)
    local d, A = p.data, p.data.addons
    p.client = nil
    d.cdmSpells = nil
    if A.EllesmereUIResourceBars then A.EllesmereUIResourceBars.swingTimer = nil end
    local uf = A.EllesmereUIUnitFrames
    if uf then
        uf.threatPctEnabled = nil
        if uf.playerAuraBars then uf.playerAuraBars.fvBuffWipe = nil end
    end
    if A.EllesmereUIAuraBuffReminders then A.EllesmereUIAuraBuffReminders.forever = nil end
    local ul = d.unlockLayout
    if ul then
        if ul.widthMatch then ul.widthMatch.EUI_ThreatMeter = nil end
        if ul.heightMatch then ul.heightMatch.EUI_ThreatMeter = nil end
    end

    local DARK, BLACK = { r = 0.054, g = 0.054, b = 0.054, a = 0.75 }, { r = 0, g = 0, b = 0, a = 1 }
    local ACCENT = { r = 0.0588, g = 0.5137, b = 0.851, a = 1 }

    -- Mythic+ Tools: flat dark, black bar borders, accent title and forces bar.
    -- No position set: it sits on the quest tracker's top right (the addon default).
    A.EllesmereUIMythicTimer = {
        enabled = true, standaloneAlpha = 0.75,
        customBorderStyle = true, borderSize = 1, borderTexture = "solid",
        borderR = 0, borderG = 0, borderB = 0, borderA = 1, borderApplyToForces = true,
        titleUseAccent = true, enemyBarUseAccent = true, showAccent = false,
        showAffixes = true, showDeaths = true, showPlusTwoTimer = true, showPlusThreeTimer = true,
        showEnemyBar = true, showEnemyText = true, enemyForcesTextFormat = "PERCENT",
        showPullBar = true,
        showObjectives = true, showObjectiveTimes = true,
    }

    -- Friends list: EllesmereUI look, class coloured names. The window background is an
    -- account-wide window skin setting, so it cannot travel in a profile string.
    A.EllesmereUIFriends = { friends = {
        enabled = true, useBlizzardStyle = false, useClassicStyle = false,
        classColorNames = true, showClassIcons = true,
    } }

    -- Dragon Riding HUD: rage bar width, flat dark rows, accent vigor pips, just above
    -- the Cooldown Manager rows (their top edge is at y 452).
    A.EllesmereUIDragonRiding = {
        enabled = true, useBlizzardStyle = false, useClassicStyle = false, vigorStyle = "bars",
        width = 200, speedHeight = 14, skyridingHeight = 10, secondWindHeight = 6, gap = 2, stackSpacing = 2,
        barTexture = "none", borderThickness = 1, borderColor = BLACK,
        speedBarBg = DARK, skyridingBg = DARK, secondWindBg = DARK,
        skyridingFilled = ACCENT,
        showSpeed = true, showSecondWind = true, showWhirlingSurge = true,
        unlockPos = { point = "BOTTOM", relPoint = "BOTTOM", x = 0, y = 462 },
    }
    return p
end
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("forever")
    ap.add_argument("retail")
    args = ap.parse_args()
    lua = euilib.runtime()
    lua.execute(TRANSFORM)
    g = lua.globals()
    p = g.DecodeEUI(euilib.read_string(args.forever))
    if p["type"] != "full":
        raise SystemExit(f"expected a profile export (type full), got {p['type']}")
    s = g.EncodeEUI(g.MakeRetail(p))
    back = g.DecodeEUI(s)
    assert back["client"] is None and back["data"]["cdmSpells"] is None
    n = len(list(back["data"]["addons"].keys()))
    euilib.write_string(args.retail, s)
    print(f"retail profile: {n} modules, {len(s)} chars, starts {s[:12]} ends {s[-8:]} -> {args.retail}")


if __name__ == "__main__":
    main()
