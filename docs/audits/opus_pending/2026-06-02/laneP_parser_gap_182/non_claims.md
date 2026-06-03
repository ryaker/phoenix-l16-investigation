# Lane P — Non-claims

1. **NOT claimed that the 182 belong to Unit-1 or Unit-2.** They cannot be unit-fingerprinted by the
   field-13 intrinsics method (no such block exists in them). This packet establishes only that they yield
   **no** signature and therefore introduce **no third unit**. Their actual unit identity is unknown.

2. **NOT claimed the 182 lack per-camera calibration entirely.** They lack a 16×field-13 intrinsics
   *block*. Whether per-camera calibration exists under a different proto field/structure (assignable by an
   extended parser) is OPEN. The L16_00795 single block parsed to no recognized fields, suggesting a
   different proto/layout the current field map doesn't cover.

3. **NOT a parser fix.** The 90 early-walk-termination files were re-parsed by magic-scan here only to test
   for hidden intrinsics/third-unit; this packet does not fix `lri_field_inspect.scan_lri_blocks`.

4. **NOT a claim about what these files are** (capture mode, bridge vs non-bridge, preview, etc.). Only the
   block/field structure was characterized.

5. **Scope:** the integrity claim is "no third unit signature among the 182" — deterministic and complete.
   Everything else (their identity, content type, recoverability) is explicitly left open.

6. Deterministic data analysis only; reproducible via `commands.txt`. `NEEDS_CODEX_VALIDATION` (re-run to
   confirm the counts).
