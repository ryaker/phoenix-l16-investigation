# Bundle Proof: `FusionCacheBayer` Flag-Origin Static Boundary

## Scope

This note statically bounds the origin and constructor use of the
`FusionCacheBayer` object byte at `+0x18`, the same byte later observed by the
visible-`src2` `0x406a10` branch proof.

This is installed-bundle static evidence only. It does not admit a four-zoom
runtime claim by itself.

## Artifacts

- Installed bundle disassembly:
  `tools/libcp_disasm_intel.txt`
- Prior visible-`src2` branch runtime proof:
  [lldb_src2_406a10_branch_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_406a10_branch_four_zoom.md)
- Prior wrapper / `PipelineCache+0x1d8` custody proof:
  [bundle_proof_src_wrappers.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src_wrappers.md)
- Runtime probe:
  [fusioncachebayer_flag_origin_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_probe.py)
- Four-zoom runtime companion proof:
  [lldb_fusioncachebayer_flag_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_fusioncachebayer_flag_origin_four_zoom.md)

Runtime custody note: a transient failed rerun occurred on 2026-05-26 while
`/Volumes/Base Photos` was unavailable. The probe has since been hardened to
refuse overwriting evidence JSON when no constructor call is captured, and the
four canonical JSON reports were regenerated after the volume returned.

## Static Chain

### `PipelineCache` constructs and stores the object

The `PipelineCache` constructor path around `0x3eab13..0x3eab5e` builds the
object that prior evidence identifies as the `PipelineCache+0x1d8`
`FusionCacheBayer` object:

- `0x3eab32`: allocates `0x138` bytes.
- `0x3eab3c`: saves the new object pointer in `r13`.
- `0x3eab3f`: loads `rsi = [r14+0x170]`.
- `0x3eab46`: sets `rdi = r13`.
- `0x3eab49`: sets `rdx = r12`.
- `0x3eab4c`: calls `0x406960`.
- `0x3eab58..0x3eab5b`: stores `r13` through the holder that prior proof
  bounds to `PipelineCache+0x1d8`.

### `0x406960` thunks into the constructor body

`0x406960` has only a tiny frame shim and then jumps into `0x4064c0`:

- `0x406960`: prologue.
- `0x406965`: `jmp 0x4064c0`.

Therefore the substantive constructor body is `0x4064c0`.

### `0x4064c0` calls the base initializer before installing the final vtable

The constructor body starts by preserving constructor arguments and calling
`0x402d20`:

- `0x4064d4`: saves the third constructor argument in `r14`.
- `0x4064d7`: saves the new object pointer in `r13`.
- `0x4064e8`: calls `0x402d20`.
- `0x4064ed`: writes vtable address point `0x6600c0` to object offset `0`.

The flag write happens inside `0x402d20`, before the final
`FusionCacheBayer` vtable is installed at `0x4064ed`.

### `0x402d20` initializes object fields and writes byte `+0x18`

The base initializer copies the incoming shared-ptr-like pair into the object
and computes the flag byte:

- `0x402d5a..0x402d65`: copies `*rsi` to object `+0x8` and `rsi+0x8` to
  object `+0x10`, retaining the second pointer when non-null.
- `0x402d73..0x402d80`: calls `0x1be960`; when that test is true, the path
  reaches `0x402d89` and zeroes `eax`.
- `0x402d90..0x402e64`: otherwise scans upstream `0x10`-byte records reached
  from the copied source object.
- `0x402dcb`: initializes `r15d = 0x10`.
- `0x402df4..0x402e05`: calls `0xf2720` and normalizes/compares its result.
- `0x402e18..0x402e25`: calls `0xf2750` and tests the returned two-int field.
- `0x402e2d..0x402e35`: on the first matching record, calls `0xf2720` again
  and stores that key into `r15d`.
- `0x402e6a..0x402e6e`: compares `r15d` with sentinel `0x10` and computes
  `al = (r15d != 0x10)`.
