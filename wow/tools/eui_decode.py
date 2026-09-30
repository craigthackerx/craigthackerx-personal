"""Decode EllesmereUI (!EUI_) profile strings into readable files.

Usage: python3 eui_decode.py <string-file> [...] [--out DIR]
Writes <name>.lua (a readable Lua table) and <name>.json for each input, and prints a
one-line summary: payload type, client (forever or retail), UI scale and modules.
Works for normal profile exports and full account exports.
"""
import argparse
import json
import os
import sys

import euilib


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", help="output folder (default: next to each input)")
    args = ap.parse_args()
    lua = euilib.runtime()
    g = lua.globals()
    for path in args.files:
        p = g.DecodeEUI(euilib.read_string(path))
        base = os.path.splitext(os.path.basename(path))[0]
        out_dir = args.out or os.path.dirname(os.path.abspath(path))
        os.makedirs(out_dir, exist_ok=True)
        stem = os.path.join(out_dir, base)
        with open(stem + ".lua", "w", encoding="utf-8") as fh:
            fh.write("return " + g.Dump(p) + "\n")
        with open(stem + ".json", "w", encoding="utf-8") as fh:
            json.dump(euilib.to_py(p), fh, indent=1, sort_keys=True)
        d = p["data"]
        addons = d["addons"]
        mods = sorted(k.replace("EllesmereUI", "") for k in addons.keys()) if addons else []
        client = p["client"] or "retail"
        print(f"{os.path.basename(path)}: type={p['type']} client={client} scale={d['uiScale']} "
              f"modules={len(mods)} -> {stem}.lua / .json")
        if mods:
            print("   ", ", ".join(mods))
        if p["type"] != "full":
            print(f"    WARNING: type {p['type']} is not a profile export. A full account export carries gold, "
                  "bag contents and click cast bindings: never commit it.", file=sys.stderr)


if __name__ == "__main__":
    main()
