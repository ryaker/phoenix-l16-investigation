"""Validate the decoded 0x18e940 patch-noise formula against Lumen's own
captured arguments and return values."""
import json

P = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/prefusion_monofusion_mode0_tile/unit1_35mm/noise_helper.json"
hits = json.load(open(P))["hits"]
print("hits:", len(hits))
print("%3s %10s %10s %10s %10s %12s %12s %8s" %
      ("i", "mu", "muview", "patchmean", "H", "V_pred", "V_ret", "ratio"))
bad = 0
for i, h in enumerate(hits):
    if "V_returned" not in h or "H" not in h:
        continue
    mu, a, b, B, W = h["mu"], h["a"], h["b"], h["black"], h["white"]
    H = h["H"]
    z = max(B / W, (B + (H - B) / mu) / W)
    model = max(1e-5, a * z + b)
    V = (W * mu) ** 2 * model
    r = V / h["V_returned"] if h["V_returned"] else float("nan")
    if abs(r - 1.0) > 2e-3:
        bad += 1
    print("%3d %10.6f %10.6f %10.3f %10.3f %12.5f %12.5f %8.5f  %s" %
          (i, mu, h.get("muview_mean", float("nan")), h["patch_mean"], H, V,
           h["V_returned"], r, "clamp" if a * z + b < 1e-5 else ""))
print("mismatches (>0.2%%):", bad)
mv = [h for h in hits if "muview_mean" in h]
if mv:
    d = max(abs(h["muview_mean"] - h["mu"]) for h in mv)
    print("max |muview_mean - mu| over %d hits = %.6g" % (len(mv), d))
    h = mv[0]
    print("muview ints:", h["muview_ints"], "range",
          h.get("muview_min"), h.get("muview_max"))
