# Static + Runtime Evidence: Denoise Route / CNR Entry Parameters

## Scope

This bundle narrows `CLM-DENOISE-002`. It asks which denoise and
`ColorNoiseReduction` bodies are live on the canonical profile-3 bridge-HDR
route, and which entry parameters reach the live CNR body.

It does not decode the full `0x307ee0` / `0x3085a0`
`ColorNoiseReduction` worker formula, public-name the worker's internal
vectors, or prove body/firmware invariance for every possible LRI.

## Artifacts

- Probe harness:
  [denoise_route_census_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/denoise_route_census/denoise_route_census_probe.py)
- Verifier:
  [verify_denoise_route_census.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/denoise_route_census/verify_denoise_route_census.py)
- Unit-1 four-focal runners:
  [run_unit1_cnr_four_zoom.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/denoise_route_census/run_unit1_cnr_four_zoom.sh),
  [run_unit1_denoise_algo_four_zoom.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/denoise_route_census/run_unit1_denoise_algo_four_zoom.sh),
  [run_unit1_setdenoise_four_zoom.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/denoise_route_census/run_unit1_setdenoise_four_zoom.sh)
- Unit-2 exact-35mm control runner:
  [run_unit2_35mm_control.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/denoise_route_census/run_unit2_35mm_control.sh)
- Raw rerunnable reports:
  `runs/denoise_route_census/unit1_{28mm,35mm,70mm,150mm}_{cnr,denoise_algo,setdenoise}.json`
  and `runs/denoise_route_census/unit2_35mm_{cnr,denoise_algo,setdenoise}.json`

All runtime launches used `tools/lri_process`, profile `3`, export format `3`,
and `--no-auto-lris`.

## Static Pin

The verifier pins installed
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
at SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

It also verifies the installed RTTI names for `ColorNoiseReduction` and the
three `Pipeline::setColorNoiseReduction` closures. The static body hashes used
by this admission include:

| Range | SHA-256 |
|---:|---|
| `0x34b3f0..0x34b808` | `6f7ac1fc4faf18ccc4ef5c9b70dff4336a807ff53194efcb357ba25e467fbf0d` |
| `0x34b8a0..0x34b8ae` | `3f0d36a7821c312ba21322f86d38fd3c7abd516b1623d140b83517be02faa8c0` |
| `0x34b970..0x34b97e` | `da807245a672e5e59053caf759203375711558d3125ceadaf4891865891647a0` |
| `0x307ee0..0x308459` | `dfbaee4a6921cbac9c4d6da49e2306c19bb4e18710ab1f805dbddd6d64dcf254` |
| `0x308520..0x308567` | `e464875586d0a4f45738567d87dec65fabf39935a8d248fc885ba9a3a54b58c6` |
| `0x3085a0..0x308d00` | `9dd68fec69d6f63e5346f938d1ea7516bdab909050ef0c8c2015c159f99367d7` |
| `0x2f53d0..0x2f5ef0` | `14bf861649acec9c7e0375499a05a3b232104f74f1e496df853502fa96d61474` |
| `0x2f6420..0x2f68a0` | `5f28dc1fdbd035a13e71867718f6865cc1b3c43ebfa70869526f090ae2b7cbb0` |
| `0x2fb320..0x2fc11f` | `c6a6926cffdfa8f79b8f6c0caa4a65066ab0b7f42f7ce4e15dc95a1ed65b7861` |
| `0x2fd070..0x2fdce0` | `c4660f0f361c2a4e9886d125197181dab9f50b7757c5ce3032197c65f547860a` |
| `0x3066d0..0x306d40` | `bfebe7619117a2db022e28894a2dbc2456fe8f2d255306939a508675d91b3da8` |
| `0x3070e0..0x307d90` | `862f185f5d4cd3d365ebf5ff65091520b2697cdd9d83a1e8bf4c42a4b2a5ddbb` |
| `0x307d90..0x307ea7` | `1415cf342baae4666c4a15d84d99acb004eff16de46a3c71dd042643de8d5cab` |

`0x2fd070` is the slot `+0x30` worker of address point `0x65a868`, one of the
same `0x2f6420` callback-family arms previously classified in
[lldb_2f53d0_callback_bodies_static.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_2f53d0_callback_bodies_static.md).

## Runtime Route Census

All listed packets exited normally, had no probe errors, and did not hit the
drive step cap. Counts below are breakpoint counts for the targeted narrow
census groups, not global program call counts.

| Sample | `setDenoising` closures hit | Denoise algorithm bodies hit | CNR family and body args |
|---|---|---|---|
| Unit-1 `28mm` `L16_02130` | `0x345c80`, `0x345920`, `0x345a10` | `0x2f53d0`, `0x2f6420`, `0x2fb320`, `0x3066d0`, `0x3070a0`, `0x3070e0`, `0x307d90` | `0x34b970` family; `0x34b3f0 -> 0x307ee0 -> 0x308520 -> 0x3085a0`; args `(1.0, 1.0, 42, 1023)` |
| Unit-1 `35mm` `L16_03041` | `0x345c80`, `0x345920`, `0x345a10` | `0x2f53d0`, `0x2f6420`, `0x2fb320`, `0x3066d0`, `0x3070a0`, `0x3070e0`, `0x307d90` | `0x34b970` family; same body chain; args `(1.0, 1.0, 42, 1023)` |
| Unit-1 `70mm` `L16_03434` | `0x345ae0`, `0x345920`, `0x345a10` | `0x2f53d0`, `0x2f6420`, `0x2fb320`, `0x3066d0`, `0x3070a0`, `0x3070e0`, `0x307d90` | `0x34b8a0` family; same body chain; args `(1.0, 1.0, 42, 1023)` |
| Unit-1 `150mm` `L16_02285` | `0x345ae0`, `0x345920`, `0x345a10` | `0x2f53d0`, `0x2f6420`, `0x2fb320`, `0x3066d0`, `0x3070a0`, `0x3070e0`, `0x307d90` | `0x34b8a0` family; same body chain; args `(1.0, 1.0, 42, 1023)` |
| Unit-2 exact `35mm` `L16_01956` | `0x345c80`, `0x345920`, `0x345a10` | Unit-1 set plus extra `0x2fd070` | `0x34b970` family; same body chain; args `(1.0, 1.0, 43, 1023)` |

