#!/usr/bin/env python3
"""Extend the admitted post-terminal finalizer verifier to four focal tiers."""

from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "verify_postterminal.py"
CASES = ("unit1_28mm", "unit1_35mm", "unit1_70mm", "unit1_150mm")


def load_base():
    spec = importlib.util.spec_from_file_location("postterminal_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    base = load_base()
    digest = base.verify_static()
    print(f"static_postterminal_four_zoom={digest}")
    for case in CASES:
        summary = base.verify_case(case)
        print(
            f"{case}=OK state=0x{summary['state_root']:x} owner=0x{summary['owner']:x} "
            f"sibling=0x{summary['sibling_before']:x}->0x{summary['sibling_after']:x} "
            f"first_touch=0x{summary['first_touch']:x} "
            f"initresamp_joins={summary['initresamp_join_count']}"
        )
    print("postterminal_four_zoom=OK")


if __name__ == "__main__":
    main()
