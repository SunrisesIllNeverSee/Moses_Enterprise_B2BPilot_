"""Governance enforcement — the 6 items added to spec 12 from the MO§ES™
enterprise pilot readiness framework §13.

Each item has a technical enforcement mechanism, not just a policy
statement. This module provides the dataclasses, gate functions, and
audit logging for:

1. Purpose limitation — processing_purpose on pilot config, ingestion gate
2. Employee disclosure — notification + acknowledgment tracking + ingestion gate
3. Consent — consent model selection + withdrawal-triggered deletion
4. Bias review — review process + evidence grade downgrade trigger
5. Right to challenge — Challenge dataclass + workflow + grade downgrade
6. Correction process — correction records + propagation tracking

All governance actions are logged to a GovernanceAuditLog.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── 1. Purpose limitation ───────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ProcessingPurpose:
    """A declared processing purpose for a pilot configuration.

    Data ingested under this purpose may not be used for any other
    purpose without a new purpose declaration and customer authorization.
    """
    purpose_id: str
    description: str
    eval_questions: List[str] = field(default_factory=list)
    declared_at: datetime = field(default_factory=_now)
    authorized_by: str = ""

    def to_dict(self) -> dict:
        return {
            "purpose_id": self.purpose_id,
            "description": self.description,
            "eval_questions": list(self.eval_questions),
            "declared_at": self.declared_at.isoformat(),
            "authorized_by": self.authorized_by,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProcessingPurpose":
        declared = d.get("declared_at")
        if isinstance(declared, str):
            declared = datetime.fromisoformat(declared.replace("Z", "+00:00"))
        return cls(
            purpose_id=d["purpose_id"],
            description=d["description"],
            eval_questions=list(d.get("eval_questions", [])),
            declared_at=declared or _now(),
            authorized_by=d.get("authorized_by", ""),
        )


class PurposeLimitationGate:
    """Enforces purpose limitation at ingestion time.

    The system refuses to ingest data without a declared processing
    purpose. Each computation job logs the purpose it was run under.
    """

    def __init__(self) -> None:
        self._purposes: Dict[str, ProcessingPurpose] = {}

    def declare_purpose(self, purpose: ProcessingPurpose) -> None:
        self._purposes[purpose.purpose_id] = purpose

    def get_purpose(self, purpose_id: str) -> Optional[ProcessingPurpose]:
        return self._purposes.get(purpose_id)

    def check_ingestion(self, purpose_id: str) -> tuple[bool, str]:
        """Check whether ingestion is permitted under this purpose.

        Returns (permitted, reason). If no purpose is declared,
        ingestion is blocked.
        """
        if not purpose_id:
            return False, "No processing purpose declared — ingestion blocked per spec 12 purpose limitation."
        purpose = self._purposes.get(purpose_id)
        if purpose is None:
            return False, f"Unknown purpose '{purpose_id}' — ingestion blocked. Declare the purpose first."
        return True, f"Ingestion permitted under purpose '{purpose_id}': {purpose.description}"

    def check_computation(self, purpose_id: str, eval_question: str) -> tuple[bool, str]:
        """Check whether a computation is permitted under this purpose.

        The eval question must be within the purpose's declared scope.
        """
        purpose = self._purposes.get(purpose_id)
        if purpose is None:
            return False, f"Unknown purpose '{purpose_id}' — computation blocked."
        if eval_question and purpose.eval_questions and eval_question not in purpose.eval_questions:
            return False, f"Eval question '{eval_question}' not in declared scope of purpose '{purpose_id}'."
        return True, f"Computation permitted under purpose '{purpose_id}'."


# ─── 2. Employee disclosure ──────────────────────────────────────────

DISCLOSURE_TEMPLATE = """\
MO§ES™ Operator Measurement Notification

You are being measured as part of an enterprise AI operator evaluation pilot.

What is collected:
  - Token telemetry (input/output/read/write counts per session)
  - Session metadata (timestamps, model/platform used)
  - Workflow context (which stage of work)

What is NOT collected:
  - Message content (prompts, outputs, code, emails)
  - Personal communications
  - HR data

How long data is retained:
  - Per the pilot configuration's retention window (default: 90 days)

Who can see your individual results:
  - You (your own profile)
  - Your manager (only with your consent — aggregate by default)
  - Executives (aggregate only, never individual)