For Unit-1 four-focal reports, the other probed `0x2f6420` callback arms
`0x2f6ad0`, `0x2f78e0`, `0x2f87e0`, `0x2f97e0`, `0x2fa5d0`, `0x2fc140`, and
`0x2fd070` had zero hits in these narrow complete renders. The older
first-visible-`src1` proof already cautioned that zero-hit arm results are
tested-route facts, not global dead-code facts; the Unit-2 exact-35mm control
confirms that caution by hitting `0x2fd070`.

## Verifier Output

The repo-local verifier command:

```bash
python3 tools/lldb_probes/denoise_route_census/verify_denoise_route_census.py
```

currently reports:

```text
static_denoise_route=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
Unit-1 28mm L16_02130 CNR route census: CNR route OK first=0x34b970 args=(1,1,42,1023)
Unit-1 28mm L16_02130 denoise algorithm route census: denoise algorithms OK selected=0x2fb320+PatchNLM
Unit-1 28mm L16_02130 setDenoising closure census: setDenoising OK first=0x345c80 shared=0x345920,0x345a10
Unit-1 35mm L16_03041 CNR route census: CNR route OK first=0x34b970 args=(1,1,42,1023)
Unit-1 35mm L16_03041 denoise algorithm route census: denoise algorithms OK selected=0x2fb320+PatchNLM
Unit-1 35mm L16_03041 setDenoising closure census: setDenoising OK first=0x345c80 shared=0x345920,0x345a10
Unit-1 70mm L16_03434 CNR route census: CNR route OK first=0x34b8a0 args=(1,1,42,1023)
Unit-1 70mm L16_03434 denoise algorithm route census: denoise algorithms OK selected=0x2fb320+PatchNLM
Unit-1 70mm L16_03434 setDenoising closure census: setDenoising OK first=0x345ae0 shared=0x345920,0x345a10
Unit-1 150mm L16_02285 CNR route census: CNR route OK first=0x34b8a0 args=(1,1,42,1023)
Unit-1 150mm L16_02285 denoise algorithm route census: denoise algorithms OK selected=0x2fb320+PatchNLM
Unit-1 150mm L16_02285 setDenoising closure census: setDenoising OK first=0x345ae0 shared=0x345920,0x345a10
Unit-2 35mm L16_01956 CNR route census: CNR route OK first=0x34b970 args=(1,1,43,1023)
Unit-2 35mm L16_01956 denoise algorithm route census: denoise algorithms OK selected=0x2fb320+PatchNLM extra=['bilateral_arm_0x2fd070']
Unit-2 35mm L16_01956 setDenoising closure census: setDenoising OK first=0x345c80 shared=0x345920,0x345a10
denoise_route_census=OK
```

## Admission

This is an admitted `CLM-DENOISE-002` partial:

- Unit-1 canonical `28mm`, `35mm`, `70mm`, and `150mm` profile-3 bridge-HDR
  renders select the same denoise algorithm chain
  `0x2f53d0 -> 0x2f6420 -> 0x2fb320`, the live
  `ImageDenoiseNLM` positive body `0x3066d0`, and the PatchNLM callbacks
  `0x3070a0`, `0x3070e0`, and `0x307d90`.
- Unit-1 wide focals select `setDenoising` family `0x345c80`; Unit-1 tele
  focals select `0x345ae0`; all four share `0x345920` and `0x345a10`.
- Unit-1 wide focals select CNR family `0x34b970`; Unit-1 tele focals select
  `0x34b8a0`; all four reach common effective body `0x34b3f0`, CNR body
  `0x307ee0`, callback `0x308520`, and worker `0x3085a0` with entry args
  `(xmm0=1.0, xmm1=1.0, r9d=42, stack_i32_arg0=1023)`.
- Unit-2 exact `35mm` validates the same wide `setDenoising` / CNR family and
  body chain, but its CNR low endpoint is `43` and its denoise route also hits
  sibling `0x2fd070`. This is a body/sample discriminator, not a refutation of
  the Unit-1 four-focal route.

## Remaining Work

The parity blocker is narrowed but not closed. Still open:

- exact formula of the live CNR worker family `0x307ee0 -> 0x308520 ->
  0x3085a0`;
- public origins/names for the endpoint integers and any CNR object/vector
  parameters beyond the captured entry tuple;
- the condition that selects `0x2fd070` in Unit-2 exact `35mm`, and whether it
  is body, firmware, calibration, or content dependent;
- broader cross-body risk checks if the formula extraction shows additional
  body- or firmware-selected arms.
