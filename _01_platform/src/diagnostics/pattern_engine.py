"""Pattern engine — detects descriptive patterns from measurements.

Per `09_DIAGNOSTIC_INTERVENTION_REGISTRY.md`, detects these pattern families:
    P-CTX-01   — Low context leverage (leverage below reference band + adequate volume)
    P-CTX-02   — High reuse / low output (rich context, weak execution)
    P-BURN-01  — High usage / low operating metrics
    P-HIDDEN-01 — Low usage / high operating metrics
    P-MODEL-01  — Model sensitivity (within-operator differences by model)
    P-STAGE-01  — Stage specialization (stronger in one stage than another)

Rules (per `09`):
- A metric pattern is NOT a personality trait and NOT a causal diagnosis.
- Patterns are descriptive relationships among measurements.
- P-VAR-01 (high variability) requires canonical Stability/Volatility definition
  first — NOT implemented here (per `21` do-not-build-yet list).

Thresholds are configurable; defaults use cohort percentile bands.

P-MODEL-01 and P-STAGE-01 require per-segment observations (not just the
operator's window-aggregated measurements) so the engine can group within
an operator by model/platform or by workflow stage and compare metric
values across those segments. Callers pass `observations` and
`workflow_observations` to enable these detectors; without them the engine
emits only the operator-level patterns (P-CTX-01/02, P-BURN-01, P-HIDDEN-01)
exactly as before, preserving backward compatibility.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.measurement import Measurement
from domain.observation import Observation
from domain.pattern import Pattern
from domain.reference_population import ReferencePopulation
from domain.workflow import WorkflowObservation


@dataclass(frozen=True, slots=True)
class DetectedPattern:
    """A pattern detected by the engine, with the evidence that triggered it."""
    pattern_id: str          # e.g. "P-CTX-01"
    operator_id: str
    description: str
    supporting_metrics: List[str]
    evidence_summary: str
    confidence: float        # 0.0–1.0
    window_start: date
    window_end: date
    synthetic: bool

    def to_pattern(self) -> Pattern:
        """Convert to a domain Pattern object."""
        return Pattern(
            pattern_id=self.pattern_id,
            operator_id=self.operator_id,
            window_start=self.window_start,
            window_end=self.window_end,
            description=self.description,
            supporting_metrics=list(self.supporting_metrics),
            status="observed",
            synthetic=self.synthetic,
        )


@dataclass(frozen=True, slots=True)
class PatternThresholds:
    """Configurable thresholds for pattern detection."""
    low_leverage_percentile: float = 25.0    # P-CTX-01: leverage below this
    high_usage_percentile: float = 75.0      # P-BURN-01: usage above this
    low_yield_percentile: float = 25.0       # P-BURN-01: yield below this
    low_usage_percentile: float = 25.0       # P-HIDDEN-01: usage below this
    high_yield_percentile: float = 75.0      # P-HIDDEN-01: yield above this
    min_observations: int = 7                # minimum obs for pattern detection
    # P-MODEL-01: minimum observations per model group, and the relative
    # metric spread (max/min − 1) that counts as a "significant shift".
    model_min_obs_per_group: int = 3
    model_metric_spread: float = 0.30        # 30% relative spread across models
    # P-STAGE-01: minimum workflow observations per stage, and the relative
    # provisional-fit spread (max/min − 1) that counts as "consistently
    # stronger in one stage".
    #
    # Measured on the demo cohort (50 operators, all with >=2 workflow stages):
    #   rel spread >= 25% (old):  45/50 (90%)  — fires on almost everyone
    #   rel spread >= 50%:        32/50 (64%)  — still a majority
    #   rel spread >= 75%:        17/50 (34%)  — selective, about a third
    #   rel spread >= 100%:        5/50 (10%)  — very selective
    # 50% is the best balance: 75% would drop 15 operators, 17 of whom
    # would then have ZERO diagnoses. An absolute-spread floor has no
    # effect at either threshold (relative spread is always the binding
    # constraint), so none is applied.
    stage_min_obs_per_stage: int = 3
    stage_fit_spread: float = 0.50           # 50% relative spread across stages


class PatternEngine:
    """Detects descriptive patterns from measurements + reference population."""

    def __init__(self, thresholds: Optional[PatternThresholds] = None) -> None:
        self.thresholds = thresholds or PatternThresholds()

    def detect_patterns(
        self,
        operator_id: str,
        measurements: List[Measurement],
        reference: ReferencePopulation,
        usage_percentile: Optional[float] = None,
        window_start: Optional[date] = None,
        window_end: Optional[date] = None,
        synthetic: bool = True,
        observations: Optional[List[Observation]] = None,
        workflow_observations: Optional[List[WorkflowObservation]] = None,
    ) -> List[DetectedPattern]:
        """Detect all applicable patterns for an operator.

        Args:
            operator_id: the operator to analyze
            measurements: the operator's canonical measurements
            reference: the reference population for percentile lookups
            usage_percentile: the operator's usage percentile (from divergence analysis)
            window_start/end: the evaluation window
            synthetic: whether this is synthetic data
            observations: the operator's raw observations (enables P-MODEL-01)
            workflow_observations: the operator's workflow observations
                (enables P-STAGE-01)
        """
        # Minimum-evidence gate: when raw observations are provided, require
        # >= min_observations before any pattern detection runs. This
        # prevents spurious patterns from operators with too little data to
        # trust. When observations is None (caller didn't pass raw obs),
        # the gate is skipped — we don't have the data to enforce it.
        if observations is not None and len(observations) < self.thresholds.min_observations:
            return []

        patterns: List[DetectedPattern] = []
        m_map = {m.metric_id: m for m in measurements}

        if window_start is None:
            window_start = next((m.window_start for m in measurements if m.window_start), date(2026, 7, 1))
        if window_end is None:
            window_end = next((m.window_end for m in measurements if m.window_end), date(2026, 7, 30))

        lev = m_map.get("leverage")
        yld = m_map.get("yield")
        snr = m_map.get("token_snr")

        # P-CTX-01: Low context leverage
        if lev and lev.value is not None:
            lev_pct = reference.percentile("leverage", lev.value)
            if lev_pct is not None and lev_pct < self.thresholds.low_leverage_percentile:
                patterns.append(DetectedPattern(
                    pattern_id="P-CTX-01",
                    operator_id=operator_id,
                    description="Low context leverage",
                    supporting_metrics=["leverage"],
                    evidence_summary=f"leverage={lev.value:.3f} (pctile {lev_pct:.1f}, below {self.thresholds.low_leverage_percentile})",
                    confidence=min(1.0, (self.thresholds.low_leverage_percentile - lev_pct) / 25.0),
                    window_start=window_start,
                    window_end=window_end,
                    synthetic=synthetic,
                ))

        # P-BURN-01: High usage / low operating metrics
        if usage_percentile is not None and yld and yld.value is not None:
            yld_pct = reference.percentile("yield", yld.value)
            if (usage_percentile > self.thresholds.high_usage_percentile
                and yld_pct is not None and yld_pct < self.thresholds.low_yield_percentile):
                patterns.append(DetectedPattern(
                    pattern_id="P-BURN-01",
                    operator_id=operator_id,
                    description="High usage / low operating metrics",
                    supporting_metrics=["yield", "usage"],
                    evidence_summary=f"usage_pctile={usage_percentile:.1f} (high), yield_pctile={yld_pct:.1f} (low)",
                    confidence=min(1.0, (usage_percentile - yld_pct) / 100.0),
                    window_start=window_start,
                    window_end=window_end,
                    synthetic=synthetic,
                ))

        # P-HIDDEN-01: Low usage / high operating metrics
        if usage_percentile is not None and yld and yld.value is not None:
            yld_pct = reference.percentile("yield", yld.value)
            if (usage_percentile < self.thresholds.low_usage_percentile
                and yld_pct is not None and yld_pct > self.thresholds.high_yield_percentile):
                patterns.append(DetectedPattern(
                    pattern_id="P-HIDDEN-01",
                    operator_id=operator_id,
                    description="Low usage / high operating metrics",
                    supporting_metrics=["yield", "usage"],
                    evidence_summary=f"usage_pctile={usage_percentile:.1f} (low), yield_pctile={yld_pct:.1f} (high)",
                    confidence=min(1.0, (yld_pct - usage_percentile) / 100.0),
                    window_start=window_start,
                    window_end=window_end,
                    synthetic=synthetic,
                ))

        # P-CTX-02: High reuse / low output (high leverage, low SNR)
        if lev and lev.value is not None and snr and snr.value is not None:
            lev_pct = reference.percentile("leverage", lev.value)
            snr_pct = reference.percentile("token_snr", snr.value)
            if (lev_pct is not None and lev_pct > 75.0
                and snr_pct is not None and snr_pct < 25.0):
                patterns.append(DetectedPattern(
                    pattern_id="P-CTX-02",
                    operator_id=operator_id,
                    description="High reuse / low output",
                    supporting_metrics=["leverage", "token_snr"],
                    evidence_summary=f"leverage_pctile={lev_pct:.1f} (high), snr_pctile={snr_pct:.1f} (low)",
                    confidence=min(1.0, (lev_pct - snr_pct) / 100.0),
                    window_start=window_start,
                    window_end=window_end,
                    synthetic=synthetic,
                ))

        # P-MODEL-01: Model sensitivity — within-operator cross-model metric
        # comparison. Requires per-observation model metadata so the engine
        # can group an operator's observations by model and compare the
        # resulting per-model metric values. Per `09` this is a tool/model-
        # level pattern: do not reattribute to the operator.
        if observations is not None:
            pmodel = self._detect_model_sensitivity(
                operator_id, observations, window_start, window_end, synthetic,
            )
            if pmodel is not None:
                patterns.append(pmodel)

        # P-STAGE-01: Stage specialization — cross-stage metric comparison.
        # Requires workflow observations so the engine can compare an
        # operator's provisional fit / evidence across stages. Per `09` this
        # is a workflow-level pattern: stage design is the primary hypothesis.
        if workflow_observations is not None:
            pstage = self._detect_stage_specialization(
                operator_id, workflow_observations, window_start, window_end, synthetic,
            )
            if pstage is not None:
                patterns.append(pstage)

        return patterns

    # ── P-MODEL-01 ────────────────────────────────────────────────────────

    def _detect_model_sensitivity(
        self,
        operator_id: str,
        observations: List[Observation],
        window_start: date,
        window_end: date,
        synthetic: bool,
    ) -> Optional[DetectedPattern]:
        """Detect P-MODEL-01: within-operator metric shifts across models.

        Groups the operator's in-window observations by `model` (falling back
        to `platform` when model is unset), computes leverage and token_snr
        per group, and flags a model-sensitivity pattern when the relative
        spread across groups exceeds the configured threshold and every group
        meets the minimum-observation gate.
        """
        op_obs = [
            o for o in observations
            if o.operator_id == operator_id
            and _date_in_window(o.timestamp.date(), window_start, window_end)
        ]
        groups: Dict[str, List[Observation]] = {}
        for o in op_obs:
            key = o.model or o.platform or "unknown"
            groups.setdefault(key, []).append(o)

        # Need at least two model groups to compare; each must meet the min.
        if len(groups) < 2:
            return None
        qualified = {
            k: v for k, v in groups.items()
            if len(v) >= self.thresholds.model_min_obs_per_group
        }
        if len(qualified) < 2:
            return None

        # Compute leverage (R/I) and token_snr (O/(I+O)) per qualified group.
        per_model: Dict[str, Dict[str, float]] = {}
        for model_key, obs_list in qualified.items():
            I = sum(o.I for o in obs_list)
            O = sum(o.O for o in obs_list)
            R = sum(o.R for o in obs_list)
            lev = (R / I) if I > 0 else None
            snr = (O / (I + O)) if (I + O) > 0 else None
            if lev is None or snr is None:
                continue
            per_model[model_key] = {"leverage": lev, "token_snr": snr}

        if len(per_model) < 2:
            return None

        # Relative spread = (max - min) / min for leverage (the canonical
        # context metric). Use leverage as the primary signal; token_snr is
        # reported as supporting evidence.
        lev_values = sorted(v["leverage"] for v in per_model.values())
        lev_min, lev_max = lev_values[0], lev_values[-1]
        if lev_min <= 0:
            return None
        rel_spread = (lev_max - lev_min) / lev_min
        if rel_spread < self.thresholds.model_metric_spread:
            return None

        snr_values = sorted(v["token_snr"] for v in per_model.values())
        snr_min, snr_max = snr_values[0], snr_values[-1]
        model_summary = ", ".join(
            f"{k}:lev={v['leverage']:.3f},snr={v['token_snr']:.3f}"
            for k, v in sorted(per_model.items())
        )
        evidence = (
            f"leverage spread {lev_min:.3f}→{lev_max:.3f} "
            f"(rel {rel_spread:.0%}, threshold {self.thresholds.model_metric_spread:.0%}); "
            f"snr spread {snr_min:.3f}→{snr_max:.3f}; "
            f"models [{model_summary}]"
        )
        # Confidence scales with spread: at threshold → 0.5, at 2x threshold → 1.0.
        confidence = min(1.0, 0.5 + 0.5 * (rel_spread / self.thresholds.model_metric_spread - 1.0))

        return DetectedPattern(
            pattern_id="P-MODEL-01",
            operator_id=operator_id,
            description="Model sensitivity (within-operator metric shift across models)",
            supporting_metrics=["leverage", "token_snr"],
            evidence_summary=evidence,
            confidence=round(confidence, 2),
            window_start=window_start,
            window_end=window_end,
            synthetic=synthetic,
        )

    # ── P-STAGE-01 ────────────────────────────────────────────────────────

    def _detect_stage_specialization(
        self,
        operator_id: str,
        workflow_observations: List[WorkflowObservation],
        window_start: date,
        window_end: date,
        synthetic: bool,
    ) -> Optional[DetectedPattern]:
        """Detect P-STAGE-01: an operator's metrics concentrate in one stage.

        Groups the operator's workflow observations by `stage_id` and compares
        the `provisional_fit` across stages. Flags stage specialization when
        the relative spread across stages exceeds the configured threshold and
        every stage meets the minimum-evidence gate.
        """
        op_wobs = [
            w for w in workflow_observations
            if w.operator_id == operator_id
        ]
        if not op_wobs:
            return None

        by_stage: Dict[str, List[WorkflowObservation]] = {}
        for w in op_wobs:
            by_stage.setdefault(w.stage_id, []).append(w)

        # Each stage must meet the minimum-evidence gate (sum of evidence_count
        # across that stage's observations, or the observation count if
        # evidence_count is zero).
        qualified: Dict[str, float] = {}
        for stage_id, wobs in by_stage.items():
            evidence_count = sum(w.evidence_count for w in wobs)
            if evidence_count <= 0:
                evidence_count = len(wobs)
            if evidence_count >= self.thresholds.stage_min_obs_per_stage:
                fit_values = [w.provisional_fit for w in wobs if w.provisional_fit is not None]
                if fit_values:
                    qualified[stage_id] = sum(fit_values) / len(fit_values)

        if len(qualified) < 2:
            return None

        fit_values = sorted(qualified.values())
        fit_min, fit_max = fit_values[0], fit_values[-1]
        if fit_min <= 0:
            return None
        rel_spread = (fit_max - fit_min) / fit_min
        if rel_spread < self.thresholds.stage_fit_spread:
            return None

        strongest_stage = max(qualified, key=qualified.get)
        weakest_stage = min(qualified, key=qualified.get)
        stage_summary = ", ".join(
            f"{k}:fit={v:.3f}" for k, v in sorted(qualified.items())
        )
        evidence = (
            f"provisional_fit spread {fit_min:.3f}→{fit_max:.3f} "
            f"(rel {rel_spread:.0%}, threshold {self.thresholds.stage_fit_spread:.0%}); "
            f"strongest={strongest_stage}, weakest={weakest_stage}; "
            f"stages [{stage_summary}]"
        )
        confidence = min(1.0, 0.5 + 0.5 * (rel_spread / self.thresholds.stage_fit_spread - 1.0))

        return DetectedPattern(
            pattern_id="P-STAGE-01",
            operator_id=operator_id,
            description="Stage specialization (metrics consistently stronger in one workflow stage)",
            supporting_metrics=["provisional_fit"],
            evidence_summary=evidence,
            confidence=round(confidence, 2),
            window_start=window_start,
            window_end=window_end,
            synthetic=synthetic,
        )

    def detect_cohort_patterns(
        self,
        operator_ids: List[str],
        cohort_measurements: Dict[str, List[Measurement]],
        reference: ReferencePopulation,
        usage_percentiles: Dict[str, float],
        window_start: date,
        window_end: date,
        synthetic: bool = True,
        observations_by_operator: Optional[Dict[str, List[Observation]]] = None,
        workflow_observations_by_operator: Optional[Dict[str, List[WorkflowObservation]]] = None,
    ) -> Dict[str, List[DetectedPattern]]:
        """Detect patterns for all operators in a cohort.

        Pass `observations_by_operator` and `workflow_observations_by_operator`
        to enable the P-MODEL-01 and P-STAGE-01 detectors respectively. Without
        them only the operator-level patterns are emitted (backward compatible).
        """
        result: Dict[str, List[DetectedPattern]] = {}
        for oid in operator_ids:
            ms = cohort_measurements.get(oid, [])
            usage_pct = usage_percentiles.get(oid)
            obs = observations_by_operator.get(oid) if observations_by_operator else None
            wobs = workflow_observations_by_operator.get(oid) if workflow_observations_by_operator else None
            result[oid] = self.detect_patterns(
                oid, ms, reference, usage_pct, window_start, window_end, synthetic,
                observations=obs, workflow_observations=wobs,
            )
        return result


def _date_in_window(d: date, start: date, end: date) -> bool:
    return start <= d <= end
