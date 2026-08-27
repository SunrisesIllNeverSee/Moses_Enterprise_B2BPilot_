"""PilotService — the shared service layer for CLI/TUI/MCP.

This is the single entry point for all pilot operations. No interface layer
(CLI/TUI/MCP) implements business logic; all call this service (per `21`:
"Do not let CLI/TUI/MCP each implement business logic independently").

The service composes:
    DemoRepository  — loads demo data from disk
    ScoringEngine   — computes canonical measurements from observations
    analysis        — divergence, percentiles, distributions, eligibility, quality
    ingest          — fixture/claude/codex adapters for telemetry ingestion
"""
from __future__ import annotations

import csv
import json
import logging
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain import (
    Cohort, Diagnosis, Intervention, Measurement, Operator,
    Observation, QualityResult, ReferencePopulation, Workflow, WorkflowObservation,
    GateRule, GateResult, DEFAULT_GATE_RULES,
    evaluate_gate, evaluate_all_gates, evaluate_cohort_gates, summarize_gates,
    Artifact, Lineage, System, Outcome,
    TaskContext, adjust_metric_for_context, context_adjustment,
    OperatorIdentity, IdentityConflictError,
)
from metrics.engine import ScoringEngine
from metrics.composite_score import (
    CompositeScore, compute_composite_score, compute_cohort_composite_scores,
    composite_score_summary, COMPOSITE_NAME, COMPOSITE_ID,
)
from repository import DemoRepository, SQLiteRepository
from analysis import (
    compute_divergence, compute_percentiles, DivergenceResult,
    compute_cohort_distributions, MetricDistribution,
    check_eligibility, check_cohort_eligibility, EligibilityConfig,
    run_all_quality_checks, summarize_quality,
    PrePostVerifier, VerificationResult, MetricDelta,
    ReplicationEngine, ReplicationResult, ReplicationStatus, SplitMethod,
    compute_org_topology, OrgTopology,
    compute_operator_similarity, SimilarityResult,
    compute_operator_system_decomposition, OperatorSystemDecomposition,
    compute_outcome_correlation, OutcomeCorrelationResult,
    compute_context_architecture, ContextArchitecture,
    compute_longitudinal_movement, LongitudinalMovement,
    compute_team_composition, TeamComposition,
    compute_dependency_risk, DependencyRisk,
    compute_learning_curve, LearningCurveAnalysis,
)
from ingest import FixtureAdapter, ClaudeAdapter, CodexAdapter, IngestResult
from ingest import ClaudeApiAdapter, CodexApiAdapter, GroqApiAdapter
from diagnostics import PatternEngine, DiagnosisEngine, DetectedPattern
from interventions import InterventionRegistry, InterventionManager
from workflow import WorkflowFitEngine, WorkflowFitReport
from outcomes import (
    OutcomeJoinEngine, OutcomeGovernance, GovernanceLevel,
    InterventionOutcomeAnalyzer, InterventionOutcomeResult,
)
from governance import GovernanceEnforcement