How results may be used:
  - Developmental coaching and training recommendations
  - Workflow and tool optimization
  - Research and measurement validation
  - NOT automatic personnel decisions (hiring, firing, compensation)

Your rights:
  - Withdraw consent at any time (triggers data deletion)
  - Challenge any result about you
  - Request correction of incorrect data

Contact: Your pilot lead or governance contact for questions.
"""


@dataclass(frozen=True, slots=True)
class DisclosureAcknowledgment:
    """Records that an operator has been notified and acknowledged."""
    operator_id: str
    notified_at: datetime
    acknowledged_at: Optional[datetime] = None
    status: str = "pending"  # pending | acknowledged | declined
    notification_text: str = DISCLOSURE_TEMPLATE

    @property
    def is_acknowledged(self) -> bool:
        return self.status == "acknowledged" and self.acknowledged_at is not None

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "notified_at": self.notified_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "status": self.status,
            "notification_text": self.notification_text,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DisclosureAcknowledgment":
        notified = d.get("notified_at")
        if isinstance(notified, str):
            notified = datetime.fromisoformat(notified.replace("Z", "+00:00"))
        acked = d.get("acknowledged_at")
        if isinstance(acked, str):
            acked = datetime.fromisoformat(acked.replace("Z", "+00:00"))
        return cls(
            operator_id=d["operator_id"],
            notified_at=notified or _now(),
            acknowledged_at=acked,
            status=d.get("status", "pending"),
            notification_text=d.get("notification_text", DISCLOSURE_TEMPLATE),
        )


class DisclosureGate:
    """Enforces employee disclosure at ingestion time.

    The ingestion layer refuses to ingest data for an operator whose
    acknowledgment status is 'pending' or 'declined'.
    """

    def __init__(self) -> None:
        self._records: Dict[str, DisclosureAcknowledgment] = {}

    def notify(self, operator_id: str) -> DisclosureAcknowledgment:
        """Send notification to an operator (creates a pending record)."""
        record = DisclosureAcknowledgment(
            operator_id=operator_id,
            notified_at=_now(),
            status="pending",
        )
        self._records[operator_id] = record
        return record

    def acknowledge(self, operator_id: str) -> DisclosureAcknowledgment:
        """Record an operator's acknowledgment."""
        existing = self._records.get(operator_id)
        if existing is None:
            raise ValueError(f"Operator {operator_id} has not been notified yet.")
        record = DisclosureAcknowledgment(
            operator_id=operator_id,
            notified_at=existing.notified_at,
            acknowledged_at=_now(),
            status="acknowledged",
        )
        self._records[operator_id] = record
        return record

    def decline(self, operator_id: str) -> DisclosureAcknowledgment:
        """Record an operator's decline."""
        existing = self._records.get(operator_id)
        if existing is None:
            raise ValueError(f"Operator {operator_id} has not been notified yet.")
        record = DisclosureAcknowledgment(
            operator_id=operator_id,
            notified_at=existing.notified_at,
            status="declined",
        )
        self._records[operator_id] = record
        return record

    def check_ingestion(self, operator_id: str) -> tuple[bool, str]:
        """Check whether ingestion is permitted for this operator."""
        record = self._records.get(operator_id)
        if record is None:
            return False, f"Operator {operator_id} has not been notified — ingestion blocked per spec 12 employee disclosure."
        if not record.is_acknowledged:
            return False, f"Operator {operator_id} acknowledgment status is '{record.status}' — ingestion blocked."
        return True, f"Operator {operator_id} acknowledged at {record.acknowledged_at.isoformat()}."

    def get_record(self, operator_id: str) -> Optional[DisclosureAcknowledgment]:
        return self._records.get(operator_id)

    def all_records(self) -> List[DisclosureAcknowledgment]:
        return list(self._records.values())


# ─── 3. Consent ──────────────────────────────────────────────────────

class ConsentModel(str, Enum):
    OPT_IN = "opt_in"
    OPT_OUT = "opt_out"
    CORPORATE_AUTHORIZATION = "corporate_authorization"


