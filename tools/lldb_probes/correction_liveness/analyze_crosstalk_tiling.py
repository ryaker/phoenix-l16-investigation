#!/usr/bin/env python3
"""Analyze the cross-talk helper tiling census report.

Derives:
  * how many helper invocations, how they group into grid cells
  * the (offset, scale) contract per cell
  * whether tiles carry a source halo (source.origin / data-vs-allocation delta)
  * the global frame rectangle each tile writes
"""
import json, sys, collections

path = sys.argv[1]
blob = json.load(open(path))
records = blob["records"]
print("label:", blob.get("label"), "truncated:", blob.get("truncated"),
      "errors:", blob.get("errors"))
print("records:", len(records))

# --- scale / parity / matrices uniformity -------------------------------
scales = collections.Counter(tuple(r["scale_f32"]) for r in records)
parities = collections.Counter(tuple(r["parity_i32"]) for r in records)
print("\ndistinct scale_f32:", dict(scales))
print("distinct parity_i32:", dict(parities))

threads = collections.Counter(r["thread"] for r in records)
print("threads:", len(threads))

# --- group by matrices (a grid cell has its own 4 prepared corners) -----
bycell = collections.defaultdict(list)
for r in records:
    bycell[(r["matrices_sha_prefix"], tuple(r["offset_f32"]))].append(r)
print("\ndistinct (matrices,offset) groups:", len(bycell))

bysha = collections.defaultdict(set)
for r in records:
    bysha[r["matrices_sha_prefix"]].add(tuple(r["offset_f32"]))
print("distinct matrices_sha:", len(bysha))

# --- offsets ------------------------------------------------------------
offs = sorted({tuple(r["offset_f32"]) for r in records})
oxs = sorted({o[0] for o in offs}); oys = sorted({o[1] for o in offs})
print("distinct offsets:", len(offs))
print("offset x values:", oxs[:40], "..." if len(oxs) > 40 else "")
print("offset y values:", oys[:40], "..." if len(oys) > 40 else "")

# --- tile extents -------------------------------------------------------
ext = collections.Counter()
for r in records:
    s, e = r["start"], r["end"]
    ext[(e[0]-s[0], e[1]-s[1])] += 1
print("\ntile (w,h) histogram (top 20):", ext.most_common(20))

starts = collections.Counter(tuple(r["start"]) for r in records)
print("distinct starts:", len(starts), "top:", starts.most_common(5))

# --- source halo evidence ----------------------------------------------
halo = collections.Counter()
for r in records:
    src, dst = r["source"], r["destination"]
    halo[(tuple(src["origin"]), src["data"] - src["allocation"], src["stride"],
          tuple(src["size"]), tuple(src["bounds"]),
          tuple(dst["origin"]), dst["data"] - dst["allocation"], dst["stride"],
          tuple(dst["size"]), tuple(dst["bounds"]))] += 1
print("\nsource/destination descriptor shapes:", len(halo))
for k, v in halo.most_common(12):
    print("  n=%-5d src origin=%s dataoff=%d stride=%d size=%s bounds=%s | dst origin=%s dataoff=%d stride=%d size=%s bounds=%s"
          % (v, k[0], k[1], k[2], k[3], k[4], k[5], k[6], k[7], k[8], k[9]))

# --- global coverage: offset + [start,end) ------------------------------
covered = []
for r in records:
    ox, oy = r["offset_f32"]
    s, e = r["start"], r["end"]
    covered.append((int(oy)+s[1], int(oy)+e[1], int(ox)+s[0], int(ox)+e[0]))
xs = sorted({c[2] for c in covered}); xe = sorted({c[3] for c in covered})
ys = sorted({c[0] for c in covered}); ye = sorted({c[1] for c in covered})
print("\nglobal x start range:", xs[0], "->", xs[-1], " x end range:", xe[0], "->", xe[-1])
print("global y start range:", ys[0], "->", ys[-1], " y end range:", ye[0], "->", ye[-1])

# area sum
area = sum((c[1]-c[0])*(c[3]-c[2]) for c in covered)
print("summed tile area:", area, " (4160*3120 =", 4160*3120, ", /4 =", 4160*3120//4, ")")
