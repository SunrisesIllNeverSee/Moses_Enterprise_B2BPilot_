"""EVAL-009 — Team Composition.

Analyzes team-level operator archetype coverage and complementarity.
The core question: does a team have the right mix of operating patterns
to cover the work it needs to do?

Per spec 18:
    Input: operator profiles + stage requirements.
    Output: coverage and complementarity hypotheses.

Per Build B §6.3 (Operator Contribution Eval):
    This eval examines the *composition* of teams — what archetypes are
    present, what's missing, and how well team members complement each
    other. Archetypes are derived from the operator's pattern_demo label
    (a demo-only archetype tag) and/or their metric profile.

    Coverage gaps: archetypes that are absent from a team but present in
    the broader organization. These are hypotheses, not prescriptions.

    Complementarity score: measures how diverse a team's archetype mix is.
    A team with all the same archetype has low complementarity; a team
    with a spread of archetypes has high complementarity.

    Recommended additions: if a team has a coverage gap, suggest which
    archetype would fill it. These are developmental hypotheses, not
    personnel decisions.

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


# Canonical archetype set derived from the demo data's pattern_demo labels.
# These are developmental archetypes, not personnel labels.
KNOWN_ARCHETYPES: List[str] = [
    "balanced_operator",
    "context_compounder",
    "declining_operator",
    "efficient_minimalist",
    "high_volume_burner",
    "improving_operator",
    "kinetic_generator",
    "recursive_builder",
    "volatile_switcher",
]


@dataclass(frozen=True, slots=True)
class TeamCompositionProfile:
    """One team's composition profile."""
    team: str
    operator_count: int
    archetype_distribution: Dict[str, int] = field(default_factory=dict)
    coverage_gaps: List[str] = field(default_factory=list)
    complementarity_score: float = 0.0  # 0–1, higher = more diverse
    recommended_additions: List[str] = field(default_factory=list)
    median_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "team": self.team,
            "operator_count": self.operator_count,
            "archetype_distribution": dict(self.archetype_distribution),
            "coverage_gaps": list(self.coverage_gaps),
            "complementarity_score": round(self.complementarity_score, 4),
            "recommended_additions": list(self.recommended_additions),
            "median_metrics": dict(self.median_metrics),
        }


@dataclass(frozen=True, slots=True)
class TeamComposition:
    """The complete team-composition analysis result."""
    total_teams: int
    team_profiles: List[TeamCompositionProfile] = field(default_factory=list)
    org_archetype_distribution: Dict[str, int] = field(default_factory=dict)
    org_complementarity_score: float = 0.0
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "total_teams": self.total_teams,
            "team_profiles": [t.to_dict() for t in self.team_profiles],
            "org_archetype_distribution": dict(self.org_archetype_distribution),
            "org_complementarity_score": round(self.org_complementarity_score, 4),
            "summary": self.summary,
        }


