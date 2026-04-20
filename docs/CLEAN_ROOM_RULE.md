# Phoenix Clean-Room Rule (Rule #0)

**Phoenix is a clean-room reimplementation. Phoenix does NOT link against, `dlopen`, bundle bytes from, or otherwise depend on `libcp.dylib`, `Lumen.app`, or any other Light Inc. proprietary binary — at build time OR runtime.**

## What this means for the implementer

All VAs cited in `phoenix-pipeline-facts.md` are **reverse-engineering references only**. They tell you where to read the reference algorithm in a disassembler, NOT which bytes to copy into Phoenix's binary.

Every constant Phoenix needs must come from one of three sources:

1. **Parsed from the input LRI file at render time.** Calibration blocks (vignetting, CRA, CCM, geometric, per-camera black/white levels), Block 8 AWB gains, LightHeader per-capture metadata. LRI files travel with their own factory calibration.
2. **Published / derivable / CIE-standard values.** Wyszecki-Stiles Robertson tables, standard illuminant xy coordinates, CIE constants, sRGB conversion math.
3. **Reimplemented from scratch based on a documented algorithm in phoenix-pipeline-facts.md.** "Hamilton-Adams green interpolation with gradient-weighted directional selection" is an algorithm name you code from scratch, not "the bytes at VA 0x2eeb20."

## Things that MUST NOT ship with Phoenix

- Tone curve LUT bytes copied from libcp's `__TEXT __const` at 0x5e31b0 / 0x5e41b4 / 0x5e51b8 / 0x5e61bc
- Robertson forward-lookup table bytes copied from bss at 0x66d420
- Pre-shaper constants at 0x5e3180, illuminant xy tables at 0x5ab720 / 0x5ab760, CCT constants at 0x5ab180 / 0x5aae64, or any other rodata literal read out of libcp
- `cal_color_l16_02130.npz` or any pre-extracted calibration archive — these are per-device, per-LRI, and MUST be parsed from each input file at render time

## Legal caveat

Tone curves and the Robertson forward table sit in a grey zone. They may be "device firmware characterization constants" (shippable with provenance) or "app-level Lumen IP" (not shippable). **Phoenix distribution is blocked on a legal decision.** See open item #27 in `phoenix-pipeline-facts.md`.

Technical mitigations if shipping is disallowed:
- User supplies their own copy of libcp for local extraction at install time
- Phoenix recomputes an equivalent tone curve from a published formula
- Phoenix uses a user-configurable open curve (ACES, Rec709) with documented deviation from Lumen

## Reverse-engineering vocabulary in this handoff

- "**VA 0xNNNN**" = reference location in libcp.dylib for reading the algorithm. NEVER "bytes to copy."
- "**closure +0xNN**" = field the reference kernel reads from its own closure. Phoenix reimplements the closure layout from scratch.
- "**Block N of LRI**" or "**LightHeader.field_X**" = parsed from the input LRI file at runtime. This IS Phoenix's real runtime data source.
- "**port verbatim**" language from earlier draft revisions was a mistake and has been removed. Read any remnant as "reimplement based on the documented algorithm."
