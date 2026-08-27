"""EVAL-010 — Capability Dependency Risk.

Identifies concentration risks in AI operating patterns across teams and
stages. The core question: is the organization's AI capability concentrated
in too few operators, creating single-point-of-failure risks?

Per spec 18:
    Input: concentration of rare operating patterns across teams/stages.
    Output: single-point-of-failure / coverage risk hypotheses.

Per Build B §6.3 (Operator Contribution Eval):
    This eval examines the *dependency structure* of AI capability:

    - Per-metric Gini coefficient across teams: how concentrated is each
      canonical metric at the team level? A high Gini means a few teams
      hold most of the capability for that metric.
    - Single-point-of-failure detection: if one operator accounts for
      >40% of a team's total for a high-performance metric, that team
      has a dependency risk.
    - Risk summary: aggregate view of concentration and SPOF risks.

    These are *hypotheses* about structural risk, not personnel judgments.
    The goal is to surface coverage gaps so the organization can develop
    capability breadth, not to penalize high performers.

All metrics are content-free (token counts only). No punitive labels or
leaderboards. Outcome claims are ASSOCIATION, never CAUSATION.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.measurement import Measurement
from domain.operator import Operator


@dataclass(frozen=True, slots=True)
class MetricConcentrationRisk:
    """Concentration risk for one metric across teams."""
    metric_id: str
    team_gini: float  # Gini coefficient across team-level totals (0–1)
    interpretation: str
    team_shares: Dict[str, float] = field(default_factory=dict)  # team → share of total

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "team_gini": round(self.team_gini, 4),
            "team_shares": {k: round(v, 4) for k, v in self.team_shares.items()},
            "interpretation": self.interpretation,
        }


@dataclass(frozen=True, slots=True)
class SinglePointOfFailureRisk:
    """A single-point-of-failure risk for a team + metric."""
    team: str
    metric_id: str
    operator_id: str
    operator_share: float  # fraction of team's total for this metric
    team_total: float
    risk_level: str  # "high" | "moderate"
    description: str

    def to_dict(self) -> dict:
        return {
            "team": self.team,
            "metric_id": self.metric_id,
            "operator_id": self.operator_id,
            "operator_share": round(self.operator_share, 4),
            "team_total": round(self.team_total, 4),
            "risk_level": self.risk_level,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class DependencyRisk:
    """The complete capability dependency risk analysis."""
    metric_concentration: List[MetricConcentrationRisk] = field(default_factory=list)
    single_points_of_failure: List[SinglePointOfFailureRisk] = field(default_factory=list)
    total_teams: int = 0
    total_operators: int = 0
    high_risk_count: int = 0
    moderate_risk_count: int = 0
    risk_summary: str = ""
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "metric_concentration": [m.to_dict() for m in self.metric_concentration],
            "single_points_of_failure": [s.to_dict() for s in self.single_points_of_failure],
            "total_teams": self.total_teams,
            "total_operators": self.total_operators,
            "high_risk_count": self.high_risk_count,
            "moderate_risk_count": self.moderate_risk_count,
            "risk_summary": self.risk_summary,
            "summary": self.summary,
        }


def _gini(values: List[float]) -> float:
    """Compute the Gini coefficient for a list of non-negative values.

    0 = perfectly distributed, 1 = perfectly concentrated.
    """
    if not values:
        return 0.0
    sorted_vals = sorted(v for v in values if v is not None and v >= 0)
    n = len(sorted_vals)
    if n == 0:
        return 0.0
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    cumulative = 0.0
    weighted_sum = 0.0
    for i, v in enumerate(sorted_vals):
        cumulative += v
        weighted_sum += (i + 1) * v
    gini = (2 * weighted_sum) / (n * total) - (n + 1) / n
    return max(0.0, min(1.0, gini))


def compute_dependency_risk(
    operators: List[Operator],
    measurements: List[Measurement],
    metric_ids: List[str],
) -> DependencyRisk:
    """Compute capability dependency risk across teams.

    Args:
        operators: All operators in the cohort.
        measurements: All measurements for the cohort.
        metric_ids: Canonical metric IDs to analyze.

    Returns:
        DependencyRisk with per-metric team-level Gini coefficients,
        single-point-of-failure detections, and a risk summary.
    """
    if not operators:
        return DependencyRisk(summary="No operators.")

    # Build lookup: (operator_id, metric_id) → value
    ms_map: Dict[Tuple[str, str], float] = {}
    for m in measurements:
        if m.value is not None:
            ms_map[(m.operator_id, m.metric_id)] = m.value

    # Group operators by team.
    teams: Dict[str, List[Operator]] = {}
    for o in operators:
        team = o.team or "unassigned"
        teams.setdefault(team, []).append(o)

    total_teams = len(teams)
    total_ops = len(operators)

    # ── Per-metric team-level Gini ───────────────────────────────────
    metric_concentration: List[MetricConcentrationRisk] = []
    for mid in metric_ids:
        # Compute team-level totals for this metric.
        team_totals: Dict[str, float] = {}
        for team_name, team_ops in teams.items():
            total = sum(
                ms_map.get((o.operator_id, mid), 0) for o in team_ops
            )
            team_totals[team_name] = total

        all_totals = list(team_totals.values())
        grand_total = sum(all_totals)
        g = _gini(all_totals)

        # Team shares.
        team_shares: Dict[str, float] = {}
        if grand_total > 0:
            for t, v in team_totals.items():
                team_shares[t] = v / grand_total

        if g > 0.5:
            interp = "Highly concentrated — a few teams hold most capability."
        elif g > 0.3:
            interp = "Moderately concentrated — capability is unevenly distributed across teams."
        else:
            interp = "Distributed — capability is spread across teams."

        metric_concentration.append(MetricConcentrationRisk(
            metric_id=mid,
            team_gini=g,
            interpretation=interp,
            team_shares=team_shares,
        ))

    # ── Single-point-of-failure detection ────────────────────────────
    # For each team + metric, check if one operator accounts for >40%
    # of the team's total for that metric.
    spofs: List[SinglePointOfFailureRisk] = []
    for team_name, team_ops in teams.items():
        if len(team_ops) < 3:
            continue  # Small teams are inherently concentrated; skip.
        for mid in metric_ids:
            op_values: List[Tuple[str, float]] = []
            for o in team_ops:
                v = ms_map.get((o.operator_id, mid), 0)
                if v is not None and v >= 0:
                    op_values.append((o.operator_id, v))

            team_total = sum(v for _, v in op_values)
            if team_total <= 0:
                continue

            # Find operators who account for >40% of the team's total.
            for oid, v in op_values:
                share = v / team_total
                if share > 0.40:
                    risk_level = "high" if share > 0.60 else "moderate"
                    spofs.append(SinglePointOfFailureRisk(
                        team=team_name,
                        metric_id=mid,
                        operator_id=oid,
                        operator_share=share,
                        team_total=team_total,
                        risk_level=risk_level,
                        description=(
                            f"Operator {oid} accounts for {share:.0%} of "
                            f"{team_name}'s {mid} — potential single point of failure."
                        ),
                    ))

    # Deduplicate: if the same operator is flagged for the same team+metric
    # (shouldn't happen, but be safe), keep the first.
    seen: Set[Tuple[str, str, str]] = set()
    unique_spofs: List[SinglePointOfFailureRisk] = []
    for s in spofs:
        key = (s.team, s.metric_id, s.operator_id)
        if key not in seen:
            seen.add(key)
            unique_spofs.append(s)
    spofs = unique_spofs

    high_risk = [s for s in spofs if s.risk_level == "high"]
    moderate_risk = [s for s in spofs if s.risk_level == "moderate"]

    # ── Risk summary ─────────────────────────────────────────────────
    high_concentration = [c for c in metric_concentration if c.team_gini > 0.4]
    risk_parts: List[str] = []
    if high_concentration:
        risk_parts.append(
            f"High team-level concentration in {len(high_concentration)} metric(s): "
            + ", ".join(c.metric_id for c in high_concentration) + "."
        )
    if high_risk:
        risk_parts.append(f"{len(high_risk)} high-risk single point(s) of failure.")
    if moderate_risk:
        risk_parts.append(f"{len(moderate_risk)} moderate-risk concentration(s).")
    if not risk_parts:
        risk_parts.append("No significant dependency risks detected.")
    risk_summary = " ".join(risk_parts)

    # ── Summary ──────────────────────────────────────────────────────
    summary_parts = [
        f"{total_ops} operators across {total_teams} teams.",
        f"{len(metric_concentration)} metric(s) analyzed for team-level concentration.",
        risk_summary,
    ]

    return DependencyRisk(
        metric_concentration=metric_concentration,
        single_points_of_failure=spofs,
        total_teams=total_teams,
        total_operators=total_ops,
        high_risk_count=len(high_risk),
        moderate_risk_count=len(moderate_risk),
        risk_summary=risk_summary,
        summary=" ".join(summary_parts),
    )
