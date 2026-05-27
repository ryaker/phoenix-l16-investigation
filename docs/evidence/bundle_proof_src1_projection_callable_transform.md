# Bundle Proof: Visible `src1` Projection Callable Transform

## Scope

This note decodes the installed-bundle body at `libcp+0x3e42e0`, the
projection callable target proven live by
[lldb_src1_worker_projection_record_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src1_worker_projection_record_four_zoom.md).

It proves:

- the callable address point `0x65f188` has substantive slot
  `+0x30 = 0x3e42e0`
- `0x3e42e0` is a two-float coordinate-transform body
- the body uses one transform state pointer from callable field `+0x8`
- the body applies three affine rows over input `(x, y)`, divides by the third
  row, recenters, applies a radius-indexed scale table, and writes two output
  floats
- the same family has scaled variants at `0x3e44b0`, `0x3e46a0`, and
  `0x3e4890`
- the visible `src1` payload constructor installs these callables into the
  payload callable slots beginning at `payload+0x150`

It does not prove:

- the semantic name of the transform
- the LRI/public-calibration origin of every transform field
- that any projection-record index is a physical camera id
- the semantic contents of visible `src1`
- the exact upstream merge/reduction mechanism behind `src1` / `src2`
- C6 routing or final merge acceptance / rejection logic

## Bundle + Commands

Binary:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

Commands:

```bash
arch -x86_64 lldb --batch \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'memory read --format x --size 8 --count 48 0x65f180' \
  -o 'memory read --format x --size 8 --count 48 0x65f300' \
  -o 'disassemble --start-address 0x3e42e0 --end-address 0x3e4a80' \
  -o 'disassemble --start-address 0x3e27a0 --end-address 0x3e2db0'
```

Constants spot-check:

```bash
arch -x86_64 lldb --batch \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'memory read --format f --size 4 --count 32 0x5a8120' \
  -o 'memory read --format f --size 4 --count 32 0x5a8860' \
  -o 'memory read --format f --size 4 --count 32 0x5a9af0'
```

## Vtable Facts

The live runtime packet loaded callable vtable/address point `base+0x65f188`.
Static vtable bytes at that address point show:

| Address-point-relative slot | Target |
|---:|---:|
| `+0x00` | `0x3e4250` |
| `+0x08` | `0x3e4260` |
| `+0x10` | `0x3e4270` |
| `+0x18` | `0x3e42a0` |
| `+0x20` | `0x3e42c0` |
| `+0x28` | `0x3e42d0` |
| `+0x30` | `0x3e42e0` |
| `+0x38` | `0x3e43f0` |
| `+0x40` | `0x3e4410` |

Therefore the runtime-observed virtual call through slot `+0x30` reaches
`0x3e42e0`.

## Formula At `0x3e42e0`

Calling convention at the worker call site:

- `rdi`: output pointer for two `float` values
- `rsi`: callable object pointer
- `rdx`: pointer to input `x` float
- `rcx`: pointer to input `y` float

The body begins with:

- `0x3e42e4`: `state = *(uint64_t *)(callable + 0x8)`
- `0x3e42e8`: `x = *(float *)rdx`
- `0x3e42ec`: `y = *(float *)rcx`

Static instruction sequence gives this exact single-precision formula:

```text
h0 = state[0x120] * x + state[0x124] * y + state[0x128]
h1 = state[0x12c] * x + state[0x130] * y + state[0x134]
h2 = state[0x138] * x + state[0x13c] * y + state[0x140]

px = h0 / h2
py = h1 / h2

cx = state[0x118]
cy = state[0x11c]

dx = px - cx
dy = py - cy

sx = state[0x0f8]
sy = state[0x0fc]

r = trunc(sqrt((sx * dx)^2 + (sy * dy)^2))
i = min(r, 0x0fff)

k = ((float *)state[0x100])[i]

out[0] = cx + k * dx
out[1] = cy + k * dy
```

The `1.0` numerator for the reciprocal divide is loaded from static float
constant `0x5a8128`.

The table index is clamped to `0xfff`, so the visible body uses radius-table
indices `0..4095`.

This is a coordinate transform. It is not a multi-source reducer or a
cross-camera blend body.

## Transform Field Map

The visible field use inside `0x3e42e0` is:

| State field | Use |
|---:|---|
| `+0x0f8` | x scale before radius computation |
| `+0x0fc` | y scale before radius computation |
| `+0x100` | float table base for radius-indexed scale |
| `+0x118` | x center / recenter field |
| `+0x11c` | y center / recenter field |
| `+0x120` | row 0, column x |
| `+0x124` | row 0, column y |
| `+0x128` | row 0, constant |
| `+0x12c` | row 1, column x |
| `+0x130` | row 1, column y |
| `+0x134` | row 1, constant |
| `+0x138` | row 2, column x |
| `+0x13c` | row 2, column y |
| `+0x140` | row 2, constant |

The public calibration names and LRI origins of these fields are not proven by
this note.

## Scaled Variants In The Same Family

Static vtable bytes expose four neighboring address points with the same
substantive structure:

| Address point | Slot `+0x30` body | Input scale before row math | Output scale after recentering |
|---:|---:|---:|---:|
| `0x65f188` | `0x3e42e0` | `1` | `1` |
| `0x65f208` | `0x3e44b0` | `2` | `0.5` |
| `0x65f288` | `0x3e46a0` | `4` | `0.25` |
| `0x65f308` | `0x3e4890` | `8` | `0.125` |

The constants were verified at:

- `0x5a886c = 0.5`
- `0x5a8870 = 4.0`
- `0x5a8200 = 0.25`
- `0x5a9b00 = 0.125`
- `0x5a9b0c = 8.0`

The `0x3e44b0` body doubles input `x/y` with `addss` before row math and
multiplies both output floats by `0.5`.

The `0x3e46a0` body multiplies input `x/y` by `4.0` before row math and
multiplies both output floats by `0.25`.

The `0x3e4890` body multiplies input `x/y` by `8.0` before row math and
multiplies both output floats by `0.125`.

## Constructor Installation

The visible `src1` payload constructor at `0x3e27a0` installs this callable
family into the visible payload:

- `0x3e27f2`: computes `payload+0x150`
- `0x3e2800`: initializes `payload+0x170` to null
- `0x3e280b`: initializes `payload+0x1a0` to null
- `0x3e2816`: initializes `payload+0x1d0` to null
- `0x3e2821`: initializes `payload+0x200` to null
- `0x3e28db..0x3e291e`: calls `0x3f6170` and stores the returned scale tuple
  into `payload+0xf8/+0xfc`
- `0x3e2930..0x3e2990`: installs the radius table vector fields at
  `payload+0x100/+0x108/+0x110`
- `0x3e29a6..0x3e29b8`: stores the recenter tuple into
  `payload+0x118/+0x11c`
- `0x3e29bf..0x3e29e2`: stores row fields into `payload+0x120..+0x140`
- `0x3e29ee..0x3e2a0b`: builds a callable with address point `0x65f188`,
  stores the payload pointer at callable `+0x8`, and installs it at
  `payload+0x150` through `0x3e55f0`
- `0x3e2a39..0x3e2a56`: installs the `0x65f208` variant at `payload+0x180`
- `0x3e2a77..0x3e2a94`: installs the `0x65f288` variant at `payload+0x1b0`
- `0x3e2ab5..0x3e2ad2`: installs the `0x65f308` variant at `payload+0x1e0`

The four-zoom worker/projection-record runtime packets proved the first
captured projection record used low i32 index `0`, so it loaded the first
callable through the `payload+0x170` control pointer and reached
`0x65f188` / `0x3e42e0`.

This index is payload-internal. It is not proven to be a physical camera id.

## Safe Conclusions

- Proven:
  the next callable target under the first captured visible `src1` worker path
  is a coordinate-transform body.
- Proven:
  `0x3e42e0` computes a homogeneous-style three-row projection over input
  `(x, y)`, then applies a radius-indexed scale-table correction around
  `state+0x118/+0x11c`.
- Proven:
  the same callable family has scaled variants for input scales `2`, `4`, and
  `8`.
- Proven:
  the visible payload constructor installs the callable family into payload
  slots beginning at `payload+0x150`.
- Excluded:
  `0x3e42e0` is not the exact pre-fusion N-to-1 reducer, a multi-camera loop,
  or a cross-camera pixel blend.
- Still unproven:
  the public semantic names and LRI origins for the transform fields.
- Still unproven:
  the exact upstream merge/reduction mechanism behind `src1` / `src2`.

## Canonical Consequence

This evidence narrows `CLM-PREFUSION-001` and `CLM-PREFUSION-002`.

It turns the newly proven `0x3e42e0` runtime target into concrete coordinate
math that can eventually be used by a clean-room spec after its field origins
are decoded.

It does not close `CLM-PREFUSION-002`.
