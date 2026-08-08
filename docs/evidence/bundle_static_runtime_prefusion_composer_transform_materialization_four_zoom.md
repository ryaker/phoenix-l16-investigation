# Evidence: Prefusion Composer Transform Materialization, Four Zoom

**Correction (2026-06-28):** follow-up static/runtime proof reverses the
earlier branch labels below: `score <= existing` materializes the candidate,
while `score > existing` retains and transfers the existing keyed record.
See
`bundle_static_runtime_prefusion_wide_minimum_selector_calibstage_transfer.md`.

## Scope

This note follows
`bundle_static_runtime_prefusion_264270_output_to_23faf0_four_zoom.md`.
That proof carries one exact accepted selector-1 record through `0x264270`,
`0x23faf0`, and the first post-composer read. This note follows the same
runtime record through the immediate wide or tele calculation and its first
durable store.

SHA-pinned static code plus route-gated runtime captures prove:

- the first nine floats of the composer destination are used as an internal
  `3x3` transform coefficient block;
- wide `0x239e00` applies that block to positive 3D records, projects to two
  coordinates, accumulates Euclidean residuals against positive coordinate
  pairs, divides by the accepted count, and returns a scalar;
- `0x239ac0` stores that exact returned scalar into a keyed payload;
- tele `0x20dbe0` multiplies the `3x3` composer block by three SIMD rows,
  producing a `3x4` matrix;
- `0x20afb0` copies those exact 48 result bytes into keyed node
  `+0x20..+0x4f`;
- the wide keyed scalar is next read unchanged through `0x23a530`;
- State `0x22d250` compares that exact wide scalar with a keyed node's `+0x28`
  scalar; the outcome-targeted corrective bundle proves both
  candidate-materialization and existing-record-transfer effects;
- for the tracked tele node in each run, the watched first eight matrix bytes
  have no intervening touch and are first touched again only during recursive
  tree cleanup after HDR output.

This proves transform and score materialization. It does not prove a public
record or matrix name, image-buffer contribution, distributed reducer closure,
or final merge acceptance/rejection.

## Artifacts

- Probe:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_264270_output_watch_probe.py`
- LLDB command files:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/output_watch_28mm.lldb`
  through `output_watch_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_264270_output_watch_four_zoom.sh`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_264270_output_watch.py`
- Runtime reports and HDR outputs:
  `runs/prefusion_264270_output_watch/`

Only the four clean completed reports are evidence dependencies. An
instrumentation-sensitive exploratory `70mm` attempt stopped at the known
`0x2e8cc0` race before the identity gate and was replaced by a clean completed
repeat.

## Static Wide Formula

The verifier pins:

```text
0x23a200..0x23a387 SHA-256:
3087c7f73073d1215cf08eadbbfb833b51b7f1dfe64d882ed84501b6e83fd355

0x239c34..0x239c43 SHA-256:
b3cf90d5151ea0669037e3c609e8e648d10c04b1af591736180226a1237bbf85

0x239d2d..0x239d46 SHA-256:
a0f27e3e6b9fbe4069f2569b358f18eb9ca06e6a7153cc6a7d131d020b4efdf7

0x23a530..0x23a5bc SHA-256:
e073ce3833a2d3d75de1e3e6b930406034c7b6d786a9f3ce927a6773c9241396

0x22d8ed..0x22d907 SHA-256:
f0cce948c7dad3ae0ac8b30306fe98c104134854ffd632153ee19d5794b9f027

0x22de81..0x22debc SHA-256:
2fdfaa641ff7d96c1488c3451b2897ef535ea3f022c40364a0f65b7d6cfb35f3

