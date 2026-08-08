#!/usr/bin/env python3
"""Two-body x four-focal master verification.

For each canonical shot compare:
  * Lumen profile-3 fmt-3 HDR master chroma
  * Phoenix master chroma (AWB-free default)
  * the counterfactual "AWB applied" chroma = phoenix chroma scaled by the
    shot's own awb_rgb = (1/r, 1/g, 1/b) ratios.

The awb gains differ per shot, so if the Lumen master tracks the AWB-free
Phoenix render (and NOT the counterfactual) across all five, the no-AWB
conclusion is proven rather than inferred.
"""
import numpy as np, sys, re, os, json, glob

OUT = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master"


def load(path):
    with open(path, "rb") as f:
        data = f.read()
    i = data.find(b"\n\n")
    if i < 0:
        raise RuntimeError("no header end")
    j = data.index(b"\n", i + 2)
    m = re.match(r"-Y (\d+) \+X (\d+)", data[i + 2:j].decode().strip())
    H, W = int(m.group(1)), int(m.group(2))
    need = W * H * 4
    if len(data) - (j + 1) < need:
        raise RuntimeError("truncated / RLE")
    px = np.frombuffer(data, dtype=np.uint8, count=need, offset=j + 1).reshape(H, W, 4)
    e = px[..., 3].astype(np.int32)
    scale = np.where(e > 0, np.ldexp(1.0, e - 136), 0.0)
    return W, H, px[..., :3].astype(np.float64) * scale[..., None]


def stats(path):
    W, H, rgb = load(path)
    m = rgb[..., 1] > 1e-6
    R, G, B = rgb[..., 0][m], rgb[..., 1][m], rgb[..., 2][m]
    med = np.median(np.stack([R, G, B]), 1)
    return dict(w=W, h=H, valid=float(m.mean()),
                mR=float(R.mean()), mG=float(G.mean()), mB=float(B.mean()),
                rg=float(R.mean() / G.mean()), bg=float(B.mean() / G.mean()),
                med_rg=float(med[0] / med[1]), med_bg=float(med[2] / med[1]),
                med_g=float(med[1]))


def awb_from_log(path):
    """Pull awb_rgb = (1/r, 1/g_r, 1/b) out of the phoenix log."""
    if not os.path.exists(path):
        return None
    txt = open(path, errors="replace").read()
    m = re.search(r"\[awb \] supplied awb_rgb ([-\d.eE]+) ([-\d.eE]+) ([-\d.eE]+)", txt)
    if m:
        try:
            return [float(m.group(i)) for i in (1, 2, 3)]
        except ValueError:
            return None
    return None


NAMES = ["u1_28", "u1_35", "u1_70", "u1_150", "u2_35"]
rows = []
for n in NAMES:
    lp, pp = f"{OUT}/{n}_lumen.hdr", f"{OUT}/{n}_phx.hdr"
    if not (os.path.exists(lp) and os.path.exists(pp)):
        print(f"[skip] {n}: missing render")
        continue
    try:
        L, P = stats(lp), stats(pp)
    except Exception as ex:
        print(f"[skip] {n}: {ex}")
        continue
    g = awb_from_log(f"{OUT}/{n}_phx.log")
    row = dict(name=n, lumen=L, phx=P, awb=g)
    if g:
        # counterfactual: what phoenix chroma would be with awb folded in
        row["cf_rg"] = P["rg"] * g[0] / g[1]
        row["cf_bg"] = P["bg"] * g[2] / g[1]
    rows.append(row)

hdr = ("shot      lumenR/G  phxR/G   err%   | lumenB/G  phxB/G   err%   | "
       "awb(r,g,b)                 | cf R/G  cf B/G  cfErr%")
print(hdr)
print("-" * len(hdr))
for r in rows:
    L, P, g = r["lumen"], r["phx"], r["awb"]
    erg = 100 * abs(P["rg"] - L["rg"]) / L["rg"]
    ebg = 100 * abs(P["bg"] - L["bg"]) / L["bg"]
    gs = ("%.5f,%.5f,%.5f" % tuple(g)) if g else "(n/a)"
    if "cf_rg" in r:
        cerg = 100 * abs(r["cf_rg"] - L["rg"]) / L["rg"]
        cebg = 100 * abs(r["cf_bg"] - L["bg"]) / L["bg"]
        cf = "%.4f  %.4f  %.1f/%.1f" % (r["cf_rg"], r["cf_bg"], cerg, cebg)
    else:
        cf = "-"
    print("%-9s %.4f    %.4f   %5.2f  | %.4f    %.4f   %5.2f  | %-25s | %s"
          % (r["name"], L["rg"], P["rg"], erg, L["bg"], P["bg"], ebg, gs, cf))

print()
print("brightness (mean G) and geometry")
for r in rows:
    L, P = r["lumen"], r["phx"]
    print("  %-9s lumen %dx%d G=%.5f   phx %dx%d G=%.5f   ratio=%.4f  medG %.5f/%.5f=%.4f"
          % (r["name"], L["w"], L["h"], L["mG"], P["w"], P["h"], P["mG"],
             P["mG"] / L["mG"], P["med_g"], L["med_g"], P["med_g"] / L["med_g"]))

json.dump(rows, open(f"{OUT}/verify.json", "w"), indent=1)
print(f"\nwrote {OUT}/verify.json")
