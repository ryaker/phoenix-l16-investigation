# C6 context +0xa0 consumer probe

This probe checks whether the context object constructed at `ctx+0xa0` in the
tele C6 path is consumed by the candidate `0x3c9540 -> 0xe6c30` route under
canonical bridge HDR renders.

The probe is deliberately narrow:

- re-captures constructor custody of `ctx+0xa0`
- captures entry into `0x3c9540`
- captures the object pointer passed to `0xe6c30`
- captures the `0xe6c30` return byte for that invocation

It does not assert final image contribution or exclusion.