class ConsentState(str, Enum):
    GRANTED = "granted"
    PENDING = "pending"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    """Tracks consent state for an operator under a specific consent model."""
    operator_id: str
    model: ConsentModel
    state: ConsentState
    changed_at: datetime = field(default_factory=_now)
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "model": self.model.value,
            "state": self.state.value,
            "changed_at": self.changed_at.isoformat(),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ConsentRecord":
        changed = d.get("changed_at")
        if isinstance(changed, str):
            changed = datetime.fromisoformat(changed.replace("Z", "+00:00"))
        return cls(
            operator_id=d["operator_id"],
            model=ConsentModel(d.get("model", "opt_in")),
            state=ConsentState(d.get("state", "pending")),
            changed_at=changed or _now(),
            reason=d.get("reason", ""),
        )


class ConsentManager:
    """Manages consent state and enforces consent-based ingestion gates.

    Supports three consent models:
    - opt_in: operator must actively consent before data collection
    - opt_out: data collected unless operator actively opts out
    - corporate_authorization: employer authorizes, operator notified

    Regardless of model, withdrawal triggers immediate cessation and
    data deletion queueing.
    """

    def __init__(self, default_model: ConsentModel = ConsentModel.OPT_OUT) -> None:
        self._default_model = default_model
        self._records: Dict[str, ConsentRecord] = {}
        self._deletion_queue: List[str] = []  # operator_ids pending deletion

    def set_model(self, operator_id: str, model: ConsentModel,
                  initial_state: Optional[ConsentState] = None) -> ConsentRecord:
        """Set the consent model for an operator."""
        if initial_state is None:
            if model == ConsentModel.OPT_IN:
                initial_state = ConsentState.PENDING
            else:
                initial_state = ConsentState.GRANTED
        record = ConsentRecord(
            operator_id=operator_id,
            model=model,
            state=initial_state,
        )
        self._records[operator_id] = record
        return record

    def grant(self, operator_id: str, reason: str = "") -> ConsentRecord:
        existing = self._records.get(operator_id)
        model = existing.model if existing else self._default_model
        record = ConsentRecord(
            operator_id=operator_id, model=model,
            state=ConsentState.GRANTED, reason=reason,
        )
        self._records[operator_id] = record
        return record

    def withdraw(self, operator_id: str, reason: str = "") -> ConsentRecord:
        existing = self._records.get(operator_id)
        model = existing.model if existing else self._default_model
        record = ConsentRecord(
            operator_id=operator_id, model=model,
            state=ConsentState.WITHDRAWN, reason=reason,
        )
        self._records[operator_id] = record
        if operator_id not in self._deletion_queue:
            self._deletion_queue.append(operator_id)
        return record

    def check_ingestion(self, operator_id: str) -> tuple[bool, str]:
        """Check whether ingestion is permitted for this operator."""
        record = self._records.get(operator_id)
        if record is None:
            if self._default_model == ConsentModel.OPT_IN:
                return False, f"Operator {operator_id} has no consent record and model is opt_in — ingestion blocked."
            return True, f"Operator {operator_id} no explicit record, default model {self._default_model.value} — ingestion permitted."
        if record.state == ConsentState.WITHDRAWN:
            return False, f"Operator {operator_id} has withdrawn consent — ingestion blocked. Data queued for deletion."
        if record.state == ConsentState.PENDING and record.model == ConsentModel.OPT_IN:
            return False, f"Operator {operator_id} consent is pending (opt_in model) — ingestion blocked until consent granted."
        return True, f"Operator {operator_id} consent state: {record.state.value} (model: {record.model.value})."

    @property
    def deletion_queue(self) -> List[str]:
        return list(self._deletion_queue)

    def clear_deletion_queue(self, operator_id: str) -> None:
        if operator_id in self._deletion_queue:
            self._deletion_queue.remove(operator_id)

    def get_record(self, operator_id: str) -> Optional[ConsentRecord]:
        return self._records.get(operator_id)


# ─── 4. Bias review ──────────────────────────────────────────────────

