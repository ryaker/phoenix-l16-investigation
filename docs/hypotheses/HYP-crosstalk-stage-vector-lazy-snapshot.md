# HYP: Cross-Talk Stage-Vector Backing Dumps Are Not Synchronized Pairs

## Status

Hypothesis only. This document carries no ledger authority.

## Observation

The selected-color stage-vector probe captures descriptor backing allocations
when one callback thread reaches consecutive pipeline stages. Replaying the
admitted cross-talk formula from the stage-5 `payload+0xd0` dump into the
stage-6 `payload+0xd0` dump fails essentially every tested word, even after
applying the mapped-rectangle origin cancellation already proved for the lens
worker.

This does not contradict the selected cross-talk formula. Two stopped
same-thread `0x1019d0` helper packets independently replay all
`67,600/67,600` words exactly, and the public matrix/IR preparation replays
exactly. The stage-vector artifacts were admitted only for stage order,
normalization, and stable lens-worker tiles; they were never admitted as a
synchronized whole-allocation cross-talk before/after pair.

## Provenance

Codex produced this hypothesis on 2026-07-29 while attempting a new
multi-cell replay from existing stage-vector artifacts. A temporary verifier
tested the common `508 x 508` interior of Unit-1 A1 and failed
`258,063/258,064` words before the invalid oracle path was stopped and the
temporary verifier removed. This is one diagnostic experiment over a backing
allocation, not task-identity proof.

## Why It Is Not Fact

No captured task identifier, completion barrier, or same-thread worker
entry/return pair currently joins the two whole backing-store dumps. The
lazy/concurrent explanation is plausible and consistent with the executor,
but has not been directly observed.

## Working Explanation

The executor is lazy and tiled. Other tile jobs may populate or reuse the
descriptor backing allocations while the selected callback thread advances.
Therefore a whole backing-store dump at consecutive callback stops can mix
regions from different task completion states even when the descriptor object
itself is the correct selected payload.

## Proof Or Disproof Path

Use the extended
`tools/lldb_probes/correction_liveness/crosstalk_scalar_formula_probe.py`
helper-index selector. Each accepted packet must capture source, destination,
prepared matrices, coordinates, and output on one worker thread between
`0x1019d0` entry and its caller return. Capture nonzero helper indices that
select interior and lower-right matrix cells, then run
`verify_crosstalk_scalar_formula.py` independently on each packet.

Do not use `stage_05_before_slot_d0.bin` and
`stage_06_before_slot_d0.bin` as a pixel-aligned cross-talk pair unless a new
task-identity and completion-barrier probe proves that relationship.

## Disproof Criteria

Refute this hypothesis if a task-identity probe proves both stage dumps are
complete, immutable, pixel-aligned views of the same tile at the two stage
boundaries. In that case the multi-cell mismatch becomes evidence of a real
formula or coordinate omission and must reopen the relevant correction claim.

## Current Instrumentation Limitation

On 2026-07-29, fresh LLDB launches stopped inside `process launch` before the
probe could install, even with a module-scoped `main` breakpoint and after
stale debugserver cleanup. Existing captures remain valid; no failed launch
artifact is admitted. Retry the helper-index path when LLDB launch service is
healthy.
