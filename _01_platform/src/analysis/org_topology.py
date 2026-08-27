"""EVAL-013 — Org AI Topology.

Organization-level map of AI operating structure. Synthesizes operator
metrics, team groupings, role families, platform usage, and capability
distribution into an organization-wide view.

Per spec 18:
    Input: team/role/workflow relationships plus operator patterns.
    Output: organization-level map of AI operating structure.

Per Build B §6.3 (Operator Contribution Eval) and §6.10 (Comparative Eval):
    This eval cross-cuts team, role, and platform dimensions to produce
    the org-level topology — where capability is concentrated, where it's
    distributed, and what structural patterns exist.

The topology is NOT a ranking. It is a structural map showing:
    - Team-level metric distributions
    - Role-level capability patterns
    - Platform adoption distribution
    - Capability concentration (Gini-like measure)
    - Cross-team complementarity
    - Single-point-of-failure risks
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.measurement import Measurement
from domain.operator import Operator


@dataclass(frozen=True, slots=True)
class TeamTopology:
    """One team's position in the org AI topology."""
    team: str
    operator_count: int
    median_metrics: Dict[str, float] = field(default_factory=dict)
    metric_spread: Dict[str, float] = field(default_factory=dict)  # IQR
    platforms_used: List[str] = field(default_factory=list)
    role_composition: Dict[str, int] = field(default_factory=dict)
    level_composition: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "team": self.team,
            "operator_count": self.operator_count,
            "median_metrics": dict(self.median_metrics),
            "metric_spread": dict(self.metric_spread),
            "platforms_used": list(self.platforms_used),
            "role_composition": dict(self.role_composition),
            "level_composition": dict(self.level_composition),
        }


@dataclass(frozen=True, slots=True)
class CapabilityConcentration:
    """Measures how concentrated AI capability is across the org.

    A high concentration means a few operators account for most of the
    capability. A low concentration means capability is distributed.
    """
    metric_id: str
    gini: float  # 0 = perfectly distributed, 1 = perfectly concentrated
    top_10pct_share: float  # share of total metric value held by top 10%
    top_20pct_share: float
    bottom_50pct_share: float
    interpretation: str

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "gini": round(self.gini, 4),
            "top_10pct_share": round(self.top_10pct_share, 4),
            "top_20pct_share": round(self.top_20pct_share, 4),
            "bottom_50pct_share": round(self.bottom_50pct_share, 4),
            "interpretation": self.interpretation,
        }


@dataclass(frozen=True, slots=True)
class PlatformAdoption:
    """Platform adoption distribution across the org."""
    platform: str
    operator_count: int
    share: float  # fraction of org using this platform
    median_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "operator_count": self.operator_count,
            "share": round(self.share, 4),
            "median_metrics": dict(self.median_metrics),
        }


@dataclass(frozen=True, slots=True)
class SinglePointOfFailure:
    """A capability that depends on very few operators."""
    capability: str  # metric_id or pattern label
    operator_ids: List[str]
    team: str
    risk_level: str  # "high" | "moderate" | "low"
    description: str

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "operator_ids": list(self.operator_ids),
            "team": self.team,
            "risk_level": self.risk_level,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class OrgTopology:
    """The complete organization-level AI topology map."""
    total_operators: int
    total_teams: int
    team_topologies: List[TeamTopology] = field(default_factory=list)
    capability_concentration: List[CapabilityConcentration] = field(default_factory=list)
    platform_adoption: List[PlatformAdoption] = field(default_factory=list)
    single_points_of_failure: List[SinglePointOfFailure] = field(default_factory=list)
    cross_team_complementarity: Dict[str, str] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "total_operators": self.total_operators,
            "total_teams": self.total_teams,
            "team_topologies": [t.to_dict() for t in self.team_topologies],
            "capability_concentration": [c.to_dict() for c in self.capability_concentration],
            "platform_adoption": [p.to_dict() for p in self.platform_adoption],
            "single_points_of_failure": [s.to_dict() for s in self.single_points_of_failure],
            "cross_team_complementarity": dict(self.cross_team_complementarity),
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


