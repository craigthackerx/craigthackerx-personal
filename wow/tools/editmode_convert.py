"""Parse, validate and convert a WoW Forever Edit Mode layout string to retail.

Usage: python3 editmode_convert.py ../blizz-ui/Craigtho-forever.txt ../blizz-ui/Craigtho-retail.txt

Format (from the strings themselves; version 4 is Forever's, version 3 has no
interfaceStyle field):
  v4: <version> <interfaceStyle> <count> <entry>...
  v3: <version> <count> <entry>...
  entry: <system> <systemIndex> <isInDefaultPosition> <point> <relativePoint>
         <relativeTo> <offsetX> <offsetY> <anchorInfo2 marker (-1 = none)> <settings>
  settings: "#" (none) or (setting, value) character pairs, each char - 35.

System IDs come from Blizzard's generated docs (Gethe/wow-ui-source):
  retail 12.1:  ... 25=TotemActionBar 26=LossOfControl
  forever 1.60: ... 25=TotemActionBar 26=MainActionBarEndCap 27=GroupFinder
                28=LossOfControl 29=SwingTimer
Every other system and every per-system settings enum is identical (checked against
live 12.1.0 build 69933 and forever 1.60.1 build 70124). Re-check both branches'
Blizzard_APIDocumentationGenerated/EditModeManagerConstants*Documentation.lua after
major patches.

Assumption: retail reads the version 3 format (the one Forever itself wrote before it
added interfaceStyle). If retail rejects the output, export a native retail layout.
"""
import sys

FOREVER_ONLY = {26: "MainActionBarEndCap", 27: "GroupFinder", 29: "SwingTimer"}
RENUMBER = {28: 26}                     # LossOfControl


def parse(text):
    tok = text.split()
    version = int(tok[0])
    if version >= 4:
        interface_style, count, i = int(tok[1]), int(tok[2]), 3
    else:
        interface_style, count, i = None, int(tok[1]), 2
    entries = []
    while i < len(tok):
        e = tok[i:i + 10]
        assert len(e) == 10, f"truncated entry at token {i}: {e}"
        system, index, default, point, relpoint = (int(x) for x in e[:5])
        rel, x, y, a2, blob = e[5], float(e[6]), float(e[7]), int(e[8]), e[9]
        assert a2 == -1, f"unexpected anchorInfo2 at token {i}"
        assert 0 <= point <= 8 and 0 <= relpoint <= 8 and default in (0, 1), f"bad anchor at token {i}"
        assert blob == "#" or len(blob) % 2 == 0, f"odd settings blob {blob!r} (system {system} {index})"
        assert all(33 <= ord(c) <= 126 for c in blob), f"non-printable in {blob!r}"
        settings = [] if blob == "#" else [(ord(blob[j]) - 35, ord(blob[j + 1]) - 35) for j in range(0, len(blob), 2)]
        entries.append(dict(system=system, index=index, default=default, point=point, relpoint=relpoint,
                            rel=rel, x=e[6], y=e[7], blob=blob, settings=settings))
        i += 10
    assert len(entries) == count, f"header says {count} systems, found {len(entries)}"
    return version, interface_style, entries


def to_retail(entries):
    out = []
    for e in entries:
        if e["system"] in FOREVER_ONLY:
            continue
        e = dict(e, system=RENUMBER.get(e["system"], e["system"]))
        out.append(e)
    return out


def serialise_v3(entries):
    parts = ["3", str(len(entries))]
    for e in entries:
        parts += [str(e["system"]), str(e["index"]), str(e["default"]), str(e["point"]), str(e["relpoint"]),
                  e["rel"], e["x"], e["y"], "-1", e["blob"]]
    return " ".join(parts)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    v, style, entries = parse(open(src).read())
    print(f"source: version {v}, interfaceStyle {style}, {len(entries)} systems parsed cleanly")
    dropped = [f"{e['system']}:{FOREVER_ONLY[e['system']]}" for e in entries if e["system"] in FOREVER_ONLY]
    retail = to_retail(entries)
    rels = sorted({e["rel"] for e in retail})
    print("dropped (Forever only):", ", ".join(dropped))
    print("relativeTo frames kept:", ", ".join(rels))
    chat = next(e for e in retail if e["system"] == 8)["settings"]
    cs = dict(chat)
    print(f"chat frame check: {cs[0]*100 + cs[1]} x {cs[2]*100 + cs[3]}")
    s = serialise_v3(retail)
    v2, _, back = parse(s)
    assert [(e['system'], e['index'], e['blob']) for e in back] == [(e['system'], e['index'], e['blob']) for e in retail]
    with open(dst, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    print(f"retail: version 3, {len(back)} systems, {len(s)} chars, re-parsed OK -> {dst}")
