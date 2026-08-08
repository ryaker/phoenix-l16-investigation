#!/usr/bin/env python3
"""Second-pass tiling analysis: group helper calls by destination buffer (tile)."""
import json, sys, collections

blob = json.load(open(sys.argv[1]))
records = blob["records"]

bytile = collections.defaultdict(list)
for r in records:
    bytile[(r["destination"]["allocation"], tuple(r["destination"]["size"]))].append(r)
print("distinct destination buffers:", len(bytile))

sizes = collections.Counter(k[1] for k in bytile)
print("destination sizes:", sizes.most_common())

calls_per_tile = collections.Counter(len(v) for v in bytile.values())
print("helper calls per destination buffer:", calls_per_tile.most_common())

# show a few tiles in detail
shown = 0
for key, recs in sorted(bytile.items(), key=lambda kv: -len(kv[1])):
    if shown >= 4:
        break
    shown += 1
    print("\n=== dest alloc=0x%x size=%s  (%d calls) ===" % (key[0], key[1], len(recs)))
    src = recs[0]["source"]
    print("   src origin=%s bounds=%s size=%s stride=%d dataoff=%d" % (
        src["origin"], src["bounds"], src["size"], src["stride"],
        src["data"] - src["allocation"]))
    rows = sorted(recs, key=lambda r: (r["start"][1], r["start"][0]))
    for r in rows[:40]:
        print("   off=(%7.1f,%7.1f) start=%s end=%s sha=%s" % (
            r["offset_f32"][0], r["offset_f32"][1], r["start"], r["end"],
            r["matrices_sha_prefix"][:12]))
    if len(rows) > 40:
        print("   ... %d more" % (len(rows) - 40))

# global: check offset+start == cell-aligned frame coordinate
print("\n--- per-call cell check ---")
bad = 0
for r in records:
    ox, oy = r["offset_f32"]
    s, e = r["start"], r["end"]
    # hypothesis: (start+off) .. (end+off) lies inside [0,260]
    if not (0 <= ox + s[0] and ox + e[0] <= 260 and 0 <= oy + s[1] and oy + e[1] <= 260):
        bad += 1
print("calls violating [0,260] cell containment:", bad, "/", len(records))
