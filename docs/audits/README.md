# Audit Artifact Boundary

This folder is the repo-owned home for investigation audits that must survive
across sessions.

## Rule

Durable audit artifacts must not live in `/tmp` or `/private/tmp`.

Use these locations instead:

- `docs/audits/` for committed audit registers, sweep summaries, and
  contradiction maps.
- `docs/evidence/` for committed proof documents that can feed the canonical
  ledger.
- `tools/lldb_probes/` for reusable LLDB probe harnesses.
- `runs/<topic>/` for rerunnable raw probe outputs that are useful locally but
  intentionally ignored by git.

`/tmp` and `/private/tmp` may be used only as operating-system scratch during a
single command. They are not stable evidence locations and must not be cited as
live dependencies in handoffs, canonical docs, or specs.

## Historical `/tmp` References

Some older evidence docs truthfully record that a historical probe wrote raw
packets under `/private/tmp`. Those references are provenance notes only. They
are not durable inputs unless the proof doc embeds the verified packet facts or
points to a repo-local probe that can reproduce the observation.

If a historical `/tmp` artifact is needed again, rerun or reconstruct the
investigation and write the durable result here or in `docs/evidence/`.

## Registers

- `codex_deterministic_reaudit_2026-06-01.md` — deterministic re-audit of the
  2026-05-31 Opus/Claude work: reran the nine local verifier scripts,
  independently re-read corrected VAs, swept for hypothesis contamination, and
  audited commit range `3559b65..aa9904c`.
- `codex_opus_quarantine_validation_2026-06-04.md` — Codex validation against
  Opus quarantine branch `research/opus-quarantine-2026-06-02`; records the
  first independent static re-extraction of the terminal IRAMP candidate
  cluster plus a first four-zoom runtime harness, while keeping full
  reducer/magnitude semantics explicitly unadmitted.
- `untracked_lri_verifier_quarantine_2026-06-05.md` — custody note for six
  loose untracked LRI/protobuf verifier scripts moved into
  `tools/quarantine/lri_field_verifiers_2026-06-05/` as candidate material only,
  with no claim admission.
- `implementation_repair_handoff_2026-07-16.md` — reconciles the failed
  `/Users/ryaker/L16_Phoenix` implementation against TRUTH v3.0.305, identifies
  stale gaps and invented parity-path substitutions, and maps each required
  repair to current admitted claims/evidence. It is an implementation audit,
  not a new truth or spec authority.
- `phoenix_implementation_reconciliation_2026-07-29.md` — pins the current
  Phoenix source snapshot against TRUTH v3.0.342, records the still-unwired
  selected cross-talk and MonoFusion flow/public-operand path, the duplicated
  source affine and wrong luma weights, and the now-removable exact-reciprocal
  portability waiver. It is an implementation audit, not claim evidence.
- `tele_band_53pct_reconciliation_2026-08-08.md` — independently re-audits the
  disputed Phoenix tele range-band statistic, refutes the global-vs-local bound
  contradiction, records why the historical `53.1%` is not reproducible from
  retained artifacts, and defines the stage-matched capture needed to localize
  the current tele residual.
- `phoenix_metric_claim_sweep_2026-08-08.md` — adversarially sweeps the live
  Phoenix Pearson/within-N/flip/null narrative, separates retained measurements
  from admissible conclusions, control-validates the Unit-2 tele repeat, and
  records the still-mixed candidate corpus generation.

## Verified Cleanup Note

On 2026-05-13, the session handoff referenced:

- `/tmp/l16_audit_sweep.sh`
- `/tmp/l16_open_audit/_FINDINGS.md`
- `/tmp/l16_open_audit/NN_TOPIC.txt`

Direct file-existence checks showed those paths were not present under `/tmp`
or `/private/tmp` during this session. They must therefore be treated as
unavailable historical references, not active evidence.
