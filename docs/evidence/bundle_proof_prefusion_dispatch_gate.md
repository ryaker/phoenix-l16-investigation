# Bundle Proof: Prefusion Dispatchers and Shared Record-State Gate

## Scope

This note proves only what the installed `libcp.dylib` shows for the next layer beneath the already-bounded heavy consumers.

It proves:

- `0x248580`, `0x248960`, and `0x2481a0` are sibling dispatcher wrappers that build temporary context objects and all hand off to a shared deeper routine at `0x2439b0`
- `0x2439b0` is a shared record-state gate over installed block regions `0x300` and `0x360`, not a direct pixel reducer
- `0x241fd0` counts and rewrites 0x2c-stride record states, clears installed blocks under threshold conditions, and dispatches onward to `0x2416d0`
- `0x2416d0` selects record indices whose fields match a requested target/type pair and promotes selected records from state `4` to state `5`

It does not prove that the exact `src1` / `src2` N-to-1 reducer has been found.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Dispatcher / shared-gate disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x248580 --count 1200' -o 'disassemble --start-address 0x248960 --count 1200' -o 'disassemble --start-address 0x2481a0 --count 1200' -o 'disassemble --start-address 0x2439b0 --count 900'`
- Downstream selector disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x241fd0 --count 1200' -o 'disassemble --start-address 0x2416d0 --count 1800'`

## Proven Facts

### 1. `0x248580`, `0x248960`, and `0x2481a0` are sibling dispatcher wrappers that all hand off to `0x2439b0`

- Each function allocates a heap object with:
  `operator new(0xa8)`
- Each function populates that object with pointers to:
  - incoming state / vector inputs
  - local scalar parameters stored on the stack
  - local rectangle / range structures stored on the stack
- Each function invokes the same temporary-object helper sequence:
  - `0x24bed0`
  - `0x5670`
  - destructor call through the temporary object's vtable
- Each function then calls the same deeper body:
  `0x2439b0`
- Therefore these three functions are sibling dispatcher wrappers around a shared deeper record-state routine rather than three independent reducers.

### 2. `0x2439b0` is a shared record-state gate over block regions `0x300` and `0x360`

- `0x2439b0` first checks block activity at:
  - `state + 0x300`
  - `state + 0x360`
  by calling `0x25d070`
- For each active block it iterates 0x2c-stride records from the supplied vector.
- The visible SIMD and scalar scans count records whose fields satisfy:
  - `record+0x24 == 4`
  - `record+0x28 == 1` for the first block
  - `record+0x28 == 2` for the second block
- If the matching-count total for the scanned block is `<= 7`, the function walks the same 0x2c-stride records and promotes matching records from:
  - `record+0x24 == 3`
  to:
  - `record+0x24 = 4`
- No image-width x image-height accumulation loop appears in `0x2439b0`; its visible work is record counting and state promotion inside the installed block families.

### 3. `0x241fd0` still operates on record-state counts, installed blocks, and record relabeling

- `0x241fd0` requires the callable at `0x220(%state)` and throws `std::__1::bad_function_call` if it is absent.
- It scans the supplied 0x2c-stride record vector and counts records satisfying:
  - `record+0x24 == 4`
  - `record+0x28 == 1`
  - `record+0x28 == 2`
- Under threshold conditions it clears block-active state by calling:
  - `0x25d080` on `state + 0x300`
  - `0x25d080` on `state + 0x360`
- In two branches it writes the packed qword value:
  - `0x0000000200000005`
  into `record+0x24 .. record+0x2b` for matching subsets of the 0x2c-stride records
- It computes capped combinatorial counts from the group-1 and group-2 tallies and then dispatches onward to:
  - `0x2416d0`
  with mode `1` or mode `2`
- Therefore `0x241fd0` is still a record-count / block-clear / record-relabel dispatcher, not direct pixel reduction.

### 4. `0x2416d0` selects target-matching record indices and promotes selected records from state `4` to state `5`

- `0x2416d0` scans the 0x2c-stride record vector and selects indices whose fields satisfy:
  - `record+0x28 == requested target`
  - `record+0x24 == 4`
- It stores the selected record indices into a temporary integer vector.
- If the number of selected indices is `<= 7`, it directly marks those selected records:
  - `record+0x24 = 5`
- If the selected count exceeds `7`, the visible body still remains index / bitset / candidate-selection logic:
  - it allocates temporary integer buffers
  - it copies and zero-initializes selection buffers
  - it calls helper routines such as `0x249020`, `0x247900`, and `0x249410`
  - later visible stores again write:
    `record+0x24 = 5`
    for selected record indices
- Therefore the visible body of `0x2416d0` is target-specific candidate selection and promotion of record state, not a direct exposed image reducer.

## Safe Conclusion

- Proven:
  the deeper dispatcher family `0x248580` / `0x248960` / `0x2481a0` is only a wrapper layer around `0x2439b0`.
- Proven:
  `0x2439b0` is a shared installed-block gate that counts and promotes 0x2c-stride record states.
- Proven:
  `0x241fd0` and `0x2416d0` still operate on record counts, index lists, block actives, and state relabeling.
- Still unproven:
  the exact `src1` / `src2` N-to-1 reducer.

## Consequence For Blocker Work

Future anchor pre-fusion work can now treat this layer as bounded:

1. dispatcher wrappers `0x248580`, `0x248960`, `0x2481a0`
2. shared record-state gate `0x2439b0`
3. downstream selector / promoter pair `0x241fd0`, `0x2416d0`

The next unresolved surfaces are deeper helpers reached from that selector-heavy path, especially:

- `0x249020`
- `0x247900`
- `0x249410`

Those are the next concrete places where the still-unresolved pre-IRAMP reducer question could close.
