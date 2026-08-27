"""TaskContext — models the difficulty/context of a task for fair benchmarking.

Per Jaimie's product review (Gap 4): "Two operators in same workflow stage
solving different complexity tasks shouldn't be benchmarked as peers without
context adjustment."

A TaskContext captures the difficulty envelope of a task so that metric
scores can be normalized to a common difficulty scale before comparison.
This is a content-free object: it carries no task content, only structural
signals (complexity estimate, task type, workflow stage, token-budget
expectation). All fields are developmental context, never personnel labels.

Governance guardrails (per `12` §Development doctrine + §Avoid-list):
- Context adjustment is for fair developmental benchmarking, NOT for
  ranking operators against each other.
- No punitive labels: difficulty is a structural property of the task,
  not a judgment of the operator.
- Outcome claims are ASSOCIATION, never CAUSATION.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Difficulty levels (ordered low → high for normalization).
_DIFFICULTY_ORDER = {"low": 0.2, "medium": 0.5, "high": 0.8}

# Default complexity estimates per task type (normalized 0–1).
# These are structural priors, not judgments about the operator.
# They exist so that two operators solving different task types can be
# compared on a common difficulty scale. A "debugging" task is
# structurally harder to get high Yield on than a "writing" task because
# debugging often requires many exploratory turns before output.
_TASK_TYPE_COMPLEXITY_PRIOR: dict[str, float] = {
    "coding": 0.6,
    "analysis": 0.5,
    "writing": 0.3,
    "research": 0.55,
    "debugging": 0.75,
    "review": 0.4,
    "planning": 0.45,
}


@dataclass(frozen=True, slots=True)
class TaskContext:
    """The difficulty/context envelope of a task.

    Attributes:
        task_complexity: Normalized complexity in [0, 1]. 0 = trivial,
            1 = maximally complex. Used as the primary difficulty signal.
        task_type: Categorical task type (e.g. "coding", "analysis",
            "writing", "research", "debugging"). Drives the complexity
            prior when task_complexity is not explicitly supplied.
        workflow_stage: Optional workflow stage ID this task belongs to
            (links to the Workflow → Stage graph).
        estimated_difficulty: Coarse difficulty label — "low", "medium",
            or "high". Derived from task_complexity if not supplied.
        context_tokens_required: Optional estimate of how much context
            (input tokens) the task typically needs. Content-free: a
            token budget, not task content.
        synthetic: Whether this context was inferred/synthetic.
    """
    task_complexity: float
    task_type: str
    workflow_stage: Optional[str] = None
    estimated_difficulty: str = "medium"
    context_tokens_required: Optional[int] = None
    synthetic: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.task_complexity <= 1.0:
            raise ValueError(
                f"task_complexity must be in [0, 1], got {self.task_complexity}"
            )
        if self.estimated_difficulty not in _DIFFICULTY_ORDER:
            raise ValueError(
                f"estimated_difficulty must be one of "
                f"{sorted(_DIFFICULTY_ORDER)}, got {self.estimated_difficulty!r}"
            )

    @property
    def difficulty_weight(self) -> float:
        """A scalar difficulty weight in [0.2, 0.8] for normalization.

        Blends the explicit task_complexity with the task-type prior and
        the coarse estimated_difficulty label. Higher = harder task.
        Used by context_adjustment to normalize metrics to a common
        difficulty scale.
        """
        type_prior = _TASK_TYPE_COMPLEXITY_PRIOR.get(self.task_type, 0.5)
        label_weight = _DIFFICULTY_ORDER[self.estimated_difficulty]
        # Weighted blend: explicit complexity is primary (60%),
        # task-type prior is secondary (20%), coarse label is tertiary (20%).
        return round(0.6 * self.task_complexity + 0.2 * type_prior + 0.2 * label_weight, 4)

    @classmethod
    def from_task_type(
        cls,
        task_type: str,
        workflow_stage: Optional[str] = None,
        context_tokens_required: Optional[int] = None,
        synthetic: bool = False,
    ) -> "TaskContext":
        """Build a TaskContext from a task type, deriving complexity + difficulty.

        Convenience constructor for the common case where only the task
        type is known. Complexity and difficulty are derived from the
        task-type prior.
        """
        complexity = _TASK_TYPE_COMPLEXITY_PRIOR.get(task_type, 0.5)
        if complexity <= 0.33:
            difficulty = "low"
        elif complexity <= 0.66:
            difficulty = "medium"
        else:
            difficulty = "high"
        return cls(
            task_complexity=complexity,
            task_type=task_type,
            workflow_stage=workflow_stage,
            estimated_difficulty=difficulty,
            context_tokens_required=context_tokens_required,
            synthetic=synthetic,
        )

    def to_dict(self) -> dict:
        return {
            "task_complexity": self.task_complexity,
            "task_type": self.task_type,
            "workflow_stage": self.workflow_stage,
            "estimated_difficulty": self.estimated_difficulty,
            "context_tokens_required": self.context_tokens_required,
            "difficulty_weight": self.difficulty_weight,
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TaskContext":
        return cls(
            task_complexity=float(d["task_complexity"]),
            task_type=d["task_type"],
            workflow_stage=d.get("workflow_stage"),
            estimated_difficulty=d.get("estimated_difficulty", "medium"),
            context_tokens_required=d.get("context_tokens_required"),
            synthetic=d.get("synthetic", False),
        )


def adjust_metric_for_context(
    raw_value: Optional[float],
    context: TaskContext,
    baseline_difficulty: float = 0.5,
) -> Optional[float]:
    """Normalize a raw metric value to a common difficulty scale.

    The adjustment models the intuition that achieving a given metric
    value on a harder task is more developmentally significant than
    achieving the same value on an easier task. A Yield of 0.20 on a
    high-complexity debugging task is not equivalent to a Yield of 0.20
    on a low-complexity writing task.

    The adjustment is multiplicative relative to a baseline difficulty
    (default 0.5, the neutral midpoint). For metrics where higher is
    better (Yield, Leverage, Construction, Token SNR), a harder task
    context *raises* the adjusted value, acknowledging the difficulty
    premium. The adjustment is bounded so it never inflates a metric
    beyond 2x or deflates it below 0.5x — it is a normalization, not a
    reward.

    Args:
        raw_value: The raw metric value (e.g. Yield = 0.20).
        context: The TaskContext for the task the metric was measured on.
        baseline_difficulty: The reference difficulty to normalize
            against (default 0.5 = neutral midpoint).

    Returns:
        The context-adjusted metric value, or None if raw_value is None.

    Governance: This is a developmental normalization for fair
    benchmarking, NOT a personnel adjustment. It does not rank operators;
    it places their metric on a comparable difficulty scale.
    """
    if raw_value is None:
        return None
    weight = context.difficulty_weight
    # Ratio of task difficulty to baseline. >1 means harder than baseline.
    ratio = weight / baseline_difficulty if baseline_difficulty > 0 else 1.0
    # Bound the adjustment to [0.5, 2.0] so it's a normalization, not a reward.
    ratio = max(0.5, min(2.0, ratio))
    adjusted = raw_value * ratio
    return round(adjusted, 6)


def context_adjustment(
    measurements: list,
    context: TaskContext,
    baseline_difficulty: float = 0.5,
) -> list:
    """Apply context adjustment to a list of Measurements.

    Returns a new list of Measurement-like dicts with an added
    `context_adjusted_value` field and the `task_context` tag. The
    original Measurement objects are immutable and untouched; this
    produces enriched copies for the measurement pipeline.

    Per Gap 4 requirement: "Add context to the measurement pipeline so
    metrics can be tagged with their task context."
    """
    adjusted = []
    for m in measurements:
        m_dict = m.to_dict() if hasattr(m, "to_dict") else dict(m)
        raw = m_dict.get("value")
        adj = adjust_metric_for_context(raw, context, baseline_difficulty)
        m_dict["context_adjusted_value"] = adj
        m_dict["task_context"] = context.to_dict()
        m_dict["baseline_difficulty"] = baseline_difficulty
        adjusted.append(m_dict)
    return adjusted
