# IRAMP Partner-Gate LLDB Probes

These scripts are reusable probe harnesses, not canonical truth.

Use the `gate_*_first_*.lldb` and `sad_first_*.lldb` scripts to collect runtime evidence for the IRAMP partner-vector short-circuit around `libcp+0x3692dc..0x3692e4` and the first SAD instruction at `libcp+0x3694b1`.

Do not use combined hot-breakpoint probes for this path. They can perturb `70mm` / `150mm` renders into the known `libcp+0x2e945d` instrumentation race.

Canonical admission still requires a separate evidence document under `docs/evidence/` and claim-ledger updates.

Outputs are written under `runs/iramp_partner_gate/`, which is ignored by git.
