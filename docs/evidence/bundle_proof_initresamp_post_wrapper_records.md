# Bundle Proof: `initResAmp` Post-Wrapper Per-Key Records

## Scope

This note proves only what the installed `libcp.dylib` exposes immediately after the known `src1` / `src2` wrapper installation in the `initResAmp`-path body at `libcp+0x3eb3c0`.

It does not prove the exact upstream N-to-1 reducer behind `src1` / `src2`.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Constructor / zero-initialization context:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3ea7d0 --count 230'`
- Post-wrapper body:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3eb3c0 --count 260'`
- Post-wrapper body continuation:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3eb8c0 --count 120'`
- Key lookup helper:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e0a60 --count 80'`
- Key-vector collector:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e0bb0 --count 90'`
- Tiny offset helper:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3d0c80 --count 20'`
- Two-float field helpers:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x25e560 --count 45'`
- Per-key record dispatcher:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3f7040 --count 110'`
- Map/tree population helper:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e0330 --count 150'`
- Map/tree population helper continuation:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e0528 --count 180'`

## Proven Facts

### 1. The relevant `PipelineCache` fields are constructor-zeroed before `initResAmp`

- `libcp+0x3ea8cd` zeroes the 16-byte range beginning at `PipelineCache+0x278`.
- `libcp+0x3ea8d5` zeroes the 16-byte range beginning at `PipelineCache+0x268`.
- `libcp+0x3ea8dd` zeroes the 16-byte range beginning at `PipelineCache+0x258`.
- `libcp+0x3ea8e5` zeroes the 16-byte range beginning at `PipelineCache+0x248`.
- `libcp+0x3ea8ed` zeroes the 16-byte range beginning at `PipelineCache+0x238`.
- Constructor cleanup paths later walk/release `PipelineCache+0x270..+0x280`, delete `PipelineCache+0x258`, and release the `+0x250` / `+0x240` owners.
- Therefore the later `+0x238`, `+0x248`, `+0x258`, and `+0x270` writes are to explicit `PipelineCache` fields, not accidental stack aliases.

### 2. `initResAmp` first installs the known `src1` / `src2` wrappers

- The first wrapper install remains the already-proven sequence:
  `libcp+0x3eb4d1` stores `PipelineCache*` at wrapper `+0x28`, `0x3eb4d5..0x3eb4d8` store dimensions at wrapper `+0x50/+0x54`, `0x3eb4df` stores the wrapper inner pointer to `PipelineCache+0x238`, and `0x3eb4ed` stores the owner at `PipelineCache+0x240`.
- The second wrapper install remains the already-proven sequence:
  `libcp+0x3eb549` stores `PipelineCache*` at wrapper `+0x28`, `0x3eb54d..0x3eb550` store dimensions at wrapper `+0x50/+0x54`, `0x3eb557` stores the wrapper inner pointer to `PipelineCache+0x248`, and `0x3eb565` stores the owner at `PipelineCache+0x250`.
- This document starts after those stores.

### 3. The post-wrapper body derives two float ratios at `PipelineCache+0x1e8/+0x1ec`

- `libcp+0x3eb57a` takes the address of `PipelineCache+0x1e8`.
- `libcp+0x3eb588..0x3eb5a2` reads four integer fields from the level-vector begin pointer stored at `PipelineCache+0x8` and performs two single-precision divisions:
  vector entry `0` width over entry `1` width, and vector entry `0` height over entry `1` height.
- `libcp+0x3eb5a6` stores the first result to `PipelineCache+0x1e8`.
- `libcp+0x3eb5af` stores the second result to `PipelineCache+0x1ec`.
- These two fields are later passed by address into `0x3f7040` and used in a follow-up division before `0x25e590` writes two fields into each per-key record.
- Follow-up four-zoom runtime proof in [lldb_pipelinecache_level_vector_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_pipelinecache_level_vector_four_zoom.md) confirms `PipelineCache+0x8` is a packed `(int32 width, int32 height)` level-vector header, not an image/composite pointer.

### 4. The post-wrapper body populates map/tree state and collects integer keys

- `libcp+0x3eb5b8..0x3eb5c6` calls `0x3e0330` with:
  `rdi = PipelineCache+0x170`, and `rsi = &PipelineCache+0x180`.
- The visible body of `0x3e0330` checks that `(%rsi)` is non-null, walks key-like entries from the object reached through `PipelineCache+0x170`, allocates `0x30`-byte tree nodes keyed at node `+0x20`, calls `0x3f6170`, allocates a `0x1f0`-byte object initialized through `0x3e77d0`, and stores that object at node `+0x28`.
- `libcp+0x3eb5cb..0x3eb5d9` calls `0x3e0bb0` with output vector storage on the stack and input `PipelineCache+0x170`.
- `0x3e0bb0` zeroes the output vector, walks tree nodes rooted through the input object's `+0x28` / sentinel `+0x30` fields, and pushes each node's integer key at `node+0x20` into the output vector.
- Therefore the later loops in `0x3eb3c0` are per-key loops over keys collected from `PipelineCache+0x170` state.

### 5. The first per-key loop performs helper lookups and conditional calls

