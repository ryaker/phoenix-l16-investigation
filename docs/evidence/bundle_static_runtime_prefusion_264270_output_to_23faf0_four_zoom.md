# Evidence: Prefusion `0x264270` Output to `0x23faf0`, Four Zoom

## Scope

This note follows
`bundle_static_runtime_prefusion_216f60_accepted_bank_downstream_custody_matrix.md`.
That proof shows the first accepted selector-1 bank is read by `0x264270`.
This note follows the exact output record assembled by that invocation.

SHA-pinned static code plus four complete one-hit hardware-watch runs prove:

- `0x264270` assembles its caller-provided output record from the accepted
  selector-1 bank and the already-bounded calibration accessors;
- the first downstream read of that exact output address is `0x23faf0`;
- `0x23faf0` receives the address as its `rdx` argument, assigns it to `rbx`,
  and copies the record into its own `rdi` / `r12` destination;
- the composer returns that exact destination in `rax`, after which wide tiers
  first load it into `0x239e00` score-input locals while tele tiers first pass
  it into `0x20dbe0` matrix-composition math;
- wide and tele focal families use different State/helper caller chains.

This is exact accepted-bank assembly-output to record-composer custody. It does
not prove the composed record's public name, later image/source contribution,
distributed reducer closure, or final merge acceptance/rejection.

## Artifacts

- Probe:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_264270_output_watch_probe.py`
- LLDB command files:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/output_watch_28mm.lldb`,
  `output_watch_35mm.lldb`, `output_watch_70mm.lldb`, and
  `output_watch_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_264270_output_watch_four_zoom.sh`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_264270_output_watch.py`
- Complete runtime reports and HDR outputs:
  `runs/prefusion_264270_output_watch/`

Only the clean completed one-hit runs are admitted. Interrupted exploratory
runs are not evidence dependencies.

## Static Assembly

The verifier pins:

```text
libcp SHA-256:
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9

0x264270..0x2643c7 SHA-256:
acde803cf7789e4ccf0c61450feb6e83d827f7c95d2a4312724b0f35e22b2cda

0x23faf0..0x23fbd0 SHA-256:
d07dbe6d5b04ffae62e114283c13a04e0c2b14d85741c0ab7932c105aeba6472

0x2404b5..0x2404ca SHA-256:
a8a20e67d96580280c22e561dc258f94c748d870032125bc8e62b5546c43f7d8

wide 0x23a179..0x23a220 SHA-256:
a78734cbbabf871e40b1e936125aeb4cb74a4546c116105121ea441ce734b3c4

tele 0x20dbe0..0x20dc80 SHA-256:
d68d9fb771afc90b17938576ac1774fc2b45c06dd308bb27341584d71d9c8e28
```

At `0x264270`, `r15 = source object`, `rbx = output record`, and `r14d =
selector`. Three `0xf34e0` calls plus `0xf3360` / `0xf3350` assemble the
record. For the selector-1 source bank admitted by the preceding proof, the
first 84 output bytes are reconstructed as:

```text
output +0x00..+0x23 = bank +0x00..+0x23
output +0x24..+0x2f = bank +0x48..+0x53
output +0x30..+0x53 = bank +0x24..+0x47
```

The verifier reconstructs this prefix from the runtime source-bank snapshot
and requires exact equality at `0x2643c6`.

## First Consumer

The hardware watch arms on the completed `0x264270` output record only after
the matched function return. Every focal tier stops once at `0x23fb26` with
unchanged watched bits.

Static `0x23faf0` begins:

```text
0x23fb04  rbx = rdx
0x23fb0e  r12 = rdi
0x23fb1b  copy source +0x20
0x23fb23  load source +0x00..+0x0f
0x23fb26  load source +0x10..+0x1f
0x23fb2a  store destination +0x10..+0x1f
0x23fb30  store destination +0x00..+0x0f
...
0x23fb63  store destination +0x30..+0x3f
```

At the watch stop, runtime `rbx` exactly equals the tracked `0x264270` output
address. The watch reports PC `0x23fb26` after the preceding
`0x23fb23` source read.

At `0x2404b5`, the composer moves destination `r12` to return register `rax`.
A second one-hit watch is armed at pre-epilogue site `0x2404b8` on that exact
destination.

## Four-Zoom Routes

| Tier | Assembly-output consumer | Caller route | Composer-destination consumer |
|---|---|---|---|
| `28mm` | `0x23fb26` | `0x239e00 -> 0x239ac0 -> State 0x22d250` | `0x23a181` |
| `35mm` | `0x23fb26` | `0x239e00 -> 0x239ac0 -> State 0x22d250` | `0x23a181` |
| `70mm` | `0x23fb26` | `0x20afb0 -> 0x20ada0 -> State 0x22ae60` | `0x20dbf3` |
| `150mm` | `0x23fb26` | `0x20afb0 -> 0x20ada0 -> State 0x22ae60` | `0x20dbf3` |

The runtime pointers differ by process and are not constants. The stable fact
is exact address equality within each run and the repeated wide/tele caller
split.

For wide tiers, watch stop `0x23a181` follows `0x23a179`, which reads the
composer destination's first float from parent local `[rbp-0x110]`. Adjacent
loads copy additional fields into a local score-input block before the visible
`0x23a200` positive-pair scoring loop.

For tele tiers, watch stop `0x20dbf3` follows `0x20dbef`, which reads the
composer destination through runtime `rsi`. Static helper `0x20dbe0` combines
successive scalar fields from `rsi` with three SIMD rows from `rdx`, writing
three composed vectors to `rdi`.

Every second-phase watch observes unchanged bits. These consumers establish
transform/score-state use, not image-buffer use.

The preceding accepted-bank proof already includes an exact-focal Unit-2
`35mm` discriminator for the selector-1 bank-to-`0x264270` edge. This
follow-up tests all four canonical focal tiers because its new risk is the
wide/tele State-route split; it does not repeat four Unit-2 renders.

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
28mm: source_object=0x7f89bc729c00 output_record=0x304c680e8 composer_destination=0x304c68190 first_consumer=0x23fb26 route=0x239e00->0x239ac0->State0x22d250 composer_consumer=0x23a181 composer_route=0x239e00 local score-input load
35mm: source_object=0x7f8e7da125c0 output_record=0x304c680e8 composer_destination=0x304c68190 first_consumer=0x23fb26 route=0x239e00->0x239ac0->State0x22d250 composer_consumer=0x23a181 composer_route=0x239e00 local score-input load
70mm: source_object=0x7f7ce7247360 output_record=0x304c68450 composer_destination=0x304c684f8 first_consumer=0x23fb26 route=0x20afb0->0x20ada0->State0x22ae60 composer_consumer=0x20dbf3 composer_route=0x20dbe0 matrix composition
150mm: source_object=0x7fa2b8837420 output_record=0x304c68450 composer_destination=0x304c684f8 first_consumer=0x23fb26 route=0x20afb0->0x20ada0->State0x22ae60 composer_consumer=0x20dbf3 composer_route=0x20dbe0 matrix composition
```

## Safe Conclusion

The exact record assembled by `0x264270` from an accepted `0x216f60`
selector-1 destination bank is immediately consumed by `0x23faf0` and copied
into that composer's destination on every canonical focal tier. The composer
destination is then consumed as wide score-input state or tele
matrix-composition state. Wide and tele tiers use distinct State/helper routes.

This closes one more internal custody boundary. Public record semantics,
downstream image/source contribution, distributed reducer closure, and final
merge acceptance/rejection remain open.
