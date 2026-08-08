#!/usr/bin/env python3
"""Third pass: do the source/destination data pointers advance per sub-call?"""
import json, sys, collections

blob = json.load(open(sys.argv[1]))
records = blob["records"]

bytile = collections.defaultdict(list)
for r in records:
    bytile[r["destination"]["allocation"]].append(r)

for alloc, recs in sorted(bytile.items(), key=lambda kv: -len(kv[1]))[:2]:
    print("=== dest alloc=0x%x  size=%s  (%d calls) ===" % (
        alloc, recs[0]["destination"]["size"], len(recs)))
    for r in sorted(recs, key=lambda r: (r["start"][1], r["start"][0])):
        s, e, o = r["start"], r["end"], r["offset_f32"]
        src, dst = r["source"], r["destination"]
        print("  off=(%6.1f,%6.1f) start=%-12s end=%-12s "
              "srcdata=+%-6d srcorg=%-9s srcbnd=%-11s srcsz=%-11s srcstr=%-4d "
              "dstdata=+%-6d dstsz=%s" % (
            o[0], o[1], s, e,
            src["data"] - src["allocation"], src["origin"], src["bounds"],
            src["size"], src["stride"],
            dst["data"] - dst["allocation"], dst["size"]))
    print()

# Is destination allocation reused across tiles? map alloc -> set of sizes
print("total distinct dest allocations:", len(bytile))