def _median(values: List[float]) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    if n % 2 == 0:
        return (s[n // 2 - 1] + s[n // 2]) / 2
    return s[n // 2]


def _shannon_evenness(counts: List[int]) -> float:
    """Shannon evenness (normalized entropy) for archetype distribution.

    Returns 0–1 where 1 = perfectly even distribution across archetypes.
    A team with all one archetype gets 0; a team with equal representation
    of many archetypes gets close to 1.
    """
    total = sum(counts)
    if total == 0 or len(counts) <= 1:
        return 0.0
    import math
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log(p)
    max_entropy = math.log(len(counts)) if len(counts) > 1 else 1.0
    if max_entropy == 0:
        return 0.0
    return entropy / max_entropy


def _get_archetype(op: Operator) -> str:
    """Get an operator's archetype label.

    Falls back to "unclassified" if pattern_demo is not set.
    """
    return op.pattern_demo or "unclassified"


def compute_team_composition(
    operators: List[Operator],
    measurements: List[Measurement],
    metric_ids: List[str],
    team_id: str = "",
) -> TeamComposition:
    """Compute team-composition profiles for the cohort.

    Args:
        operators: All operators in the cohort.
        measurements: All measurements for the cohort.
        metric_ids: Canonical metric IDs for median computation.
        team_id: If provided, only analyze this team. If empty, analyze
            all teams.

    Returns:
        TeamComposition with per-team archetype distribution, coverage
        gaps, complementarity scores, and recommended additions.
    """
    if not operators:
        return TeamComposition(total_teams=0, summary="No operators.")

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

    # Filter to a specific team if requested.
    if team_id:
        # Match by team name or by normalized team_id.
        matching_teams = [
            t for t in teams
            if t == team_id
            or t.lower().replace(" ", "_").replace("/", "_") == team_id.lower().replace(" ", "_").replace("/", "_")
        ]
        if matching_teams:
            teams = {t: teams[t] for t in matching_teams}
        else:
            return TeamComposition(
                total_teams=0,
                summary=f"Team {team_id} not found.",
            )

    # Compute org-wide archetype distribution.
    org_archetypes: Dict[str, int] = {}
    for o in operators:
        arch = _get_archetype(o)
        org_archetypes[arch] = org_archetypes.get(arch, 0) + 1

    # All archetypes present in the org (for coverage gap detection).
    org_archetype_set: Set[str] = set(org_archetypes.keys())

    # Org-level complementarity.
    org_counts = list(org_archetypes.values())
    org_complementarity = _shannon_evenness(org_counts)

    team_profiles: List[TeamCompositionProfile] = []
    for team_name, team_ops in sorted(teams.items()):
        # Archetype distribution for this team.
        team_archetypes: Dict[str, int] = {}
        for o in team_ops:
            arch = _get_archetype(o)
            team_archetypes[arch] = team_archetypes.get(arch, 0) + 1

        # Coverage gaps: archetypes present in org but absent in this team.
        team_archetype_set = set(team_archetypes.keys())
        coverage_gaps = sorted(org_archetype_set - team_archetype_set)

        # Complementarity score: Shannon evenness of the team's archetype mix.
        # Use all org archetypes as the base (so teams missing archetypes
        # get penalized in evenness).
        all_archetypes_sorted = sorted(org_archetype_set)
        counts_for_evenness = [team_archetypes.get(a, 0) for a in all_archetypes_sorted]
        complementarity = _shannon_evenness(counts_for_evenness)

        # Recommended additions: suggest archetypes that would fill gaps.
        # Prioritize archetypes that are rare in the org (more valuable to add).
        recommended: List[str] = []
        for gap in coverage_gaps:
            org_count = org_archetypes.get(gap, 0)
            recommended.append(gap)
        # Limit to top 3 recommendations.
        recommended = recommended[:3]

        # Median metrics for the team.
        medians: Dict[str, float] = {}
        for mid in metric_ids:
            vals = [ms_map.get((o.operator_id, mid)) for o in team_ops]
            vals = [v for v in vals if v is not None]
            med = _median(vals)
            if med is not None:
                medians[mid] = round(med, 4)

        team_profiles.append(TeamCompositionProfile(
            team=team_name,
            operator_count=len(team_ops),
            archetype_distribution=team_archetypes,
            coverage_gaps=coverage_gaps,
            complementarity_score=complementarity,
            recommended_additions=recommended,
            median_metrics=medians,
        ))

    # Summary.
    summary_parts = [
        f"{len(teams)} team(s) analyzed.",
        f"Org-level complementarity: {org_complementarity:.2f}.",
    ]
    low_complementarity = [t for t in team_profiles if t.complementarity_score < 0.3]
    if low_complementarity:
        summary_parts.append(
            f"{len(low_complementarity)} team(s) with low complementarity (< 0.30)."
        )
    total_gaps = sum(len(t.coverage_gaps) for t in team_profiles)
    if total_gaps:
        summary_parts.append(f"{total_gaps} total coverage gap(s) identified.")

    return TeamComposition(
        total_teams=len(teams),
        team_profiles=team_profiles,
        org_archetype_distribution=org_archetypes,
        org_complementarity_score=org_complementarity,
        summary=" ".join(summary_parts),
    )
