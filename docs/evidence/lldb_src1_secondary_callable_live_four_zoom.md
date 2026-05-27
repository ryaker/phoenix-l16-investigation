# LLDB Evidence: Visible `src1` Secondary Callable Live Four-Zoom

## Scope

This note records live runtime packets for the visible `src1` payload's
secondary callable path on the corrected canonical four-zoom bridge HDR seed
set.

It proves only:

- the visible `src1` secondary callable body at `libcp+0x3e4a80` is reached on
  `28mm`, true `35mm`, `70mm`, and `150mm`
- the first captured `0x3e4a80` entry in each run reads the primary payload
  through `this+0x8`
- the first captured call site at `libcp+0x3e4b09` passes that same `0x490`
  payload to `libcp+0x3e2e90`
- the captured live path reaches `0x3e4a80` from the same caller stack on all
  four seeds

It does not prove:

- the semantic contents of visible `src1`
- the semantic contents of visible `src2`
- the exact upstream merge/reduction mechanism
- C6 routing
- final merge acceptance / rejection logic
- that every possible `0x3e4a80` call uses the same tile rectangle or call
  order

## Probe Method

The probe used LLDB Python against:

`/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`

Runtime environment:

- `DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`
- `DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`
- `--profile 3 --export-fmt 3`

Breakpoints:

| VA | Meaning |
|---:|---|
| `0x3e4a80` | visible `src1` secondary callable entry |
| `0x3e4b09` | immediately before the call from `0x3e4a80` into `0x3e2e90` |

Each run captured the first `0x3e4a80` entry packet and the first
`0x3e4b09` call-site packet, then intentionally killed the process. These are
not render-completion tests.

The first captured tile is scheduler-dependent under threaded render
execution. Tile rectangles below are evidence that a valid first tile packet
was captured, not a claim about global render ordering.

## Runtime Artifacts

| Zoom | Artifact |
|---|---|
| `28mm` | `/private/tmp/l16_secondary_call_probe_28mm.json` |
| `35mm` | `/private/tmp/l16_secondary_call_probe_35mm_true.json` |
| `70mm` | `/private/tmp/l16_secondary_call_probe_70mm.json` |
| `150mm` | `/private/tmp/l16_secondary_call_probe_150mm.json` |

The temporary probe script was:

`/private/tmp/l16_secondary_call_probe.py`

## Tested Files

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Capture Counts

| Zoom | `0x3e4a80` hits before kill | `0x3e4b09` captures | Finish reason |
|---|---:|---:|---|
| `28mm` | `7` | `1` | `captured_src1_secondary_entry_and_3e2e90_call` |
| `35mm` | `5` | `1` | `captured_src1_secondary_entry_and_3e2e90_call` |
| `70mm` | `7` | `1` | `captured_src1_secondary_entry_and_3e2e90_call` |
| `150mm` | `7` | `1` | `captured_src1_secondary_entry_and_3e2e90_call` |

## Live Payload Facts At `0x3e4a80`

For the first captured `0x3e4a80` entry in each run:

| Zoom | Primary payload from `this+0x8` | Payload vtable | Payload `+0x60` | Payload `+0x68` | `+0x10/+0x14` | `+0xa8/+0xac` | `byte+0xf0` | `i32+0xf4` | Request `+0x18` |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|
| `28mm` | `0x7ff64c011a00` | `base+0x65f140` | `base+0x65f388` | `0x7ff64c011a00` | `512,512` | `4160,3120` | `1` | `17` | `0` |
| `35mm` | `0x7fab59922800` | `base+0x65f140` | `base+0x65f388` | `0x7fab59922800` | `512,512` | `4160,3120` | `1` | `17` | `0` |
| `70mm` | `0x7fb644874e00` | `base+0x65f140` | `base+0x65f388` | `0x7fb644874e00` | `512,512` | `4160,3120` | `1` | `17` | `0` |
| `150mm` | `0x7f8b78e32e00` | `base+0x65f140` | `base+0x65f388` | `0x7f8b78e32e00` | `512,512` | `4160,3120` | `1` | `17` | `0` |

