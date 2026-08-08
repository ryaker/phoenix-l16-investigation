# CalibDataProcessor Public State-Machine Identity

## Question

Name the overall owner and public role of the previously described 13-body
calibration State machine.

## Reusable artifacts

- `tools/lldb_probes/calibdataprocessor_public_identity/verify_calibdataprocessor_public_identity.py`
- `tools/lldb_probes/state_machine_return_runtime/`
- ignored reports under `runs/state_machine_return_runtime/`
- prior static body bounds in
  `bundle_proof_calibdataprocessor_lambda_family.md` and
  `bundle_proof_state_machine_terminal_22e1d0_static.md`

Reproduce:

```bash
python3 tools/lldb_probes/calibdataprocessor_public_identity/verify_calibdataprocessor_public_identity.py
```

## Installed public identity

The 13 installed `std::__function::__func` RTTI records name one exact owner:

```text
lt::CalibDataProcessor
```

They split into these owner methods:

```text
lt::CalibDataProcessor::runReferenceGroupCams::$_0 .. $_6
lt::CalibDataProcessor::runHigherGroupCams::$_7 .. $_12
```

Every callback signature returns the public nested type:

```text
lt::CalibDataProcessor::State ()
```

The verifier checks every RTTI owner/method/ordinal, every vtable `+0x30`
operator slot, and all 13 installed bodies from `0x229df0` through
`0x22e1d0`. It also pins dispatcher `0x22f0f0` through its installed
`"State machine"` and registration-error labels plus the indirect-call /
returned-State store instruction bytes at `0x22f3f6..0x22f3ff`.

## Runtime scope

Complete accepted no-auto-LRIS bridge HDR reports for `28mm`, `35mm`, `70mm`,
and `150mm` each:

- pair 38 dispatcher pre/post calls;
- exercise all 13 RTTI-bound operator bodies;
- exit `0` with no probe errors or step-cap truncation; and
- write a populated Radiance HDR.

## Admission boundary

The whole-state object's public identity is therefore:

> `lt::CalibDataProcessor`, a camera-group calibration processor whose
> `runReferenceGroupCams` and `runHigherGroupCams` methods register and execute
> `CalibDataProcessor::State()` callbacks through the shared State-machine
> dispatcher.

This closes checklist B4's class/method/RTTI identity. It does not assign
semantic enum labels to the numeric values returned by `State()`, and it does
not turn the State-machine family into the still-unproven `src1`/`src2`
reducer.