- `0x402e78`: writes `al` to object byte `+0x18`.
- `0x402e7c`: clears object field `+0x20` to zero immediately after the flag
  write.

Static consequence: object byte `+0x18` is not an arbitrary later mutation in
the visible `src2` path. It is initialized in the constructor's base init
routine from the upstream collection reachable through the constructor's
`rsi` shared-ptr-like argument. The public semantic name of that collection
and its records remains unknown.

### Accessor/helper facts inside the flag computation

The helper bodies used by the `0x402d20` computation are small enough to bound
statically:

- `0x1be960` returns byte field `object+0x14`.
- `0x1bea00` loads `*rdi` and tail-calls `0xe6cf0`.
- `0x1bdfa0` returns its `rdi` argument unchanged.
- `0xe78d0` returns `rdi+0x10`.
- `0xf2720` returns int32 field `object+0x60`.
- `0xf2750` returns address `object+0x58`.

Therefore, within the scanned upstream records, the flag-setting predicate is
not opaque at this level:

- record item pointer `+0x0` supplies the object inspected by `0xf2720` and
  `0xf2750`;
- record item pointer `+0x8` is retained/released around the inspection when
  non-null;
- `0xf2720(object)` supplies the candidate integer key from `object+0x60`;
- `0xf2750(object)` supplies a two-int field at `object+0x58`;
- the two-int field must have at least one negative/sign bit after OR for the
  tested predicate to continue;
- the first accepted candidate key replaces sentinel `0x10` in `r15d`;
- final byte `+0x18` is true only when `r15d != 0x10`.

This is still a structural predicate, not a public semantic label. The meaning
of fields `+0x58`, `+0x60`, and sentinel `0x10` remains unknown.

### `0x4064c0` later consumes byte `+0x18`

The same constructor later branches on the initialized byte:

- `0x4066fc`: compares object byte `+0x18` with zero.
- If the byte is zero, the constructor jumps to `0x4067a5` and does not build
  field `+0x20` on this path.
- If the byte is nonzero, `0x406707..0x40676b` allocates and initializes a
  `0x250`-byte object using helper calls `0x40b1d0`, `0x40b290`,
  `0x40b2b0`, and `0x1b17b0`.
- `0x406774`: stores the newly allocated object into `FusionCacheBayer+0x20`.

Static consequence: field `+0x20` is a constructor-created companion object
only on the nonzero-flag path. The public semantic name of that companion
object remains unknown.

## Safe Static Conclusion

The `FusionCacheBayer+0x18` byte used by visible-`src2` body `0x406a10` is
statically bounded to constructor initialization:

`PipelineCache ctor -> 0x406960 -> 0x4064c0 -> 0x402d20 -> write object+0x18`

The byte is computed from an upstream collection reachable through the
constructor's `rsi` shared-ptr-like argument. A sentinel comparison against
`0x10` determines the boolean written to `+0x18`.

The constructor later consumes the same byte at `0x4066fc`; the nonzero path
alone constructs and stores object field `+0x20`.

## Not Proven Here

- Public semantic meaning of the four-zoom runtime values proven in
  [lldb_fusioncachebayer_flag_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_fusioncachebayer_flag_origin_four_zoom.md).
- Public semantic meaning of byte `+0x18`.
- Public semantic name or LRI origin of the upstream collection scanned by
  `0x402d20`.
- Public semantic name of the optional object stored at `+0x20`.
- Merge/reducer closure, final contributor acceptance/rejection, or final
  anti-ghosting policy.

## Runtime Follow-Up

The required four-zoom runtime rerun is captured in
[lldb_fusioncachebayer_flag_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_fusioncachebayer_flag_origin_four_zoom.md).
Remaining work is semantic, not constructor-custody: identify the public
meaning and LRI origin of the upstream collection, fields `+0x58` / `+0x60`,
sentinel `0x10`, and optional object `+0x20`.
