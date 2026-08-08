# Editor RenderingMode enum, dispatch, DebugView census, and default QuickSelect

## Result

Installed Lumen Qt metadata, installed libcp dispatch, and controlled runtime
captures close the public editor rendering-mode identity and top-level route:

| value | public `ImageEdit::RenderMode` | installed entry | tested primary route |
|---:|---|---:|---|
| `0` | `Normal` | `0x3bb524` | `DOFCache` when the admitted threshold passes |
| `1` | `RefocusPoint` | `0x3bb588` | `DOFCache` when depth is ready and the threshold passes |
| `2` | `RefocusSlider` | `0x3bb5fa` | `PipelineCache`, followed by a distinct focus visualization |
| `3` | `DebugView` | `0x3bb718` | selected object from an 11-entry debug tree |
| `4` | `QuickSelect` | `0x3bb76d` | `DOFCache`, followed by a DepthEditor byte-mask overlay |

`ImageEditItem::setRenderMode` forwards the enum unchanged to
`ImageEditor::setRenderingMode`, which forwards it unchanged to public
`CIAPI::Renderer::setMode`. The libcp five-way jump table resolves exactly to
the entries above.

Runtime scope is one Unit-1 `28mm`, profile-3, RenderType-1, five-level
treatment with `MaximumInFocusBlurPixels=9`, public `f_num=2`, and public
center-derived `focus_depth=6020.888671875 mm`. This bundle does not close the
mode-2 visualization formula, the formulas or public meanings of the eleven
debug objects, the internal QuickSelect segmentation formula, committed-
selection semantics, edit history semantics, or other body/focal runtime.

## Installed proof

Installed identities:

```text
libcp  b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
Lumen  1cd727486f9b21c4eacab4a99cff4a85f3c1c3f5e4f3a78b76617ec12438065d
```

Pinned ranges:

| Binary/range | Role | SHA-256 |
|---|---|---|
| libcp `0x3bb4f2..0x3bc13d` | five-mode renderer body | `2028df3497459309c77869701f83f46b41b71c16a0d4677aa53fdda3243fa55f` |
| libcp `0x3b0dd0..0x3b155e` | 11-object debug-tree construction | `da283ba71a2c4d55d987489a261ec88aa5fb38b6349f8facc7dbd1b43d7ecace` |
| libcp `0x3b8970..0x3b8a99` | renderer defaults | `3dade3831d235eb2a3e83d24171712a6b27d4a809a53057443ee506f55872d56` |
| libcp `0x3c5ed0..0x3c5fc4` | public `ParamInt` setter | `0127af1688f0bbb09045753b09d497bdeebc9ee7aaaaa3e4021ac7069055319b` |
| libcp `0x396120..0x396130` | public QuickSelect wrapper | `66c80e744188f5938e96db3d4c84120bf48369172dfb40a3e81f59092cec7687` |
| libcp `0x3a7150..0x3a7820` | QuickSelect packet validation/generator driver | `9cf0cb46996ec9f7e7e6b23833b7fca4f1816c5768da55179d96ebf824582c8a` |
| libcp `0x3bbf37..0x3bc0e6` | QuickSelect mask overlay | `9f83060846505e08f5a9adb3cbcc45b0925f893b86e374897e08558a93b8b3ed` |
| Lumen `0x2c670..0x2c6b4` | `ImageEditItem::setRenderMode` | `586cbc33c3cfbe0ac9d0bd8d68cd4e43d534437069bca393be7ffbfe639640bd` |
| Lumen `0x68c80..0x68c9c` | `ImageEditor::setRenderingMode` | `23bd284c8ea1e2e0c3d28f1b97650d8a3cdf38ee975cbea1befa2320caf2a56c` |
| Lumen `0x31350..0x315fe` | public QuickSelect packet construction | `7fb63907a8e80c5d2105440b177affecf5e22464d0effaca4951e5f602af7291` |
| Lumen `0xcc52f0..0xcc53d8` | `qt_meta_data_ImageEdit` | `825c126e69e99011e3b360a6c63477067fe0464044e30a46bc895255a5166897` |

The verifier parses the Qt 5 string records and enum table rather than relying
on a disassembly label. The exact five jump-table words at `0x3bc480` are:

```text
a4f0ffff 08f1ffff 7af1ffff 98f2ffff edf2ffff
```

