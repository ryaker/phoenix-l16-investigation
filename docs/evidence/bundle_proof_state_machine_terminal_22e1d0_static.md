# Bundle Proof: Terminal `CalibDataProcessor::State()` Body `0x22e1d0` And Dispatcher `0x22f0f0`

## Scope

This note follows the corrected `CalibDataProcessor::State()` family proven in:

- [bundle_proof_calibdataprocessor_lambda_family.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_calibdataprocessor_lambda_family.md)
- [lldb_calib_state_operator_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_calib_state_operator_runtime_four_zoom.md)

It statically bounds the terminal corrected State body `0x22e1d0` and the shared
dispatcher body `0x22f0f0` in the installed `libcp.dylib`.

This is an installed-bundle static proof. It does not decode public State
semantics and does not close `CLM-PREFUSION-002`.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Static LLDB disassembly raw output:
  `runs/static_state_22e1d0/state_22e1d0_static_disasm.txt`
- Repo-local static callgraph outputs:
  `runs/static_state_22e1d0/callers_0x22f0f0.txt`,
  `runs/static_state_22e1d0/callers_0x22e1d0.txt`,
  `runs/static_state_22e1d0/callers_0x22f3ff.txt`,
  `runs/static_state_22e1d0/callers_0x23c5f0.txt`,
  `runs/static_state_22e1d0/callers_0xf33d0.txt`
- LLDB extraction command:
  `arch -x86_64 lldb -b -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x22e1d0 --end-address 0x22e80e' -o 'disassemble --start-address 0x22f0f0 --end-address 0x22f5ea' -o 'disassemble --start-address 0x226f00 --end-address 0x227190' -o 'disassemble --start-address 0x227680 --end-address 0x227930' -o 'memory read --format c --size 1 --count 14 0x6326c5' -o 'memory read --format c --size 1 --count 40 0x6326d3' -o 'memory read --format f --size 4 --count 2 0x5a8870' -o 'memory read --format f --size 4 --count 2 0x5aae9c' -o 'memory read --format f --size 8 --count 1 0x5d42c8'`
- Callgraph commands:
  `python3 tools/disasm_callgraph.py callers 0x22f0f0`,
  `python3 tools/disasm_callgraph.py callers 0x22e1d0`,
  `python3 tools/disasm_callgraph.py callers 0x22f3ff`,
  `python3 tools/disasm_callgraph.py callers 0x23c5f0`,
  `python3 tools/disasm_callgraph.py callers 0xf33d0`

## Proven Facts

### 1. `0x22e1d0` is the terminal corrected State body

The corrected State-family proof identifies vtable address point `0x658958` as
`runHigherGroupCams::$_12`, with `+0x30` operator body `0x22e1d0`. The
four-zoom runtime census separately proves `0x22e1d0` is live once per complete
accepted bridge HDR render at `28mm`, `35mm`, `70mm`, and `150mm`.

This note starts from that proven identity. It does not re-open `0x247390` as a
State candidate.

### 2. `0x22e1d0` performs keyed record/tree work, not a visible pixel reducer

Static disassembly proves the following visible structure:

- The body reads a state-like object from `this+0x8` into `r15`.
- It initializes a local container at `rbp-0xd8` from `r15+0x30`.
- It calls `0x23c5f0` twice with inputs from `r15+0x40`, `r15+0x50`,
  `r15+0xa0`, the local container, the object at `this+0x10`, and constants
  `r8d = 1`, `r9d = 0xb`.
- It calls `0x239ac0` using `r15+0x28` and the installed pointer/string-like
  object at `0x66ff50`.
- It selects a float threshold of `4.0` when the dword pointed to by qword
  field `this+0x18` is `< 5`, otherwise `15.0`.
- It iterates the 4-byte integer vector at `this+0x20`.
- For each integer key, it searches keyed tree nodes under `this+0x28`,
  creates missing nodes via `0x232340`, inserts them via `0xdb240`, and updates
  node float/key fields.
- It calls `0x23a530` for the current key, then searches another keyed tree
  under `this+0x10`.
- If the visible threshold predicate passes, it calls shared object lookup
  helper `0xe6ba0` with the current key, then creates or finds additional
  keyed nodes and calls `0xf33d0`.
- The visible `0xf33d0` call at `0x22e755` uses:
  `rdi = lookup result`, `rsi = node_a+0x30`, `rdx = node_b+0x60`,
  `rcx = node_c+0x54`, and `r8d = 1`.
