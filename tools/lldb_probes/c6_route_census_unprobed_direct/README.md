# C6 Unprobed Direct `0xf2720` Route Census

This folder contains chunked LLDB harnesses for the 34 direct `call 0xf2720`
sites that were not covered by the admitted focused C6 route census.

The scripts reuse `../c6_route_census/c6_route_census_probe.py` and only change
the selected callsite list. They are intentionally sequential and chunked to
avoid the old broad all-58 breakpoint pressure.

## Scope

- Canonical tele bridge HDR seeds only:
  - `70mm`: `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri`
  - `150mm`: `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri`
- Same-name `.lris` auto-loading disabled.
- Direct `0xf2720` callsites only.

## Admitted Evidence

The admitted evidence document is:

- [../../../docs/evidence/lldb_c6_unprobed_direct_f2720_route_census_tele.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_c6_unprobed_direct_f2720_route_census_tele.md)

Admitted runs completed for all four scripts with exit status `0`, all
requested breakpoints installed, no JSON errors, and no cap-disabled sites.
LLDB/debugserver had to run outside the sandbox; sandboxed failed attempts are
not evidence.

## Chunks

Chunk A:

`0xdf8f3`, `0xe3273`, `0xe327e`, `0xe32f3`, `0xe4063`, `0xe5fd9`,
`0xe6020`, `0xe609a`, `0xe680f`, `0xe688f`, `0xe69df`, `0xe6be0`,
`0xe745f`, `0xe75f3`, `0xe7763`, `0xfb329`, `0xfb95f`

Chunk B:

`0xfe5fc`, `0x144c80`, `0x145703`, `0x1459d9`, `0x1b7e82`,
`0x1b7e8d`, `0x20b044`, `0x20b17d`, `0x227d5e`, `0x227d77`,
`0x227e30`, `0x2280de`, `0x22819c`, `0x27d7ce`, `0x27db11`,
`0x31bce0`, `0x31bd00`

## Admission Rules

Only cite a run as evidence if:

- the process exits cleanly,
- JSON exists under `runs/c6_route_census_unprobed_direct/`,
- all requested breakpoints install,
- the JSON has no `errors`,
- no selected site is disabled at the hit cap unless the claim is explicitly
  scoped to "before cap disablement".
