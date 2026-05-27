# LLDB Evidence: Visible `src1` Payload Constructor Live Four-Zoom

## Scope

This note records live runtime packets for the constructor path that creates
the `0x490`-byte visible `src1` payload returned by the `0x3e0af0` map/tree
lookup.

It proves only:

- `libcp+0x3dfcc0` reaches its payload-constructor call site at
  `libcp+0x3e005d` on `28mm`, true `35mm`, `70mm`, and `150mm`
- the call target is the `0x3e2db0 -> 0x3e27a0` constructor path already
  identified by installed-bundle proof
- the runtime key passed into the constructor is `0` at `28mm` / `35mm` and
  `8` at `70mm` / `150mm`
- the constructor receives a four-entry level vector with pairs
  `4160x3120`, `2080x1560`, `1040x780`, and `520x390` on all four tested
  focal seeds
- the first successful constructor packet in each run produces the same
  visible `src1` payload family shape: vtable address point `base+0x65f140`,
  secondary callable address point `base+0x65f388`, payload `+0x68`
  self-pointer, `+0x10/+0x14 = 512,512`, `+0xa8/+0xac = 4160,3120`, and
  `byte+0xf0 = 1`

It does not prove:

- the semantic contents of visible `src1`
- the semantic contents of visible `src2`
- the exact upstream merge/reduction mechanism
- C6 routing
- final merge acceptance / rejection logic
- that constructor argument vectors alone describe the full payload behavior
- that `i32+0xf4 = 0` remains true after later setup calls; later live
  secondary-callable evidence observes `i32+0xf4 = 17`

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
| `0x3e005d` | immediately before `0x3dfcc0` calls `0x3e2db0` |
| `0x3e27a0` | payload constructor entry |
| `0x3e2b6a` | constructor success path immediately before epilogue |

Each run captured the first pre-call packet, first constructor-entry packet,
and first constructor-success packet, then intentionally killed the process.
These are constructor-path captures, not render-completion tests.

The probe initially captured the `rsi` argument as raw memory. Static
instruction context showed that `rsi` points to a vector control block, so the
probe was corrected to capture both the raw control words and the dereferenced
vector begin/end/capacity contents. Only the dereferenced vector contents are
used as dimension-pair evidence below.

## Runtime Artifacts

| Zoom | Artifact |
|---|---|
| `28mm` | `/private/tmp/l16_src1_constructor_probe_28mm.json` |
| `35mm` | `/private/tmp/l16_src1_constructor_probe_35mm_true.json` |
| `70mm` | `/private/tmp/l16_src1_constructor_probe_70mm.json` |
| `150mm` | `/private/tmp/l16_src1_constructor_probe_150mm.json` |

The temporary probe script was:

`/private/tmp/l16_src1_constructor_probe.py`

## Tested Files

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Capture Counts

| Zoom | `0x3e005d` | `0x3e27a0` | `0x3e2b6a` | Finish reason |
|---|---:|---:|---:|---|
| `28mm` | `1` | `1` | `1` | `captured_constructor_call_entry_and_success` |
| `35mm` | `1` | `1` | `1` | `captured_constructor_call_entry_and_success` |
| `70mm` | `1` | `1` | `1` | `captured_constructor_call_entry_and_success` |
| `150mm` | `1` | `1` | `1` | `captured_constructor_call_entry_and_success` |

## Live Constructor Arguments

For the first captured constructor-entry packet in each run:

| Zoom | Constructor key | Payload `rdi` | Level vector count | Level vector pairs |
|---|---:|---:|---:|---|
| `28mm` | `0` | `0x7fe68984cc00` | `4` | `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |
| `35mm` | `0` | `0x7f8d3f873c00` | `4` | `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |
| `70mm` | `8` | `0x7fc98907b000` | `4` | `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |
| `150mm` | `8` | `0x7fa5d801e400` | `4` | `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |

The same key and payload pointer were observed at the pre-call site
`0x3e005d` and at constructor entry `0x3e27a0` in each run.

## Constructor Success Payload Facts

For the first captured constructor-success packet in each run:

