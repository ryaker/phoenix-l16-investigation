# C6 Mutation Identity Probe

Purpose: prove the object-identity path for tele C6 (`key_item_0x60 == 15`) across the constructor path, the `0x3c90a5` active-byte mutation store, the immediate after-store checkpoint, and the later `0x3b2143` context walk.

This is a reusable LLDB evidence harness, not replacement Lumen code. Raw run outputs belong under ignored `runs/c6_mutation_identity/`.

Verified scope when run:
- 70mm bridge HDR: `L16_03434` (`/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri`)
- 150mm bridge HDR: `L16_02285` (`/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri`)

Key breakpoints:
- `0x3b20cd`: call into the `0x3c9370` constructor path.
- `0x3c9401`: after `0x3c9370` stores the constructed object at context `+0xa0`.
- `0x3c8f90`: start of the downstream mutation routine reading context `+0xa0`.
- `0x1bdbab` / `0x1bdbdd`: key-list helper getter sites.
- `0x3c9043` / `0x3c9098`: mutation routine key getter sites.
- `0x3c90a5`: C6 active-byte store site, before execution.
- `0x3c90a9`: immediate post-store site.
- `0x3b2143`: later context walk getter site.

Run from repo root with `arch -x86_64 lldb -b -s ...`.
