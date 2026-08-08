#!/usr/bin/env python3
"""Bit-exact G-42 cost replay vs Lumen's captured local_curve.u16le, ALL cells.
For each g42_cost_curve/<cell> with report.json+local_curve, recompute the exact
G-42 photometric cost at the captured reference pixel over the captured hypothesis
window using ONLY the cell's own captured planes/records/lookup, and require the
result to equal Lumen's captured curve byte-for-byte. Deterministic; no scoring."""
import struct, math, json, glob, os, sys

ROOT = "/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/g42_cost_curve"
IMGW = 2080

def f32(x): return struct.unpack("<f", struct.pack("<f", float(x)))[0]
def mul(a, b): return f32(f32(a) * f32(b))
def add(a, b): return f32(f32(a) + f32(b))
def div(a, b): return f32(f32(a) / f32(b))
def pavgb(a, b): return (a + b + 1) >> 1

def project(record, u, v, depth, w, h):
    values = struct.unpack_from("<16f", record, 0)
    cols = [values[i:i+4] for i in range(0, 16, 4)]
    sx_, sy_ = struct.unpack_from("<2f", record, 0x48)
    qx = mul(mul(f32(u), depth), sx_); qy = mul(mul(f32(v), depth), sy_)
    p = []
    for lane in range(4):
        val = mul(depth, cols[2][lane]); val = add(val, cols[3][lane])
        val = add(val, mul(qx, cols[0][lane])); val = add(val, mul(qy, cols[1][lane]))
        p.append(val)
    if not (math.isfinite(p[2]) and p[2] != 0.0): return None
    iz = div(1.0, p[2]); cx = add(mul(p[0], iz), 0.25); cy = add(mul(p[1], iz), 0.25)
    sx = min(max(cx, 1.0), w - 3.0); sy = min(max(cy, 1.0), h - 3.0)
    return [int(sx), int(sy)], [int(f32(sx + sx)) & 1, int(f32(sy + sy)) & 1]

def sampled_patch(raw, base, half, w):
    bx, by = base; hx, hy = half; rows = []
    for py in range(3):
        row = []
        for px in range(4):
            x = bx - 1 + px; y = by - 1 + py
            for ch in range(4):
                off = 4*(y*w + x) + ch; left = raw[off]
                if hy: left = pavgb(left, raw[off + 4*w])
                if hx:
                    right = raw[off + 4]
                    if hy: right = pavgb(right, raw[off + 4 + 4*w])
                    left = pavgb(left, right)
                row.append(left)
        rows.append(bytes(row))
    return rows

def source_cost(rows, anchor_rows, cap, weight):
    sums = [0, 0, 0, 0]
    for sr, ar in zip(rows, anchor_rows):
        for pixel in range(3):
            for ch in range(4):
                idx = 4*pixel + ch; sums[ch] += min(abs(sr[idx] - ar[idx]), cap[ch])
    scaled = [((weight[c]*sums[c]) + 16) >> 5 for c in range(4)]
    return min(sum(scaled), 65535)

def verify(run):
    rep = json.load(open(run + "/report.json"))
    lookup = struct.unpack(f"<{rep['lookup_count']}f", open(run + "/lookup.f32le", "rb").read())
    rr = open(run + "/projection_records.bin", "rb").read()
    nrec = rep['projection_record_count']
    records = [rr[0x50*i:0x50*(i+1)] for i in range(nrec)]
    nsrc = rep['source_count']
    imgs = [open(run + f"/image{i}.rgba8", "rb").read() for i in range(1 + nsrc)]
    cap = bytes.fromhex(rep['cap_hex'])[:4]
    wh = bytes.fromhex(rep['weights_hex'])
    weights = [struct.unpack_from("<4H", wh, 8*i) for i in range(nsrc)]
    ux, uy = rep['reference_pixel']; lo = rep['lower_hypothesis']; hc = rep['hypothesis_count']
    captured = list(struct.unpack(f"<{hc}H", open(run + "/local_curve.u16le", "rb").read()))
    anchor = imgs[0]
    def anchor_patch(u, v):
        rows = []
        for r in range(3):
            off = 4*((v-1+r)*IMGW + (u-1)); rows.append(anchor[off:off+16])
        return rows
    def combined(u, v, h):
        depth = lookup[h]; running = 0; ar = anchor_patch(u, v)
        for si in range(nsrc):
            pr = project(records[si], u, v, depth, 2080, 1560)
            if pr is None: return 65535
            rows = sampled_patch(imgs[si+1], pr[0], pr[1], 2080)
            running = (running + source_cost(rows, ar, cap, weights[si])) & 0xFFFF
        return running
    mine = [combined(ux, uy, lo + i) for i in range(hc)]
    return mine == captured, lo, hc, captured, mine

cells = sorted(glob.glob(ROOT + "/*/"))
print("%-22s %-6s %-6s %-8s %s" % ("cell", "pixel", "hyps", "BITEXACT", "curve"))
ok_all = True
for c in cells:
    name = os.path.basename(c.rstrip("/"))
    if not (os.path.exists(c + "report.json") and os.path.exists(c + "local_curve.u16le")): continue
    try:
        ok, lo, hc, cap, mine = verify(c)
    except Exception as e:
        print("%-22s ERROR %s" % (name, e)); ok_all = False; continue
    ok_all = ok_all and ok
    print("%-22s hyps%d..%d  %s  cap=%s" % (name, lo, lo+hc-1, "YES" if ok else "NO ->mine="+str(mine), cap))
print("\nALL BIT-EXACT:", ok_all)
