"""EVAL-014 — Operator Similarity Search.

Finds the nearest comparable operators/cohorts based on canonical metric
vectors. This is NOT a personality match — it is a metric-space nearest-
neighbor search.

Per spec 18:
    Input: canonical metric vectors + declared normalization.
    Output: nearest comparable operators/cohorts; not a personality match.

Per Build B §6.10 (Comparative Eval):
    The Comparative Eval places an operator's results in context. This
    module implements the similarity-search half: given an operator,
    find the N most similar operators by metric profile.

Similarity is computed using normalized Euclidean distance across the
5 canonical metrics. Normalization uses the cohort's percentile ranks
so that operators are compared on their relative position, not absolute
token counts (which vary by platform/model).

Results carry:
    - The distance metric and normalization method
    - The nearest N operators with their distance scores
    - Whether the nearest neighbors form a meaningful cluster
    - A note that this is metric similarity, not personality match
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
class SimilarityMatch:
    """One nearest-neighbor match."""
    operator_id: str
    pseudonym: str
    team: Optional[str]
    distance: float  # normalized Euclidean distance (0 = identical)
    similarity: float  # 1 - distance, on a 0-1 scale
    metric_vector: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "pseudonym": self.pseudonym,
            "team": self.team,
            "distance": round(self.distance, 4),
            "similarity": round(self.similarity, 4),
            "metric_vector": dict(self.metric_vector),
        }


@dataclass(frozen=True, slots=True)
class SimilarityResult:
    """The result of an operator similarity search."""
    query_operator_id: str
    normalization: str  # "percentile_rank"
    distance_metric: str  # "euclidean"
    nearest_neighbors: List[SimilarityMatch] = field(default_factory=list)
    cluster_quality: str = ""  # "tight" | "moderate" | "dispersed"
    cluster_description: str = ""
    note: str = "Metric similarity, not personality match. Operators with similar operating patterns, not similar people."

    def to_dict(self) -> dict:
        return {
            "query_operator_id": self.query_operator_id,
            "normalization": self.normalization,
            "distance_metric": self.distance_metric,
            "nearest_neighbors": [n.to_dict() for n in self.nearest_neighbors],
            "cluster_quality": self.cluster_quality,
            "cluster_description": self.cluster_description,
            "note": self.note,
        }


def _percentile_rank(value: float, all_values: List[float]) -> float:
    """Compute the percentile rank of a value within a distribution.

    Returns a 0-100 score. Used for normalization so operators are
    compared on relative position, not absolute token counts.
    """
    if not all_values:
        return 0.0
    count_below = sum(1 for v in all_values if v < value)
    count_equal = sum(1 for v in all_values if v == value)
    n = len(all_values)
    # Standard percentile rank formula
    return 100.0 * (count_below + 0.5 * count_equal) / n


def _euclidean(a: List[float], b: List[float]) -> float:
    """Euclidean distance between two vectors."""
    if len(a) != len(b):
        raise ValueError("Vectors must have same length.")
    return sum((ai - bi) ** 2 for ai, bi in zip(a, b)) ** 0.5


def compute_operator_similarity(
    query_operator_id: str,
    operators: List[Operator],
    measurements: List[Measurement],
    metric_ids: List[str],
    n_neighbors: int = 5,
) -> SimilarityResult:
    """Find the nearest comparable operators by metric profile.

    Args:
        query_operator_id: The operator to find neighbors for.
        operators: All operators in the cohort.
        measurements: All measurements for the cohort.
        metric_ids: Canonical metric IDs to use for similarity.
        n_neighbors: Number of nearest neighbors to return.

    Returns:
        SimilarityResult with the nearest N operators, their distance
        scores, and cluster quality assessment.
    """
    # Build lookup: (operator_id, metric_id) → value
    ms_map: Dict[Tuple[str, str], float] = {}
    for m in measurements:
        if m.value is not None:
            ms_map[(m.operator_id, m.metric_id)] = m.value

    # Build operator lookup
    op_map = {o.operator_id: o for o in operators}

    # Collect all values per metric for percentile normalization
    all_values_by_metric: Dict[str, List[float]] = {}
    for mid in metric_ids:
        vals = [ms_map.get((o.operator_id, mid)) for o in operators]
        all_values_by_metric[mid] = [v for v in vals if v is not None]

    # Build percentile-rank vectors for all operators
    vectors: Dict[str, List[float]] = {}
    for o in operators:
        vec = []
        for mid in metric_ids:
            val = ms_map.get((o.operator_id, mid))
            if val is None:
                vec.append(50.0)  # median if missing
            else:
                vec.append(_percentile_rank(val, all_values_by_metric.get(mid, [val])))
        vectors[o.operator_id] = vec

    query_vec = vectors.get(query_operator_id)
    if query_vec is None:
        return SimilarityResult(
            query_operator_id=query_operator_id,
            normalization="percentile_rank",
            distance_metric="euclidean",
            nearest_neighbors=[],
            cluster_quality="unknown",
            cluster_description=f"Operator {query_operator_id} not found.",
        )

    # Compute distances to all other operators
    distances: List[Tuple[str, float]] = []
    for o in operators:
        if o.operator_id == query_operator_id:
            continue
        other_vec = vectors.get(o.operator_id)
        if other_vec is None:
            continue
        d = _euclidean(query_vec, other_vec)
        distances.append((o.operator_id, d))

    # Sort by distance (ascending = most similar first)
    distances.sort(key=lambda x: x[1])

    # Take top N
    top_n = distances[:n_neighbors]

    # Build match objects
    matches: List[SimilarityMatch] = []
    for oid, dist in top_n:
        op = op_map.get(oid)
        # Normalize distance to 0-1 similarity (max possible distance
        # in percentile space is sqrt(5 * 100^2) = ~223.6)
        max_dist = (len(metric_ids) * 100 ** 2) ** 0.5
        similarity = max(0.0, 1.0 - dist / max_dist) if max_dist > 0 else 0.0

        metric_vec = {}
        for mid in metric_ids:
            val = ms_map.get((oid, mid))
            if val is not None:
                metric_vec[mid] = round(val, 4)

        matches.append(SimilarityMatch(
            operator_id=oid,
            pseudonym=op.pseudonym if op else oid,
            team=op.team if op else None,
            distance=dist,
            similarity=similarity,
            metric_vector=metric_vec,
        ))

    # Assess cluster quality
    if len(matches) < 2:
        cluster_quality = "insufficient"
        cluster_description = "Not enough neighbors to assess cluster quality."
    else:
        # Mean distance to nearest neighbors
        mean_dist = sum(m.distance for m in matches) / len(matches)
        # In percentile space, a mean distance < 50 is tight, < 100 is moderate
        if mean_dist < 50:
            cluster_quality = "tight"
            cluster_description = (
                f"Nearest {len(matches)} operators are very similar — "
                f"mean distance {mean_dist:.1f} in percentile space. "
                "This operator has a clear peer group."
            )
        elif mean_dist < 100:
            cluster_quality = "moderate"
            cluster_description = (
                f"Nearest {len(matches)} operators are moderately similar — "
                f"mean distance {mean_dist:.1f} in percentile space. "
                "Some peer overlap but not a tight cluster."
            )
        else:
            cluster_quality = "dispersed"
            cluster_description = (
                f"Nearest {len(matches)} operators are dispersed — "
                f"mean distance {mean_dist:.1f} in percentile space. "
                "This operator's pattern is relatively unique."
            )

    return SimilarityResult(
        query_operator_id=query_operator_id,
        normalization="percentile_rank",
        distance_metric="euclidean",
        nearest_neighbors=matches,
        cluster_quality=cluster_quality,
        cluster_description=cluster_description,
    )