class PilotService:
    """The shared service layer for all pilot interfaces."""

    def __init__(self, data_dir: Optional[str] = None, db_path: Optional[str] = None) -> None:
        if db_path is not None:
            self.repo = SQLiteRepository(db_path, data_dir=data_dir)
        else:
            self.repo = DemoRepository(data_dir)
        self.engine = ScoringEngine()
        # Governance enforcement (spec 12 additions: purpose limitation,
        # employee disclosure, consent, bias review, right to challenge,
        # correction process). The service exposes this so interfaces
        # can check gates and log governance actions.
        self.governance = GovernanceEnforcement()
        # Mutable in-memory state for write operations (P1+ write tools).
        # Seeded from the demo repository; write tools append/replace here
        # so that subsequent read tools observe the change.
        self._assigned_interventions: List[Intervention] = []
        self._closed_intervention_ids: Dict[str, InterventionOutcome] = {}
        self._experiments: List[dict] = []
        # Diagnoses cache: generated once, never invalidated. Diagnoses
        # depend only on observations + measurements + reference population,
        # none of which change at runtime. The cache avoids recomputing
        # the full pattern engine + diagnosis engine on every property
        # access.
        self._diagnoses_cache: Optional[Dict[str, List[Diagnosis]]] = None
        # Cross-system operator identity registry (Gap 5). Maps
        # system-specific IDs to canonical operator IDs so telemetry
        # from multiple platforms can be attributed correctly. Populated
        # incrementally via add_operator_identity.
        self._identity_registry: OperatorIdentity = OperatorIdentity()

    # ── Cohort / pilot overview ──────────────────────────────────────────

    @property
    def cohort(self) -> Cohort:
        return self.repo.cohort

    @property
    def operators(self) -> List[Operator]:
        return self.repo.operators

    @property
    def operator_ids(self) -> List[str]:
        return self.repo.operator_ids

    def get_operator(self, operator_id: str) -> Optional[Operator]:
        return self.repo.get_operator(operator_id)

    @property
    def observations(self) -> List[Observation]:
        return self.repo.observations

    @property
    def workflow(self) -> Workflow:
        return self.repo.workflow

    @property
    def workflow_observations(self) -> List[WorkflowObservation]:
        return self.repo.workflow_observations

    @property
    def diagnoses(self) -> List[Diagnosis]:
        """All diagnoses for the cohort, generated dynamically.

        Uses the pattern engine + diagnosis engine to detect patterns
        (including P-MODEL-01, P-STAGE-01) and generate hypotheses in
        hierarchy order. Falls back to repo-loaded diagnoses if the
        engines produce nothing. Results are cached after first
        computation (diagnoses depend only on immutable data).
        """
        cohort = self.generate_cohort_diagnoses()
        if cohort:
            return [d for diags in cohort.values() for d in diags]
        return self.repo.diagnoses

    def diagnoses_for(self, operator_id: str) -> List[Diagnosis]:
        """Diagnoses for a single operator, generated dynamically.

        Uses the cached cohort diagnoses dict rather than recomputing
        per-operator.
        """
        cohort = self.generate_cohort_diagnoses()
        if cohort and operator_id in cohort:
            return cohort[operator_id]
        # Fall back to repo diagnoses if cache is empty or operator not in cache.
        return self.repo.diagnoses_for(operator_id)

    @property
    def interventions(self) -> List[Intervention]:
        """All interventions: demo-loaded + MCP-assigned, with applied closures.

        Closed interventions are returned with their updated outcome so that
        subsequent read tools (get_intervention_status, verify_change) observe
        the write.
        """
        from domain.intervention import Intervention as _Intervention
        base = list(self.repo.interventions) + list(self._assigned_interventions)
        result: List[Intervention] = []
        for iv in base:
            if iv.intervention_id in self._closed_intervention_ids:
                new_outcome = self._closed_intervention_ids[iv.intervention_id]
                result.append(_Intervention(
                    intervention_id=iv.intervention_id,
                    operator_id=iv.operator_id,
                    catalog_id=iv.catalog_id,
                    reason_pattern=iv.reason_pattern,
                    target_metric=iv.target_metric,
                    start_date=iv.start_date,
                    followup_days=iv.followup_days,
                    synthetic_outcome=new_outcome,
                    synthetic=iv.synthetic,
                ))
            else:
                result.append(iv)
        return result

    @property
    def reference_population(self) -> ReferencePopulation:
        return self.repo.reference_population

    @property
    def cohort_summary_raw(self) -> dict:
        return self.repo.cohort_summary

    # ── Canonical domain object accessors (new) ──────────────────────────

    @property
    def artifacts(self) -> List[Artifact]:
        return self.repo.artifacts

    @property
    def lineages(self) -> List[Lineage]:
        return self.repo.lineages

    @property
    def outcomes(self) -> list:
        return self.repo.outcomes

    @property
    def teams(self) -> list:
        return self.repo.teams

    @property
    def workflows(self) -> List[Workflow]:
        return self.repo.workflows

    @property
    def systems(self) -> List[System]:
        return self.repo.systems

    @property
    def observations_full(self) -> List[Observation]:
        """Full observations from observations.jsonl (1668 records)."""
        return self.repo.observations_jsonl

    def artifacts_for(self, operator_id: str) -> List[Artifact]:
        return self.repo.artifacts_for(operator_id)

    def lineages_for(self, operator_id: str) -> List[Lineage]:
        return self.repo.lineages_for(operator_id)

    def lineage_summary(self) -> dict:
        """Summary of lineage chains for reporting."""
        lins = self.repo.lineages
        outcomes = self.repo.outcomes
        # Count by workflow
        by_workflow: dict[str, int] = {}
        for lin in lins:
            wf = lin.workflow_id or "unassigned"
            by_workflow[wf] = by_workflow.get(wf, 0) + 1
        # Average micro_eval metrics across lineages
        metric_sums: dict[str, float] = {}
        metric_counts: dict[str, int] = {}
        for lin in lins:
            me = lin.micro_eval or {}
            for k, v in me.items():
                if isinstance(v, (int, float)):
                    metric_sums[k] = metric_sums.get(k, 0.0) + v
                    metric_counts[k] = metric_counts.get(k, 0) + 1
        avg_micro_eval = {
            k: round(metric_sums[k] / metric_counts[k], 4)
            for k in metric_sums
        }
        # Outcome linkage
        linked = sum(1 for lin in lins if lin.outcome_id)
        return {
            "total": len(lins),
            "by_workflow": by_workflow,
            "avg_micro_eval": avg_micro_eval,
            "outcomes_linked": linked,
            "outcomes_total": len(outcomes),
        }

    def lineage_chain(self, operator_id: str) -> dict:
        """Return the full lineage chain for an operator.

        Connects observations -> transformations -> artifact -> outcome
        per the BI -> AAI -> committed-state -> outcome sequence.
        """
        lins = self.lineages_for(operator_id)
        if not lins:
            return {"operator_id": operator_id, "chains": []}
        outcomes_by_id = {o.outcome_id: o for o in self.repo.outcomes}
        artifacts_by_id = {a.artifact_id: a for a in self.repo.artifacts}
        chains = []
        for lin in lins:
            chain: dict = {
                "lineage_id": lin.lineage_id,
                "workflow_id": lin.workflow_id,
                "workflow_stage": lin.workflow_stage,
                "micro_eval": lin.micro_eval,
                "links": [],
            }
            # Build the link sequence
            link_defs = [
                ("state_a", lin.state_a_observation_id, "STATE_A"),
                ("bi_action", lin.bi_action_observation_id, "BI_ACTION"),
                ("aai_transformation", lin.aai_transformation_observation_id, "AAI_TRANSFORMATION"),
                ("bi_redirection", lin.bi_redirection_observation_id, "BI_REDIRECTION"),
                ("aai_extension", lin.aai_extension_observation_id, "AAI_EXTENSION"),
            ]
            for name, obs_id, link_type in link_defs:
                if obs_id:
                    chain["links"].append({
                        "link_type": link_type,
                        "observation_id": obs_id,
                    })
            # Committed artifact
            if lin.committed_artifact_id:
                art = artifacts_by_id.get(lin.committed_artifact_id)
                chain["links"].append({
                    "link_type": "COMMITTED_STATE",
                    "artifact_id": lin.committed_artifact_id,
                    "artifact_type": art.artifact_type.value if art else None,
                })
            # Outcome
            if lin.outcome_id:
                out = outcomes_by_id.get(lin.outcome_id)
                if out:
                    chain["links"].append({
                        "link_type": "OUTCOME",
                        "outcome_id": out.outcome_id,
                        "outcome_type": out.outcome_type.value
                            if hasattr(out.outcome_type, "value")
                            else out.outcome_type,
                        "outcome_status": out.outcome_status.value
                            if hasattr(out.outcome_status, "value")
                            else out.outcome_status,
                        "external_quality_score": out.external_quality_score,
                        "cycle_time_minutes": out.cycle_time_minutes,
                    })
            chains.append(chain)
        return {"operator_id": operator_id, "chains": chains}

    def outcomes_for(self, operator_id: str) -> List[Outcome]:
        """Return typed Outcome objects for an operator."""
        return [o for o in self.repo.outcomes if o.operator_id == operator_id]

    # ── Scoring (the single canonical path) ──────────────────────────────

    def score_operator(self, operator_id: str) -> List[Measurement]:
        """Compute all canonical metrics for an operator over the cohort window."""
        c = self.cohort
        obs = self.repo.observations_for(operator_id)
        return self.engine.score_operator(operator_id, obs, c.window_start, c.window_end)

    def score_cohort(self) -> Dict[str, List[Measurement]]:
        """Score all operators in the cohort."""
        c = self.cohort
        return self.engine.score_cohort(self.operator_ids, self.observations, c.window_start, c.window_end)

    # ── Composite Employee Score (Item 9) ────────────────────────────────

    def composite_score(self, operator_id: str) -> CompositeScore:
        """Compute the composite developmental score for a single operator.

        Per `21` §8: "one proprietary composite employee score."
        Combines canonical metrics (leverage, yield, token_snr, construction)
        into a 0–100 developmental index using reference-population
        percentile normalization.

        Governance: labeled DEVELOPMENTAL, never PERSONNEL. Per `12`
        avoid-list: no bottom-employee leaderboard, no automatic adverse
        actions, no punitive labels.
        """
        ms = self.score_operator(operator_id)
        return compute_composite_score(
            operator_id=operator_id,
            measurements=ms,
            reference=self.reference_population,
            synthetic=True,
        )

    def cohort_composite_scores(self) -> Dict[str, CompositeScore]:
        """Compute composite scores for all operators in the cohort.

        Returns a dict of operator_id → CompositeScore. Does NOT sort or
        rank — per governance avoid-list, the caller must not surface a
        worst-to-best leaderboard.
        """
        cohort_ms = self.score_cohort()
        return compute_cohort_composite_scores(
            self.operator_ids, cohort_ms, self.reference_population, synthetic=True,
        )

    def composite_score_summary(self) -> dict:
        """Summarize composite scores across the cohort (aggregate stats only).

        Returns distribution statistics (min, max, median, mean, quartiles)
        without exposing individual operator rankings. Per governance: this
        is for cohort-level development planning, not individual evaluation.
        """
        scores = self.cohort_composite_scores()
        summary = composite_score_summary(scores)
        return {
            **summary,
            "score_id": COMPOSITE_ID,
            "name": COMPOSITE_NAME,
            "label": "DEVELOPMENTAL — cohort distribution, not individual ranking",
            "weights": {
                "leverage": 0.30, "yield": 0.30,
                "token_snr": 0.20, "construction": 0.20,
            },
        }

    # ── Analysis ─────────────────────────────────────────────────────────

    def cohort_measurements_flat(self) -> List[Measurement]:
        """All measurements for all operators, flattened."""
        return [m for ms in self.score_cohort().values() for m in ms]

    def percentiles(self) -> Dict[str, Dict[str, Measurement]]:
        """Compute percentile measurements for all operators."""
        return compute_percentiles(self.cohort_measurements_flat(), self.reference_population)

    def divergence(self) -> List[DivergenceResult]:
        """Compute usage-vs-operation divergence for all operators."""
        pcts = self.percentiles()
        # Usage = total tokens (I + O + R + W) per operator.
        usage_tokens: Dict[str, int] = {}
        for obs in self.observations:
            usage_tokens[obs.operator_id] = usage_tokens.get(obs.operator_id, 0) + obs.I + obs.O + obs.R + obs.W
        return compute_divergence(pcts, usage_tokens)

    def divergence_counts(self) -> Dict[str, int]:
        """Count operators in each divergence class."""
        return dict(Counter(r.divergence_class for r in self.divergence()))

    def cohort_medians(self) -> Dict[str, Optional[float]]:
        """Median value for each canonical metric across the cohort."""
        ms = self.cohort_measurements_flat()
        medians: Dict[str, Optional[float]] = {}
        for metric_id in ("leverage", "yield", "token_snr", "construction"):
            values = sorted(m.value for m in ms if m.metric_id == metric_id and m.value is not None)
            if values:
                n = len(values)
                medians[metric_id] = values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2
            else:
                medians[metric_id] = None
        return medians

    def operator_profile(self, operator_id: str) -> dict:
        """Build a complete operator profile: metrics, percentiles, diagnoses."""
        op = self.get_operator(operator_id)
        if op is None:
            return {"error": f"Unknown operator {operator_id}"}
        ms = self.score_operator(operator_id)
        pcts = self.percentiles().get(operator_id, {})
        diags = self.diagnoses_for(operator_id)
        return {
            "operator": op.to_dict(),
            "measurements": [m.to_dict() for m in ms],
            "percentiles": {k: v.to_dict() for k, v in pcts.items()},
            "diagnoses": [d.to_dict() for d in diags],
        }

    def workflow_fit_by_stage(self) -> Dict[str, List[WorkflowObservation]]:
        """Top operators per workflow stage by provisional fit."""
        wobs = self.workflow_observations
        by_stage: Dict[str, List[WorkflowObservation]] = {}
        for w in wobs:
            by_stage.setdefault(w.stage_id, []).append(w)
        for stage_id in by_stage:
            by_stage[stage_id].sort(key=lambda w: w.provisional_fit or 0, reverse=True)
        return by_stage

    # ── P0-D: Distributions, eligibility, quality ───────────────────────

    def cohort_distributions(self) -> Dict[str, MetricDistribution]:
        """Distribution statistics for each canonical metric across the cohort."""
        return compute_cohort_distributions(self.cohort_measurements_flat())

    def eligibility(self) -> Dict[str, QualityResult]:
        """Eligibility check for every operator in the cohort."""
        c = self.cohort
        return check_cohort_eligibility(
            self.operator_ids, self.observations, c.window_start, c.window_end
        )

    def operator_eligibility(self, operator_id: str) -> QualityResult:
        """Eligibility check for a single operator."""
        c = self.cohort
        return check_eligibility(
            operator_id, self.observations, c.window_start, c.window_end
        )

    def data_quality(self) -> Dict[str, List[QualityResult]]:
        """Run all data quality checks on the cohort."""
        c = self.cohort
        return run_all_quality_checks(
            self.operator_ids, self.observations, c.window_start, c.window_end
        )

    def data_quality_summary(self) -> Dict[str, int]:
        """Summarize quality check results into counts by severity."""
        return summarize_quality(self.data_quality())

    def pilot_status(self) -> dict:
        """Complete pilot status per `06` Pilot screen and `08` get_pilot_status."""
        c = self.cohort
        elig = self.eligibility()
        eligible_count = sum(1 for r in elig.values() if r.passed)
        providers = sorted(set(o.platform for o in self.observations if o.platform))
        dq = self.data_quality_summary()
        return {
            "cohort_id": c.cohort_id,
            "window": {"start": c.window_start.isoformat(), "end": c.window_end.isoformat()},
            "eligible_operators": eligible_count,
            "total_operators": len(self.operator_ids),
            "providers": providers,
            "observation_count": len(self.observations),
            "metric_registry_version": self.engine.registry.registry_version,
            "reference_field_version": self.reference_population.version,
            "active_interventions": len(self.interventions),
            "data_quality": dq,
            "synthetic": True,
        }

    def compare_operator_to_reference(
        self, operator_id: str, metric_ids: Optional[List[str]] = None
    ) -> dict:
        """Compare an operator's metrics to the reference population."""
        ms = self.score_operator(operator_id)
        pcts = self.percentiles().get(operator_id, {})
        ref = self.reference_population
        if metric_ids is None:
            metric_ids = [m.metric_id for m in ms]

        comparisons = []
        for mid in metric_ids:
            m = next((x for x in ms if x.metric_id == mid), None)
            pct_m = pcts.get(f"{mid}_percentile")
            comparisons.append({
                "metric_id": mid,
                "value": m.value if m else None,
                "percentile": pct_m.value if pct_m else None,
                "reference_version": ref.version,
                "status": m.status.value if m else None,
            })
        return {
            "operator_id": operator_id,
            "comparisons": comparisons,
            "reference_version": ref.version,
            "synthetic": True,
        }

    def cohort_distribution_for_metric(self, metric_id: str) -> Optional[MetricDistribution]:
        """Get the distribution for a single metric."""
        return self.cohort_distributions().get(metric_id)

    def compare_teams(self) -> Dict[str, Dict[str, float]]:
        """Compare teams by median metric values."""
        ms = self.cohort_measurements_flat()
        op_teams = {o.operator_id: o.team for o in self.operators}
        team_metrics: Dict[str, Dict[str, List[float]]] = {}
        for m in ms:
            if m.value is None:
                continue
            team = op_teams.get(m.operator_id, "unknown")
            team_metrics.setdefault(team, {}).setdefault(m.metric_id, []).append(m.value)

        result: Dict[str, Dict[str, float]] = {}
        for team, metrics in team_metrics.items():
            result[team] = {}
            for mid, values in metrics.items():
                values.sort()
                n = len(values)
                result[team][mid] = round(values[n // 2], 4) if n > 0 else 0
        return result

    # ── EVAL-013: Org AI Topology ────────────────────────────────────────

    def org_topology(self) -> dict:
        """Compute the organization-level AI topology map (EVAL-013).

        Produces a structural map of the organization's AI operating
        structure: team-level metric distributions, capability
        concentration (Gini), platform adoption, single points of
        failure, and cross-team complementarity.

        This is NOT a ranking. It is a structural map.
        """
        ms = self.cohort_measurements_flat()
        topology = compute_org_topology(
            operators=self.operators,
            measurements=ms,
            metric_ids=self.engine.registry.canonical_metric_ids(),
        )
        return topology.to_dict()

    # ── EVAL-014: Operator Similarity Search ─────────────────────────────

    def operator_similarity(self, operator_id: str, n_neighbors: int = 5) -> dict:
        """Find the nearest comparable operators by metric profile (EVAL-014).

        Uses normalized Euclidean distance across the 5 canonical metrics.
        Normalization is by percentile rank so operators are compared on
        relative position, not absolute token counts.

        This is metric similarity, NOT a personality match.
        """
        ms = self.cohort_measurements_flat()
        result = compute_operator_similarity(
            query_operator_id=operator_id,
            operators=self.operators,
            measurements=ms,
            metric_ids=self.engine.registry.canonical_metric_ids(),
            n_neighbors=n_neighbors,
        )
        return result.to_dict()

    # ── EVAL-003: Context Architecture ───────────────────────────────────

    def context_architecture(self, operator_id: str = "") -> dict:
        """Analyze how operators structure context (EVAL-003).

        Computes per-operator reuse ratio (R/(R+I)), construction ratio
        (W/(W+I)), and context efficiency ((R+W)/(I+R+W)). Classifies
        each operator's context pattern: "context builder", "context
        reuser", "fresh input heavy", or "balanced".

        Includes provider caveats when cache tokens (R, W) are not
        reported by the provider.

        If operator_id is provided, the result is filtered to that
        operator only. All metrics are content-free (token counts only).
        """
        result = compute_context_architecture(
            operators=self.operators,
            observations=self.observations,
        )
        d = result.to_dict()
        if operator_id:
            d["operator_profiles"] = [
                p for p in d["operator_profiles"] if p["operator_id"] == operator_id
            ]
        return d

    # ── EVAL-004: Longitudinal Movement ──────────────────────────────────

    def longitudinal_movement(self, operator_id: str = "", window_count: int = 3) -> dict:
        """Track metric changes over time windows (EVAL-004).

        Divides the cohort window into N consecutive sub-windows, scores
        each operator in each window, and computes metric deltas, trend
        direction (improving/declining/stable), band movement, and
        stability scores.

        If operator_id is provided, only that operator is analyzed.
        Trend labels are developmental observations, not personnel
        judgments. Outcome claims are ASSOCIATION, never CAUSATION.
        """
        c = self.cohort
        result = compute_longitudinal_movement(
            operators=self.operators,
            observations=self.observations,
            engine=self.engine,
            metric_ids=self.engine.registry.canonical_metric_ids(),
            window_start=c.window_start,
            window_end=c.window_end,
            window_count=window_count,
            operator_id=operator_id,
        )
        return result.to_dict()

    # ── EVAL-009: Team Composition ───────────────────────────────────────

    def team_composition(self, team_id: str = "") -> dict:
        """Analyze team-level archetype coverage (EVAL-009).

        Computes per-team archetype distribution, coverage gaps
        (archetypes present in the org but absent from a team),
        complementarity score (Shannon evenness of archetype mix), and
        recommended additions to fill gaps.

        If team_id is provided, only that team is analyzed. Team ID
        matching is case-insensitive and normalizes spaces/slashes to
        underscores. These are developmental hypotheses, not personnel
        decisions.
        """
        ms = self.cohort_measurements_flat()
        result = compute_team_composition(
            operators=self.operators,
            measurements=ms,
            metric_ids=self.engine.registry.canonical_metric_ids(),
            team_id=team_id,
        )
        return result.to_dict()

    # ── EVAL-010: Capability Dependency Risk ─────────────────────────────

    def dependency_risk(self) -> dict:
        """Identify capability concentration risks (EVAL-010).

        Computes per-metric Gini coefficients across teams (how
        concentrated is each canonical metric at the team level),
        single-point-of-failure detection (if one operator accounts
        for >40% of a team's total for a metric), and an aggregate
        risk summary.

        These are structural risk hypotheses, not personnel judgments.
        The goal is to surface coverage gaps for capability development.
        """
        ms = self.cohort_measurements_flat()
        result = compute_dependency_risk(
            operators=self.operators,
            measurements=ms,
            metric_ids=self.engine.registry.canonical_metric_ids(),
        )
        return result.to_dict()

    # ── EVAL-015: AI Learning Curve ──────────────────────────────────────

    def learning_curve(self, operator_id: str = "") -> dict:
        """Model operator improvement trajectories (EVAL-015).

        Divides the cohort window into consecutive sub-windows, scores
        each operator in each window, and models the trajectory of their
        canonical metrics over time. Computes improvement rate (metric
        slope), curve shape (linear/diminishing/accelerating/flat),
        uncertainty bounds (95% CI on slope), and plateau detection.

        Intervention history (if available) provides temporal context —
        co-occurrence is noted as ASSOCIATION, never CAUSATION.

        If operator_id is provided, only that operator is analyzed.
        Curve shape labels are developmental observations, not personnel
        judgments.
        """
        c = self.cohort
        # Build intervention context from assigned + repo interventions.
        interventions = [
            {
                "operator_id": iv.operator_id,
                "start_date": iv.start_date.isoformat() if iv.start_date else "",
                "target_metric": iv.target_metric or "",
                "reason_pattern": iv.reason_pattern or "",
            }
            for iv in self.interventions
        ]
        result = compute_learning_curve(
            operators=self.operators,
            observations=self.observations,
            engine=self.engine,
            metric_ids=self.engine.registry.canonical_metric_ids(),
            window_start=c.window_start,
            window_end=c.window_end,
            window_count=4,
            operator_id=operator_id,
            interventions=interventions,
        )
        return result.to_dict()

    # ── Operator×System Decomposition ────────────────────────────────────

    def operator_system_decomposition(self, operator_id: str = "") -> dict:
        """Decompose observed metrics into operator/system/interaction effects.

        For each operator with data on 2+ systems, decomposes their metric
        outcomes into:
        - Operator effect (their general capability across systems)
        - System effect (the system's general effect across operators)
        - Operator×System interaction (the pairing-specific residual)

        If operator_id is provided, the result highlights that operator's
        decomposition. If empty, returns the cohort-level decomposition.

        Per Jaimie's review §2: "this is where the deepest intellectual
        value lies."
        """
        # Build {operator_id: {system: {metric_id: value}}}
        canonical_ids = self.engine.registry.canonical_metric_ids()
        op_sys_metrics: dict[str, dict[str, dict[str, float]]] = {}

        for op_id in self.operator_ids:
            obs = self.repo.observations_for(op_id)
            # Group by system (platform or model)
            by_system: dict[str, list] = {}
            for o in obs:
                sys_name = o.platform or o.model or "unknown"
                by_system.setdefault(sys_name, []).append(o)

            for sys_name, sys_obs in by_system.items():
                measurements = self.engine.score_operator(
                    op_id, sys_obs,
                    self.cohort.window_start, self.cohort.window_end,
                )
                for m in measurements:
                    if m.metric_id in canonical_ids and m.value is not None:
                        op_sys_metrics.setdefault(op_id, {}).setdefault(sys_name, {})[m.metric_id] = m.value

        result = compute_operator_system_decomposition(
            operator_system_metrics=op_sys_metrics,
            metric_ids=canonical_ids,
            operator_id=operator_id or None,
        )
        return result.to_dict()

    # ── Outcome Correlation through Lineage ───────────────────────────────

    def outcome_correlation(self) -> dict:
        """Correlate operating patterns (micro_eval) with outcomes.

        Connects lineage micro_eval metrics to Outcome nodes (quality
        score, cycle time). All results are labeled ASSOCIATION with
        evidence grade OBSERVATIONAL — never CAUSATION.

        Per Jaimie's review §17: "With an Outcome object, it can become
        performance science."
        """
        lins = self.repo.lineages
        outcomes_by_id = {o.outcome_id: o for o in self.repo.outcomes}

        lineage_outcomes: list[tuple[dict, dict]] = []
        for lin in lins:
            if lin.outcome_id and lin.outcome_id in outcomes_by_id:
                out = outcomes_by_id[lin.outcome_id]
                lineage_outcomes.append((lin.micro_eval or {}, out.to_dict()))

        result = compute_outcome_correlation(lineage_outcomes)
        return result.to_dict()

    # ── Benchmark Engine (§7) ───────────────────────────────────────────

    def benchmark_operator(
        self,
        operator_id: str,
        metric: str = "leverage",
    ) -> dict:
        """Run the benchmark engine for a single operator.

        Implements the §7.14 selection algorithm: determines the legitimate
        benchmark class for this operator given the available data, computes
        the comparison with appropriate statistical methods (§7.15), and
        returns the result with full uncertainty disclosure (§7.17).
        """
        from benchmark import BenchmarkEngine, BenchmarkContext

        engine = BenchmarkEngine()

        # Get the operator's metric value
        ms = self.score_operator(operator_id)
        m = next((x for x in ms if x.metric_id == metric), None)
        if m is None or m.value is None:
            return {
                "operator_id": operator_id,
                "metric": metric,
                "error": "no measurement available for this metric",
            }

        # Build comparison group: all other operators' values for this metric
        cohort_ms = self.score_cohort()
        comparison_values = []
        for op_id, measurements in cohort_ms.items():
            if op_id == operator_id:
                continue
            for meas in measurements:
                if meas.metric_id == metric and meas.value is not None:
                    comparison_values.append(meas.value)

        # Get operator metadata for selection algorithm
        op = self.get_operator(operator_id)
        team = op.team if op else None
        role_family = op.role_family if op else None

        # Check for prior window data (for self_vs_prior)
        prior_values = []
        # The demo data has a 30-day window; if we had a prior window we'd
        # use it. For now, leave empty — the selection algorithm will fall
        # through to peer/cohort.

        # Check for intervention
        op_interventions = [
            iv for iv in self.interventions if iv.operator_id == operator_id
        ]
        is_intervention = len(op_interventions) > 0

        ctx = BenchmarkContext(
            operator_id=operator_id,
            metric=metric,
            operator_value=m.value,
            window_start=self.cohort.window_start,
            window_end=self.cohort.window_end,
            comparison_values=tuple(comparison_values),
            comparison_description="cohort peers",
            team=team,
            role_family=role_family,
            cohort_id=self.cohort.cohort_id,
            prior_window_values=tuple(prior_values),
            is_intervention=is_intervention,
            operator_sample_size=len(self.repo.observations_for(operator_id)),
            synthetic=True,
        )

        # Run selection + evaluation
        selection = engine.select(ctx)
        result = engine.evaluate(ctx)

        return {
            "operator_id": operator_id,
            "metric": metric,
            "selected_benchmark": selection.selected_class.value if selection.selected_class else None,
            "selection_reason": selection.reason,
            "alternatives_considered": [a.value for a in selection.alternatives_considered],
            "benchmark": result.to_dict(),
        }

    def benchmark_cohort(
        self,
        metric: str = "leverage",
    ) -> List[dict]:
        """Run the benchmark engine for all operators in the cohort.

        Returns one benchmark result per operator. Each result includes
        the selected benchmark class, comparison statistics, confidence
        intervals, and limitations.
        """
        results = []
        for op_id in self.operator_ids:
            try:
                result = self.benchmark_operator(op_id, metric)
                results.append(result)
            except Exception as e:
                results.append({
                    "operator_id": op_id,
                    "metric": metric,
                    "error": str(e),
                })
        return results

    def benchmark_summary(
        self,
        metric: str = "leverage",
    ) -> dict:
        """Summarize benchmark results across the cohort.

        Returns aggregate statistics: how many operators were benchmarked,
        which benchmark classes were selected, distribution of percentile
        ranks. Does NOT produce a ranked leaderboard (per §7.0.1: no false
        leaderboards).
        """
        results = self.benchmark_cohort(metric)
        class_counts = {}
        percentile_ranks = []
        errors = 0
        for r in results:
            if "error" in r:
                errors += 1
                continue
            bench = r.get("benchmark", {})
            cls = r.get("selected_benchmark", "unknown")
            class_counts[cls] = class_counts.get(cls, 0) + 1
            pct = bench.get("result", {}).get("percentile_rank")
            if pct is not None:
                percentile_ranks.append(pct)

        import statistics as _stats
        return {
            "metric": metric,
            "operators_benchmarked": len(results) - errors,
            "operators_with_errors": errors,
            "benchmark_classes_selected": class_counts,
            "percentile_rank_distribution": {
                "min": min(percentile_ranks) if percentile_ranks else None,
                "median": _stats.median(percentile_ranks) if percentile_ranks else None,
                "max": max(percentile_ranks) if percentile_ranks else None,
                "count": len(percentile_ranks),
            },
            "no_false_leaderboards": True,
            "synthetic": True,
        }

    # ── P0-C: Ingest ────────────────────────────────────────────────────

    def check_ingestion_governance(self, operator_id: str, purpose_id: str = "") -> dict:
        """Check all governance gates before ingesting data for an operator.

        Returns a dict with 'permitted' (bool) and 'reasons' (list of str).
        Logs the result to the governance audit log.

        Per spec 12 additions: purpose limitation, employee disclosure,
        and consent are checked. If any fails, ingestion is blocked.
        """
        ok, reasons = self.governance.check_ingestion(operator_id, purpose_id)
        return {"permitted": ok, "reasons": reasons}

    def ingest_file(self, provider: str, path: str, operator_id: str = "",
                    purpose_id: str = "", skip_governance: bool = False) -> IngestResult:
        """Ingest a file using the specified provider adapter.

        If operator_id and purpose_id are provided, governance checks
        are run before ingestion. Set skip_governance=True to bypass
        (for demo/test data only).
        """
        if not skip_governance and operator_id:
            ok, reasons = self.governance.check_ingestion(operator_id, purpose_id)
            if not ok:
                return IngestResult(
                    source=provider, observations=[],
                    errors=[f"Governance gate blocked ingestion: {'; '.join(reasons)}"],
                )
        adapters = {
            "fixture": FixtureAdapter,
            "claude": ClaudeAdapter,
            "codex": CodexAdapter,
        }
        cls = adapters.get(provider)
        if cls is None:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(adapters)}")
        return cls().ingest(path)

    def ingest_api(self, provider: str, operator_id: str, days: int = 30,
                   api_key: Optional[str] = None, persist: bool = False,
                   purpose_id: str = "", skip_governance: bool = False) -> IngestResult:
        """Fetch telemetry from a provider API and optionally persist to storage.

        API adapters run in stub mode when no API key is available,
        producing deterministic synthetic data for testing.

        Args:
            provider: One of 'claude', 'codex', 'groq'.
            operator_id: The operator to fetch telemetry for.
            days: Number of days of history.
            api_key: Optional API key (falls back to env var).
            persist: If True and using SQLiteRepository, persist observations.
            purpose_id: Processing purpose for governance check.
            skip_governance: Bypass governance checks (demo/test only).
        """
        if not skip_governance and operator_id:
            ok, reasons = self.governance.check_ingestion(operator_id, purpose_id)
            if not ok:
                return IngestResult(
                    source=provider, observations=[],
                    errors=[f"Governance gate blocked ingestion: {'; '.join(reasons)}"],
                )
        adapters = {
            "claude": ClaudeApiAdapter,
            "codex": CodexApiAdapter,
            "groq": GroqApiAdapter,
        }
        cls = adapters.get(provider)
        if cls is None:
            raise ValueError(f"Unknown API provider: {provider}. Available: {list(adapters)}")
        adapter = cls(api_key=api_key)
        if persist and hasattr(self.repo, "insert_observations"):
            return adapter.fetch_and_persist(operator_id, self.repo, days)
        return adapter.fetch(operator_id, days)

    # ── P0-F: Export ────────────────────────────────────────────────────

    def export_cohort(self, fmt: str = "json") -> str:
        """Export cohort data in the specified format."""
        from reporting import export_cohort_json, export_cohort_csv, export_cohort_markdown
        exporters = {
            "json": export_cohort_json,
            "csv": export_cohort_csv,
            "md": export_cohort_markdown,
            "markdown": export_cohort_markdown,
        }
        exporter = exporters.get(fmt)
        if exporter is None:
            raise ValueError(f"Unknown format: {fmt}. Available: {list(exporters)}")
        return exporter(self)

    def export_operator(self, operator_id: str, fmt: str = "json") -> str:
        """Export a single operator profile in the specified format."""
        from reporting import export_operator_json, export_operator_markdown
        exporters = {
            "json": export_operator_json,
            "md": export_operator_markdown,
            "markdown": export_operator_markdown,
        }
        exporter = exporters.get(fmt)
        if exporter is None:
            raise ValueError(f"Unknown format: {fmt}. Available: {list(exporters)}")
        return exporter(self, operator_id)

    # ── P1: Pattern engine, diagnosis, interventions, verification ──────

    def _usage_percentiles(self) -> Dict[str, float]:
        """Compute usage percentiles for all operators (for pattern detection)."""
        usage_tokens: Dict[str, int] = {}
        for obs in self.observations:
            usage_tokens[obs.operator_id] = usage_tokens.get(obs.operator_id, 0) + obs.I + obs.O + obs.R + obs.W
        sorted_usage = sorted(usage_tokens.items(), key=lambda x: x[1])
        n = len(sorted_usage)
        return {oid: round(100.0 * i / max(n - 1, 1), 1) for i, (oid, _) in enumerate(sorted_usage)}

    def detect_patterns(self, operator_id: str) -> List[DetectedPattern]:
        """Detect patterns for a single operator.

        Passes the operator's raw observations and workflow observations to
        the pattern engine so the P-MODEL-01 (model sensitivity) and
        P-STAGE-01 (stage specialization) detectors can fire. Without these
        the engine emits only the operator-level patterns.
        """
        engine = PatternEngine()
        ms = self.score_operator(operator_id)
        ref = self.reference_population
        usage_pct = self._usage_percentiles().get(operator_id)
        c = self.cohort
        obs = self.repo.observations_for(operator_id)
        wobs = [w for w in self.workflow_observations if w.operator_id == operator_id]
        return engine.detect_patterns(
            operator_id, ms, ref, usage_pct, c.window_start, c.window_end,
            observations=obs, workflow_observations=wobs,
        )

    def detect_cohort_patterns(self) -> Dict[str, List[DetectedPattern]]:
        """Detect patterns for all operators in the cohort.

        Passes per-operator observations and workflow observations to the
        pattern engine so the P-MODEL-01 and P-STAGE-01 detectors can fire.
        """
        engine = PatternEngine()
        all_ms = self.score_cohort()
        ref = self.reference_population
        usage_pcts = self._usage_percentiles()
        c = self.cohort
        obs_by_op: Dict[str, list] = {
            oid: self.repo.observations_for(oid) for oid in self.operator_ids
        }
        wobs_by_op: Dict[str, list] = {}
        for w in self.workflow_observations:
            wobs_by_op.setdefault(w.operator_id, []).append(w)
        return engine.detect_cohort_patterns(
            self.operator_ids, all_ms, ref, usage_pcts, c.window_start, c.window_end,
            observations_by_operator=obs_by_op,
            workflow_observations_by_operator=wobs_by_op,
        )

    def generate_diagnoses(self, operator_id: str) -> List[Diagnosis]:
        """Generate diagnostic hypotheses for a single operator.

        Per P1 acceptance: every diagnosis contains evidence + alternatives +
        status=HYPOTHESIS.
        """
        patterns = self.detect_patterns(operator_id)
        diag_engine = DiagnosisEngine()
        return diag_engine.generate_diagnoses(operator_id, patterns)

    def generate_cohort_diagnoses(self) -> Dict[str, List[Diagnosis]]:
        """Generate diagnoses for all operators with detected patterns.

        Results are cached after first computation. Diagnoses depend only
        on observations + measurements + reference population, none of
        which change at runtime, so the cache is safe to populate once
        and never invalidate. The cache avoids recomputing the full
        pattern engine + diagnosis engine across all operators on every
        access.

        On failure, logs a warning and returns an empty dict so callers
        can fall back to repo diagnoses. Real bugs surface in the log
        rather than being silently swallowed.
        """
        if self._diagnoses_cache is not None:
            return self._diagnoses_cache
        try:
            cohort_patterns = self.detect_cohort_patterns()
            diag_engine = DiagnosisEngine()
            self._diagnoses_cache = diag_engine.generate_cohort_diagnoses(cohort_patterns)
            return self._diagnoses_cache
        except Exception as e:
            logging.getLogger(__name__).warning(
                "generate_cohort_diagnoses failed, falling back to repo diagnoses: %s", e,
            )
            return {}

    def recommend_interventions(self, operator_id: str) -> list:
        """Recommend interventions for an operator based on their diagnoses."""
        diags = self.generate_diagnoses(operator_id)
        mgr = InterventionManager()
        recs = mgr.recommend(diags)
        return [r.to_dict() for r in recs]

    def intervention_catalog(self) -> list:
        """Return the full intervention catalog."""
        reg = InterventionRegistry()
        return [e.to_dict() for e in reg.all()]

    def verify_intervention(self, intervention_id: str) -> VerificationResult:
        """Verify a pre/post intervention with target + non-target deltas.

        Per P1 acceptance: "pre/post verifier shows target + non-target metric
        deltas" and "intervention failure is representable and reportable."
        """
        ivs = [i for i in self.interventions if i.intervention_id == intervention_id]
        if not ivs:
            raise ValueError(f"Unknown intervention: {intervention_id}")
        iv = ivs[0]
        obs = self.repo.observations_for(iv.operator_id)
        c = self.cohort
        verifier = PrePostVerifier(self.engine)
        return verifier.verify(iv, obs, c.window_start, c.window_end)

    def verify_all_interventions(self) -> List[VerificationResult]:
        """Verify all interventions in the cohort."""
        c = self.cohort
        verifier = PrePostVerifier(self.engine)
        results: List[VerificationResult] = []
        for iv in self.interventions:
            obs = self.repo.observations_for(iv.operator_id)
            try:
                result = verifier.verify(iv, obs, c.window_start, c.window_end)
                results.append(result)
            except Exception as e:
                # Log but don't suppress silently — surface the issue for debugging
                # without aborting the whole batch.
                import logging
                logging.getLogger(__name__).warning(
                    "verify_all_interventions: skipped %s for operator %s: %s",
                    iv.intervention_id, iv.operator_id, e,
                )
        return results

    # ── P1+: Write operations (MCP write tools) ──────────────────────────

    def assign_intervention(
        self,
        operator_id: str,
        catalog_id: str,
        target_metric: str,
        followup_days: int,
        reason_pattern: str = "",
        intervention_id: str = "",
    ) -> Intervention:
        """Assign a new intervention and persist it in service state.

        Per `08` §Write tools (P1+): the caller must supply authorized_by
        (enforced in the MCP layer). The service enforces target_metric and
        followup_days per P1 acceptance: "intervention declares target
        metric/window before follow-up."

        The assigned intervention is appended to the in-memory intervention
        list so that subsequent read tools (get_intervention_status,
        verify_change) observe it.
        """
        from datetime import date as _date
        from interventions import InterventionManager

        mgr = InterventionManager()
        iv_id = intervention_id or f"int_mcp_{operator_id}_{catalog_id}_{_date.today().isoformat()}"
        iv = mgr.assign(
            intervention_id=iv_id,
            operator_id=operator_id,
            catalog_id=catalog_id,
            reason_pattern=reason_pattern or "MCP-assigned",
            target_metric=target_metric,
            start_date=_date.today(),
            followup_days=followup_days,
            synthetic=True,
        )
        self._assigned_interventions.append(iv)
        return iv

    def close_intervention(
        self,
        intervention_id: str,
        outcome: str,
    ) -> Intervention:
        """Close an intervention with a declared outcome and persist the change.

        Per `08` §Write tools (P1+): the caller must supply authorized_by
        (enforced in the MCP layer). Per P1: "intervention failure is
        representable and reportable." Outcome must be one of
        SUCCESS/PARTIAL/NO_EFFECT/NEGATIVE.

        The closure is recorded in service state so that subsequent read
        tools observe the updated outcome.
        """
        from domain.intervention import InterventionOutcome

        ivs = [i for i in self.interventions if i.intervention_id == intervention_id]
        if not ivs:
            raise ValueError(f"Unknown intervention: {intervention_id}")
        outcome_enum = InterventionOutcome(outcome)
        self._closed_intervention_ids[intervention_id] = outcome_enum
        # Return the updated intervention from the now-mutated property
        updated = [i for i in self.interventions if i.intervention_id == intervention_id]
        return updated[0]

    def create_experiment(
        self,
        operator_id: str,
        target_metric: str,
        window_days: int,
        description: str = "",
    ) -> dict:
        """Create a predeclared experiment and persist it in service state.

        Per `08` §Write tools (P1+): the caller must supply authorized_by
        (enforced in the MCP layer). Per P2: experiments are predeclared
        with metrics before execution.

        The experiment is recorded in service state so that subsequent read
        tools can enumerate it.
        """
        from datetime import date as _date
        experiment = {
            "experiment_id": f"exp_{operator_id}_{target_metric}_{_date.today().isoformat()}",
            "operator_id": operator_id,
            "target_metric": target_metric,
            "window_days": window_days,
            "description": description or "Predeclared experiment",
            "start_date": _date.today().isoformat(),
            "label": "EXPERIMENT — predeclared metrics, not outcome claims",
        }
        self._experiments.append(experiment)
        return experiment

    @property
    def experiments(self) -> List[dict]:
        """All predeclared experiments created via write tools."""
        if isinstance(self.repo, SQLiteRepository):
            return self.repo.experiments
        return list(self._experiments)

    def record_workflow_observation(
        self,
        operator_id: str,
        stage_id: str,
        workflow_id: str = "",
        provisional_fit: Optional[float] = None,
        evidence_count: int = 0,
        time_spent_minutes: float = 0.0,
        tasks_completed: int = 0,
        external_quality_score: Optional[float] = None,
        status: str = "provisional",
    ) -> WorkflowObservation:
        """Record a workflow stage observation and persist it.

        Per `08` §Write tools (P1+): the caller must supply authorized_by
        (enforced in the MCP layer). The observation is persisted to the
        repository so subsequent read tools (get_workflow_fit) observe it.
        """
        from datetime import date as _date
        wf_id = workflow_id or self.workflow.workflow_id
        wobs = WorkflowObservation(
            operator_id=operator_id,
            workflow_id=wf_id,
            stage_id=stage_id,
            date=_date.today(),
            time_spent_minutes=time_spent_minutes,
            tasks_completed=tasks_completed,
            external_quality_score=external_quality_score,
            provisional_fit=provisional_fit,
            evidence_count=evidence_count,
            status=status,
            synthetic=True,
        )
        if isinstance(self.repo, SQLiteRepository):
            self.repo.insert_workflow_observation(wobs)
        return wobs

    def attach_outcome_dataset(
        self,
        source_path: str,
        attached_by: str = "",
        operator_id: Optional[str] = None,
    ) -> dict:
        """Attach an external outcome dataset and persist the attachment record.

        Per `08` §Write tools (P1+): the caller must supply authorized_by
        (enforced in the MCP layer). Per P2: outcome joins remain separately
        governed and labeled ASSOCIATION, never CAUSATION.

        Validates that the file exists and counts records. The attachment
        is persisted to the repository so subsequent reads can enumerate
        attached datasets.
        """
        from pathlib import Path
        p = Path(source_path)
        if not p.exists():
            raise FileNotFoundError(f"Outcome dataset not found: {source_path}")

        # Count records (CSV rows minus header, or JSONL lines)
        record_count = 0
        if p.suffix == ".csv":
            with open(p, newline="") as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                record_count = sum(1 for _ in reader)
        elif p.suffix in (".jsonl", ".ndjson"):
            with open(p) as f:
                record_count = sum(1 for line in f if line.strip())
        elif p.suffix == ".json":
            with open(p) as f:
                data = json.load(f)
                record_count = len(data) if isinstance(data, list) else 1

        if isinstance(self.repo, SQLiteRepository):
            dataset_id = self.repo.attach_outcome_dataset(
                source_path=source_path,
                record_count=record_count,
                attached_by=attached_by,
                operator_id=operator_id,
            )
        else:
            dataset_id = len(self._experiments)  # fallback id for in-memory

        return {
            "dataset_id": dataset_id,
            "source_path": source_path,
            "record_count": record_count,
            "attached_by": attached_by,
            "operator_id": operator_id,
            "claim_type": "ASSOCIATION",
            "label": "ATTACHED — outcome dataset registered, associations only (never causation)",
        }

    @property
    def outcome_datasets(self) -> List[dict]:
        """All attached outcome datasets."""
        if isinstance(self.repo, SQLiteRepository):
            return self.repo.outcome_datasets
        return []

    # ── P2: Workflow fit + outcome joins ─────────────────────────────────

    def workflow_fit_report(self) -> WorkflowFitReport:
        """Compute workflow fit for the cohort with sample-size gates.

        Per P2: "workflow fit exposes observation count and uncertainty" and
        "no stage-fit claim without minimum sample rule."
        """
        engine = WorkflowFitEngine()
        wobs = self.repo.workflow_observations
        return engine.compute_cohort_fit(self.operator_ids, self.workflow, wobs)

    def join_outcomes(self, outcome_csv_path: str) -> list:
        """Join external outcome data to pilot internal metrics.

        Per P2: "outcome joins remain separately governed" and "outcome
        analysis separates association from causal claim."

        Returns a list of OutcomeJoinResult objects, each labeled ASSOCIATION.
        """
        gov = OutcomeGovernance.synthetic()
        join_engine = OutcomeJoinEngine(gov)
        records = join_engine.load_outcomes_csv(outcome_csv_path)

        # Build internal deltas from verification results
        internal_deltas: Dict[str, Dict[str, Optional[float]]] = {}
        for vr in self.verify_all_interventions():
            deltas = {}
            for d in vr.deltas:
                deltas[d.metric_id] = d.percent_delta
            internal_deltas[vr.operator_id] = deltas

        results = join_engine.join_cohort(internal_deltas, records)
        return [r.to_dict() for r in results]

    def intervention_outcome_analysis(self, outcome_csv_path: str) -> List[InterventionOutcomeResult]:
        """Cross-analyze intervention results against external outcomes.

        Wires the pre/post verifier (internal metric deltas) to the outcome
        join engine (external outcome deltas). Every result is labeled
        ASSOCIATION — never CAUSATION.

        Per P2: "outcome analysis separates association from causal claim."
        """
        gov = OutcomeGovernance.synthetic()
        join_engine = OutcomeJoinEngine(gov)
        records = join_engine.load_outcomes_csv(outcome_csv_path)

        verifier = PrePostVerifier(self.engine)
        analyzer = InterventionOutcomeAnalyzer(verifier, join_engine)

        c = self.cohort
        obs_by_op: Dict[str, list] = {}
        for iv in self.interventions:
            if iv.operator_id not in obs_by_op:
                obs_by_op[iv.operator_id] = self.repo.observations_for(iv.operator_id)

        return analyzer.analyze(
            interventions=self.interventions,
            observations_by_operator=obs_by_op,
            outcome_records=records,
            baseline_start=c.window_start,
            baseline_end=c.window_end,
        )

    def executive_brief(self) -> str:
        """Generate the Executive Solution Brief (deliverable #11 + #12).

        Per `13`: communicates decisions, next experiments, and the
        next-evaluations flywheel (3-4 evidence-backed observations mapped
        to eval families from `18`).
        """
        from reporting import export_executive_brief
        return export_executive_brief(self)

    # ── P3: Privacy governance surfaces (per `12`) ──────────────────────

    def preferred_manager_objects(self) -> dict:
        """Surface the 8 preferred manager objects per `12` §Development doctrine.

        Returns a dict of object_name → list of findings. These are
        developmental objects, NOT performance rankings. The avoid-list
        (no leaderboard, no punitive labels, no composite score) is
        enforced across the codebase; this method surfaces the positive
        half of the doctrine.
        """
        from governance import compute_preferred_manager_objects
        return compute_preferred_manager_objects(self).to_dict()

    # ── Production gates (per MO§ES™ enterprise pilot readiness framework) ───

    def gate_rules(self) -> List[GateRule]:
        """Return the default gate rules.

        Gates are workflow routing rules, NOT personnel decisions. Every
        gate result carries a DEVELOPMENTAL decision-use label.
        """
        return list(DEFAULT_GATE_RULES)

    def evaluate_gates_for(self, operator_id: str) -> List[GateResult]:
        """Evaluate all gate rules for a single operator.

        Uses the operator's canonical measurements and resolves percentile
        thresholds against the cohort reference population.
        """
        ms = self.score_operator(operator_id)
        percentile_lookup = self._gate_percentile_lookup()
        return evaluate_all_gates(operator_id, ms, percentile_lookup=percentile_lookup)

    def evaluate_cohort_gates(self) -> dict:
        """Evaluate gates for the entire cohort and return a summary dict.

        The summary includes total evaluations, total fired, operators
        flagged, counts by action, and the list of fired gates. Every
        result carries a DEVELOPMENTAL decision-use label.
        """
        cohort_ms = self.score_cohort()
        percentile_lookup = self._gate_percentile_lookup()
        results = evaluate_cohort_gates(
            self.operator_ids, cohort_ms, percentile_lookup=percentile_lookup,
        )
        return summarize_gates(results)

    def _gate_percentile_lookup(self) -> Dict[str, float]:
        """Build a metric_id → absolute-value-at-threshold-percentile lookup.

        For each default gate rule, resolves the gate's percentile threshold
        to an absolute metric value using the reference population
        distributions (e.g. p10 → 2.1). This lets the gate compare an
        operator's raw metric value against the cohort-relative cutoff.
        """
        lookup: Dict[str, float] = {}
        ref = self.reference_population
        for rule in DEFAULT_GATE_RULES:
            if not rule.is_percentile:
                continue
            dist = ref.distributions.get(rule.metric_id)
            if not dist:
                continue
            # Look up the absolute value at the rule's percentile (e.g. p10)
            key = f"p{int(rule.threshold)}"
            abs_val = dist.get(key)
            if abs_val is not None:
                lookup[rule.metric_id] = abs_val
        return lookup

    def replicate_finding(
        self,
        finding_type: str,
        finding_id: str,
        split_method: str = "window",
    ) -> ReplicationResult:
        """Replicate a finding across a window or cohort split.

        Per P2: "replicated validation — not built." This checks whether a
        descriptive finding (pattern, divergence) is stable across splits.

        Replication is descriptive stability, NOT causal validation.
        """
        engine = ReplicationEngine(self.engine)
        c = self.cohort
        method = SplitMethod(split_method)

        if finding_type == "pattern":
            # finding_id is the pattern_id; we need an operator_id
            # Use the first operator that has this pattern
            cohort_patterns = self.detect_cohort_patterns()
            operator_id = None
            for oid, patterns in cohort_patterns.items():
                if any(p.pattern_id == finding_id for p in patterns):
                    operator_id = oid
                    break
            if operator_id is None:
                return ReplicationResult(
                    finding_type="pattern",
                    finding_id=finding_id,
                    split_method=split_method,
                    status=ReplicationStatus.INSUFFICIENT_DATA.value,
                    split_a_count=0, split_b_count=0,
                    split_a_found=False, split_b_found=False,
                    synthetic=True,
                    caveat=f"Pattern {finding_id} not found in any operator.",
                )
            obs = self.repo.observations_for(operator_id)
            return engine.replicate_pattern(
                pattern_id=finding_id,
                operator_id=operator_id,
                observations=obs,
                window_start=c.window_start,
                window_end=c.window_end,
                split_method=method,
                reference_population=self.reference_population,
            )

        elif finding_type == "divergence":
            # finding_id is the operator_id
            return engine.replicate_divergence(
                operator_id=finding_id,
                observations=self.repo.observations_for(finding_id),
                all_operator_ids=self.operator_ids,
                all_observations=self.observations,
                window_start=c.window_start,
                window_end=c.window_end,
                split_method=method,
            )

        else:
            return ReplicationResult(
                finding_type=finding_type,
                finding_id=finding_id,
                split_method=split_method,
                status=ReplicationStatus.INSUFFICIENT_DATA.value,
                split_a_count=0, split_b_count=0,
                split_a_found=False, split_b_found=False,
                synthetic=True,
                caveat=f"Unknown finding type: {finding_type}. Supported: pattern, divergence.",
            )

    # ── Gap 4: Task context for difficulty-aware benchmarking ───────────

    def context_adjustment(
        self,
        operator_id: str,
        context: TaskContext,
        baseline_difficulty: float = 0.5,
    ) -> dict:
        """Adjust an operator's metric scores for task difficulty context.

        Per Jaimie's review (Gap 4): "Two operators in same workflow
        stage solving different complexity tasks shouldn't be benchmarked
        as peers without context adjustment."

        An operator doing a high-complexity task with a Yield of 0.20 is
        not the same as an operator doing a low-complexity task with a
        Yield of 0.20. This method normalizes metrics to a common
        difficulty scale so fair developmental benchmarking is possible.

        The adjustment is multiplicative relative to a baseline
        difficulty (default 0.5, the neutral midpoint). It is bounded to
        [0.5x, 2.0x] so it is a normalization, never a reward or
        penalty.

        Governance: developmental normalization for fair benchmarking,
        NOT a personnel adjustment. No punitive labels. Outcome claims
        are ASSOCIATION, never CAUSATION.

        Args:
            operator_id: The operator whose metrics to adjust.
            context: The TaskContext for the task being benchmarked.
            baseline_difficulty: Reference difficulty to normalize against.

        Returns:
            A dict with the operator_id, task_context, and a list of
            per-metric adjusted values (each carrying the raw value,
            adjusted value, and context tag).
        """
        ms = self.score_operator(operator_id)
        adjusted = context_adjustment(ms, context, baseline_difficulty)
        return {
            "operator_id": operator_id,
            "task_context": context.to_dict(),
            "baseline_difficulty": baseline_difficulty,
            "adjusted_metrics": adjusted,
            "label": "DEVELOPMENTAL — difficulty-normalized for fair benchmarking",
            "synthetic": True,
        }

    def score_operator_with_context(
        self,
        operator_id: str,
        context: TaskContext,
        baseline_difficulty: float = 0.5,
    ) -> List[dict]:
        """Score an operator and tag each measurement with its task context.

        Per Gap 4: "Add context to the measurement pipeline so metrics
        can be tagged with their task context."

        Returns a list of enriched measurement dicts, each carrying the
        canonical metric fields plus `context_adjusted_value` and
        `task_context`. The original immutable Measurement objects are
        untouched; this produces enriched copies for downstream
        consumers that need difficulty-aware comparison.
        """
        ms = self.score_operator(operator_id)
        return context_adjustment(ms, context, baseline_difficulty)

    # ── Gap 5: Cross-system operator identity ───────────────────────────

    def add_operator_identity(
        self,
        canonical_operator_id: str,
        system: str,
        system_id: str,
    ) -> dict:
        """Add a cross-system identity mapping for a canonical operator.

        Per Jaimie's review (Gap 5): "Need a robust way to map operators
        across platforms."

        Maps a system-specific identity (e.g. "alice@company.com" in
        ChatGPT) to the canonical operator ID (e.g. "alice") so that
        telemetry from multiple platforms can be attributed correctly.

        If the same (system, system_id) pair is already mapped to a
        *different* canonical operator, an IdentityConflictError is
        raised rather than silently overwriting — this prevents
        mis-attribution of telemetry.

        Args:
            canonical_operator_id: The canonical pseudonymous operator ID.
            system: The platform/system name (e.g. "chatgpt", "claude").
            system_id: The system-specific identity handle.

        Returns:
            A dict confirming the mapping was added.
        """
        self._identity_registry.add_mapping(canonical_operator_id, system, system_id)
        return {
            "canonical_operator_id": canonical_operator_id,
            "system": system,
            "system_id": system_id,
            "status": "added",
        }

    def resolve_operator_identity(
        self,
        system: str,
        system_id: str,
    ) -> dict:
        """Resolve a system-specific identity to the canonical operator.

        Per Gap 5: "Supports identity resolution: given a system +
        system-specific ID, resolve to the canonical operator."

        Args:
            system: The platform/system name.
            system_id: The system-specific identity handle.

        Returns:
            A dict with the resolved canonical_operator_id (or None if
            no mapping exists) and the resolution status.
        """
        canonical = self._identity_registry.resolve(system, system_id)
        return {
            "system": system,
            "system_id": system_id,
            "canonical_operator_id": canonical,
            "resolved": canonical is not None,
        }

    @property
    def operator_identity_registry(self) -> OperatorIdentity:
        """The cross-system identity registry (Gap 5)."""
        return self._identity_registry

    # ── Gap 8: Decision-oriented reporting ──────────────────────────────

    def decision_report(self, operator_id: str = "") -> dict:
        """Produce a decision-oriented report translating metrics to actions.

        Per Jaimie's review (Gap 8): "Translate measurement vocabulary
        to decision vocabulary in the product surface."

        Instead of "Yield is 0.15 (10th percentile)" → "This operator's
        output efficiency is in the bottom 10% of the cohort. Recommended
        action: context structuring coaching."

        Decision recommendations are developmental (coaching, workshops,
        reviews) — never personnel actions. Outcome claims are
        ASSOCIATION, never CAUSATION. No punitive labels.

        Args:
            operator_id: If provided, produce a per-operator decision
                report. If empty, produce a cohort-level summary of
                decision recommendations.

        Returns:
            A dict with decision-oriented findings and recommended
            developmental actions.
        """
        from reporting import build_decision_report
        return build_decision_report(self, operator_id=operator_id)
