"""Diagnosis engine — generates Diagnosis objects from detected patterns.

Per `21` P1 acceptance: "every diagnosis contains evidence + alternatives +
status=HYPOTHESIS."

Per `09`: "a metric pattern is not a personality trait and not a causal
diagnosis." Diagnoses are HYPOTHESES explaining observed patterns, with
alternative explanations and confidence scores.

Per `09` §Diagnostic hierarchy (the ordering rule — the spec's primary
safeguard against operator-blame misattribution):
    1. Operator       — individual operating pattern
    2. Tool / Model   — model mismatch, tool fit, provider caching
    3. Workflow       — stage design, handoff, review policy
    4. Organization   — training, access, incentives, role design
The engine labels each diagnosis with its level, emits diagnoses in
hierarchy order (operator first), and flags a higher-level hypothesis as
structurally_stronger when evidence supports both an operator-level and a
higher-level hypothesis for the same operator. Do not advance to a higher
level until the current level has been examined and ruled out (or noted as
a contributor).

The diagnosis engine maps each pattern family to:
    - One or more candidate hypotheses (from `09`)
    - Alternative explanations (from `09`)
    - Recommended intervention classes (from `09`)
    - Confidence based on pattern strength + evidence quality
    - Hierarchy level (from `09` §Pattern families)
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.diagnosis import Diagnosis, DiagnosisStatus, DiagnosticLevel
from .pattern_engine import DetectedPattern


# Pattern family → (hypotheses, alternatives, recommended_interventions, level)
# Sourced from `09_DIAGNOSTIC_INTERVENTION_REGISTRY.md`.
# The `level` field implements the diagnostic hierarchy ordering rule.
PATTERN_KNOWLEDGE: Dict[str, dict] = {
    "P-CTX-01": {
        "hypotheses": [
            "repeated context reconstruction",
            "task mix dominated by short-lived tasks",
            "provider caching not enabled",
            "operator intentionally works statelessly",
        ],
        "alternatives": [
            "provider cache semantics differ from expected",
            "short project duration reduces cache benefit",
            "operator works across many small repos",
        ],
        "interventions": ["CTX-001", "CTX-002", "CTX-003"],
        "level": DiagnosticLevel.OPERATOR,
    },
    "P-CTX-02": {
        "hypotheses": [
            "rich context but weak execution/request framing",
            "model mismatch",
            "review/research stage rather than generation stage",
        ],
        "alternatives": [
            "operator in research/exploration phase",
            "task complexity requires more output relative to context",
        ],
        "interventions": ["FRM-001", "MOD-001"],
        # `09`: operator → tool_model (rich context but weak output may be a
        # model mismatch, not an operator skill issue). Primary level operator.
        "level": DiagnosticLevel.OPERATOR,
    },
    "P-BURN-01": {
        "hypotheses": [
            "excessive fresh-input reconstruction",
            "task churn",
            "repeated retries",
            "complex legitimate workload",
        ],
        "alternatives": [
            "legitimately complex project requiring high input volume",
            "onboarding period with higher trial-and-error",
            "tooling mismatch causing retries",
        ],
        "interventions": ["COA-001", "CTX-001", "FRM-002"],
        # `09`: operator → workflow (excessive reconstruction may indicate a
        # workflow that forces fresh starts, not an operator habit).
        "level": DiagnosticLevel.OPERATOR,
    },
    "P-HIDDEN-01": {
        "hypotheses": [
            "potentially efficient or underutilized operator",
        ],
        "alternatives": [
            "operator has low telemetry due to working outside tracked tools",
            "operator uses tools not yet connected to telemetry",
            "operator's tasks require less AI assistance",
        ],
        "interventions": [],  # P-HIDDEN-01: "do not infer superior job performance"
        # `09`: operator → organization (underutilization may be an
        # access/role-design issue, not an operator choice).
        "level": DiagnosticLevel.OPERATOR,
    },
    "P-MODEL-01": {
        "hypotheses": [
            "model routing mismatch",
            "model capability differences",
            "stage-specific model policy needed",
        ],
        "alternatives": [
            "different tasks assigned to different models",
            "model version change during window",
        ],
        "interventions": ["MOD-001", "AGT-001"],
        # `09`: tool_model (this is the canonical tool/model-level pattern;
        # do not reattribute to operator).
        "level": DiagnosticLevel.TOOL_MODEL,
    },
    "P-STAGE-01": {
        "hypotheses": [
            "operator metrics consistently stronger in one workflow stage",
        ],
        "alternatives": [
            "insufficient cross-stage samples",
            "task complexity varies by stage",
        ],
        "interventions": ["STG-001"],
        # `09`: workflow (this is a workflow-level pattern; stage design is
        # the primary hypothesis, not operator preference).
        "level": DiagnosticLevel.WORKFLOW,
    },
}


class DiagnosisEngine:
    """Generates Diagnosis objects from detected patterns.

    Every diagnosis:
    - Has status = HYPOTHESIS (never VALIDATED without separate validation)
    - Contains evidence (the pattern's evidence summary)
    - Contains alternatives (from the pattern knowledge base)
    - Contains recommended interventions (from the pattern knowledge base)
    - Is labeled with its diagnostic hierarchy level (per `09`)
    - Is emitted in hierarchy order (operator → tool_model → workflow → org)
    - Is flagged structurally_stronger when a higher-level hypothesis is
      emitted alongside an operator-level one for the same operator
    """

    def generate_diagnoses(
        self,
        operator_id: str,
        patterns: List[DetectedPattern],
    ) -> List[Diagnosis]:
        """Generate one diagnosis per detected pattern, in hierarchy order.

        Each diagnosis carries the primary hypothesis, all alternatives,
        and recommended interventions from the pattern knowledge base, plus
        its hierarchy level. The returned list is sorted by hierarchy level
        (operator first). When evidence supports both an operator-level and
        a higher-level hypothesis for the same operator, the higher-level
        diagnosis is flagged structurally_stronger=True.
        """
        # Build the raw diagnoses (one per pattern) with hierarchy levels.
        raw: List[Diagnosis] = []
        for i, pat in enumerate(patterns):
            knowledge = PATTERN_KNOWLEDGE.get(pat.pattern_id, {
                "hypotheses": ["unknown pattern — manual review needed"],
                "alternatives": ["insufficient pattern knowledge"],
                "interventions": [],
                "level": DiagnosticLevel.OPERATOR,
            })

            primary_hypothesis = knowledge["hypotheses"][0]
            alternatives = knowledge["alternatives"]
            interventions = knowledge["interventions"]
            level: DiagnosticLevel = knowledge["level"]

            # Combine pattern evidence with the hypothesis
            full_evidence = f"Pattern {pat.pattern_id}: {pat.evidence_summary}. Hypothesis: {primary_hypothesis}."

            raw.append(Diagnosis(
                diagnosis_id=f"diag_{operator_id}_{pat.pattern_id}_{i:02d}",
                operator_id=operator_id,
                pattern_id=pat.pattern_id,
                hypothesis=primary_hypothesis,
                confidence=round(pat.confidence, 2),
                status=DiagnosisStatus.HYPOTHESIS,  # ALWAYS HYPOTHESIS per P1 acceptance
                evidence=full_evidence,
                alternatives=list(alternatives),
                recommended_interventions=list(interventions),
                window_start=pat.window_start,
                window_end=pat.window_end,
                synthetic=pat.synthetic,
                level=level,
            ))

        # Apply the hierarchy ordering rule: sort by level (operator first).
        # Stable sort preserves the original pattern order within a level.
        ordered = sorted(raw, key=lambda d: DiagnosticLevel.order(d.level))

        # Flag structurally_stronger on higher-level diagnoses when evidence
        # supports both an operator-level and a higher-level hypothesis for
        # the same operator. Per `09`: "A hypothesis at a higher level should
        # be flagged as structurally stronger than one at a lower level when
        # evidence supports both."
        has_operator_level = any(d.level == DiagnosticLevel.OPERATOR for d in ordered)
        if has_operator_level:
            for d in ordered:
                if DiagnosticLevel.order(d.level) > DiagnosticLevel.order(DiagnosticLevel.OPERATOR):
                    # Use object.__setattr__ because Diagnosis is frozen.
                    object.__setattr__(d, "structurally_stronger", True)

        return ordered

    def generate_cohort_diagnoses(
        self,
        cohort_patterns: Dict[str, List[DetectedPattern]],
    ) -> Dict[str, List[Diagnosis]]:
        """Generate diagnoses for all operators in a cohort."""
        return {
            oid: self.generate_diagnoses(oid, patterns)
            for oid, patterns in cohort_patterns.items()
            if patterns  # only include operators with detected patterns
        }