The vtable and secondary address-point offsets match the already documented
visible `src1` payload family:

- payload vtable address point `0x65f140`
- secondary callable address point `0x65f388`
- substantive secondary slot `0x3e4a80`

## Live Call Site Into `0x3e2e90`

For the first captured `0x3e4b09` call-site packet in each run:

| Zoom | `rdi` payload passed to `0x3e2e90` | Same as entry payload | `ecx` level | Captured tile rect from `rdx` |
|---|---:|---|---:|---|
| `28mm` | `0x7ff64c011a00` | yes | `0` | `[2048,1536,2560,2048]` |
| `35mm` | `0x7fab59922800` | yes | `0` | `[1536,1024,2048,1536]` |
| `70mm` | `0x7fb644874e00` | yes | `0` | `[2048,0,2560,512]` |
| `150mm` | `0x7f8b78e32e00` | yes | `0` | `[512,1536,1024,2048]` |

The call-site payload fields matched the entry packet fields in each run:

- vtable `base+0x65f140`
- secondary callable pointer `base+0x65f388`
- payload `+0x68` self-pointer equal to the payload address
- payload `+0x10/+0x14 = 512,512`
- payload `+0xa8/+0xac = 4160,3120`
- `byte+0xf0 = 1`
- `i32+0xf4 = 17`

## Caller Stack

All four first-entry packets shared the same first six libcp-relative frames:

| Zoom | Frames |
|---|---|
| `28mm` | `0x3e4a80 <- 0x3d4842 <- 0x5d97 <- 0x3873 <- 0x55a2 <- 0x3d03d6` |
| `35mm` | `0x3e4a80 <- 0x3d4842 <- 0x5d97 <- 0x3873 <- 0x55a2 <- 0x3d03d6` |
| `70mm` | `0x3e4a80 <- 0x3d4842 <- 0x5d97 <- 0x3873 <- 0x55a2 <- 0x3d03d6` |
| `150mm` | `0x3e4a80 <- 0x3d4842 <- 0x5d97 <- 0x3873 <- 0x55a2 <- 0x3d03d6` |

Static disassembly of the caller chain shows:

- `0x3d01b0` is the already-bounded checked level/ROI tile-read body.
- At `0x3d0374..0x3d03d1`, it builds a `0x30`-byte callback object and
  dispatches it through generic executor `0x5440`.
- `0x3d47d0` is the callback worker reached by that executor path.
- At `0x3d4828..0x3d4840`, `0x3d47d0` reads an active callable at
  `0x70(%rbx)`, loads virtual slot `+0x30`, and calls it.
- The return address after that virtual call is `0x3d4842`, matching the live
  packets.

## Safe Conclusions

- Proven:
  the visible `src1` secondary callable body at `0x3e4a80` is live on the
  corrected canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR seeds.
- Proven:
  the first captured `0x3e4a80` entry in each run reads the same `0x490`
  visible `src1` payload family through `this+0x8`.
- Proven:
  the first captured `0x3e4b09` packet in each run passes that same payload to
  `0x3e2e90`.
- Proven:
  the live caller stack is the same across the four seeds and reaches
  `0x3e4a80` from the already-bounded `0x3d01b0` tile-read / `0x5440`
  executor path through callback worker `0x3d47d0`.
- Still unproven:
  the semantic contents or upstream producer math for visible `src1`.
- Still unproven:
  the exact upstream merge/reduction mechanism behind `src1` / `src2`.
- Still unproven:
  C6 routing and final merge acceptance / rejection logic.

## Canonical Consequence

This evidence narrows `CLM-PREFUSION-001` and `CLM-PREFUSION-002`.

It confirms the visible `src1` secondary callable is not just a static vtable
surface: it is live across the four canonical focal seeds and routes into the
already-bounded `0x3e2e90` single-payload ROI/process path.

It does not close `CLM-PREFUSION-002`.
