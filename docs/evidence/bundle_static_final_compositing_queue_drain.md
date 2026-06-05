# Bundle Proof: Static Final-Compositing Queue / Drain Surface

## Scope

This static installed-bundle proof validates the bounded parts of Opus's
quarantined final-compositing packet:

- `0x3bf820` builds a tile-update-like stack record and inserts it into a
  container at owner offset `+0x260`.
- `0x3bfc40` inserts that record into a hand-rolled intrusive ring/list, not an
  RB-tree or `std::list`.
- `0x3c25a0` waits on the same container's count/stop state.
- `0x3bfe60` drains the ring into a vector-like 0x70-stride record array and
  deletes the ring nodes.
- `0x3bca90` calls the wait and drain surfaces, filters 0x70-byte records, and
  reaches ImagePyramid/Image descriptor plus virtual-processor dispatch
  surfaces.

This proof is static only. It does not prove four-zoom runtime liveness, public
type names, byte-level copy-vs-blend behavior, final file/display sink, or final
merge acceptance/rejection.

## Artifacts

Raw logs are under ignored repo-local `runs/`:

- `runs/codex_opus_final_compositing_static/static_3bf820_collector.log`
- `runs/codex_opus_final_compositing_static/static_3bfc40_insert.log`
- `runs/codex_opus_final_compositing_static/static_3bfe60_gather.log`
- `runs/codex_opus_final_compositing_static/static_3c25a0_join_wait.log`
- `runs/codex_opus_final_compositing_static/static_3bca90_orchestrator.log`
- `runs/codex_opus_final_compositing_static/nm_cxxfilt.log`
- `runs/codex_opus_final_compositing_static/strings_offsets.log`
- `runs/codex_opus_final_compositing_static/otool_L.log`
- `runs/codex_opus_final_compositing_static/libcp_sha256.txt`
- `runs/codex_opus_final_compositing_static/tree_list_symbol_count.txt`

Binary:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

SHA-256:

`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`

Example reproduction commands:

```bash
arch -x86_64 lldb -b \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'disassemble --start-address 0x3bfc40 --count 180'

arch -x86_64 lldb -b \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'disassemble --start-address 0x3bfe60 --count 180'

nm -m /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib | c++filt
strings -a -t x /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
```

## Static Proof

### Collector / Insert Edge

The `0x3bf820` window builds a stack record and inserts it into a container at
owner offset `+0x260`:

- `0x3bf85e` writes tag-like field `0xd` to `rbp-0xa0`.
- `0x3bf868` writes level-like field `2` to `rbp-0x9c`.
- `0x3bf88a` advances the owner/container base by `+0x260`.
- `0x3bf8bc` calls `0x3bfc40` with the stack record.
- The local error path contains the string
  `"Tile update has incorrect level!"`.

### Intrusive Insert Body

The `0x3bfc40` body is a hand-rolled queue insert:

- `0x3bfc5e` locks mutex at `this+0x20`.
- `0x3bfc63` checks stop flag byte `this+0x18`.
- `0x3bfc7a` starts walking from `this+0x08`.
- `0x3bfc90` compares the incoming priority against node field `+0x14`.
- `0x3bfc95..0x3bfc9f` advances through node `+0x08` until the insertion
  point or the ring sentinel is reached.
- `0x3bfcab` allocates `0x80` bytes for the node.
- `0x3bfce0` copies the stack payload into `node+0x10` via `0x3efda0`.
- `0x3bfce5..0x3bfcf3` splices pointer fields directly.
- `0x3bfcf8` increments container count at `this+0x10`.
- `0x3bfd07` broadcasts the condition variable at `this+0x60`.

This local layout is not compatible with an RB-tree node shape. The body uses a
ring sentinel and direct previous/next pointer splicing; it does not expose
left/right/parent/color fields.

### Join / Wait Body

The `0x3c25a0` body waits on the same container shape:

- `0x3c25b5` locks mutex at `this+0x20`.
- `0x3c25ba` checks stop flag byte `this+0x18`.
- `0x3c25d2` checks count field `this+0x10`.
- `0x3c25e0..0x3c25e6` waits on condition variable `this+0x60` with the mutex.
- Return `al` is set from `bl`, where `bl = 1` only when count becomes nonzero
  before stop.