- `libcp+0x3eb630` reads the current 32-bit key from the collected key vector.
- `libcp+0x3eb633..0x3eb63f` calls `0x1be970` with the retained object pointer from `PipelineCache+0x170` and the current key.
- `libcp+0x3eb644..0x3eb655` calls `0xf2750`, ORs two returned 32-bit fields, and skips the later body if that OR is negative.
- `libcp+0x3eb657..0x3eb666` calls `0xf3340` and skips the later body if the first returned 32-bit field equals `4`.
- `libcp+0x3eb668..0x3eb685` calls `0x1bdc80` for the same object/key pair and releases the returned owner if present.
- This loop is proven as key-driven helper plumbing. It is not exposed N-to-1 reducer math.

### 6. The second per-key loop builds a `0x50`-byte record vector at `PipelineCache+0x258..+0x268`

- `libcp+0x3eb6d6..0x3eb6dd` stores the address of `PipelineCache+0x258` for later vector insertion.
- For each key, `libcp+0x3eb70f..0x3eb72d` calls `0x3f7040` with:
  output record stack storage, `rsi = *(PipelineCache+0x180)`, `edx = current key`, `rcx = &PipelineCache+0x1e8`, and `r8d = 1`.
- The visible dispatcher at `0x3f7040` compares two `0xf6c60`-derived categories and dispatches to either `0x3f70d0` or `0x3f72f0`.
- `libcp+0x3eb732..0x3eb740` calls `0x25e560` on the stack record.
- `0x25e560` computes two divisions from a shared float constant and record fields `+0x48/+0x4c`, then writes the two results to its output.
- `libcp+0x3eb745..0x3eb76f` divides those two results by `PipelineCache+0x1e8` and `PipelineCache+0x1ec`.
- `libcp+0x3eb777..0x3eb785` calls `0x25e590`.
- `0x25e590` computes two divisions from a shared float constant and the supplied two-float input, then writes the results back to record fields `+0x48/+0x4c`.
- `libcp+0x3eb78a..0x3eb7e1` copies the stack record into the vector at `PipelineCache+0x258..+0x268` and advances `PipelineCache+0x260` by `0x50`.
- If the vector is full, `libcp+0x3eb7f0..0x3eb7fe` calls the grow/insert helper `0x3edec0`.
- Therefore this branch creates one `0x50`-byte record per collected key in the `PipelineCache+0x258` vector.

### 7. The same second loop builds a shared-ptr-like wrapper-pair vector at `PipelineCache+0x270..+0x280`

- `libcp+0x3eb6c8..0x3eb6cf` stores the address of `PipelineCache+0x270` for later vector insertion.
- `libcp+0x3eb803..0x3eb810` calls `0x3e0a60` with `PipelineCache+0x170` and the current key.
- `0x3e0a60` is a map/tree lookup:
  it walks nodes rooted at input `+0x30`, compares the current key against `node+0x20`, returns `node+0x28` on match, and throws `"map::at:  key not found"` if no match is found.
- `libcp+0x3eb818..0x3eb836` obtains one float through `0x1bdfa0` and `0xe67c0` using the same key.
- `libcp+0x3eb83e..0x3eb847` calls `0x3d0c80` on the looked-up payload's `+0x10` subobject.
- `0x3d0c80` returns `rdi + 0x8`.
- `libcp+0x3eb84a..0x3eb8a7` allocates a `0x60`-byte wrapper object, writes a local address point at wrapper `+0x20`, copies the looked-up payload pointer plus the float into wrapper fields beginning at `+0x28`, stores dimensions at `+0x50/+0x54`, and clears byte `+0x58`.
- `libcp+0x3eb8c9..0x3eb8db` stores the wrapper inner pointer and owner into the vector at `PipelineCache+0x270..+0x280` and advances `PipelineCache+0x278` by `0x10`.
- If the vector is full, `libcp+0x3eb8f0..0x3eb8fe` calls the grow/insert helper `0x3ee080`.
- Therefore this branch creates one shared-ptr-like wrapper pair per collected key in the `PipelineCache+0x270` vector.

### 8. The branch marks `initResAmp` completion

- After the second per-key loop completes, `libcp+0x3eb925` stores byte `1` to `PipelineCache+0x1f0`.
- The entry path checks this byte at `libcp+0x3eb3f7..0x3eb3ff` and skips the body if it is already set.
- Therefore the `+0x258` and `+0x270` per-key vectors are part of the same guarded initialization path as the already-proven `src1` / `src2` wrapper stores.

## Safe Conclusion

- Proven:
  after installing the known `src1` / `src2` wrappers, the visible `initResAmp` body derives two float ratio fields, populates or updates map/tree state, collects integer keys, and builds two per-key vectors under `PipelineCache+0x258` and `PipelineCache+0x270`.
- Proven:
  `PipelineCache+0x258..+0x268` stores `0x50`-byte per-key records derived through `0x3f7040`, `0x25e560`, ratio division by `PipelineCache+0x1e8/+0x1ec`, and `0x25e590`.
- Proven:
  `PipelineCache+0x270..+0x280` stores per-key shared-ptr-like wrapper pairs whose payloads are looked up from `PipelineCache+0x170` by key.
- Still unproven:
  exact reducer body, exact reducer inputs, exact reducer outputs, and exact reducer math behind `src1` / `src2`.

## Consequence For Blocker Work

The visible post-wrapper `initResAmp` branch is now bounded as per-key map/vector/record/wrapper construction. It should be treated as another exclusion surface for `CLM-PREFUSION-002`, not as reducer closure.

Future reducer work should continue beyond this branch only when a downstream or upstream body is proven to expose true N-to-1 image input shape or reduction math.
