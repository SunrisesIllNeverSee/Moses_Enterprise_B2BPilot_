"""Operator×System decomposition — the deepest intellectual value per
Jaimie's review §2.

Decomposes observed metric outcomes into:

    Observed = Operator Effect + System Effect + Operator×System Effect + Error

This is a two-way ANOVA-style decomposition without replication. For
each metric, given operators × systems with one observation per cell:

- **Operator effect**: how much each operator shifts the metric on
  average across all systems (their general capability level).
- **System effect**: how much each system shifts the metric on average
  across all operators (the system's general effect).
- **Operator×System interaction**: the residual after subtracting
  operator and system effects — the pairing-specific effect that
  neither the operator alone nor the system alone explains.
- **Error**: unexplained variance (zero when there's one observation
  per cell; nonzero with replication).

The decomposition answers Jaimie's key questions:
- "Does a strong operator remain strong when the model changes?"
  → Check if operator effect dominates system effect.
- "Is the observed improvement caused by the human, the system, or
  the pairing?"
  → Compare the three effect magnitudes.
- "Does someone transfer operating capability from ChatGPT to Claude?"
  → Check if operator effect is consistent across systems.

This is a structural analysis, NOT a ranking. It reveals how variance
is partitioned, not who is "best."
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True, slots=True)
class SystemEffect:
    """Per-system effect for one metric."""
    system: str
    mean: float
    effect: float  # deviation from grand mean
    observation_count: int


@dataclass(frozen=True, slots=True)
class OperatorEffect:
    """Per-operator effect for one metric."""
    operator_id: str
    mean: float
    effect: float  # deviation from grand mean
    system_count: int


@dataclass(frozen=True, slots=True)
class InteractionCell:
    """A single operator×system cell with decomposed effects."""
    operator_id: str
    system: str
    observed: float
    operator_effect: float
    system_effect: float
    interaction: float  # residual = observed - grand_mean - operator_effect - system_effect
    predicted: float  # grand_mean + operator_effect + system_effect


@dataclass(frozen=True, slots=True)
class MetricDecomposition:
    """Full decomposition for one metric across all operators and systems."""
    metric_id: str
    grand_mean: float
    operator_effects: List[OperatorEffect]
    system_effects: List[SystemEffect]
    interaction_cells: List[InteractionCell]
    # Variance partition (sum of squares)
    ss_operator: float
    ss_system: float
    ss_interaction: float
    ss_total: float
    # Proportion of variance explained by each component
    pct_operator: float  # how much of variance is the operator
    pct_system: float    # how much is the system
    pct_interaction: float  # how much is the pairing
    # Interpretation
    dominant_effect: str  # "operator", "system", "interaction", or "balanced"
    label: str

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "grand_mean": round(self.grand_mean, 4),
            "operator_effects": [
                {
                    "operator_id": e.operator_id,
                    "mean": round(e.mean, 4),
                    "effect": round(e.effect, 4),
                    "system_count": e.system_count,
                }
                for e in self.operator_effects
            ],
            "system_effects": [
                {
                    "system": e.system,
                    "mean": round(e.mean, 4),
                    "effect": round(e.effect, 4),
                    "observation_count": e.observation_count,
                }
                for e in self.system_effects
            ],
            "interaction_cells": [
                {
                    "operator_id": c.operator_id,
                    "system": c.system,
                    "observed": round(c.observed, 4),
                    "operator_effect": round(c.operator_effect, 4),
                    "system_effect": round(c.system_effect, 4),
                    "interaction": round(c.interaction, 4),
                    "predicted": round(c.predicted, 4),
                }
                for c in self.interaction_cells
            ],
            "variance_partition": {
                "ss_operator": round(self.ss_operator, 4),
                "ss_system": round(self.ss_system, 4),
                "ss_interaction": round(self.ss_interaction, 4),
                "ss_total": round(self.ss_total, 4),
                "pct_operator": round(self.pct_operator, 4),
                "pct_system": round(self.pct_system, 4),
                "pct_interaction": round(self.pct_interaction, 4),
            },
            "dominant_effect": self.dominant_effect,
            "label": self.label,
        }


@dataclass(frozen=True, slots=True)
class OperatorSystemDecomposition:
    """Full decomposition across all metrics for an operator or cohort."""
    operator_id: Optional[str]  # None for cohort-level
    metrics: List[MetricDecomposition]
    systems_compared: List[str]
    operators_analyzed: int
    total_observations: int
    summary: str

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "systems_compared": self.systems_compared,
            "operators_analyzed": self.operators_analyzed,
            "total_observations": self.total_observations,
            "metrics": [m.to_dict() for m in self.metrics],
            "summary": self.summary,
        }


def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _decompose_metric(
    metric_id: str,
    # operator_id -> system -> value
    data: Dict[str, Dict[str, float]],
) -> Optional[MetricDecomposition]:
    """Compute the two-way decomposition for one metric.

    Args:
        metric_id: The metric being decomposed.
        data: Nested dict {operator_id: {system: value}}.

    Returns:
        MetricDecomposition, or None if insufficient data (need at
        least 2 operators and 2 systems).
    """
    # Flatten to cells
    cells: List[Tuple[str, str, float]] = []
    for op_id, systems in data.items():
        for sys_name, val in systems.items():
            if val is not None and val == val:  # not None, not NaN
                cells.append((op_id, sys_name, val))

    if len(cells) < 4:
        return None  # need at least 2x2

    operators = sorted(set(c[0] for c in cells))
    systems = sorted(set(c[1] for c in cells))

    if len(operators) < 2 or len(systems) < 2:
        return None

    # Grand mean
    grand_mean = _mean([c[2] for c in cells])

    # Operator means (across systems)
    op_values: Dict[str, List[float]] = {op: [] for op in operators}
    for op, sys_name, val in cells:
        op_values[op].append(val)
    op_means = {op: _mean(vals) for op, vals in op_values.items()}
    op_effects = {op: op_means[op] - grand_mean for op in operators}

    # System means (across operators)
    sys_values: Dict[str, List[float]] = {s: [] for s in systems}
    for op, sys_name, val in cells:
        sys_values[sys_name].append(val)
    sys_means = {s: _mean(vals) for s, vals in sys_values.items()}
    sys_effects = {s: sys_means[s] - grand_mean for s in systems}

    # Interaction cells (residuals)
    interaction_cells: List[InteractionCell] = []
    ss_operator = 0.0
    ss_system = 0.0
    ss_interaction = 0.0
    ss_total = 0.0

    for op, sys_name, val in cells:
        oe = op_effects[op]
        se = sys_effects[sys_name]
        predicted = grand_mean + oe + se
        interaction = val - predicted
        interaction_cells.append(InteractionCell(
            operator_id=op,
            system=sys_name,
            observed=val,
            operator_effect=oe,
            system_effect=se,
            interaction=interaction,
            predicted=predicted,
        ))
        # Sum of squares
        ss_operator += oe ** 2
        ss_system += se ** 2
        ss_interaction += interaction ** 2
        ss_total += (val - grand_mean) ** 2

    # Variance proportions
    pct_op = ss_operator / ss_total if ss_total > 0 else 0.0
    pct_sys = ss_system / ss_total if ss_total > 0 else 0.0
    pct_int = ss_interaction / ss_total if ss_total > 0 else 0.0

    # Dominant effect
    if pct_op > 0.5:
        dominant = "operator"
        label = "Operator capability dominates — strong operators stay strong across systems"
    elif pct_sys > 0.5:
        dominant = "system"
        label = "System choice dominates — the tool matters more than who uses it"
    elif pct_int > 0.4:
        dominant = "interaction"
        label = "Operator×System pairing matters — specific combinations outperform"
    elif abs(pct_op - pct_sys) < 0.15 and pct_int < 0.2:
        dominant = "balanced"
        label = "Operator and system contribute roughly equally"
    else:
        dominant = "mixed"
        label = "Effects are mixed — no single dominant factor"

    return MetricDecomposition(
        metric_id=metric_id,
        grand_mean=grand_mean,
        operator_effects=[
            OperatorEffect(op, op_means[op], op_effects[op], len(op_values[op]))
            for op in operators
        ],
        system_effects=[
            SystemEffect(s, sys_means[s], sys_effects[s], len(sys_values[s]))
            for s in systems
        ],
        interaction_cells=interaction_cells,
        ss_operator=ss_operator,
        ss_system=ss_system,
        ss_interaction=ss_interaction,
        ss_total=ss_total,
        pct_operator=pct_op,
        pct_system=pct_sys,
        pct_interaction=pct_int,
        dominant_effect=dominant,
        label=label,
    )


def compute_operator_system_decomposition(
    # operator_id -> system -> metric_id -> value
    operator_system_metrics: Dict[str, Dict[str, Dict[str, float]]],
    metric_ids: Optional[List[str]] = None,
    operator_id: Optional[str] = None,
) -> OperatorSystemDecomposition:
    """Compute the Operator×System decomposition across all metrics.

    Args:
        operator_system_metrics: Nested dict
            {operator_id: {system: {metric_id: value}}}.
        metric_ids: If provided, only decompose these metrics.
            Otherwise, use all metrics found in the data.
        operator_id: If provided, filter to just this operator's
            systems (single-operator cross-system comparison). If None,
            decompose across all operators (cohort-level).

    Returns:
        OperatorSystemDecomposition with per-metric breakdowns.
    """
    if operator_id:
        # Single-operator: we still need other operators for the
        # decomposition to work (to separate operator from system effect).
        # Include all operators but mark the query operator.
        pass

    # Determine metric set
    if metric_ids is None:
        all_metrics: set = set()
        for op_data in operator_system_metrics.values():
            for sys_data in op_data.values():
                all_metrics.update(sys_data.keys())
        metric_ids = sorted(all_metrics)

    # Build per-metric data
    all_systems: set = set()
    total_obs = 0
    metrics_decomposed: List[MetricDecomposition] = []

    for mid in metric_ids:
        # {operator_id: {system: value}}
        metric_data: Dict[str, Dict[str, float]] = {}
        for op_id, sys_dict in operator_system_metrics.items():
            for sys_name, metrics in sys_dict.items():
                if mid in metrics and metrics[mid] is not None:
                    metric_data.setdefault(op_id, {})[sys_name] = metrics[mid]
                    all_systems.add(sys_name)
                    total_obs += 1

        if len(metric_data) < 2:
            continue

        decomp = _decompose_metric(mid, metric_data)
        if decomp is not None:
            metrics_decomposed.append(decomp)

    # Summary
    if not metrics_decomposed:
        summary = "Insufficient data for decomposition — need at least 2 operators on 2 systems."
    else:
        dominant_counts: Dict[str, int] = {}
        for m in metrics_decomposed:
            dominant_counts[m.dominant_effect] = dominant_counts.get(m.dominant_effect, 0) + 1
        parts = [f"{k}({v})" for k, v in sorted(dominant_counts.items(), key=lambda x: -x[1])]
        summary = f"Decomposed {len(metrics_decomposed)} metrics across {len(all_systems)} systems. Dominant effects: {', '.join(parts)}."

    return OperatorSystemDecomposition(
        operator_id=operator_id,
        metrics=metrics_decomposed,
        systems_compared=sorted(all_systems),
        operators_analyzed=len(operator_system_metrics),
        total_observations=total_obs,
        summary=summary,
    )
