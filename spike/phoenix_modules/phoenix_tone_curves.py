"""
phoenix_tone_curves.py — Phoenix clean-room tone-curve module
=============================================================

Clean-room reimplementation of Lumen L16's four tone curves:
  - acr            (ACR-style baseline)
  - light_v1       (Phoenix bridge default, MOST IMPORTANT)
  - light_v1_low   (Light v1 lowlight variant)
  - light_v2       (Light v2)

This module contains NO bytes from Lumen's libcp.dylib LUTs. Instead, it
fits each 1024-entry float32 reference LUT (extracted via separate static
analysis, NOT shipped here) to a small parametric tone-mapping operator
and stores only the fitted parameter constants.

Each function takes scene-linear input x ∈ [0, ~1] and returns the
tone-mapped output y ∈ [0, ~1]. NO pre-shaper is required: every selected
fit operates directly in the linear scene-radiance domain (Space B per
the session-6 fit report). Phoenix's full tone-mapping pipeline remains:

    output = exp2f(EV) * tone_curve(input)

Per-curve fit metadata
----------------------
                      formula           RMS         max-dev    imax
    acr               naka-rushton (S)  0.002840    0.005837    71
    light_v1          hable normalized  0.002047    0.004392   460
    light_v1_low      hable normalized  0.000493    0.003888     0
    light_v2          hable normalized  0.001012    0.002466  1023

(RMS and max are absolute deviation from the 1024-entry reference LUT
sampled in linear scene-radiance space x ∈ [0.0025, 0.999].)

Fit pedigree
------------
Reference LUT data was independently extracted from Lumen's libcp.dylib
during reverse-engineering and characterized in
  /Volumes/Dev/lumen-phoenix-scratch/session6_tone_curve_fit.md
This module embeds only the fitted parameter constants, not LUT bytes.

License: Phoenix project — clean-room reimplementation.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "acr",
    "light_v1",
    "light_v1_low",
    "light_v2",
    "FIT_METADATA",
]

# ---------------------------------------------------------------------------
# Generic tone-mapping operators
# ---------------------------------------------------------------------------


def _naka_rushton_scaled(
    x: np.ndarray, n: float, k: float, S: float
) -> np.ndarray:
    """Scaled Naka-Rushton / Michaelis-Menten saturation.

    f(x) = S * x^n / (x^n + k^n)
    """
    x = np.asarray(x, dtype=np.float64)
    xn = np.power(np.clip(x, 0.0, None), n)
    return S * xn / (xn + k**n)


def _hable_normalized(
    x: np.ndarray,
    A: float,
    B: float,
    C: float,
    D: float,
    E: float,
    F: float,
    W: float,
) -> np.ndarray:
    """Hable / Uncharted-2 filmic operator, normalized so f(W)=1.

    h(v) = ((v*(A*v+C*B) + D*E) / (v*(A*v+B) + D*F)) - E/F
    f(x) = h(x) / h(W)
    """
    x = np.asarray(x, dtype=np.float64)

    def h(v):
        return ((v * (A * v + C * B) + D * E) / (v * (A * v + B) + D * F)) - E / F

    return h(x) / h(W)


# ---------------------------------------------------------------------------
# Per-curve fitted parameters (clean-room, NOT LUT bytes)
# ---------------------------------------------------------------------------

# acr — scaled Naka-Rushton fit in linear scene-radiance space
_ACR_PARAMS = dict(
    n=1.5380996876,
    k=0.2901225049,
    S=1.1542944504,
)

# light_v1 — Hable normalized in linear space
_LIGHT_V1_PARAMS = dict(
    A=1.9029749895,
    B=0.8618452784,
    C=0.4464326714,
    D=0.5932445037,
    E=0.2288710010,
    F=0.9887411740,
    W=0.9982246225,
)

# light_v1_low — Hable normalized in linear space
_LIGHT_V1_LOW_PARAMS = dict(
    A=0.9491188144,
    B=0.5093368232,
    C=0.2648064523,
    D=0.0021224365,
    E=0.0493645566,
    F=0.1824188575,
    W=1.0025391771,
)

# light_v2 — Hable normalized in linear space
_LIGHT_V2_PARAMS = dict(
    A=3.1459375703,
    B=1.7440807349,
    C=0.2757465192,
    D=0.6741084709,
    E=0.1908854987,
    F=1.1575390660,
    W=0.9951600147,
)


# ---------------------------------------------------------------------------
# Public per-curve functions
# ---------------------------------------------------------------------------


def acr(x):
    """ACR-style baseline tone curve. Input: scene-linear x in [0, ~1]."""
    return _naka_rushton_scaled(x, **_ACR_PARAMS)


def light_v1(x):
    """Phoenix bridge default Light v1 tone curve. Input: scene-linear x."""
    return _hable_normalized(x, **_LIGHT_V1_PARAMS)


def light_v1_low(x):
    """Light v1 lowlight variant. Input: scene-linear x."""
    return _hable_normalized(x, **_LIGHT_V1_LOW_PARAMS)


def light_v2(x):
    """Light v2 tone curve. Input: scene-linear x."""
    return _hable_normalized(x, **_LIGHT_V2_PARAMS)


# ---------------------------------------------------------------------------
# Fit metadata for downstream verification
# ---------------------------------------------------------------------------

FIT_METADATA = {
    "acr": {
        "formula": "naka_rushton_scaled",
        "space": "linear_scene_radiance",
        "rms": 0.002840,
        "max_abs": 0.005837,
        "imax": 71,
        "mid_rms_100_900": 0.002251,
        "params": _ACR_PARAMS,
    },
    "light_v1": {
        "formula": "hable_normalized",
        "space": "linear_scene_radiance",
        "rms": 0.002047,
        "max_abs": 0.004392,
        "imax": 460,
        "mid_rms_100_900": 0.001854,
        "params": _LIGHT_V1_PARAMS,
    },
    "light_v1_low": {
        "formula": "hable_normalized",
        "space": "linear_scene_radiance",
        "rms": 0.000493,
        "max_abs": 0.003888,
        "imax": 0,
        "mid_rms_100_900": 0.000370,
        "params": _LIGHT_V1_LOW_PARAMS,
    },
    "light_v2": {
        "formula": "hable_normalized",
        "space": "linear_scene_radiance",
        "rms": 0.001012,
        "max_abs": 0.002466,
        "imax": 1023,
        "mid_rms_100_900": 0.000874,
        "params": _LIGHT_V2_PARAMS,
    },
}


# ---------------------------------------------------------------------------
# Self-check
# ---------------------------------------------------------------------------


def _self_check():
    """Print fit summary and a few sample evaluations."""
    print("Phoenix tone curves — clean-room module")
    print("=" * 60)
    for name, meta in FIT_METADATA.items():
        print(
            f"  {name:14s}  {meta['formula']:20s}  "
            f"RMS={meta['rms']:.6f}  max={meta['max_abs']:.6f}"
        )
    print()
    print("Sample evaluations (x in linear scene-radiance):")
    xs = np.array([0.0, 0.005, 0.05, 0.18, 0.5, 1.0])
    print(f"  {'x':>7s}  " + "  ".join(f"{n:>14s}" for n in FIT_METADATA))
    for x in xs:
        row = [
            f"{float(acr(x)):14.6f}",
            f"{float(light_v1(x)):14.6f}",
            f"{float(light_v1_low(x)):14.6f}",
            f"{float(light_v2(x)):14.6f}",
        ]
        print(f"  {x:7.4f}  " + "  ".join(row))


if __name__ == "__main__":
    _self_check()