### Gather / Drain Body

The `0x3bfe60` body drains the ring into a vector-like destination:

- `0x3bfe7b` locks mutex at `this+0x20`.
- `0x3bfe80` checks stop flag byte `this+0x18`.
- `0x3bfeb8` loads the first node from `this+0x08`.
- `0x3bfebc` compares the node pointer against the container sentinel.
- `0x3bfed8` uses `node+0x10` as the source payload.
- `0x3bfeea` appends into existing output capacity through `0x3f0130`.
- `0x3bff03` grows/appends through `0x3c0c70` when capacity is exhausted.
- `0x3bff08` advances to the next node via `node+0x08`.
- `0x3bff35` zeroes the container count at `this+0x10`.
- `0x3bff50..0x3bff60` walks remaining nodes, destroys payloads, and deletes
  nodes.

This proves copy-out-then-destroy drain semantics for the local queue body.

### Post-Gather Orchestrator Surface

The `0x3bca90` body statically reaches the queue/drain surface and then filters
0x70-stride records:

- `0x3bcc1d` calls `0x3c25a0`.
- `0x3bcc51` calls `0x3bfe60`.
- `0x3bcc92..0x3bcca6` computes vector size using the 0x70-stride magic
  constant `0x6db6db6db6db6db7`.
- `0x3bccc0`, `0x3bccc8`, `0x3bccd0`, and `0x3bccd8` filter fields at record
  offsets `+0x00`, `+0x24`, next-record `+0x00`, and next-record `+0x24`
  under the local two-record window.
- `0x3bcf8d..0x3bcfe5` reaches `CIAPI::ImagePyramid` construction,
  level access, and Image width/height/stride/data accessors.
- `0x3bd05d`, `0x3bd270`, and `0x3bd355` are per-tile indirect dispatch
  surfaces.
- `0x3bdd73` calls helper `0x401ab0`; `0x3bddad..0x3bddce` again reaches
  Image width/height/stride/data accessors.

This bounds post-gather structure only. It does not prove whether a given
per-tile virtual processor copies, blends, clips, or performs another
operation.

### Symbol / String Census

The installed dylib links against `libc++.1.dylib`. A c++filt symbol census for
the patterns `std::__1::__tree`, `std::__1::map<`, `std::__1::set<`,
`std::__1::multimap<`, `std::__1::multiset<`, `std::__1::list<`,
`std::__1::forward_list<`, and `_Rb_tree` returned count `0`.

String census found:

- `0x634d39`: `"Tile update has incorrect level!"`
- `0x633da7`: `"blending weight has to be smaller than 128_u8!"`

The blend string proves only that a blend-related diagnostic exists somewhere
in the installed bundle. This evidence does not place that diagnostic inside
the `0x3bca90` gather/drain surface.

## Proven Facts

- The admitted static collector path builds a stack record with field values
  `0xd` and `2`, then inserts it through `0x3bf820 -> 0x3bfc40`.
- The insert container is an intrusive ring/list rooted at the `+0x260` owner
  offset, with mutex/stop/count/condvar fields local to the container.
- The local insert body allocates `0x80`-byte nodes, copies a `0x70`-byte
  payload at `node+0x10`, links nodes by direct pointer splicing, and increments
  count.
- The local gather body copies payloads out to a vector-like 0x70-stride
  storage and then unlinks/destroys/deletes the ring nodes.
- The local surface is not an RB-tree and not a `std::list` instantiation in
  the installed binary.
- The `0x3bca90` body statically calls the wait and gather surfaces, filters
  gathered records, and reaches ImagePyramid/Image descriptor plus per-tile
  virtual dispatch surfaces.

## Non-Claims

- No four-zoom runtime liveness is admitted here.
- No public C++ class/field names are admitted here beyond symbolized CIAPI
  accessor names already present in the binary.
- No copy-vs-blend byte behavior is admitted for the per-tile virtual
  processors.
- No final file/display sink is proven.
- No final merge acceptance/rejection, anti-ghosting, or parity-critical
  contributor policy is closed by this static queue/drain proof.
