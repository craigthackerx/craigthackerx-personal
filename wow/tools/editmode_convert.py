"""Parse, validate and convert a WoW Forever Edit Mode layout string to retail.

Usage: python3 editmode_convert.py ../blizz-ui/Craigtho-forever.txt ../blizz-ui/Craigtho-retail.txt
       python3 editmode_convert.py --check <layout-file> [...]

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
import argparse

FOREVER_ONLY = {26: "MainActionBarEndCap", 27: "GroupFinder", 29: "SwingTimer"}
RENUMBER = {28: 26}                     # LossOfControl
CHAT_FRAME = 8
ENTRY_TOKENS = 10


class LayoutError(ValueError):
    """The layout string is not in the format described above."""


def _check(ok, message):
    # Not assert: asserts are stripped under python -O, and these guard real input.
    if not ok:
        raise LayoutError(message)


def _int(tok, what):
    try:
        return int(tok)
    except ValueError:
        raise LayoutError(f"{what}: expected an integer, got {tok!r}") from None


def parse(text):
    """Return (version, interfaceStyle or None, entries) for a v3 or v4 layout string."""
    tok = text.split()
    _check(len(tok) >= 2, "empty or truncated layout string")
    version = _int(tok[0], "version")
    if version >= 4:
        _check(len(tok) >= 3, "truncated v4 header")
        interface_style, count, i = _int(tok[1], "interfaceStyle"), _int(tok[2], "count"), 3
    else:
        interface_style, count, i = None, _int(tok[1], "count"), 2
    entries = []
    while i < len(tok):
        e = tok[i:i + ENTRY_TOKENS]
        _check(len(e) == ENTRY_TOKENS, f"truncated entry at token {i}: {e}")
        system, index, default, point, relpoint = (_int(x, f"entry at token {i}") for x in e[:5])
        rel, blob = e[5], e[9]
        where = f"system {system} {index}"
        for axis, value in (("offsetX", e[6]), ("offsetY", e[7])):
            try:
                float(value)
            except ValueError:
                raise LayoutError(f"{where}: {axis} {value!r} is not a number") from None
        _check(_int(e[8], where) == -1, f"{where}: unexpected anchorInfo2 at token {i}")
        _check(0 <= point <= 8 and 0 <= relpoint <= 8 and default in (0, 1), f"{where}: bad anchor at token {i}")
        _check(blob == "#" or len(blob) % 2 == 0, f"{where}: odd settings blob {blob!r}")
        _check(all(33 <= ord(c) <= 126 for c in blob), f"{where}: non-printable in {blob!r}")
        settings = [] if blob == "#" else [(ord(blob[j]) - 35, ord(blob[j + 1]) - 35) for j in range(0, len(blob), 2)]
        entries.append(dict(system=system, index=index, default=default, point=point, relpoint=relpoint,
                            rel=rel, x=e[6], y=e[7], blob=blob, settings=settings))
        i += ENTRY_TOKENS
    _check(len(entries) == count, f"header says {count} systems, found {len(entries)}")
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


def read_layout(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def convert(src, dst):
    v, style, entries = parse(read_layout(src))
    print(f"source: version {v}, interfaceStyle {style}, {len(entries)} systems parsed cleanly")
    dropped = [f"{e['system']}:{FOREVER_ONLY[e['system']]}" for e in entries if e["system"] in FOREVER_ONLY]
    retail = to_retail(entries)
    rels = sorted({e["rel"] for e in retail})
    print("dropped (Forever only):", ", ".join(dropped))
    print("relativeTo frames kept:", ", ".join(rels))
    chat = next((e for e in retail if e["system"] == CHAT_FRAME), None)
    if chat is None:
        print("chat frame check: no chat frame in this layout")
    else:
        cs = dict(chat["settings"])
        print(f"chat frame check: {cs[0]*100 + cs[1]} x {cs[2]*100 + cs[3]}")
    s = serialise_v3(retail)
    _, _, back = parse(s)

    def ids(es):
        return [(e["system"], e["index"], e["blob"]) for e in es]

    _check(ids(back) == ids(retail), "retail string did not re-parse to the same systems")
    with open(dst, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    print(f"retail: version 3, {len(back)} systems, {len(s)} chars, re-parsed OK -> {dst}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only parse and validate the given layout files")
    ap.add_argument("files", nargs="+", metavar="file", help="forever and retail paths, or layouts to --check")
    args = ap.parse_args()
    try:
        if args.check:
            for path in args.files:
                v, style, entries = parse(read_layout(path))
                print(f"{path}: version {v}, interfaceStyle {style}, {len(entries)} systems parsed cleanly")
        elif len(args.files) == 2:
            convert(*args.files)
        else:
            ap.error("convert takes exactly two paths: <forever-layout> <retail-output>")
    except LayoutError as err:
        raise SystemExit(f"invalid layout: {err}") from None


if __name__ == "__main__":
    main()