| Zoom | Payload | Payload vtable | Payload `+0x60` | Payload `+0x68` | `+0x10/+0x14` | `+0xa8/+0xac` | `byte+0xf0` | `i32+0xf4` |
|---|---:|---:|---:|---:|---|---|---:|---:|
| `28mm` | `0x7fe68984cc00` | `base+0x65f140` | `base+0x65f388` | `0x7fe68984cc00` | `512,512` | `4160,3120` | `1` | `0` |
| `35mm` | `0x7f8d3f873c00` | `base+0x65f140` | `base+0x65f388` | `0x7f8d3f873c00` | `512,512` | `4160,3120` | `1` | `0` |
| `70mm` | `0x7fc98907b000` | `base+0x65f140` | `base+0x65f388` | `0x7fc98907b000` | `512,512` | `4160,3120` | `1` | `0` |
| `150mm` | `0x7fa5d801e400` | `base+0x65f140` | `base+0x65f388` | `0x7fa5d801e400` | `512,512` | `4160,3120` | `1` | `0` |

The vtable and secondary address-point offsets match the already documented
visible `src1` payload family:

- payload vtable address point `0x65f140`
- secondary callable address point `0x65f388`
- substantive secondary slot `0x3e4a80`

## Caller Stack

All four constructor-entry packets shared this first libcp-relative caller
sequence:

| Zoom | Frames |
|---|---|
| `28mm` | `0x3e27a0 <- 0x3e0062 <- 0x3b30c8 <- 0x3b1c65` |
| `35mm` | `0x3e27a0 <- 0x3e0062 <- 0x3b30c8 <- 0x3b1c65` |
| `70mm` | `0x3e27a0 <- 0x3e0062 <- 0x3b30c8 <- 0x3b1c65` |
| `150mm` | `0x3e27a0 <- 0x3e0062 <- 0x3b30c8 <- 0x3b1c65` |

All four constructor-success packets shared this first libcp-relative caller
sequence:

| Zoom | Frames |
|---|---|
| `28mm` | `0x3e2b6a <- 0x3e0062 <- 0x3b30c8 <- 0x3b1c65` |
| `35mm` | `0x3e2b6a <- 0x3e0062 <- 0x3b30c8 <- 0x3b1c65` |
| `70mm` | `0x3e2b6a <- 0x3e0062 <- 0x3b30c8 <- 0x3b1c65` |
| `150mm` | `0x3e2b6a <- 0x3e0062 <- 0x3b30c8 <- 0x3b1c65` |

Static disassembly of the same chain shows:

- `0x3dfcc0` builds the vector from the first image dimensions and three
  rounded halvings.
- `0x3e0026` allocates `0x490` bytes for the payload.
- `0x3e003e..0x3e005a` places the payload pointer, vector address, supporting
  object pointers, and key into the constructor-call ABI.
- `0x3e005d` calls `0x3e2db0`.
- `0x3e2db0` jumps to `0x3e27a0`.
- `0x3e27a0` writes the visible payload address point, initializes payload
  state, validates the reference image cache for the key, installs callable
  slots, and reaches the success path at `0x3e2b6a`.

## Safe Conclusions

- Proven:
  the visible `src1` payload constructor path `0x3dfcc0 -> 0x3e2db0 ->
  0x3e27a0` is live on the corrected canonical `28mm`, `35mm`, `70mm`, and
  `150mm` bridge HDR seeds.
- Proven:
  the constructor key split is `0` for wide-tier seeds (`28mm`, `35mm`) and
  `8` for tele-tier seeds (`70mm`, `150mm`) under these tested bridge HDR
  runs.
- Proven:
  the constructor receives the same four-entry level vector on all four seeds:
  `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)`.
- Proven:
  the successful constructor packet produces the same `0x490` visible `src1`
  payload family already observed later at runtime: vtable `base+0x65f140`,
  secondary address point `base+0x65f388`, and self-pointer at payload `+0x68`.
- Still unproven:
  the semantic contents or upstream producer math for visible `src1`.
- Still unproven:
  the exact upstream merge/reduction mechanism behind `src1` / `src2`.
- Still unproven:
  C6 routing and final merge acceptance / rejection logic.

## Canonical Consequence

This evidence narrows `CLM-PREFUSION-001` and `CLM-PREFUSION-002`.

It converts the previously static visible-`src1` payload-constructor
provenance into four-zoom runtime evidence and ties it to the already observed
visible `src1` payload family.

It does not close `CLM-PREFUSION-002`.
