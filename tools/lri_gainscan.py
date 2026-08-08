#!/usr/bin/env python3
"""lri_gainscan.py -- fast header-only census of LRI captures.

Walks the LELR block chain by SEEKING (never reads the raw surfaces) and
concatenates only the msg_type==0 (LightHeader) fragments.  Prints, per
capture: device_unique_id (body identity), focal, ref cam, ref gain/exp/dgain.

Block header (engine/lri/lelr.cpp): magic "LELR" @0, total_block_len u64 @4,
msg_offset u64 @12, msg_len u32 @20, msg_type u8 @24.

Usage: lri_gainscan.py <dir-or-file> [...]
"""
import os
import struct
import sys


def read_varint(b, o):
    r = 0
    s = 0
    while o < len(b):
        c = b[o]
        o += 1
        r |= (c & 0x7F) << s
        if not (c & 0x80):
            return r, o
        s += 7
    raise ValueError("varint")


def fields(b):
    out = []
    o = 0
    n = len(b)
    while o < n:
        try:
            k, o = read_varint(b, o)
        except ValueError:
            break
        fn, wt = k >> 3, k & 7
        if wt == 0:
            v, o = read_varint(b, o)
            out.append((fn, 0, v))
        elif wt == 1:
            if o + 8 > n:
                break
            out.append((fn, 1, b[o:o + 8]))
            o += 8
        elif wt == 2:
            ln, o = read_varint(b, o)
            if o + ln > n:
                break
            out.append((fn, 2, b[o:o + ln]))
            o += ln
        elif wt == 5:
            if o + 4 > n:
                break
            out.append((fn, 5, b[o:o + 4]))
            o += 4
        else:
            break
    return out


def header_fragments(path):
    frags = []
    sz = os.path.getsize(path)
    with open(path, "rb") as f:
        pos = 0
        while pos + 32 <= sz:
            f.seek(pos)
            h = f.read(32)
            if len(h) < 32 or h[:4] != b"LELR":
                break
            total = struct.unpack_from("<Q", h, 4)[0]
            moff = struct.unpack_from("<Q", h, 12)[0]
            mlen = struct.unpack_from("<I", h, 20)[0]
            mtyp = h[24]
            if total < 32:
                break
            if mtyp == 0 and mlen:
                f.seek(pos + moff)
                frags.append(f.read(mlen))
            pos += total
    return frags


def scan(path):
    focal = ref = None
    dlo = dhi = 0
    mods = {}
    for p in header_fragments(path):
        for fn, wt, v in fields(p):
            if fn == 4 and wt == 0:
                focal = v
            elif fn == 5 and wt == 0:
                ref = v
            elif fn == 6 and wt == 0:
                dlo = v
            elif fn == 7 and wt == 0:
                dhi = v
            elif fn == 12 and wt == 2:
                mid = gain = exp = dg = None
                for a, bw, c in fields(v):
                    if a == 2 and bw == 0:
                        mid = c
                    elif a == 7 and bw == 5:
                        gain = struct.unpack("<f", c)[0]
                    elif a == 8 and bw == 0:
                        exp = c
                    elif a == 14 and bw == 5:
                        dg = struct.unpack("<f", c)[0]
                if mid is not None:
                    cur = mods.setdefault(mid, [None, None, None])
                    if gain is not None:
                        cur[0] = gain
                    if exp is not None:
                        cur[1] = exp
                    if dg is not None:
                        cur[2] = dg
    rg, re_, rd = mods.get(ref, [None, None, None])
    return dict(path=path, body="%016x%016x" % (dhi, dlo), focal=focal,
                ref=ref, gain=rg, exp=re_, dgain=rd, nmod=len(mods),
                gains=sorted({m[0] for m in mods.values() if m[0]}))


def main():
    targets = []
    for a in sys.argv[1:]:
        if os.path.isdir(a):
            for root, _, fs in os.walk(a):
                for fn in sorted(fs):
                    if fn.lower().endswith(".lri"):
                        targets.append(os.path.join(root, fn))
        else:
            targets.append(a)
    for t in targets:
        try:
            r = scan(t)
        except Exception as ex:
            print("ERR  %s  %s" % (t, ex))
            continue
        print("%s f=%-4s ref=%-3s gain=%-7s exp=%-11s dg=%-8s n=%-3d gains=%s  %s"
              % (r["body"][-8:], r["focal"], r["ref"],
                 ("%.4f" % r["gain"]) if r["gain"] else r["gain"], r["exp"],
                 ("%.4f" % r["dgain"]) if r["dgain"] else r["dgain"],
                 r["nmod"], [round(g, 4) for g in r["gains"]], t))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
