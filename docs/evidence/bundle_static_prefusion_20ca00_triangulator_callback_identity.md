# Installed-Bundle Proof: `0x20ca00` Triangulator Lambda Callback Identity

## Scope

This note corrects the coarse historical label that treated `0x20ca00` as the
entry of `Triangulator::refine3dPoints()`.

The installed binary instead identifies `0x20ca00` as the substantive
`+0x30` callback slot of a `void(int,int,int)` lambda defined inside
`lt::Triangulator::refine3dPoints()`.

This is callback identity and dispatch-topology proof. It does not by itself
name the callback's integer arguments, prove public acceptance semantics, or
close downstream image/source contribution.

## Repo-Local Verifier

`tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_callback_identity_static.py`

The verifier:

1. reads the installed Mach-O bytes directly,
2. checks vtable address point `0x657f00`, typeinfo pointer `0x657f50`, and
   substantive slot `+0x30 = 0x20ca00`,
3. reads and demangles the exact typeinfo name,
4. SHA-guards and independently disassembles the callback-construction window
   with Capstone,
5. proves `0x20c28b` installs address point `0x657f00`, and
6. proves `0x20c2f6 -> 0x5670` dispatches callable slot `+0x30` at `0x56e9`.

## Machine-Verified Identity

Raw typeinfo name:

```text
NSt3__110__function6__funcIZN2lt12Triangulator14refine3dPointsEvE3$_0NS_9allocatorIS4_EEFviiiEEE
```

Demangled type:

```text
std::__1::__function::__func<
  lt::Triangulator::refine3dPoints()::$_0,
  std::__1::allocator<lt::Triangulator::refine3dPoints()::$_0>,
  void (int, int, int)>
```

Vtable/callable facts:

```text
address point 0x657f00
  +0x30 -> 0x20ca00

0x20c28b: install address point 0x657f00
0x20c2f6: call executor 0x5670
0x56e9:   call [callable_vtable + 0x30]
```

The constructor stores eight captured pointers at callable fields
`+0x08..+0x40` before the executor dispatch. The already admitted local gate,
Ceres residual, solve, and post-solve formula evidence therefore belongs to
this named lambda callback family, not to an independently entered top-level
`0x20ca00` method.

## Admission Check

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_callback_identity_static.py
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
typeinfo=0x657f50 raw=NSt3__110__function6__funcIZN2lt12Triangulator14refine3dPointsEvE3$_0NS_9allocatorIS4_EEFviiiEEE
demangled=std::__1::__function::__func<lt::Triangulator::refine3dPoints()::$_0, std::__1::allocator<lt::Triangulator::refine3dPoints()::$_0>, void (int, int, int)>
address_point=0x657f00 slot_0x30=0x20ca00
dispatch=0x20c28b/address-point -> 0x20c2f6/0x5670 -> [vtable+0x30]
```

## Proven Facts

1. `0x20ca00` is callback slot `+0x30` of address point `0x657f00`.
2. The address point's typeinfo names a `void(int,int,int)` lambda inside
   `lt::Triangulator::refine3dPoints()`.
3. The parent construction window installs that address point, captures eight
   pointers, and dispatches through generic executor `0x5670`.
4. Executor `0x5670` invokes the substantive `+0x30` slot.

## Safe Conclusion

Use **Triangulator `refine3dPoints()` lambda callback** for `0x20ca00` in new
evidence. Historical variable names such as `Triangulator_refine3d` may remain
as provenance labels in old probes, but they are not exact function-entry
identities.

The callback's public argument names, public output meaning, runtime values,
downstream image effect, reducer closure, and final acceptance/rejection remain
open. Internal solved-record ownership is addressed separately by
`bundle_static_prefusion_20ca00_record_range_custody.md`.