as signed offsets from the table base. Public `ParamInt(20)` subtracts `10`,
uses table index `10`, and lands at `0x3c5f48`, which stores the selected
DebugView integer in request state `+0x80`.

## Five-mode runtime census

Each treatment first prepares the complete five-level mode-0 state and then
performs the requested treatment. Counts below are classified calls to the
cache read boundary; the common 388 mode-0 PipelineCache calls are the initial
preparation pass.

| requested mode | treatment calls | retained level-4 SHA-256 |
|---:|---|---|
| `0` | `388 mode0_dof`, `388 mode0_pipeline` | `4c0441433388fa4f3364319e2d22ea1970e964837fb1055264e0d69c657816c0` |
| `1` | `388 mode1_dof`, `388 mode0_pipeline` | `4c0441433388fa4f3364319e2d22ea1970e964837fb1055264e0d69c657816c0` |
| `2` | `388 mode2_pipeline`, `388 mode0_pipeline` | `a726066884c63f86efc177a954418d98010ba87136f7d95ff7d6ce2334907628` |
| `3`, selector unset | `388 mode0_pipeline`, no debug target | `0e9b834fc7bc5c5854fe83ed4c87f9688c74991917647a90da078d00872f9c8a` |
| `4`, default mask | `388 mode4_dof`, `388 mode0_pipeline` | `4c0441433388fa4f3364319e2d22ea1970e964837fb1055264e0d69c657816c0` |

Every output is packed `652x489`, stride `2608`, pixel-format integer `0`,
and size `1,275,312` bytes. The unset DebugView selector is `-1`, misses on all
388 requests, and takes the exact zero-fill fallback; every retained output
byte is zero. RefocusSlider is distinct from Normal. Its packed channel ranges
are `[0,208]`, `[0,255]`, `[0,255]`, and constant alpha `255`; these are
incidence measurements, not its formula.

## Complete DebugView selector census

The live debug tree reports size `11`. The following eleven unique requested
keys all match on 388/388 requests, so the successful-key set exhausts the
live tree. Each key selects one stable virtual target and produces a distinct
retained level-4 output:

| key | selected target | output SHA-256 |
|---:|---:|---|
| `0x300c` | `0x42c140` | `a958af3506d0c138ea8f120df45bd520e38e8ea82c91dcdfa7fc5e2c5139104a` |
| `0x300d` | `0x42c140` | `361d92bc68dce5a74cbfd510e730cecd7a44a4fb311f2081e2a801542dc5ebf7` |
| `0x300e` | `0x42c140` | `332a786c69b1dfa50e13b736549f667ea1eb20c1d6369330f148f7509082df06` |
| `0x3017` | `0x42fb40` | `c97c3c7f3e8f38d1f0eb057802ef056cdb4b31a987ce8895836d943cbd1dc104` |
| `0x3018` | `0x42d8d0` | `e273c72c326975d9e2f54bd00ee8720acd94383b72d150cb49e9e5bb1c429b83` |
| `0x3019` | `0x42c8f0` | `14af19c08431e41fbab91751193897c68d7f74f4e6d6988af70a43077bae6c47` |
| `0x301a` | `0x42fd30` | `1e56efc8e93b4499506280918ff5b27d554ffce1395b72b9f459409fcdee867a` |
| `0x301b` | `0x42c8f0` | `d6e8590444315141d040499a0a32a7de2623af6bf7dc3c557f6464579d887078` |
| `0x301c` | `0x42c8f0` | `f7683607264ed3660ad896a9840a7b01f01c8671554b163fbbc5e78e168f88fe` |
| `0x301d` | `0x42c8f0` | `92b9400fc4fabc4b0e69176fa6ab3b3f5222bd1d248291a502d3d7e598e52e87` |
| `0x301e` | `0x42ecb0` | `7dc934f6587762499f63df1445888fce8683c5d15cf4e51ab975eee9550b452a` |

Target `0x42c140` joins the separately admitted
`lt::HigherWarpDebug::renderDebugView` surface. Its prior zero-hit bridge-HDR
census was therefore a path exclusion, not global dead code: explicit editor
DebugView activation reaches it here.

## Default QuickSelect mask and final blend

The tested default DepthEditor selection image is `5216x3912`, stride `5216`.
All 388 reads inspect all `20,404,992` bytes and find `nonzero=0`, `min=0`,
and `max=0`. Live `RendererPrivate+0x8c0` is exact float32
`[1,0,1,0.25]`.