- After the loop, it calls `0x23a5c0`, releases local shared objects, destroys
  the local vector/container, and returns constant `State` value `9`.

The visible body contains no image-width by image-height loop, no direct IRAMP
accumulator-style multi-source `vec4` blend, no final raster write, and no
direct exposed N-to-1 pixel reducer closure.

### 3. `0x22f0f0` is the shared state-machine dispatcher

Static disassembly proves:

- `0x22f0f0` embeds the string `"State machine"`.
- It uses `r14+0x6c` as the current State slot and `r14+0x68` as a target/stop
  State slot.
- It searches a keyed tree/list rooted at `r14+0x58`.
- It calls a registered State function object through vtable slot `+0x30` at
  `0x22f3f6..0x22f3fd`.
- It writes the returned `eax` value into the current State slot at `0x22f3ff`
  with `movl %eax, (%r12)`.
- It records timing using `mach_absolute_time`, multiplies the elapsed interval
  by double constant `0.001`, and stores the result into the state-history
  vector around `r14+0xa8`.
- It calls `0x2102d0`.
- If callback object `r14+0xe0` exists, it calls that object's `+0x30` slot with
  `rsi = r12`, then loops back to the next state.
- If the first gate reports completion, it copies `r14+0x68` into `r14+0x6c`,
  calls `0x210370`, cleans up local state, and returns success.
- The error path embeds `"state function has not been registered."`

Repo-local static callgraph output reports direct callers of `0x22f0f0` only at
`0x22705e` and `0x2277b3`. The same static callgraph reports no direct callers
for `0x22e1d0` or `0x22f3ff`; that is expected for this proof because the
State bodies are reached through indirect function-object dispatch.

### 4. Helper direct-caller census bounds local helper reuse

The repo-local direct callgraph reports these local helper callsite facts:

- Direct callers of `0x23c5f0` include `0x22e244` and `0x22e283`, the two calls
  in `0x22e1d0`, plus eleven earlier callsites in the `0x22b...` range.
- Direct callers of `0xf33d0` include `0x22e755`, the call inside `0x22e1d0`,
  plus nine other direct callsites.

This proves helper reuse, not helper public semantics.

## Safe Conclusion

- Proven:
  `0x22e1d0` is the terminal corrected `runHigherGroupCams::$_12`
  `CalibDataProcessor::State()` body and returns constant State value `9`.
- Proven:
  the visible `0x22e1d0` body is keyed vector/tree/object-lookup/helper
  dispatch work over per-key records.
- Proven:
  `0x22f0f0` is the shared state-machine dispatcher that invokes registered
  State function objects, stores returned `State` values at `r14+0x6c`, and can
  notify a callback object at `r14+0xe0`.
- Proven:
  the installed static bodies do not expose a direct pixel reducer closure at
  `0x22e1d0` or at the `0x22f0f0` dispatch store site.

## Non-Claims

- This does not prove public names for `this+0x8`, `this+0x10`, `this+0x18`,
  `this+0x20`, `this+0x28`, `r14+0x58`, `r14+0x68`, `r14+0x6c`, or `r14+0xe0`.
- This static proof does not prove runtime return ordering for all State
  transitions. Follow-up runtime return ordering for the canonical four-zoom
  no-auto-LRIS dispatcher path is covered by
  [lldb_state_machine_return_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_machine_return_runtime_four_zoom.md).
- This does not prove public semantics of returned State value `9`.
- This does not prove public semantics of helper calls `0x23c5f0`, `0xe6ba0`,
  or `0xf33d0`.
- This does not prove that the broader State machine is irrelevant to merging;
  it only bounds the inspected terminal State body and dispatch store.
- This does not close `CLM-PREFUSION-002`.

## Diagnostic Non-Evidence

A first runtime attempt to capture values at `0x22f3ff` lost the debugger
connection before a JSON report or any accepted event was produced. Those logs
are invalid diagnostics only and are not cited for any claim in this proof.

## Consequence For Blocker Work

The corrected terminal State candidate is no longer an open plausible direct
reducer surface. Follow-up runtime proof now covers the canonical four-zoom
State-return ordering at `0x22f3f6` / `0x22f3ff`, so future Lane A work should
move past `0x22e1d0` / `0x22f0f0` unless the goal is specifically public
State-machine semantics. The exact `src1` / `src2` merge/reduction mechanism
remains open.