0x22dcc3..0x22dce5 SHA-256:
ca5a6e8c78767badfc4840e21404f5539f1898747d7311ee4acfd269a169e8f8
```

`0x23a179..0x23a1ef` moves the composer destination's first nine floats into
the loop's three coefficient rows. For each entry passing positive coordinate
and positive-z gates, `0x23a23b..0x23a324` applies the coefficient rows to the
3D record. `0x23a330` performs perspective division; `0x23a33c..0x23a351`
subtracts the observed coordinate pair and computes the Euclidean residual.
`0x23a355` accumulates the residual and `0x23a35a` increments the accepted
count.

At `0x23a36f..0x23a383`, the function converts the sum and count to double and
divides. The installed double added to the count at `0x5d2c98` is exactly
`0.0`, so this bounded path returns `sum / accepted_count`.

The caller captures that scalar after `0x239c3a -> 0x239e00`, resolves a keyed
payload through `0x23a5d0`, and writes the scalar at `0x239d42`.
Accessor `0x23a530` resolves the nested keyed payload and reads its scalar at
`0x23a5b1`.

State `0x22d250` stores that accessor return in local `rbp-0x2a0`. At
`0x22d8ed`, it reloads the exact scalar; `0x22d8f5` compares it with keyed node
`r12+0x28`. Follow-up proof corrects the original interpretation:
`0x22d8fb -> 0x22d9a0` materializes the candidate when its score is less than
or equal to the node scalar, while fallthrough at `0x22d901` retains the
existing keyed record and transfers it into live CalibStage storage.

The same stack slot is not stable beyond that decision. Static instructions
at `0x22de81`, `0x22de98`, and `0x22deab` reuse `rbp-0x2a0` as a qword pointer.
The update-run hardware watch first observes that reuse after `0x22deab`.
Therefore later same-frame stores are not admitted as copies of the original
wide score.

The admitted `35mm` existing-record branch next reaches existing-entry subpath
`0x22dcc3`. Static code saves the found node pointer in `rbp-0x2c0`; because it
is non-null, `0x22dce4` jumps to `0x22dd4f` and bypasses the new-node allocation
at `0x22dcf0..0x22dd39`. At `0x22df45`, the selected node's `+0x30`, `+0x60`,
and `+0x54` slices are copied byte-exactly through selector-1 `0xf33d0` into
the per-camera `state+0xe0` object's CalibStage bank `+0x12c..+0x17f`.

## Static Tele Formula

The verifier pins:

```text
0x20dbe0..0x20dc91 SHA-256:
810a7349b4891bb9ede9ba0cd1e8bc32e57b0eadff3f1dc288775f682cc13907

0x20b234..0x20b272 SHA-256:
f6376af0870446c7cf20cb74cd5c4b69f671531cb0833828f570bab321a76d9f