class BiasSeverity(str, Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    SEVERE = "severe"


@dataclass(frozen=True, slots=True)
class BiasReviewReport:
    """A bias review report for a metric, benchmark, or eval."""
    review_id: str
    review_type: str  # "measurement" | "telemetry" | "benchmark"
    target_id: str  # metric_id, benchmark_class, or eval_id
    conducted_at: datetime = field(default_factory=_now)
    conducted_by: str = ""
    severity: BiasSeverity = BiasSeverity.NONE
    findings: List[str] = field(default_factory=list)
    mitigation_plan: List[str] = field(default_factory=list)
    mitigated: bool = False
    deprecated: bool = False  # severe + unmitigable → deprecate

    def to_dict(self) -> dict:
        return {
            "review_id": self.review_id,
            "review_type": self.review_type,
            "target_id": self.target_id,
            "conducted_at": self.conducted_at.isoformat(),
            "conducted_by": self.conducted_by,
            "severity": self.severity.value,
            "findings": list(self.findings),
            "mitigation_plan": list(self.mitigation_plan),
            "mitigated": self.mitigated,
            "deprecated": self.deprecated,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BiasReviewReport":
        conducted = d.get("conducted_at")
        if isinstance(conducted, str):
            conducted = datetime.fromisoformat(conducted.replace("Z", "+00:00"))
        return cls(
            review_id=d["review_id"],
            review_type=d["review_type"],
            target_id=d["target_id"],
            conducted_at=conducted or _now(),
            conducted_by=d.get("conducted_by", ""),
            severity=BiasSeverity(d.get("severity", "none")),
            findings=list(d.get("findings", [])),
            mitigation_plan=list(d.get("mitigation_plan", [])),
            mitigated=d.get("mitigated", False),
            deprecated=d.get("deprecated", False),
        )


class BiasReviewManager:
    """Manages bias reviews and enforces evidence grade downgrades for
    biased metrics.

    If a metric is flagged as biased and unmitigated, results using that
    metric are downgraded by 1 evidence grade.
    """

    def __init__(self) -> None:
        self._reviews: Dict[str, BiasReviewReport] = {}
        self._biased_targets: Set[str] = set()  # target_ids with unmitigated bias

    def submit_review(self, report: BiasReviewReport) -> None:
        self._reviews[report.review_id] = report
        if report.severity in (BiasSeverity.MODERATE, BiasSeverity.SEVERE) and not report.mitigated:
            self._biased_targets.add(report.target_id)
        elif report.mitigated or report.severity == BiasSeverity.NONE:
            self._biased_targets.discard(report.target_id)

    def is_biased(self, target_id: str) -> bool:
        return target_id in self._biased_targets

    def check_downgrade(self, target_id: str) -> bool:
        """Check whether results using this target should be downgraded."""
        return self.is_biased(target_id)

    def get_review(self, review_id: str) -> Optional[BiasReviewReport]:
        return self._reviews.get(review_id)

    def reviews_for_target(self, target_id: str) -> List[BiasReviewReport]:
        return [r for r in self._reviews.values() if r.target_id == target_id]

    def all_reviews(self) -> List[BiasReviewReport]:
        return list(self._reviews.values())


# ─── 5. Right to challenge ───────────────────────────────────────────

class ChallengeStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"


class ChallengeResolution(str, Enum):
    UPHELD = "upheld"
    PARTIALLY_UPHELD = "partially_upheld"
    NOT_UPHELD = "not_upheld"


@dataclass(frozen=True, slots=True)
class Challenge:
    """An operator's challenge of a MO§ES™ result about them."""
    challenge_id: str
    operator_id: str
    result_reference: str  # measurement_id, diagnosis_id, or benchmark_id
    result_type: str  # "measurement" | "diagnosis" | "benchmark"
    reason: str
    submitted_at: datetime = field(default_factory=_now)
    status: ChallengeStatus = ChallengeStatus.SUBMITTED
    resolution: Optional[ChallengeResolution] = None
    resolution_detail: str = ""
    resolved_at: Optional[datetime] = None
    reviewer: str = ""

    @property
    def is_unresolved(self) -> bool:
        return self.status != ChallengeStatus.RESOLVED

    @property
    def requires_downgrade(self) -> bool:
        """Unresolved challenges trigger a 1-grade evidence downgrade."""
        return self.is_unresolved

    def to_dict(self) -> dict:
        return {
            "challenge_id": self.challenge_id,
            "operator_id": self.operator_id,
            "result_reference": self.result_reference,
            "result_type": self.result_type,
            "reason": self.reason,
            "submitted_at": self.submitted_at.isoformat(),
            "status": self.status.value,
            "resolution": self.resolution.value if self.resolution else None,
            "resolution_detail": self.resolution_detail,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "reviewer": self.reviewer,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Challenge":
        submitted = d.get("submitted_at")
        if isinstance(submitted, str):
            submitted = datetime.fromisoformat(submitted.replace("Z", "+00:00"))
        resolved = d.get("resolved_at")
        if isinstance(resolved, str):
            resolved = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
        resolution = d.get("resolution")
        if resolution and isinstance(resolution, str):
            resolution = ChallengeResolution(resolution)
        return cls(
            challenge_id=d["challenge_id"],
            operator_id=d["operator_id"],
            result_reference=d["result_reference"],
            result_type=d.get("result_type", "measurement"),
            reason=d.get("reason", ""),
            submitted_at=submitted or _now(),
            status=ChallengeStatus(d.get("status", "submitted")),
            resolution=resolution,
            resolution_detail=d.get("resolution_detail", ""),
            resolved_at=resolved,
            reviewer=d.get("reviewer", ""),
        )


class ChallengeManager:
    """Manages operator challenges and enforces evidence grade downgrades.

    Unresolved challenges downgrade the challenged result's evidence
    grade by 1 level until resolved.
    """

    def __init__(self) -> None:
        self._challenges: Dict[str, Challenge] = {}

    def submit(self, challenge_id: str, operator_id: str,
               result_reference: str, result_type: str, reason: str) -> Challenge:
        challenge = Challenge(
            challenge_id=challenge_id,
            operator_id=operator_id,
            result_reference=result_reference,
            result_type=result_type,
            reason=reason,
        )
        self._challenges[challenge_id] = challenge
        return challenge

    def start_review(self, challenge_id: str, reviewer: str) -> Challenge:
        existing = self._challenges[challenge_id]
        if existing is None:
            raise ValueError(f"Unknown challenge: {challenge_id}")
        updated = Challenge(
            challenge_id=existing.challenge_id,
            operator_id=existing.operator_id,
            result_reference=existing.result_reference,
            result_type=existing.result_type,
            reason=existing.reason,
            submitted_at=existing.submitted_at,
            status=ChallengeStatus.UNDER_REVIEW,
            reviewer=reviewer,
        )
        self._challenges[challenge_id] = updated
        return updated

    def resolve(self, challenge_id: str, resolution: ChallengeResolution,
                detail: str = "") -> Challenge:
        existing = self._challenges[challenge_id]
        if existing is None:
            raise ValueError(f"Unknown challenge: {challenge_id}")
        updated = Challenge(
            challenge_id=existing.challenge_id,
            operator_id=existing.operator_id,
            result_reference=existing.result_reference,
            result_type=existing.result_type,
            reason=existing.reason,
            submitted_at=existing.submitted_at,
            status=ChallengeStatus.RESOLVED,
            resolution=resolution,
            resolution_detail=detail,
            resolved_at=_now(),
            reviewer=existing.reviewer,
        )
        self._challenges[challenge_id] = updated
        return updated

    def challenges_for_result(self, result_reference: str) -> List[Challenge]:
        return [c for c in self._challenges.values() if c.result_reference == result_reference]

    def challenges_for_operator(self, operator_id: str) -> List[Challenge]:
        return [c for c in self._challenges.values() if c.operator_id == operator_id]

    def has_unresolved_challenge(self, result_reference: str) -> bool:
        return any(c.is_unresolved for c in self.challenges_for_result(result_reference))

    def get_challenge(self, challenge_id: str) -> Optional[Challenge]:
        return self._challenges.get(challenge_id)

    def all_challenges(self) -> List[Challenge]:
        return list(self._challenges.values())


# ─── 6. Correction process ───────────────────────────────────────────

class CorrectionType(str, Enum):
    FACTUAL_ERROR = "factual_error"
    COMPUTATION_ERROR = "computation_error"
    INTERPRETATION_ERROR = "interpretation_error"
    DATA_QUALITY_ERROR = "data_quality_error"


class CorrectionStatus(str, Enum):
    IDENTIFIED = "identified"
    QUARANTINED = "quarantined"
    CORRECTED = "corrected"
    PROPAGATED = "propagated"
    NOTIFIED = "notified"
    LOGGED = "logged"


@dataclass(frozen=True, slots=True)
class CorrectionRecord:
    """Records a correction to incorrect, incomplete, or misleading data."""
    correction_id: str
    target_type: str  # "observation" | "measurement" | "diagnosis" | "benchmark"
    target_id: str
    correction_type: CorrectionType
    reason: str
    identified_at: datetime = field(default_factory=_now)
    status: CorrectionStatus = CorrectionStatus.IDENTIFIED
    corrected_at: Optional[datetime] = None
    propagated_results: List[str] = field(default_factory=list)
    notified_parties: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "correction_id": self.correction_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "correction_type": self.correction_type.value,
            "reason": self.reason,
            "identified_at": self.identified_at.isoformat(),
            "status": self.status.value,
            "corrected_at": self.corrected_at.isoformat() if self.corrected_at else None,
            "propagated_results": list(self.propagated_results),
            "notified_parties": list(self.notified_parties),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CorrectionRecord":
        identified = d.get("identified_at")
        if isinstance(identified, str):
            identified = datetime.fromisoformat(identified.replace("Z", "+00:00"))
        corrected = d.get("corrected_at")
        if isinstance(corrected, str):
            corrected = datetime.fromisoformat(corrected.replace("Z", "+00:00"))
        return cls(
            correction_id=d["correction_id"],
            target_type=d["target_type"],
            target_id=d["target_id"],
            correction_type=CorrectionType(d.get("correction_type", "factual_error")),
            reason=d.get("reason", ""),
            identified_at=identified or _now(),
            status=CorrectionStatus(d.get("status", "identified")),
            corrected_at=corrected,
            propagated_results=list(d.get("propagated_results", [])),
            notified_parties=list(d.get("notified_parties", [])),
        )


class CorrectionManager:
    """Manages the correction process: identify → quarantine → correct →
    propagate → notify → log.

    Immutable objects are never overwritten; corrections create new
    versions. The propagation step identifies dependent results via
    the lineage system.
    """

    def __init__(self) -> None:
        self._corrections: Dict[str, CorrectionRecord] = {}
        self._quarantined: Set[str] = set()  # target_ids quarantined

    def identify(self, correction_id: str, target_type: str, target_id: str,
                 correction_type: CorrectionType, reason: str) -> CorrectionRecord:
        record = CorrectionRecord(
            correction_id=correction_id,
            target_type=target_type,
            target_id=target_id,
            correction_type=correction_type,
            reason=reason,
        )
        self._corrections[correction_id] = record
        return record

    def quarantine(self, correction_id: str) -> CorrectionRecord:
        existing = self._corrections[correction_id]
        if existing is None:
            raise ValueError(f"Unknown correction: {correction_id}")
        self._quarantined.add(existing.target_id)
        updated = CorrectionRecord(
            correction_id=existing.correction_id,
            target_type=existing.target_type,
            target_id=existing.target_id,
            correction_type=existing.correction_type,
            reason=existing.reason,
            identified_at=existing.identified_at,
            status=CorrectionStatus.QUARANTINED,
        )
        self._corrections[correction_id] = updated
        return updated

    def correct(self, correction_id: str) -> CorrectionRecord:
        existing = self._corrections[correction_id]
        if existing is None:
            raise ValueError(f"Unknown correction: {correction_id}")
        updated = CorrectionRecord(
            correction_id=existing.correction_id,
            target_type=existing.target_type,
            target_id=existing.target_id,
            correction_type=existing.correction_type,
            reason=existing.reason,
            identified_at=existing.identified_at,
            status=CorrectionStatus.CORRECTED,
            corrected_at=_now(),
        )
        self._corrections[correction_id] = updated
        return updated

    def propagate(self, correction_id: str, dependent_result_ids: List[str]) -> CorrectionRecord:
        existing = self._corrections[correction_id]
        if existing is None:
            raise ValueError(f"Unknown correction: {correction_id}")
        updated = CorrectionRecord(
            correction_id=existing.correction_id,
            target_type=existing.target_type,
            target_id=existing.target_id,
            correction_type=existing.correction_type,
            reason=existing.reason,
            identified_at=existing.identified_at,
            status=CorrectionStatus.PROPAGATED,
            corrected_at=existing.corrected_at,
            propagated_results=dependent_result_ids,
        )
        self._corrections[correction_id] = updated
        return updated

    def notify(self, correction_id: str, parties: List[str]) -> CorrectionRecord:
        existing = self._corrections[correction_id]
        if existing is None:
            raise ValueError(f"Unknown correction: {correction_id}")
        updated = CorrectionRecord(
            correction_id=existing.correction_id,
            target_type=existing.target_type,
            target_id=existing.target_id,
            correction_type=existing.correction_type,
            reason=existing.reason,
            identified_at=existing.identified_at,
            status=CorrectionStatus.NOTIFIED,
            corrected_at=existing.corrected_at,
            propagated_results=existing.propagated_results,
            notified_parties=parties,
        )
        self._corrections[correction_id] = updated
        return updated

    def log(self, correction_id: str) -> CorrectionRecord:
        existing = self._corrections[correction_id]
        if existing is None:
            raise ValueError(f"Unknown correction: {correction_id}")
        updated = CorrectionRecord(
            correction_id=existing.correction_id,
            target_type=existing.target_type,
            target_id=existing.target_id,
            correction_type=existing.correction_type,
            reason=existing.reason,
            identified_at=existing.identified_at,
            status=CorrectionStatus.LOGGED,
            corrected_at=existing.corrected_at,
            propagated_results=existing.propagated_results,
            notified_parties=existing.notified_parties,
        )
        self._corrections[correction_id] = updated
        return updated

    def is_quarantined(self, target_id: str) -> bool:
        return target_id in self._quarantined

    def get_correction(self, correction_id: str) -> Optional[CorrectionRecord]:
        return self._corrections.get(correction_id)

    def all_corrections(self) -> List[CorrectionRecord]:
        return list(self._corrections.values())


# ─── Audit log ───────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class GovernanceAuditEntry:
    """A single entry in the governance audit log."""
    timestamp: datetime
    action: str
    actor: str
    target: str
    details: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "actor": self.actor,
            "target": self.target,
            "details": self.details,
        }


class GovernanceAuditLog:
    """Append-only audit log for all governance-relevant actions."""

    def __init__(self) -> None:
        self._entries: List[GovernanceAuditEntry] = []

    def log(self, action: str, actor: str, target: str, details: str = "") -> None:
        self._entries.append(GovernanceAuditEntry(
            timestamp=_now(),
            action=action,
            actor=actor,
            target=target,
            details=details,
        ))

    def entries(self) -> List[GovernanceAuditEntry]:
        return list(self._entries)

    def entries_for_target(self, target: str) -> List[GovernanceAuditEntry]:
        return [e for e in self._entries if e.target == target]


# ─── Unified governance facade ───────────────────────────────────────

class GovernanceEnforcement:
    """Unified facade for all 6 governance enforcement items.

    Provides a single entry point for the service layer to check
    governance gates and log governance actions.
    """

    def __init__(self, consent_model: ConsentModel = ConsentModel.OPT_OUT) -> None:
        self.purpose_gate = PurposeLimitationGate()
        self.disclosure_gate = DisclosureGate()
        self.consent_manager = ConsentManager(default_model=consent_model)
        self.bias_review = BiasReviewManager()
        self.challenge_manager = ChallengeManager()
        self.correction_manager = CorrectionManager()
        self.audit_log = GovernanceAuditLog()

    def check_ingestion(self, operator_id: str, purpose_id: str = "") -> tuple[bool, List[str]]:
        """Run all ingestion-time governance checks.

        Returns (permitted, reasons). If any check fails, ingestion
        is blocked and all failure reasons are returned.
        """
        reasons: List[str] = []

        ok, reason = self.purpose_gate.check_ingestion(purpose_id)
        if not ok:
            reasons.append(reason)

        ok, reason = self.disclosure_gate.check_ingestion(operator_id)
        if not ok:
            reasons.append(reason)

        ok, reason = self.consent_manager.check_ingestion(operator_id)
        if not ok:
            reasons.append(reason)

        if reasons:
            self.audit_log.log(
                action="ingestion_blocked",
                actor="system",
                target=operator_id,
                details="; ".join(reasons),
            )
            return False, reasons

        self.audit_log.log(
            action="ingestion_permitted",
            actor="system",
            target=operator_id,
            details=f"purpose={purpose_id}",
        )
        return True, ["All governance checks passed."]

    def check_computation(self, purpose_id: str, eval_question: str,
                          target_id: str = "") -> tuple[bool, List[str]]:
        """Run computation-time governance checks.

        Includes purpose scope check (blocking) and bias review
        downgrade check (warning only — computation proceeds but
        evidence grade is downgraded).
        """
        reasons: List[str] = []
        blocking = False

        ok, reason = self.purpose_gate.check_computation(purpose_id, eval_question)
        if not ok:
            reasons.append(reason)
            blocking = True

        if target_id and self.bias_review.check_downgrade(target_id):
            reasons.append(f"Target '{target_id}' flagged for bias — evidence grade downgraded by 1.")

        if blocking:
            return False, reasons
        return True, reasons if reasons else ["Computation governance checks passed."]
