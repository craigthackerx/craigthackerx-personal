"""Decode ElvUI !E1! export strings (LibDeflate print encoding + raw DEFLATE + AceSerializer) to JSON.

Usage: python3 elvui_decode.py <string-file> [...] [--out DIR]
Writes <name>.json next to each input (or into --out) and prints the export type (profile,
private, global, filters). Pure Python, no dependencies.

ElvUI has been replaced by EllesmereUI, so the ElvUI strings themselves now live in the
repository's legacy tag: git show legacy:wow/elvui/0-elvui-pofile-import.txt > elvui.txt
"""
import argparse
import json
import os
import zlib

ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789()"
LOOKUP = {c: i for i, c in enumerate(ALPHABET)}


def decode_for_print(s: str) -> bytes:
    s = "".join(ch for ch in s if ch in LOOKUP)
    out = bytearray()
    cache = 0
    bits = 0
    for ch in s:
        cache |= LOOKUP[ch] << bits
        bits += 6
        while bits >= 8:
            out.append(cache & 0xFF)
            cache >>= 8
            bits -= 8
    return bytes(out)


def unescape(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "~" and i + 1 < len(s):
            n = s[i + 1]
            # AceSerializer-3.0 escapes: ~z = \30, ~{ = \127, ~| = "~", ~} = "^",
            # anything else is a control or space character shifted up by 64 ("~`" = space)
            if n == "z":
                out.append("\x1e")
            elif n == "{":
                out.append("\x7f")
            elif n == "|":
                out.append("~")
            elif n == "}":
                out.append("^")
            else:
                out.append(chr(ord(n) - 64))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def parse_number(tok: str):
    try:
        v = float(tok)
        return int(v) if v.is_integer() else round(v, 4)
    except ValueError:
        return tok


def ace_deserialize(data: str):
    if not data.startswith("^1"):
        raise ValueError("not AceSerializer data: " + data[:20])
    pos = 2
    tokens = []
    while pos < len(data):
        if data[pos] != "^":
            pos += 1
            continue
        ctl = data[pos + 1]
        nxt = data.find("^", pos + 2)
        if nxt == -1:
            nxt = len(data)
        tokens.append((ctl, data[pos + 2:nxt]))
        pos = nxt
    it = iter(tokens)

    def read(tok):
        ctl, val = tok
        if ctl == "S":
            return unescape(val)
        if ctl == "N":
            return parse_number(val)
        if ctl == "F":
            mant = val
            ctl2, exp = next(it)
            try:
                return round(float(mant) * (2 ** int(exp)), 4)
            except ValueError:
                return mant
        if ctl == "B":
            return True
        if ctl == "b":
            return False
        if ctl == "Z":
            return None
        if ctl == "T":
            tbl = {}
            while True:
                ktok = next(it)
                if ktok[0] == "t":
                    return tbl
                k = read(ktok)
                v = read(next(it))
                tbl[str(k)] = v
        if ctl == "^":
            raise StopIteration
        raise ValueError("unknown control " + ctl)

    results = []
    try:
        while True:
            tok = next(it)
            if tok[0] == "^":
                break
            results.append(read(tok))
    except StopIteration:
        pass
    return results


def decode(export: str):
    export = export.strip()
    if export.startswith("!E1!"):
        export = export[4:]
    raw = decode_for_print(export)
    text = zlib.decompress(raw, -15).decode("utf-8", errors="replace")
    meta = ""
    if "::" in text:
        body, _, meta = text.partition("::")
    else:
        body = text
    return ace_deserialize(body), meta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", help="output folder (default: next to each input)")
    args = ap.parse_args()
    for path in args.files:
        with open(path, encoding="utf-8") as fh:
            data, meta = decode(fh.read())
        out_dir = args.out or os.path.dirname(os.path.abspath(path))
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + ".json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(data[0] if len(data) == 1 else data, fh, indent=1, sort_keys=True)
        print(path, "->", out, "| meta:", meta)


if __name__ == "__main__":
    main()
