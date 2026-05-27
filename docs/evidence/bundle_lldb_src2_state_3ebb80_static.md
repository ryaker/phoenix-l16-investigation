# Bundle LLDB Evidence: Visible `src2` `0x3ebb80` Static Boundary

## Scope

This proof replaces the scratch-era citation for the visible `src2` body with
repo-local LLDB evidence from the installed `libcp.dylib`.

Follow-up runtime/static proof now binds the first accepted `28mm` executor
target behind this generic dispatch; see
[lldb_src2_executor_target_28mm.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_executor_target_28mm.md).

It proves only the static boundary of the visible `src2` wrapper path:

- `0x3ecd80` calls `0x3ebb80`, then `0x3edb80`.
- `0x3ebb80` is a `PipelineCache+0x1e0` state-driven descriptor / table /
  executor orchestration body with a `PipelineCache+0x1d8` fallback.
- `0x3edb80` is the already-bounded one-image `sqrt(max())` normalization body.

It does not identify semantic `src2` contents, the exact upstream
`src1` / `src2` merge/reduction mechanism, or the final contributor
acceptance/rejection policy.

## Artifacts

- Probe script:
  [static_src2_state_3ebb80.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_state_3ebb80/static_src2_state_3ebb80.lldb)
- Raw rerunnable output:
  `runs/src2_state_3ebb80/static_src2_state_3ebb80.log`
- Command:
  `arch -x86_64 lldb -b -s tools/lldb_probes/src2_state_3ebb80/static_src2_state_3ebb80.lldb > runs/src2_state_3ebb80/static_src2_state_3ebb80.log`
- Verification:
  the final log has `1925` lines and `rg "error:|warning:|Traceback|EXC|SIGABRT|lost connection" runs/src2_state_3ebb80/static_src2_state_3ebb80.log` returned no matches.

## Proven Facts

### 1. The visible `src2` wrapper body is narrow

`0x3ecd80` calls `0x3ebb80` at `0x3ecda8`, then calls `0x3edb80` at
`0x3ecdc7` (`static_src2_state_3ebb80.log:58`, `:66`).

This means the visible wrapper itself is not an exposed IRAMP-like multi-source
argument body.

### 2. `0x3ebb80` is gated by `PipelineCache+0x1e0`

`0x3ebb80` loads `PipelineCache+0x1e0` at `0x3ebbab` and branches to the
fallback at `0x3ebd8a` if that pointer is null (`:101`, `:103`, `:199`).

The fallback validates through the `PipelineCache+0x170` path and calls a
virtual method from the `PipelineCache+0x1d8` object at `0x3ebdd3`
(`:199`, `:213`). The hot path later also calls the `+0x1d8` object while
building its source descriptor (`0x3ebf3d`, `0x3ebf5d`; `:308`, `:314`).

The fallback error string is explicit:
`"Unexpected PipelineCache configuration! Stereo is missing but L1 size != camera resoution!"`
at `0x3ec672` (`:694`).

### 3. The hot body builds descriptors, scalar tables, and executor work

The hot path copies state from `PipelineCache+0x1e0`, constructs temporary
records/descriptors, calls helper `0x260b70`, resolves dimensions through
`0x3e0b90`, validates source/destination descriptors, and builds a 64-entry
scalar table. The table loop stores the final table entry at `0x3ec333`
(`:519`).

The body has explicit empty-descriptor guards:

- `"empty source image!"` at `0x3ec500` (`:616`)
- `"empty destination image!"` at `0x3ec539` (`:625`)

### 4. The executor layer is generic tiling/callable plumbing

`0x3ebb80` installs a callable-like object at `0x3ec410` and dispatches
generic executor `0x5440` at `0x3ec462` (`:566`, `:581`).

The executor body partitions rectangle work and contains callable dispatch
sites through slot `+0x30` (`0x5506`, `0x2d8f`, `0x2dcc`; `:1217`,
`:1348`, `:1363`). For multi-tile work, it installs a generic tiler table at
`0x650290`; tiler worker `0x5cd0` computes tile rectangles and forwards them
through another callable dispatch at `0x5d94` (`:1715`, `:1807`, `:1871`).

This proves the exposed executor surface is rectangle tiling / callable
plumbing. This proof does not name the final callable math behind those generic
dispatch sites because that target was not runtime-bound here.

### 5. The installed callable-management table is bounded, not interpreted as the final worker

The table referenced by the object built at `0x3ec410` is readable at
`0x6607e8` (`:1415`, `:1417`). Static inspection of the code addresses in and
near that table bounds them to optional/metadata/copy/delete-style callable
management surfaces, including error strings such as
`"Cannot read data from empty Optional!"` (`:1528`, `:1537`) and
`"Invalid magic ID in Metadata record in state file!"` (`:1631`).

Because the final `+0x30` callable target was not runtime-bound in this proof,
the safe conclusion is intentionally narrower: the visible `src2` body is
descriptor/state/executor orchestration, not a proven merge/reducer closure.

### 6. `0x3edb80` remains one-image normalization

The wrapper's final call reaches `0x3edb80`. The static body contains repeated
`sqrtps` instructions (`0x3edcb8`, `0x3edcc8`, `0x3edd1a`, `0x3edd67`, and
others; first line at `:850`). This matches the prior selected-cache
classification of `0x3edb80` as one-image `sqrt(max())` normalization.

### 7. The `PipelineCache+0x1e0` initializer is state/backing-store setup

`0x1449f0` allocates backing storage through `operator new` at `0x144a2e` and
fills it with `memset_pattern16` at `0x144a45` (`:1063`, `:1068`). This supports
the existing classification of `PipelineCache+0x1e0` as a state object rather
than a hidden final reducer entry.

## Safe Conclusion

The repo-local installed-bundle evidence now supports this replacement for the
old scratch citation:

`0x3ecd80 -> 0x3ebb80 -> 0x3edb80` is a visible `src2` wrapper path over
`PipelineCache+0x1e0` state, `PipelineCache+0x1d8` fallback/source-descriptor
plumbing, descriptor validation, a 64-entry scalar table, generic tiled
executor dispatch, and one-image normalization.

This is a bounded structural surface, not the proven upstream
`src1` / `src2` semantic merge/reduction mechanism.

## Remaining Unknowns

- semantic `src2` contents
- semantic binding for the final callable target behind the generic executor
  dispatches reached from this path; the accepted gate callback slot is now
  bound across the canonical quartet as `0x65f7e8/+0x30 = 0x3ed2e0`, with
  accepted-dispatch proof, worker-entry proof, and completed `10432x7824` HDR
  output at all four seeds
- whether that downstream callable participates in the final merge/reduction
  decision or only materializes an already-selected descriptor
- final contributor acceptance/rejection policy