def _median(values: List[float]) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    if n % 2 == 0:
        return (s[n // 2 - 1] + s[n // 2]) / 2
    return s[n // 2]


def _iqr(values: List[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    q1 = s[n // 4] if n > 3 else s[0]
    q3 = s[(3 * n) // 4] if n > 3 else s[-1]
    return q3 - q1


def _share_of_total(values: List[float], top_fraction: float) -> float:
    """Share of total held by the top fraction of values."""
    if not values:
        return 0.0
    s = sorted(v for v in values if v is not None and v >= 0)
    n = len(s)
    if n == 0:
        return 0.0
    total = sum(s)
    if total == 0:
        return 0.0
    top_n = max(1, int(n * top_fraction))
    top_sum = sum(s[-top_n:])
    return top_sum / total


def compute_org_topology(
    operators: List[Operator],
    measurements: List[Measurement],
    metric_ids: List[str],
) -> OrgTopology:
    """Compute the organization-level AI topology map.

    Args:
        operators: All operators in the cohort.
        measurements: All measurements for the cohort.
        metric_ids: Canonical metric IDs to analyze.

    Returns:
        OrgTopology with team breakdowns, concentration, platform
        adoption, and single-point-of-failure risks.
    """
    total_ops = len(operators)
    if total_ops == 0:
        return OrgTopology(total_operators=0, total_teams=0, summary="No operators.")

    # Build lookup: operator_id → operator
    op_map = {o.operator_id: o for o in operators}

    # Build lookup: (operator_id, metric_id) → value
    ms_map: Dict[Tuple[str, str], float] = {}
    for m in measurements:
        if m.value is not None:
            ms_map[(m.operator_id, m.metric_id)] = m.value

    # ── Team topologies ──────────────────────────────────────────────
    teams: Dict[str, List[Operator]] = {}
    for o in operators:
        team = o.team or "unassigned"
        teams.setdefault(team, []).append(o)

    team_topologies: List[TeamTopology] = []
    for team_name, team_ops in sorted(teams.items()):
        medians: Dict[str, float] = {}
        spreads: Dict[str, float] = {}
        for mid in metric_ids:
            vals = [ms_map.get((o.operator_id, mid)) for o in team_ops]
            vals = [v for v in vals if v is not None]
            med = _median(vals)
            if med is not None:
                medians[mid] = round(med, 4)
            spreads[mid] = round(_iqr(vals), 4)

        platforms = sorted(set(o.primary_platform for o in team_ops if o.primary_platform))
        roles: Dict[str, int] = {}
        levels: Dict[str, int] = {}
        for o in team_ops:
            r = o.role_family or "unknown"
            roles[r] = roles.get(r, 0) + 1
            lv = o.level or "unknown"
            levels[lv] = levels.get(lv, 0) + 1

        team_topologies.append(TeamTopology(
            team=team_name,
            operator_count=len(team_ops),
            median_metrics=medians,
            metric_spread=spreads,
            platforms_used=platforms,
            role_composition=roles,
            level_composition=levels,
        ))

    # ── Capability concentration ─────────────────────────────────────
    concentration: List[CapabilityConcentration] = []
    for mid in metric_ids:
        vals = [ms_map.get((o.operator_id, mid)) for o in operators]
        vals = [v for v in vals if v is not None and v >= 0]
        if not vals:
            continue
        g = _gini(vals)
        top10 = _share_of_total(vals, 0.10)
        top20 = _share_of_total(vals, 0.20)
        bot50 = _share_of_total(sorted(vals, reverse=True), 0.50)

        if g > 0.5:
            interp = "Highly concentrated — a few operators account for most capability."
        elif g > 0.3:
            interp = "Moderately concentrated — capability is unevenly distributed."
        else:
            interp = "Distributed — capability is spread across the organization."

        concentration.append(CapabilityConcentration(
            metric_id=mid,
            gini=g,
            top_10pct_share=top10,
            top_20pct_share=top20,
            bottom_50pct_share=bot50,
            interpretation=interp,
        ))

    # ── Platform adoption ────────────────────────────────────────────
    platform_groups: Dict[str, List[Operator]] = {}
    for o in operators:
        p = o.primary_platform or "unknown"
        platform_groups.setdefault(p, []).append(o)

    platform_adoption: List[PlatformAdoption] = []
    for platform, plat_ops in sorted(platform_groups.items()):
        medians: Dict[str, float] = {}
        for mid in metric_ids:
            vals = [ms_map.get((o.operator_id, mid)) for o in plat_ops]
            vals = [v for v in vals if v is not None]
            med = _median(vals)
            if med is not None:
                medians[mid] = round(med, 4)
        platform_adoption.append(PlatformAdoption(
            platform=platform,
            operator_count=len(plat_ops),
            share=len(plat_ops) / total_ops,
            median_metrics=medians,
        ))

    # ── Single points of failure ─────────────────────────────────────
    # For each team + metric, check if capability is concentrated in
    # ≤2 operators (high risk) or ≤3 (moderate risk).
    spofs: List[SinglePointOfFailure] = []
    for team_name, team_ops in teams.items():
        for mid in metric_ids:
            vals = [(o.operator_id, ms_map.get((o.operator_id, mid), 0)) for o in team_ops]
            vals = [(oid, v) for oid, v in vals if v is not None and v >= 0]
            if len(vals) < 3:
                continue
            total = sum(v for _, v in vals)
            if total == 0:
                continue
            # Find operators who contribute >40% of total
            major = [(oid, v) for oid, v in vals if v / total > 0.40]
            if len(major) <= 2 and len(major) > 0:
                risk = "high" if len(major) <= 1 else "moderate"
                spofs.append(SinglePointOfFailure(
                    capability=mid,
                    operator_ids=[oid for oid, _ in major],
                    team=team_name,
                    risk_level=risk,
                    description=f"{len(major)} operator(s) account for >40% of {mid} in {team_name}",
                ))

    # ── Cross-team complementarity ───────────────────────────────────
    # Identify teams whose median metric profiles complement each other
    # (one team's strength offsets another's weakness).
    complementarity: Dict[str, str] = {}
    team_medians: Dict[str, Dict[str, float]] = {}
    for tt in team_topologies:
        team_medians[tt.team] = tt.median_metrics

    team_names = list(team_medians.keys())
    for i, t1 in enumerate(team_names):
        for t2 in team_names[i + 1:]:
            m1 = team_medians[t1]
            m2 = team_medians[t2]
            if not m1 or not m2:
                continue
            # Check if t1 is high where t2 is low and vice versa
            all_metrics = set(m1.keys()) & set(m2.keys())
            if not all_metrics:
                continue
            org_medians = {}
            for mid in all_metrics:
                all_vals = [ms_map.get((o.operator_id, mid), 0) for o in operators]
                all_vals = [v for v in all_vals if v is not None]
                org_medians[mid] = _median(all_vals) or 0

            t1_high_t2_low = any(
                m1[mid] > org_medians[mid] and m2[mid] < org_medians[mid]
                for mid in all_metrics
            )
            t2_high_t1_low = any(
                m2[mid] > org_medians[mid] and m1[mid] < org_medians[mid]
                for mid in all_metrics
            )
            if t1_high_t2_low and t2_high_t1_low:
                complementarity[f"{t1} ↔ {t2}"] = (
                    f"Complementary: {t1} and {t2} have offsetting strengths across metrics."
                )

    # ── Summary ──────────────────────────────────────────────────────
    high_concentration = [c for c in concentration if c.gini > 0.4]
    high_spof = [s for s in spofs if s.risk_level == "high"]
    summary_parts = [
        f"{total_ops} operators across {len(teams)} teams.",
        f"{len(platform_adoption)} platforms in use.",
    ]
    if high_concentration:
        summary_parts.append(
            f"High capability concentration in {len(high_concentration)} metric(s): "
            + ", ".join(c.metric_id for c in high_concentration) + "."
        )
    if high_spof:
        summary_parts.append(
            f"{len(high_spof)} high-risk single point(s) of failure detected."
        )
    if complementarity:
        summary_parts.append(
            f"{len(complementarity)} complementary team pair(s) identified."
        )

    return OrgTopology(
        total_operators=total_ops,
        total_teams=len(teams),
        team_topologies=team_topologies,
        capability_concentration=concentration,
        platform_adoption=platform_adoption,
        single_points_of_failure=spofs,
        cross_team_complementarity=complementarity,
        summary=" ".join(summary_parts),
    )
