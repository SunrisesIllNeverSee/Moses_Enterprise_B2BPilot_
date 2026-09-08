"""Per-worker budgets (HRN-010 orchestration).

The pilot runs interventions across operators. Each intervention is a
"worker" that processes operators and consumes resources (time, steps,
cost). Without per-worker budgets, a single runaway intervention can
exhaust the pilot's total budget or block siblings (HRN-010: "parallel
branches require backpressure, rate-limit coordination across shared
tools, and bulkheading so one failing worker cannot exhaust the budget
or block siblings").

This module provides:
    - WorkerBudget: a budget cap for a single worker (step, time, cost)
    - BudgetTracker: tracks usage per worker and enforces caps
    - BudgetExceededError: raised when a worker exceeds its budget

Budgets are set per intervention and tracked per operator within that
intervention. A budget breach raises BudgetExceededError, which the
orchestrator catches to escalate or terminate that worker without
affecting siblings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Optional, Tuple


def _now() -> datetime:
    return datetime.now(timezone.utc)


class BudgetDimension(str, Enum):
    """The dimensions along which a worker budget can be capped."""
    STEPS = "steps"          # max number of processing steps
    TIME = "time"            # max wall-clock duration (seconds)
    COST = "cost"            # max accumulated cost (currency units)


@dataclass(frozen=True, slots=True)
class WorkerBudget:
    """A budget cap for a single worker (intervention).

    Any field set to None means "no cap" for that dimension. A worker
    with all fields None has an unlimited budget (not recommended for
    production — HRN-010 recommends explicit caps).
    """
    worker_id: str
    max_steps: Optional[int] = None
    max_time_seconds: Optional[float] = None
    max_cost: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "max_steps": self.max_steps,
            "max_time_seconds": self.max_time_seconds,
            "max_cost": self.max_cost,
        }


class BudgetExceededError(Exception):
    """Raised when a worker exceeds its budget on any dimension.

    The error message names the dimension that was exceeded and the
    current usage vs the cap. The orchestrator catches this to escalate
    or terminate the worker without affecting siblings.
    """
    def __init__(self, worker_id: str, dimension: BudgetDimension,
                 used: float, cap: float) -> None:
        self.worker_id = worker_id
        self.dimension = dimension
        self.used = used
        self.cap = cap
        super().__init__(
            f"Worker '{worker_id}' exceeded {dimension.value} budget: "
            f"used {used}, cap {cap}"
        )


@dataclass
class BudgetUsage:
    """Current usage for a single worker."""
    worker_id: str
    steps_used: int = 0
    time_started: Optional[datetime] = None
    cost_accumulated: float = 0.0
    exhausted: bool = False
    exhausted_dimension: Optional[BudgetDimension] = None

    def elapsed_seconds(self) -> float:
        if self.time_started is None:
            return 0.0
        return (_now() - self.time_started).total_seconds()

    def to_dict(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "steps_used": self.steps_used,
            "elapsed_seconds": round(self.elapsed_seconds(), 2),
            "cost_accumulated": round(self.cost_accumulated, 4),
            "exhausted": self.exhausted,
            "exhausted_dimension": self.exhausted_dimension.value if self.exhausted_dimension else None,
        }


class BudgetTracker:
    """Tracks per-worker budget usage and enforces caps (HRN-010).

    Each worker (intervention) gets a budget. The tracker records usage
    and raises BudgetExceededError when a worker exceeds any dimension.
    The orchestrator catches the error to escalate or terminate that
    worker without affecting siblings (bulkheading).
    """

    def __init__(self) -> None:
        self._budgets: Dict[str, WorkerBudget] = {}
        self._usage: Dict[str, BudgetUsage] = {}

    def set_budget(self, budget: WorkerBudget) -> None:
        """Set the budget for a worker. Overwrites any existing budget."""
        self._budgets[budget.worker_id] = budget
        if budget.worker_id not in self._usage:
            self._usage[budget.worker_id] = BudgetUsage(worker_id=budget.worker_id)

    def start(self, worker_id: str) -> None:
        """Mark a worker as started (begins the time clock)."""
        if worker_id not in self._usage:
            self._usage[worker_id] = BudgetUsage(worker_id=worker_id)
        self._usage[worker_id].time_started = _now()

    def record_step(self, worker_id: str, cost: float = 0.0) -> None:
        """Record a processing step for a worker.

        Increments the step counter and accumulates cost. Checks all
        budget dimensions and raises BudgetExceededError if any cap
        is exceeded. The error is raised AFTER recording the step, so
        the usage reflects the step that breached the budget.
        """
        if worker_id not in self._usage:
            self._usage[worker_id] = BudgetUsage(worker_id=worker_id)
        usage = self._usage[worker_id]
        usage.steps_used += 1
        usage.cost_accumulated += cost

        budget = self._budgets.get(worker_id)
        if budget is None:
            return  # no budget set — unlimited (not recommended)

        # Check step budget
        if budget.max_steps is not None and usage.steps_used > budget.max_steps:
            usage.exhausted = True
            usage.exhausted_dimension = BudgetDimension.STEPS
            raise BudgetExceededError(worker_id, BudgetDimension.STEPS,
                                      usage.steps_used, budget.max_steps)

        # Check time budget
        if budget.max_time_seconds is not None and usage.elapsed_seconds() > budget.max_time_seconds:
            usage.exhausted = True
            usage.exhausted_dimension = BudgetDimension.TIME
            raise BudgetExceededError(worker_id, BudgetDimension.TIME,
                                      usage.elapsed_seconds(), budget.max_time_seconds)

        # Check cost budget
        if budget.max_cost is not None and usage.cost_accumulated > budget.max_cost:
            usage.exhausted = True
            usage.exhausted_dimension = BudgetDimension.COST
            raise BudgetExceededError(worker_id, BudgetDimension.COST,
                                      usage.cost_accumulated, budget.max_cost)

    def is_exhausted(self, worker_id: str) -> bool:
        """Check whether a worker has exhausted its budget."""
        usage = self._usage.get(worker_id)
        return usage is not None and usage.exhausted

    def get_usage(self, worker_id: str) -> Optional[BudgetUsage]:
        """Get the current usage for a worker."""
        return self._usage.get(worker_id)

    def all_usage(self) -> Dict[str, BudgetUsage]:
        """Get usage for all workers."""
        return dict(self._usage)

    def remaining(self, worker_id: str) -> Dict[str, Optional[float]]:
        """Get remaining budget for each dimension (None = no cap or no budget)."""
        budget = self._budgets.get(worker_id)
        usage = self._usage.get(worker_id)
        if budget is None or usage is None:
            return {"steps": None, "time": None, "cost": None}
        return {
            "steps": (budget.max_steps - usage.steps_used) if budget.max_steps is not None else None,
            "time": (budget.max_time_seconds - usage.elapsed_seconds()) if budget.max_time_seconds is not None else None,
            "cost": (budget.max_cost - usage.cost_accumulated) if budget.max_cost is not None else None,
        }
