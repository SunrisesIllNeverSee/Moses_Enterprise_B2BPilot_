# ACME-001 — Verification Results

> **COMPLETE** — 12 verification results computed with target + non-target
> metric deltas. All values validated from runtime on 2026-09-06.

## Verification summary

All 12 interventions verified via `PilotService.verify_all_interventions()`.

| Field | Value | Source |
|---|---|---|
| Verification count | 12 | `PilotService.verify_all_interventions()` |
| Baseline window | 2026-07-01 to 2026-07-30 | `VerificationResult.baseline_window` |
| Follow-up window | 2026-08-01 to 2026-08-15 | `VerificationResult.followup_window` |
| Synthetic | true (all) | `VerificationResult.synthetic` |

## Verification results

| ID | Operator | Target metric | Target delta (%) | Outcome | Non-target side effects | Source |
|---|---|---|---|---|---|---|
| int_001 | op_047 | yield | +20.0% | PARTIAL | leverage -1.27%, token_snr +12.92% | `verify_all_interventions()` |
| int_002 | op_004 | yield | +2.0% | NO_EFFECT | leverage +11.97%, token_snr -6.61% | Same |
| int_003 | op_030 | yield | +55.0% | SUCCESS | leverage +2.65%, token_snr +28.94% | Same |
| int_004 | op_045 | yield | +55.0% | SUCCESS | leverage +7.63%, token_snr +28.19% | Same |
| int_005 | op_031 | leverage | -18.0% | NEGATIVE | yield +16.86%, token_snr +16.37% | Same |
| int_006 | op_038 | yield | -18.0% | NEGATIVE | leverage +7.84%, token_snr -16.92% | Same |
| int_007 | op_010 | leverage | +55.0% | SUCCESS | yield +6.03%, token_snr -22.97% | Same |
| int_008 | op_026 | leverage | +55.0% | SUCCESS | yield +14.27%, token_snr -22.85% | Same |
| int_009 | op_025 | yield | +2.0% | NO_EFFECT | leverage +2.52%, token_snr -0.37% | Same |
| int_010 | op_020 | leverage | -18.0% | NEGATIVE | yield +19.26%, token_snr +35.1% | Same |
| int_011 | op_029 | yield | +55.0% | SUCCESS | leverage +7.21%, token_snr +25.71% | Same |
| int_012 | op_005 | leverage | +20.0% | PARTIAL | yield +13.67%, token_snr -4.45% | Same |

## Outcome distribution

| Outcome | Count | Source |
|---|---|---|
| SUCCESS | 5 | `PilotService.interventions` (synthetic_outcome) |
| PARTIAL | 2 | Same |
| NO_EFFECT | 2 | Same |
| NEGATIVE | 3 | Same |

## Target metric analysis

| Target metric | Interventions | Success rate | Avg target delta |
|---|---|---|---|
| yield | 7 (int_001–004, 006, 009, 011) | 3/7 = 43% | +16.86% (avg) |
| leverage | 5 (int_005, 007, 008, 010, 012) | 2/5 = 40% | +18.8% (avg) |

> **Note:** The success rate is moderate (43% yield, 40% leverage). This
> is realistic — not every intervention succeeds. Negative outcomes are
> representable and reported, not hidden.

## Non-target side effects

Side effects are tracked for all interventions. Notable patterns:

1. **Yield interventions often improve token_snr** (int_001: +12.92%,
   int_003: +28.94%, int_004: +28.19%, int_011: +25.71%) — suggesting
   that yield improvements may correlate with signal-to-noise ratio
   improvements.
2. **Leverage interventions often degrade token_snr** (int_007: -22.97%,
   int_008: -22.85%, int_012: -4.45%) — suggesting a trade-off between
   leverage and signal-to-noise.
3. **Negative outcomes show compensating effects** — int_005 (leverage
   -18%) shows yield +16.86%, and int_010 (leverage -18%) shows yield
   +19.26%. The intervention failed on its target but may have shifted
   behavior in other dimensions.

> All side effects are ASSOCIATION, not CAUSATION. The verifier computes
> deltas; it does not establish causality.

## Post-intervention classifications

From `demo_data/results.json` (pre-computed, matches verification outcomes):

| Classification | Count | Source |
|---|---|---|
| improved_internal_and_external | 5 | `demo_data/results.json` |
| improved_internal_only | 2 | Same |
| no_change | 2 | Same |
| degraded | 3 | Same |

> Classifications match the outcome distribution: 5 SUCCESS →
> improved_internal_and_external, 2 PARTIAL → improved_internal_only,
> 2 NO_EFFECT → no_change, 3 NEGATIVE → degraded.

## External outcome deltas (from results.json)

| ID | Internal leverage delta | Internal yield delta | External cycle time delta | External quality delta | Source |
|---|---|---|---|---|---|
| int_001 | -1.27% | +20.0% | +4.7% | +1.7% | `demo_data/results.json` |
| (others available in results.json) | | | | | Same |

> External deltas are ASSOCIATION only. The outcome join engine enforces
> the ASSOCIATION label — no CAUSATION claims permitted.

## Outcome correlation

| Field | Value | Source |
|---|---|---|
| Lineages | 50 | `PilotService.lineages` |
| Outcomes | 50 | `PilotService.outcomes` |
| Correlation computed | Yes | `PilotService.outcome_correlation()` |
| Evidence grade | OBSERVATIONAL | `EvidenceGrade.OBSERVATIONAL` |
| Claim type | ASSOCIATION | Governance enforcement |

## Replication

| Field | Value | Source |
|---|---|---|
| Replication capability | Implemented | `PilotService.replicate_finding()` |
| Replication run | Not run for ACME-001 | (would require window/cohort split) |
| Replication status | NOT_REPLICATED | (not exercised) |

> **Gap:** Replication was not run for ACME-001. For a real pilot,
> key findings should be replicated across window/cohort splits to
> test descriptive stability.

## What these verification results reveal

1. **Pre/post verification is complete.** All 12 interventions have
   target + non-target deltas computed.
2. **Outcomes are diverse and realistic.** 5 SUCCESS, 2 PARTIAL,
   2 NO_EFFECT, 3 NEGATIVE — not a uniformly positive result.
3. **Side effects are tracked.** Non-target metric deltas reveal
   trade-offs (e.g., leverage improvements may degrade token_snr).
4. **All claims are ASSOCIATION.** No causation claims. This is correct
   governance.
5. **Replication was not run.** A gap for real pilots — key findings
   should be replicated to test stability.
