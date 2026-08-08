#!/usr/bin/env python3
"""G-42 operand-pairing and byte-metric verifier.

Reproduces the per-source integer cost (cost_esi) captured inside 0x2732f0 by
emulating, bit-exactly, the SSE instruction sequence 0x2735bf..0x27369e:

  for (patch, ref) in [(xmm3,+0x50),(xmm1,+0x60),(xmm2,+0x70)]:
      d   = |patch - ref|          (per uint8 byte;  pmaxub/pminub/psubb)
      d   = min(d, cap[+0x40])      (pminub)
      acc = paddusw-accumulate d    (widen lo via pmovzxbw, hi via punpckhbw)
  fold acc -> 4 channel sums c[0..3]      (movq/paddusw/pshufd/paddusw)
  prod = weight[+0x80+8k] * c            (pmullw low16 | pmulhuw high16 -> 32b)
  prod = (prod + round_const) >> 5        (paddd xmm8 ; psrld 5)
  total = horizontal_sum(prod)            (pshufd/paddd folds)
  esi   = int(min(float(total), maxcap))  (cvtsi2ss ; minss xmm9 ; cvttss2si)

Installed-code guards also prove that the fixed reference triplet comes from
the first StereoLayer Images item. If predicted == cost_esi for every captured
pair, G-42 is closed as source-k versus tier-anchor/Guidance, using clamped,
per-channel-weighted, scaled SAD. Pure/unclamped SAD and all-pairs/running-mean
pairing are refuted.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
REPORTS = {
    "28mm": ROOT / "runs/g42_cost_operand_pairing/g42_cost_28mm_index5_v3.json",
    "35mm": ROOT / "runs/g42_cost_operand_pairing/g42_cost_35mm_index5_v2.json",
    "70mm": ROOT / "runs/g42_cost_operand_pairing/g42_cost_70mm_index5_v2.json",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("g42_static_helpers", STATIC_PATH)


def verify_static():
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    windows = {
        (0x2732F0, 0x2736AC): "61d3f4ffa9d73bbe4f48122167433a166550db8447832afe446881a38344e5de",
        (0x275630, 0x275827): "27f7203e85d8993bef8433b95e5e29f33ae810e4247d4a025eb6048d0656482c",
        (0x276B98, 0x2770E3): "4c5ac926709a4e82b876e020cbbbabfc4f91808047286020f5a9b817f13c14e4",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed: {actual}")

    byte_guards = {
        0x276B98: "488b8340020000",    # first StereoLayer Images shared-ptr item
        0x276B9F: "488b30",            # raw first-image descriptor pointer
        0x27564C: "49897500",          # context+0 = that first image
        0x2770C5: "44894d80",          # anchor patch row 0 -> context+0x50
        0x2770D1: "897d90",            # anchor patch row 1 -> context+0x60
        0x2770DA: "894da0",            # anchor patch row 2 -> context+0x70
        0x2773BD: "488dbd30ffffff",    # rdi = rbp-0xd0 context
        0x2735BF: "66440f6f6f40",      # byte-difference cap at context+0x40
        0x2735C5: "660f6f4750",        # fixed anchor row 0
        0x2735F3: "660f6f5f60",        # fixed anchor row 1
        0x27361F: "660f6f4770",        # fixed anchor row 2
        0x27365C: "f3420f7e0cd1",      # per-source weight[8*k]
        0x2736A9: "660131",            # saturating-stage result added to output u16
    }
    for va, expected_hex in byte_guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")

    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0x276BD4)) == 0x275630,
        "runPass context-builder target changed",
    )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0x2773DC)) == 0x2732F0,
        "runPass general-cost target changed",
    )
    return digest


def h2b(hx):
    return list(bytes.fromhex(hx)) if hx else None


def sat_u16(x):
    return 0 if x < 0 else (0xFFFF if x > 0xFFFF else x)


def clamp_u16_add(a, b):  # paddusw lane
    return sat_u16(a + b)


def emulate(pair):
    cap = h2b(pair["cap_0x40"])
    patches = [h2b(pair["src_patch0_xmm3"]), h2b(pair["src_patch1_xmm1"]),
               h2b(pair["src_patch2_xmm2"])]
    refs = [h2b(pair["ref_patch0_0x50"]), h2b(pair["ref_patch1_0x60"]),
            h2b(pair["ref_patch2_0x70"])]
    # widened saturating accumulators, 8 low lanes + 8 high lanes
    lo = [0] * 8
    hi = [0] * 8
    for patch, ref in zip(patches, refs):
        d = []
        for i in range(16):
            diff = abs(patch[i] - ref[i])          # pmaxub/pminub/psubb (u8)
            diff = min(diff, cap[i])               # pminub with cap
            d.append(diff)
        for j in range(8):                         # pmovzxbw low 8 bytes
            lo[j] = clamp_u16_add(lo[j], d[j])
        for j in range(8):                         # punpckhbw high 8 bytes
            hi[j] = clamp_u16_add(hi[j], d[8 + j])
    # 0x27364b movq xmm3(hi)->xmm1 (low 64 = hi[0..3], upper zero);
    # 0x27364f paddusw xmm0(lo) -> s
    s = [0] * 8
    for j in range(4):
        s[j] = clamp_u16_add(lo[j], hi[j])
    for j in range(4, 8):
        s[j] = lo[j]
    # 0x273653 pshufd 0x4e (swap 64-bit halves) ; 0x273658 paddusw
    swapped = s[4:8] + s[0:4]
    folded = [clamp_u16_add(s[j], swapped[j]) for j in range(8)]
    c = folded[0:4]                                # 4 channel sums (low lanes)
    # weight (4x u16) at +0x80 + 8k
    w = list(struct.unpack("<4H", bytes.fromhex(pair["weight8_hex"])))
    round_const = struct.unpack("<4I", bytes.fromhex(pair["round_const_xmm8"]))
    prod = []
    for j in range(4):
        p = (w[j] * c[j]) & 0xFFFFFFFF             # pmullw|pmulhuw -> 32-bit
        p = (p + round_const[j]) & 0xFFFFFFFF      # paddd xmm8
        p = p >> 5                                 # psrld 5
        prod.append(p)
    total = sum(prod) & 0xFFFFFFFF
    maxcap = struct.unpack("<f", bytes.fromhex(pair["maxcap_xmm9"])[0:4])[0]
    val = float(total)
    if val > maxcap:
        val = maxcap
    esi = int(val)                                 # cvttss2si (truncation)
    return esi, c, w


def verify_report(path, tier=None, verbose=True):
    d = json.loads(Path(path).read_text())
    require(d.get("libcp_sha256") == STATIC.LIBCP_SHA256, f"{path}: libcp digest")
    require(d.get("anchor_level") == "index5_2080x1560", f"{path}: index-5 anchor")
    require(d.get("anchor_trip_dims") == {"w": 2080, "h": 1560}, f"{path}: dimensions")
    require(d.get("capture_complete"), f"{path}: incomplete capture")
    require(not d.get("errors"), f"{path}: errors {d.get('errors')}")
    require(d.get("process", {}).get("state") == "exited", f"{path}: process state")
    pairs = d["pairs"]
    require(len(pairs) == 12, f"{path}: expected 12 pairs")
    require(sorted({p["source_index_k"] for p in pairs}) == [0, 1, 2, 3], f"{path}: source indices")
    ok = 0
    if verbose:
        print(f"libcp_sha256={d.get('libcp_sha256')}")
        print(f"anchor_level={d.get('anchor_level')} anchor_trip_dims={d.get('anchor_trip_dims')}")
        print(f"pairs={len(pairs)}")
        print("idx k  csum[0..3]                 weights                 predicted  captured  match")
    for i, p in enumerate(pairs):
        require(p["accum_ptr_matches"], f"{path}: pair {i} accumulator pointer")
        require(p["guidance_dims_at_capture"] == {"w": 2080, "h": 1560}, f"{path}: pair {i} dims")
        require(p["source_bound_x0"] == 0 and p["source_bound_y0"] == 0, f"{path}: pair {i} source origin")
        require(p["source_bound_x1"] == 2080 and p["source_bound_y1"] == 1560, f"{path}: pair {i} source bounds")
        require(p["source_stride_0x18"] == 2080, f"{path}: pair {i} source stride")
        pred, c, w = emulate(p)
        cap = p["cost_esi"]
        match = (pred == cap)
        ok += 1 if match else 0
        if verbose:
            print(f"{i:>3} {p['source_index_k']}  {str(c):<26} {str(w):<22} "
                  f"{pred:>9}  {cap:>8}  {'OK' if match else 'MISMATCH'}")
    require(ok == len(pairs), f"{path}: only {ok}/{len(pairs)} costs replay")
    if verbose:
        print(f"\nRESULT: {ok}/{len(pairs)} bit-exact")
    # accumulation cross-check: per pixel, sum of per-source esi == running accum
    if verbose:
        print("\nAccumulation cross-check (accum_before + esi == next accum_before):")
    by_pixel = {}
    for p in pairs:
        by_pixel.setdefault(p["accum_ptr"], []).append(p)
    acc_ok = True
    for ptr, ps in by_pixel.items():
        run = None  # None => start of a new accumulation segment
        seg_ok = True
        for p in ps:
            before = p["accum_u16_before"]
            if before == 0:          # buffer (re)initialised -> new segment
                run = 0
            if run is None:
                run = before
            if before != run:
                seg_ok = False
            run = (run + p["cost_esi"]) & 0xFFFF
        acc_ok = acc_ok and seg_ok
        if verbose:
            print(f"  pixel@{ptr}: sources={[q['source_index_k'] for q in ps]} "
                  f"segment_consistent={seg_ok}")
    require(acc_ok, f"{path}: accumulation sequence")
    if verbose:
        print(f"accumulation_consistent={acc_ok}")
    return f"{tier or Path(path).stem}: OK pairs={len(pairs)} sources=0,1,2,3 bit_exact={ok}"


def main():
    digest = verify_static()
    print(
        "g42_static=OK "
        f"libcp={digest} pairing=source_k_vs_Images0_Guidance "
        "metric=clamped_weighted_scaled_SAD"
    )
    if len(sys.argv) > 1:
        print(verify_report(sys.argv[1], verbose=True))
    else:
        for tier, path in REPORTS.items():
            print(verify_report(path, tier=tier, verbose=False))
        print("g42_operand_pairing_metric=OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