0x230920..0x23096f SHA-256:
a2f1b6f6758af3b5589700771b2f29f68bf8df3198cd0c05ee1f13ce049ef57f
```

`0x20dbe0` reads three four-float rows from `rdx`. For each of three output
rows, it broadcasts three successive composer floats from `rsi`, multiplies
the input rows, adds them, and writes one four-float row to `rdi`. The result
is the internal matrix product:

```text
output_3x4 = composer_3x3 * input_3x4
```

At `0x20b249`, the caller uses local destination `rbp-0x1e0`. Instructions
`0x20b24e..0x20b26d` copy its three rows into keyed node
`r14+0x20`, `r14+0x30`, and `r14+0x40`.

`0x230920` is a recursive tree-deletion helper: it visits left and right
children, then tail-calls `operator delete` on the node.

## Runtime Materialization

| Tier | Route | Captured durable store |
|---|---|---|
| `28mm` | wide | first tracked candidate was higher than the existing score; existing record transferred |
| `35mm` | wide | first tracked candidate was higher than the existing score; existing-entry record copied into selector-1 CalibStage |
| `70mm` | tele | helper/caller/node 48-byte matrix exact match; observed node key `9`; watched prefix first later touched by cleanup |
| `150mm` | tele | helper/caller/node 48-byte matrix exact match; observed node key `6`; watched prefix first later touched by cleanup |

Numeric values, pointer addresses, and observed node keys are report-local facts,
not stable constants. The verifier checks the current reports directly.

For each wide run, the verifier requires exact equality among:

1. low 32 bits of `xmm0` at return site `0x239c3f`;
2. caller local `rbp-0x5c`;
3. the payload bytes after store `0x239d42`.
4. the first subsequent accessor read at watch stop `0x23a5b6`, reached from
   State `0x22d250` call return `0x22d7e6`.

The verifier then requires the exact accessor bits at compare site `0x22d8fb`,
reconstructs `jbe` from runtime flags, and checks the observed route. The
current first-hit `28mm` and `35mm` reports both observe `score > existing`;
the separate outcome-targeted corrective packet proves both comparison
outcomes without relying on first-hit ordering.

On the existing-record route, a local watch proves the first later write to
`rbp-0x2a0` is the qword-pointer reuse ending at watch stop `0x22deb2`; a
route-gated breakpoint also binds the immediate map path to existing-entry
site `0x22dcc3`. The follow-up verifier additionally binds the exact
`state+0x448` node slices to the changed selector-1 CalibStage bank.

For each tele run, it requires exact equality among:

1. the 48-byte helper destination at `0x20dc8d`;
2. caller local `rbp-0x1e0` at `0x20b24e`;
3. keyed node `+0x20..+0x4f` after `0x20b26d`.

A final route-specific hardware read/write watch is armed only after those
durable stores. On wide, its first hit is the unchanged scalar read through
`0x23a530`. On tele, it watches the first eight bytes of the tracked matrix
node: no earlier access stops occur, HDR output completes, and the first later
stop changes the bytes to zero under allocator `memset` with recursive
`0x230920` tree-cleanup ancestry. This is a scoped exclusion for the tracked
eight-byte prefixes only; it does not exclude aliases, the remaining 40 matrix
bytes, other keyed nodes, or alternate routes.

All four runs exit `0`, avoid the drive cap, report no probe errors, and write
`10432 x 7824` HDR output.

The preceding accepted-bank proof includes an exact-focal Unit-2 `35mm`
discriminator. This continuation tests both wide focal tiers and both tele
focal tiers because its new risk is the focal-family route split; it does not
repeat a second-body render for deterministic arithmetic inside each route.

## Verification

```bash
python3 -m py_compile \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_264270_output_watch_probe.py \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_264270_output_watch.py
bash -n \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_264270_output_watch_four_zoom.sh
python3 \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_264270_output_watch.py
```

Verifier output:

```text
static_264270_output_watch=OK libcp_sha256=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 assembly_sha256=acde803cf7789e4ccf0c61450feb6e83d827f7c95d2a4312724b0f35e22b2cda composer_sha256=d07dbe6d5b04ffae62e114283c13a04e0c2b14d85741c0ab7932c105aeba6472
28mm: ... route=0x239e00->0x239ac0->State0x22d250 ... decision=retain_existing_and_transfer
35mm: ... route=0x239e00->0x239ac0->State0x22d250 ... decision=retain_existing_and_transfer
70mm: ... route=0x20afb0->0x20ada0->State0x22ae60 ... first-later-touch=cleanup
150mm: ... route=0x20afb0->0x20ada0->State0x22ae60 ... first-later-touch=cleanup
```

## Safe Conclusion

The accepted selector-1 record is not merely copied into opaque State storage.
Its composed first-nine-float block participates in concrete transform math:
wide materializes a keyed mean reprojection-residual score, while tele
materializes a keyed `3x4` composed transform matrix.

The wide score is immediately read back through its keyed accessor and controls
a keyed minimum-selection branch; both branch outcomes are observed across
the two wide tiers. The lower candidate is materialized into the keyed record,
while the higher candidate causes the existing `state+0x448` record to be
copied into the per-camera `state+0xe0` selector-1 CalibStage bank. This
establishes local calibration-record decision effect, not a public quality
meaning or final acceptance rule. The
tracked tele node prefixes instead have a scoped no-intervening-touch result
before cleanup under the two canonical tele runs. This is still internal
transform/score state. Public semantic names, image/source-contribution effect
after the wide branch, alias/other-node/other-byte or alternate-route proof for
tele, distributed reducer closure, and final merge acceptance/rejection remain
open.
