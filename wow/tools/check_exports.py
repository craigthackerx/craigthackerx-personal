"""Check the committed WoW UI strings are well formed and safe to publish.

Usage: python3 check_exports.py

Run by verify.sh, and so by CI. For every string file under wow/ellesmereui and
wow/blizz-ui it checks that:
  * the file is one line of printable ASCII with no trailing newline. The strings are
    opaque data: an editor that rewraps them or adds a newline can break the import
  * EllesmereUI strings decode, through the addon's own code, to a profile export
    (type full). A full account export fails the check: it carries character gold, bag
    contents and click cast bindings, and this repository is public
  * Edit Mode layouts parse cleanly and match their header's system count, and
    retail layouts use the version retail imports
It also fails if decoded .lua or .json output is tracked anywhere under wow/.
"""
import argparse
import glob
import os
import subprocess
import sys

import editmode_convert
import euilib

HERE = os.path.dirname(os.path.abspath(__file__))
WOW = os.path.dirname(HERE)
ROOT = os.path.dirname(WOW)


def rel(path):
    return os.path.relpath(path, ROOT)


def shape_problem(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if not data:
        return "empty file"
    if b"\n" in data or b"\r" in data:
        return "must be a single line with no trailing newline"
    if any(b < 0x20 or b > 0x7E for b in data):
        return "contains characters outside printable ASCII"
    return None


def eui_problem(lua, path):
    s = euilib.read_string(path)
    if not s.startswith("!EUI_"):
        return "does not start with !EUI_"
    try:
        p = lua.globals().DecodeEUI(s)
    except Exception as err:  # lupa raises LuaError; report whatever the decoder says
        return f"does not decode: {str(err).splitlines()[0]}"
    if p["type"] != "full":
        return f"type {p['type']}, expected a profile export (type full); never commit account exports"
    return None


def layout_problem(path):
    try:
        version, _, _ = editmode_convert.parse(editmode_convert.read_layout(path))
    except editmode_convert.LayoutError as err:
        return str(err)
    # Retail rejects layout versions it does not know (version 3 failed on retail 12.1).
    if "retail" in os.path.basename(path).lower() and version != editmode_convert.RETAIL_VERSION:
        return f"retail layout is version {version}, retail imports version {editmode_convert.RETAIL_VERSION}"
    return None


def tracked_decoded_output():
    try:
        out = subprocess.run(["git", "-C", ROOT, "ls-files", "--", "wow/*.lua", "wow/*.json"],
                             capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        print("note: not a git checkout, skipping the decoded output check")
        return []
    return [line for line in out.splitlines() if line]


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    eui_files = sorted(glob.glob(os.path.join(WOW, "ellesmereui", "*.txt")))
    layout_files = sorted(glob.glob(os.path.join(WOW, "blizz-ui", "*.txt")))
    lua = euilib.runtime() if eui_files else None
    failures = 0

    def report(path, problem):
        nonlocal failures
        if problem:
            failures += 1
            print(f"FAIL {rel(path)}: {problem}")
        else:
            print(f"ok   {rel(path)}")

    for path in eui_files:
        report(path, shape_problem(path) or eui_problem(lua, path))
    for path in layout_files:
        report(path, shape_problem(path) or layout_problem(path))
    for path in tracked_decoded_output():
        failures += 1
        print(f"FAIL {path}: decoded output must not be committed")

    if failures:
        raise SystemExit(f"{failures} export check(s) failed")
    print(f"{len(eui_files) + len(layout_files)} exports checked")


if __name__ == "__main__":
    sys.exit(main())
