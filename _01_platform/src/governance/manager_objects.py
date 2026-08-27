"""Preferred manager objects per `12` §Development doctrine.

Surfaces the 8 preferred manager objects as named, first-class developmental
outputs. These are NOT performance rankings — they are the positive half of
the development doctrine (the "build these" list). The avoid-list (no
bottom-employee leaderboard, no automatic adverse-action ranking, no punitive
failure labels, no unsupported productivity claims) is enforced across the
codebase; this module surfaces the objects the product should build.

The 8 preferred objects (per `12`):
    1. development groups   — cohorts advancing together
    2. fastest improvers    — operators with positive trajectory
    3. stalled cohorts      — groups plateaued at the same level
    4. workflow bottlenecks — shared structural friction across operators
    5. tool/model-fit opportunities — operators whose metrics shift across models
    6. training candidates  — operators whose patterns match an intervention
    7. peer-support matches — complementary operator profiles
    8. remeasurement queue  — interventions awaiting follow-up windows

Each object is a dict of object_name → list of findings. Findings carry
operator_ids (where applicable), evidence, and a developmental framing —
never a ranking. The method is read-only and operates on PilotService data.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from service import PilotService


# The 8 preferred manager objects, in the order `12` lists them.
PREFERRED_OBJECT_NAMES = (
    "development_groups",
    "fastest_improvers",
    "stalled_cohorts",
    "workflow_bottlenecks",
    "tool_model_fit_opportunities",
    "training_candidates",
    "peer_support_matches",
    "remeasurement_queue",
)


class PreferredManagerObjects:
    """Container for the 8 preferred manager objects.

    Each attribute is a list of finding dicts. Findings carry operator_ids
    (where applicable), evidence, and a developmental framing — never a
    ranking. Use `to_dict()` for serialization.
    """

    def __init__(
        self,
        development_groups: List[dict],
        fastest_improvers: List[dict],
        stalled_cohorts: List[dict],
        workflow_bottlenecks: List[dict],
        tool_model_fit_opportunities: List[dict],
        training_candidates: List[dict],
        peer_support_matches: List[dict],
        remeasurement_queue: List[dict],
    ) -> None:
        self.development_groups = development_groups
        self.fastest_improvers = fastest_improvers
        self.stalled_cohorts = stalled_cohorts
        self.workflow_bottlenecks = workflow_bottlenecks
        self.tool_model_fit_opportunities = tool_model_fit_opportunities
        self.training_candidates = training_candidates
        self.peer_support_matches = peer_support_matches
        self.remeasurement_queue = remeasurement_queue

    def to_dict(self) -> dict:
        """Serialize to a dict of object_name → list of findings."""
        return {
            "development_groups": list(self.development_groups),
            "fastest_improvers": list(self.fastest_improvers),
            "stalled_cohorts": list(self.stalled_cohorts),
            "workflow_bottlenecks": list(self.workflow_bottlenecks),
            "tool_model_fit_opportunities": list(self.tool_model_fit_opportunities),
            "training_candidates": list(self.training_candidates),
            "peer_support_matches": list(self.peer_support_matches),
            "remeasurement_queue": list(self.remeasurement_queue),
        }

    @classmethod
    def empty(cls) -> "PreferredManagerObjects":
        return cls([], [], [], [], [], [], [], [])


def compute_preferred_manager_objects(svc: "PilotService") -> PreferredManagerObjects:
    """Compute the 8 preferred manager objects from PilotService data.

    Read-only. Operates on the cohort's measurements, patterns, diagnoses,
    interventions, and workflow observations. All findings are developmental
    — never a ranking, never a punitive label.
    """
    return PreferredManagerObjects(
        development_groups=_development_groups(svc),
        fastest_improvers=_fastest_improvers(svc),
        stalled_cohorts=_stalled_cohorts(svc),
        workflow_bottlenecks=_workflow_bottlenecks(svc),
        tool_model_fit_opportunities=_tool_model_fit_opportunities(svc),
        training_candidates=_training_candidates(svc),
        peer_support_matches=_peer_support_matches(svc),
        remeasurement_queue=_remeasurement_queue(svc),
    )


# ── 1. Development groups ──────────────────────────────────────────────────

def _development_groups(svc: "PilotService") -> List[dict]:
    """Cohorts advancing together — teams whose median metrics are above the
    cohort median (developmental framing: "advancing", not "best").
    """
    team_medians = svc.compare_teams()
    cohort_medians = svc.cohort_medians()
    groups: List[dict] = []
    for team, metrics in team_medians.items():
        # A team is "advancing" if its yield median meets or exceeds the
        # cohort median. Yield is the canonical operating metric.
        team_yield = metrics.get("yield")
        cohort_yield = cohort_medians.get("yield")
        if team_yield is None or cohort_yield is None:
            continue
        if team_yield >= cohort_yield:
            members = [o.operator_id for o in svc.operators if o.team == team]
            groups.append({
                "team": team,
                "operator_ids": members,
                "evidence": f"team yield median {team_yield:.4f} >= cohort median {cohort_yield:.4f}",
                "framing": "developmental — team advancing together; not a ranking",
            })
    return groups


# ── 2. Fastest improvers ───────────────────────────────────────────────────

def _fastest_improvers(svc: "PilotService") -> List[dict]:
    """Operators with a positive trajectory — those whose follow-up window
    measurements improved over baseline. Developmental framing: "improving",
    not "best". Uses the pre/post verifier results where available.
    """
    improvers: List[dict] = []
    try:
        results = svc.verify_all_interventions()
    except Exception:
        return improvers
    for r in results:
        target = r.target_delta
        if target is None or target.percent_delta is None:
            continue
        if target.percent_delta > 0:
            improvers.append({
                "operator_id": r.operator_id,
                "intervention_id": r.intervention_id,
                "target_metric": r.target_metric,
                "improvement_pct": target.percent_delta,
                "evidence": f"{r.target_metric} {target.percent_delta:+.1f}% (follow-up vs baseline)",
                "framing": "developmental — positive trajectory; not a ranking",
            })
    # Sort by numeric improvement magnitude (descending) — NOT by the
    # evidence string (which sorts alphabetically and misranks).
    # DO NOT assign ranks; the sort is for readability only.
    improvers.sort(key=lambda x: x["improvement_pct"], reverse=True)
    return improvers


# ── 3. Stalled cohorts ─────────────────────────────────────────────────────

def _stalled_cohorts(svc: "PilotService") -> List[dict]:
    """Groups plateaued at the same level — teams whose median yield is below
    the cohort median AND whose inter-operator yield spread is small (the
    team is homogeneous at a lower level, suggesting a shared structural
    constraint rather than individual variation). Developmental framing:
    "stalled", not "worst".
    """
    team_medians = svc.compare_teams()
    cohort_medians = svc.cohort_medians()
    op_teams = {o.operator_id: o.team for o in svc.operators}
    stalled: List[dict] = []
    for team, metrics in team_medians.items():
        team_yield = metrics.get("yield")
        cohort_yield = cohort_medians.get("yield")
        if team_yield is None or cohort_yield is None:
            continue
        if team_yield >= cohort_yield:
            continue
        # Compute the spread of yield values within this team.
        team_yield_values = [
            m.value for m in svc.cohort_measurements_flat()
            if m.metric_id == "yield" and m.value is not None
            and op_teams.get(m.operator_id) == team
        ]
        if len(team_yield_values) < 2:
            continue
        spread = max(team_yield_values) - min(team_yield_values)
        cohort_yield_values = [
            m.value for m in svc.cohort_measurements_flat()
            if m.metric_id == "yield" and m.value is not None
        ]
        cohort_spread = (max(cohort_yield_values) - min(cohort_yield_values)) if cohort_yield_values else 1.0
        # Stalled = below median AND tight spread (homogeneous at a lower level).
        if spread <= cohort_spread * 0.5:
            members = [o.operator_id for o in svc.operators if o.team == team]
            stalled.append({
                "team": team,
                "operator_ids": members,
                "evidence": f"team yield median {team_yield:.4f} < cohort median {cohort_yield:.4f}; spread {spread:.4f} (tight)",
                "framing": "developmental — shared structural constraint; not a ranking",
            })
    return stalled


# ── 4. Workflow bottlenecks ────────────────────────────────────────────────

def _workflow_bottlenecks(svc: "PilotService") -> List[dict]:
    """Shared structural friction across operators — workflow stages where
    many operators have low provisional fit. Developmental framing: the
    bottleneck is the stage, not the operators.

    A stage is a bottleneck when >= 25% of its operators have low fit
    (provisional_fit < 0.5), with a minimum of 5 operators (to avoid
    flagging small stages). At the old threshold (10% + min 3), 6 of 7
    stages fired — that was the baseline distribution, not bottleneck
    detection. The 25% threshold surfaces only stages where a quarter
    of operators struggle, which is a real shared structural constraint.
    """
    by_stage = svc.workflow_fit_by_stage()
    bottlenecks: List[dict] = []
    for stage_id, wobs in by_stage.items():
        if not wobs:
            continue
        low_fit = [w for w in wobs if w.provisional_fit is not None and w.provisional_fit < 0.5]
        # A bottleneck is a stage where >= 25% of operators have low fit,
        # with a minimum of 5 operators (to avoid flagging small stages).
        if len(low_fit) >= max(5, len(wobs) * 0.25):
            bottlenecks.append({
                "stage_id": stage_id,
                "operator_ids_with_low_fit": [w.operator_id for w in low_fit],
                "evidence": f"{len(low_fit)}/{len(wobs)} operators with provisional_fit < 0.5 at stage {stage_id}",
                "framing": "developmental — stage is the primary hypothesis; not an operator ranking",
            })
    return bottlenecks


# ── 5. Tool/model-fit opportunities ────────────────────────────────────────

def _tool_model_fit_opportunities(svc: "PilotService") -> List[dict]:
    """Operators whose metrics shift across models — surfaced from the
    P-MODEL-01 pattern detections. Developmental framing: a tool/model-fit
    opportunity, not an operator skill issue.
    """
    cohort_patterns = svc.detect_cohort_patterns()
    opportunities: List[dict] = []
    for oid, patterns in cohort_patterns.items():
        for p in patterns:
            if p.pattern_id == "P-MODEL-01":
                opportunities.append({
                    "operator_id": oid,
                    "evidence": p.evidence_summary,
                    "framing": "developmental — tool/model-fit opportunity; not an operator skill issue",
                })
    return opportunities


# ── 6. Training candidates ─────────────────────────────────────────────────

def _training_candidates(svc: "PilotService") -> List[dict]:
    """Operators whose patterns match a known intervention — surfaced from
    diagnoses with recommended interventions. Developmental framing: a
    training candidate, not an underperformer.

    Deduplicates by (operator_id, pattern_id): keeps only the
    highest-confidence finding per (operator, pattern) pair. If multiple
    diagnoses have the same confidence for the same (operator, pattern),
    the first one encountered is kept. An operator MAY appear multiple
    times if they have multiple different patterns.
    """
    cohort_diags = svc.generate_cohort_diagnoses()
    # Track the best finding per (operator_id, pattern_id) pair.
    best_by_pair: Dict[tuple, dict] = {}
    for oid, diags in cohort_diags.items():
        for d in diags:
            if not d.recommended_interventions:
                continue
            key = (oid, d.pattern_id)
            finding = {
                "operator_id": oid,
                "pattern_id": d.pattern_id,
                "confidence": d.confidence,
                "recommended_interventions": list(d.recommended_interventions),
                "evidence": d.evidence,
                "framing": "developmental — training candidate; not an underperformer label",
            }
            existing = best_by_pair.get(key)
            if existing is None or d.confidence > existing["confidence"]:
                best_by_pair[key] = finding
    return list(best_by_pair.values())


# ── 7. Peer-support matches ────────────────────────────────────────────────

def _peer_support_matches(svc: "PilotService") -> List[dict]:
    """Complementary operator profiles — pair an operator with a low reading
    on a metric with an operator with a high reading on the same metric, so
    they can support each other. Developmental framing: peer support, not a
    ranking. Pairs are unordered and unranked.
    """
    pcts = svc.percentiles()
    # Build operator → yield percentile
    yield_pcts: Dict[str, float] = {}
    for oid, pct_map in pcts.items():
        pct = pct_map.get("yield_percentile")
        if pct is not None and pct.value is not None:
            yield_pcts[oid] = pct.value
    if len(yield_pcts) < 2:
        return []
    sorted_ops = sorted(yield_pcts.items(), key=lambda x: x[1])
    matches: List[dict] = []
    # Pair the lowest with the highest, second-lowest with second-highest, etc.
    n = len(sorted_ops)
    for i in range(min(n // 2, 10)):  # cap at 10 pairs
        low_op, low_pct = sorted_ops[i]
        high_op, high_pct = sorted_ops[n - 1 - i]
        matches.append({
            "operator_ids": [low_op, high_op],
            "evidence": f"yield percentile {low_pct:.1f} ↔ {high_pct:.1f} (complementary)",
            "framing": "developmental — peer-support match; not a ranking",
        })
    return matches


# ── 8. Remeasurement queue ─────────────────────────────────────────────────

def _remeasurement_queue(svc: "PilotService") -> List[dict]:
    """Interventions awaiting follow-up windows — surfaced from interventions
    whose follow-up window has not yet closed or whose outcome is PENDING.
    Developmental framing: a re-measurement queue, not a performance review.
    """
    queue: List[dict] = []
    today = date.today()
    for iv in svc.interventions:
        followup_end = iv.start_date + timedelta(days=iv.followup_days)
        status = "awaiting_followup_window" if today < followup_end else "followup_window_closed_pending_outcome"
        if iv.synthetic_outcome.value == "PENDING":
            queue.append({
                "intervention_id": iv.intervention_id,
                "operator_id": iv.operator_id,
                "target_metric": iv.target_metric,
                "followup_window_end": followup_end.isoformat(),
                "status": status,
                "evidence": f"outcome PENDING; follow-up window ends {followup_end.isoformat()}",
                "framing": "developmental — re-measurement queue; not a performance review",
            })
    return queue
