"""Online evaluation — shadow judges on live traces (HRN-009).

HRN-009: "Add shadow judges on live traces. Capture user or operational
signals. Feed failures back into offline evaluation/golden sets."

Online evaluation runs a shadow judge alongside the primary evaluation
on live traces. The shadow judge's scores are NOT used for decisions —
they are collected for offline comparison. This enables:

    1. Continuous monitoring of judge quality on live data
    2. Detection of drift (judge scores shifting over time)
    3. Capture of operational signals (user feedback, escalation rates)
    4. Feeding failures back into offline evaluation/golden sets

The shadow judge is non-blocking: if it fails, the primary evaluation
proceeds. The shadow judge's results are logged for offline analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SignalType(str, Enum):
    """Types of operational signals captured during online evaluation."""
    JUDGE_SCORE = "judge_score"           # shadow judge's score
    USER_FEEDBACK = "user_feedback"       # explicit user feedback
    ESCALATION = "escalation"             # human escalation of a case
    FAILURE = "failure"                   # observed failure
    DRIFT_DETECTED = "drift_detected"     # judge score drift


@dataclass(frozen=True, slots=True)
class LiveTrace:
    """A single live evaluation trace.

    The trace carries the item being evaluated, the primary judge's
    score, and optionally the shadow judge's score. The shadow score
    is collected for offline comparison — it does NOT affect decisions.
    """
    trace_id: str
    item_id: str
    timestamp: str
    primary_score: Optional[float] = None
    shadow_score: Optional[float] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "item_id": self.item_id,
            "timestamp": self.timestamp,
            "primary_score": self.primary_score,
            "shadow_score": self.shadow_score,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class OperationalSignal:
    """An operational signal captured during online evaluation.

    Signals are user feedback, escalations, failures, or drift detections.
    They are fed back into offline evaluation/golden sets.
    """
    signal_id: str
    signal_type: SignalType
    trace_id: str
    timestamp: str
    value: Optional[float] = None
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "value": self.value,
            "detail": self.detail,
        }


@dataclass
class OnlineEvalReport:
    """Aggregate report from online evaluation.

    Metrics:
        - trace_count: number of live traces evaluated
        - shadow_judge_coverage: fraction of traces with a shadow score
        - mean_score_delta: average (shadow - primary) score difference
        - drift_traces: traces where |shadow - primary| exceeds threshold
        - signal_counts: count of each signal type
    """
    trace_count: int = 0
    shadow_judge_coverage: float = 0.0
    mean_score_delta: float = 0.0
    drift_traces: List[str] = field(default_factory=list)
    signal_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "trace_count": self.trace_count,
            "shadow_judge_coverage": round(self.shadow_judge_coverage, 4),
            "mean_score_delta": round(self.mean_score_delta, 4),
            "drift_traces": list(self.drift_traces),
            "signal_counts": dict(self.signal_counts),
        }


# Type for a shadow judge function: takes an item, returns a score.
ShadowJudgeFn = Callable[[dict], Optional[float]]


class OnlineEvaluator:
    """Runs shadow judges on live traces (HRN-009 online evaluation).

    The evaluator sits alongside the primary evaluation. For each live
    trace, it:
        1. Records the primary judge's score
        2. Runs the shadow judge (if configured) to get a shadow score
        3. Compares the two and flags drift
        4. Captures operational signals (user feedback, escalations)
        5. Logs everything for offline analysis

    The shadow judge is non-blocking: if it fails, the primary
    evaluation proceeds. Shadow scores are NEVER used for decisions.
    """

    def __init__(
        self,
        shadow_judge: Optional[ShadowJudgeFn] = None,
        drift_threshold: float = 0.2,
    ) -> None:
        self._shadow_judge = shadow_judge
        self._drift_threshold = drift_threshold
        self._traces: List[LiveTrace] = []
        self._signals: List[OperationalSignal] = []
        self._signal_counter = 0
        self._trace_counter = 0

    def evaluate(
        self,
        item: dict,
        primary_score: Optional[float] = None,
        item_id: str = "",
    ) -> LiveTrace:
        """Evaluate a live trace with the primary and shadow judges.

        The shadow judge runs in a try/except — if it fails, the trace
        is still recorded with shadow_score=None. The primary score is
        always recorded regardless of shadow judge outcome.

        Args:
            item: the item being evaluated (passed to the shadow judge)
            primary_score: the primary judge's score (already computed)
            item_id: identifier for the item

        Returns:
            The recorded LiveTrace.
        """
        self._trace_counter += 1
        trace_id = f"trace_{self._trace_counter:06d}"
        timestamp = _now().isoformat()

        # Run shadow judge (non-blocking)
        shadow_score: Optional[float] = None
        if self._shadow_judge is not None:
            try:
                shadow_score = self._shadow_judge(item)
            except Exception:
                # Shadow judge failure is non-blocking. Record None.
                shadow_score = None

        trace = LiveTrace(
            trace_id=trace_id,
            item_id=item_id,
            timestamp=timestamp,
            primary_score=primary_score,
            shadow_score=shadow_score,
        )
        self._traces.append(trace)

        # Check for drift
        if (
            primary_score is not None
            and shadow_score is not None
            and abs(shadow_score - primary_score) > self._drift_threshold
        ):
            self.record_signal(
                trace_id=trace_id,
                signal_type=SignalType.DRIFT_DETECTED,
                value=abs(shadow_score - primary_score),
                detail=f"shadow={shadow_score}, primary={primary_score}",
            )

        return trace

    def record_signal(
        self,
        trace_id: str,
        signal_type: SignalType,
        value: Optional[float] = None,
        detail: str = "",
    ) -> OperationalSignal:
        """Record an operational signal for a trace.

        Signals are user feedback, escalations, failures, or drift
        detections. They are fed back into offline evaluation/golden sets.
        """
        self._signal_counter += 1
        signal_id = f"signal_{self._signal_counter:06d}"
        signal = OperationalSignal(
            signal_id=signal_id,
            signal_type=signal_type,
            trace_id=trace_id,
            timestamp=_now().isoformat(),
            value=value,
            detail=detail,
        )
        self._signals.append(signal)
        return signal

    def report(self) -> OnlineEvalReport:
        """Generate an aggregate report from collected traces and signals."""
        trace_count = len(self._traces)
        if trace_count == 0:
            return OnlineEvalReport()

        shadow_count = sum(1 for t in self._traces if t.shadow_score is not None)
        coverage = shadow_count / trace_count

        # Mean score delta (only for traces with both scores)
        deltas = [
            t.shadow_score - t.primary_score
            for t in self._traces
            if t.shadow_score is not None and t.primary_score is not None
        ]
        mean_delta = sum(deltas) / len(deltas) if deltas else 0.0

        # Drift traces
        drift_traces = [
            t.trace_id
            for t in self._traces
            if t.shadow_score is not None
            and t.primary_score is not None
            and abs(t.shadow_score - t.primary_score) > self._drift_threshold
        ]

        # Signal counts
        signal_counts: Dict[str, int] = {}
        for s in self._signals:
            key = s.signal_type.value
            signal_counts[key] = signal_counts.get(key, 0) + 1

        return OnlineEvalReport(
            trace_count=trace_count,
            shadow_judge_coverage=coverage,
            mean_score_delta=mean_delta,
            drift_traces=drift_traces,
            signal_counts=signal_counts,
        )

    @property
    def traces(self) -> List[LiveTrace]:
        return list(self._traces)

    @property
    def signals(self) -> List[OperationalSignal]:
        return list(self._signals)

    def export_for_offline(self) -> dict:
        """Export collected traces and signals for offline evaluation.

        This is the feed-back mechanism: online data is exported so
        offline evaluation can incorporate it into golden sets and
        re-calibrate the judge.
        """
        return {
            "traces": [t.to_dict() for t in self._traces],
            "signals": [s.to_dict() for s in self._signals],
            "report": self.report().to_dict(),
        }