For output pixel `(x,y)` in rectangle origin `(x0,y0)`, base level dimensions
`(baseW,baseH)`, mask dimensions `(maskW,maskH)`, mask byte `b`, input vec4
`src`, and `C=[1,0,1,1]`, installed `0x3bbf37..0x3bc0e6` computes:

```text
mx = trunc(float(x + x0) * float(maskW) / float(baseW))
my = trunc(float(y + y0) * float(maskH) / float(baseH))
b  = mask[my*stride + mx]
a  = float(b) * 0.25
dst = (1 - a)*src + a*C
```

The observed all-zero mask therefore makes the blend an exact no-op. The
retained mode-4 packed output is byte-identical to the matching mode-0 output.
This control does not establish the value range or producer semantics of an
active mask; the treatment below supplies the first active observation.

## Active QuickSelect treatment

Installed `ImageEditItem::addQuickSelectStrokes` proves the public
`CIAPI::QuickSelectDepthEditingParams` layout:

| offset | field |
|---:|---|
| `+0x00` | `vector<Point<float>>` strokes |
| `+0x18` | normalized radius float |
| `+0x1c` | mode Boolean |
| `+0x20` | four-int level rectangle |
| `+0x30` | level index |

The private driver requires at least two points, `0 < radius < 1`, a
nonnegative rectangle origin, and an endpoint no larger than the selected
level dimensions. The app multiplies its UI radius by exact float32
`0.0010000000474974513` before forming this packet.

The controlled active treatment uses:

```text
points = [(0.49,0.5), (0.51,0.5)]
radius = 0.02
mode = true
level rectangle = [0,0,5216,3912]
level = 1
```

It produces exact binary byte data:

```text
dimensions = 5216x3912, stride 5216
nonzero = 32,268
value set = {0,1}
nonzero bbox = [2489,1873]..[2733,2036]
SHA-256 = 557a4e37597217455b0d77a7e20e9d1f19e64ff4b3de8b73eeaa939d4390633e
```

At output level 4, the installed formula samples mask coordinate `(8*x,8*y)`.
Exactly 501 output pixels sample a one. Comparing retained active and default
mode-4 packed outputs gives exactly the same 501-pixel support: no changed
pixel samples zero, no selected pixel remains unchanged, and alpha is
unchanged. There are 1,498 changed RGB bytes with maximum absolute delta `64`.
The active output SHA-256 is
`6cbaa0eaf9f2709f50705091f3a18a451e56e308338e1fcc3ce4ebf859d7eaef`.

This proves one accepted public packet, binary mask range for that treatment,
exact mask-to-output coordinate support, and final packed-image effect. It
does not close the internal segmentation helpers, generalize all masks to
binary, name the Boolean semantics, or close
`pushQuickSelectDepthEdit(float)` commit behavior.

## Reproduction

```bash
for mode in 0 1 2 3 4; do
  bash tools/lldb_probes/editor_render_type_topology/run_editor_cache_route_mode.sh "$mode" 9 sweep 2
done

for key in 0x300c 0x300d 0x300e 0x3017 0x3018 0x3019 0x301a 0x301b 0x301c 0x301d 0x301e; do
  bash tools/lldb_probes/editor_render_type_topology/run_editor_cache_route_mode.sh 3 9 sweep 2 "$key"
done

bash tools/lldb_probes/editor_render_type_topology/run_editor_cache_route_mode.sh 4 9 sweep 2 '' quick

python3 tools/lldb_probes/editor_render_type_topology/verify_editor_rendering_modes.py
```

Reusable machinery is under
`tools/lldb_probes/editor_render_type_topology/`; raw reports and buffers are
under ignored `runs/editor_render_type_topology/`.

## Scope guards and admission recommendation

- Runtime scope is one Unit-1 `28mm` treatment with the exact settings above.
- Public enum, forwarding, dispatcher, ParamInt selector, and blend formula
  are installed-static scope for the pinned binaries.
- Route counts are treatment incidence, not global algorithm constants.
- Exact RefocusSlider visualization math, exact DebugView object formulas and
  public meanings, internal QuickSelect segmentation and committed-selection
  semantics, edit history, other bodies/focals, and general editor parity
  remain open.
- Admit as a `CLM-COMPAT-001` addendum and keep the parent `PARTIAL` /
  `REFERENCE_ONLY`; this is not a base profile-3 bridge-merge blocker.
