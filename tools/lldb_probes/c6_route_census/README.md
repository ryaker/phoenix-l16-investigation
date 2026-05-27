# C6 Route Census Probes

This folder contains LLDB harnesses for direct `0xf2720` key-getter route
census work around tele key `15` / C6.

## Admitted evidence scope

The admitted evidence document is:

- [../../../docs/evidence/lldb_c6_focused_f2720_route_census_tele.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_c6_focused_f2720_route_census_tele.md)

That proof uses the focused scripts:

- `c6_route_census_focus_70mm.lldb`
- `c6_route_census_focus_150mm.lldb`

Those scripts cover 24 selected C6-adjacent direct `0xf2720` callsites and
completed with JSON reports under ignored `runs/c6_route_census/`.

## Non-admitted broad scripts

The broader scripts:

- `c6_route_census_70mm.lldb`
- `c6_route_census_150mm.lldb`

install all currently enumerated direct `call 0xf2720` sites from
`c6_route_census_probe.py`. They are reusable harnesses, but they are not
admitted evidence until a run completes and produces a validated JSON report.

Do not cite partial broad-run HDR output as evidence.
