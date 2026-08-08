# Installed-Bundle Proof: `0x20ca00` Solved-Record Range Custody

## Scope

This note traces the post-`ceres::Solve` triple written by the
`lt::Triangulator::refine3dPoints()` lambda callback at `0x20ca00` into its
immediate parent consumer.

It proves internal owner/vector custody and one concrete downstream scalar
effect. By itself it does not assign public names to the triple, prove runtime
values, or establish image/source contribution. Companion runtime proof now
supplies Unit-1 `28mm` solved-value/materialization samples in
[bundle_lldb_prefusion_20ca00_solve_output_28mm.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_prefusion_20ca00_solve_output_28mm.md).

## Repo-Local Verifier

`tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_record_range_custody_static.py`

The verifier reads the installed Mach-O directly, SHA-guards six independent
instruction windows, decodes them with Capstone, and checks every pointer,
stride, field, and consumer anchor used below.

## Machine-Verified Custody

### Parent owner to callback owner

The parent body beginning at `0x20bd60` preserves its incoming `rdi` owner in
`r15` at `0x20bd74`. Before executor dispatch, it stores that same `r15` at
callable field `+0x08` (`0x20c295`). The `0x20ca00` callback reloads
`callable+0x08` at `0x20ca2f` and stores it in local `rbp-0x2a8`.

This is a direct pointer chain:

```text
parent rdi -> parent r15 -> callable+0x08 -> callback [rbp-0x2a8]
```

### Owner vector to solved record

At `0x20d1d0..0x20d1da`, the callback dereferences the captured owner twice to
obtain the record-vector begin pointer. At `0x20d1dd`, it computes
`5 * index`; the later scale of four bytes makes the record stride `0x14`.
It saves the begin pointer in `rbp-0x2c8` and the `5 * index` offset in
`rbp-0x2d0`.

The post-solve address calculations at `0x20d616..0x20d62e` therefore resolve
to:

```text
record = vector_begin + index * 0x14
triple = record + 0x08, record + 0x0c, record + 0x10
```

The first transform writes those three fields at `0x20d6a8..0x20d6b1`; the
second transform overwrites the same fields at `0x20d729..0x20d732`.
The verifier also proves the only `rbp-0xc8` scalar access between the Solve
return and those writes is the read at `0x20d690`; there is no intervening
scalar store in the pinned window.

### Immediate parent consumer

After executor `0x5670` returns and callable cleanup completes, the parent
reloads the same vector header through `r15` at `0x20c330..0x20c336`.

The vectorized loop reads four `record+0x10` fields per iteration and advances
by `0x50`, exactly four `0x14` records. The scalar tail reads `[record+0x10]`
at `0x20c490` and advances by `0x14` at `0x20c4a5`. Nonpositive values bypass
the scalar min/max update. The resulting positive-value minimum and maximum
are stored to owner fields `+0x78` and `+0x7c` at `0x20c4ae` and `0x20c4b4`.

Thus the callback's final third triple component, `record+0x10`, has an
immediate concrete consumer: a positive-value range reduction written back to
the same owner.

## Admission Check

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_record_range_custody_static.py
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
parent_entry=0x20bd60..0x20bd81 sha256=b006ebb7fd90d3b134d4c92fb403a55aeab5bdf5b073074b9ee6d30aca774514
capture_dispatch=0x20c26a..0x20c330 sha256=31f14420213bfeb28ccced87d87e148aa4958f837494afc18f4e0d33302a3828
callback_owner=0x20ca14..0x20ca3a sha256=b376faed4ff3c139d6508c41ea97ab25c588c10cde858b05fa508f71b5afdc89
record_address=0x20d1d0..0x20d2af sha256=c0b561d3f8c660d4dd316492aa40d81d91913ac869e29a7ba66eb5f9c47eaf0b
postsolve_writes=0x20d616..0x20d737 sha256=66766b4529bd10e674c120a9f101beee3c0b51783b3038e3c130b63d84059c95
parent_scan=0x20c330..0x20c4ba sha256=9bdcc9c3c8bbbc1e780087428cb6d7be8cf7c402b7b043ba9ad349681665d408
owner=rdi@0x20bd74 -> callable+0x08 -> callback[rbp-0x2a8]
record_begin=**owner stride=0x14 selected_offset=5*index
postsolve_write=record[index]+0x08,+0x0c,+0x10
postsolve_scalar_window=read-only rbp-0xc8 before triple writes
parent_consumer=positive(record[*]+0x10) range -> owner+0x78,+0x7c
```

## Proven Facts

1. The parent owner pointer is captured at callable `+0x08` and reloaded as
   the callback owner at `rbp-0x2a8`.
2. The callback's solved triple belongs to the captured owner's `0x14`-stride
   record vector at selected record fields `+0x08/+0x0c/+0x10`.
3. After callback execution, the parent immediately scans field `+0x10` of
   that same record vector.
4. The parent reduces positive `+0x10` values to a minimum/maximum pair stored
   at owner `+0x78/+0x7c`.

## Safe Conclusion

The post-solve triple is no longer an ownerless internal write: its destination
is the captured owner's record vector, and its third component immediately
feeds a positive scalar-range reduction on that owner.

This closes internal record ownership and this immediate scalar consumer only.
Public calibration meaning, runtime solved values, later consumers of
`owner+0x78/+0x7c`, image/source contribution, reducer closure, and final
acceptance/rejection remain open.
