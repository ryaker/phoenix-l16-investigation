# Evidence Directory

This directory is intentionally empty (except for this README). The real evidence files live at:

```
/Volumes/Dev/lumen-phoenix-scratch/
```

## Why not copied/moved into the repo?

1. **Citation integrity**: `docs/TRUTH.md` cites evidence files by their full `/Volumes/Dev/lumen-phoenix-scratch/` path. Moving them would break those citations.
2. **Volume management**: the scratch directory includes sub-directories with large binaries (puzzle_pieces/, q123/ thumbnails, per-camera PNGs) that don't belong in git.
3. **Cross-tool visibility**: LLDB probe scripts, agent sessions, and other tools read from the scratch path. Centralizing as a symlink would still work, but the above two reasons make "leave in place" the cleaner choice for now.

## Reading discipline

- Read an evidence file ONLY when `docs/TRUTH.md` explicitly cites it by path.
- Do NOT browse the scratch dir looking for "more context" — that re-introduces contamination. Evidence files are individual investigations, often superseded by later ones. The TRUTH doc is the integration; evidence is the raw support.
- If you find evidence that contradicts TRUTH.md, flag it. Do not silently update TRUTH.md based on a single evidence file.

## Key evidence groups (for orientation only — read by TRUTH.md's citations)

| Group | Files | Topic |
|-------|-------|-------|
| IRAMP | iramp_*.md, image_resolution_amp_verification.md, composite_anchor_n1_reducer.md | Cross-camera merge architecture |
| Per-camera ISP | refcache_per_camera_isp.md, color_pipeline_audit.md | Per-camera pipeline stage order |
| CCM | ccm_*.md, cct_and_awb_auto.md, per_camera_ccm_matmul.md | Color correction + CCT blending |
| BLC / linearize | blc_*.md, session5_lambda0_linearize.md | Black level + linearization |
| Tone curves | session6_tone_curve_fit.md, tmo_chroma_post.md, tone_curve_*.md | light_v1 Hable fit |
| Depth | stereo_*.md, sgm_runpass_verified.md, vst_*.md, pyramid_*.md | Depth solver (Ceres pass C + Triangulator) |
| Anchor/composite | anchor_prefusion_and_c6.md, a2_destination.md, c6_destination_and_depthcache.md | 6-camera fusion set, A2/C6 filter |
| 35mm crop | 35mm_crop_math.md, 35mm_renderer_mechanism.md | Two-tier focal-length table |
| Legacy audit | legacy_doc_audit.md, legacy_doc_audit_round2.md | Prior rounds of contamination cleanup |

## Transcripts (even deeper raw evidence)

`~/.claude/projects/-Users-ryaker-Dev-L16-Lumen-ReverseEngineering/*.jsonl` — 282 MB of agent conversation transcripts with embedded LLDB output and reasoning. Source for the scratch .md summaries.
