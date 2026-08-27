"""Decision Report — translates measurement vocabulary to decision vocabulary.

Per Jaimie's product review (Gap 8): "Translate measurement vocabulary
to decision vocabulary in the product surface."

This module converts raw metric findings (Yield, Leverage, Divergence,
etc.) into actionable, decision-oriented language that a manager or
enablement lead can act on. Every recommendation is developmental
(coaching, workshops, reviews) — never a personnel action.

Governance guardrails (per `12` §Development doctrine + §Avoid-list):
- No punitive labels: findings describe patterns, not operator failings.
- No comparative ranking of individuals: cohort-level findings are aggregate, not ranked.
- Outcome claims are ASSOCIATION, never CAUSATION.
- Decision recommendations are developmental (coaching, workshops,
  reviews) — never personnel actions (PIP, termination, demotion).
- Composite score is developmental, not personnel-related.

Translation examples (from Jaimie's review):
- "Yield is 0.15 (10th percentile)" → "This operator's output efficiency
  is in the bottom 10% of the cohort. Recommended action: context
  structuring coaching."
- "Leverage is 0.05" → "This operator rarely reuses context. They're
  paying for fresh input on every turn. Recommended action: context
  caching workshop."
- "Divergence: high usage, low performance" → "This operator's AI usage
  volume suggests engagement, but their output doesn't reflect it. They
  may be stuck in a loop. Recommended action: workflow review."
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from service import PilotService

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ── Decision vocabulary mappings ────────────────────────────────────────
# Each metric maps to a human-readable "decision name" and a set of
# developmental action recommendations keyed by the finding band.
# Bands are percentile-relative so they adapt to the cohort.

_METRIC_DECISION_NAMES = {
    "yield": "output efficiency",
    "leverage": "context reuse",
    "token_snr": "signal-to-noise ratio",
    "construction": "context construction",
    "log_leverage": "context reuse (log scale)",
}

# Developmental action recommendations by band.
# These are coaching/enablement actions, NEVER personnel actions.
_METRIC_ACTIONS = {
    "yield": {
        "low": "context structuring coaching",
        "medium": "output efficiency review",
        "high": "share effective patterns with peers",
    },
    "leverage": {
        "low": "context caching workshop",
        "medium": "context reuse review",
        "high": "share context-reuse patterns with peers",
    },
    "token_snr": {
        "low": "prompt clarity coaching",
        "medium": "signal-to-noise review",
        "high": "share prompt-clarity patterns with peers",
    },
    "construction": {
        "low": "context building coaching",
        "medium": "context construction review",
        "high": "share context-building patterns with peers",
    },
}

# Divergence class → decision language + developmental action.
_DIVERGENCE_DECISIONS = {
    "HIGH_USAGE_LOW_OPERATION": {
        "finding": (
            "This operator's AI usage volume suggests engagement, but "
            "their output doesn't reflect it. They may be stuck in a "
            "loop — spending tokens without converting them to output."
        ),
        "action": "workflow review",
        "action_detail": (
            "Review the operator's workflow to identify where tokens "
            "are being spent without producing output. Consider "
            "pairing with a high-output peer for a workflow walkthrough."
        ),
    },
    "LOW_USAGE_HIGH_OPERATION": {
        "finding": (
            "This operator achieves strong output metrics with "
            "relatively low usage volume — they may be highly efficient "
            "or may be under-utilizing available capacity."
        ),
        "action": "capacity expansion review",
        "action_detail": (
            "Consider whether this operator has capacity for higher-"
            "complexity tasks. Their efficiency is a developmental "
            "asset worth understanding and sharing."
        ),
    },
    "LOW_LOW": {
        "finding": (
            "This operator shows low usage and low output metrics. "
            "This may indicate low engagement, limited access, or a "
            "role mismatch — all addressable through enablement."
        ),
        "action": "enablement onboarding",
        "action_detail": (
            "An enablement check-in can surface access barriers, "
            "training gaps, or role alignment. This is a developmental "
            "conversation, not a performance judgment."
        ),
    },
    "MIXED": {
        "finding": (
            "This operator's usage and output metrics are within "
            "typical cohort ranges. No specific developmental action "
            "is indicated at this time."
        ),
        "action": "routine development check-in",
        "action_detail": (
            "Continue regular development conversations. Monitor for "
            "trend changes over time."
        ),
    },
    "HIGH_HIGH": {
        "finding": (
            "This operator shows high usage and high output metrics — "
            "strong engagement with effective conversion."
        ),
        "action": "share effective patterns with peers",
        "action_detail": (
            "This operator's patterns may be valuable to share with "
            "the cohort through a peer learning session."
        ),
    },
}


def _band_for_percentile(percentile: Optional[float]) -> str:
    """Map a percentile (0–100) to a developmental band.

    Bands: "low" (≤25th), "medium" (25–75), "high" (≥75).
    These are relative-to-cohort bands, not absolute judgments.
    """
    if percentile is None:
        return "unknown"
    if percentile <= 25:
        return "low"
    if percentile >= 75:
        return "high"
    return "medium"


def _metric_finding(
    metric_id: str,
    value: Optional[float],
    percentile: Optional[float],
) -> Dict[str, str]:
    """Translate a single metric finding into decision vocabulary.

    Returns a dict with:
        - decision_name: human-readable metric name
        - finding: the decision-oriented finding sentence
        - recommended_action: developmental action
        - action_detail: detail on the developmental action
        - band: the developmental band (low/medium/high/unknown)
    """
    decision_name = _METRIC_DECISION_NAMES.get(metric_id, metric_id)
    band = _band_for_percentile(percentile)
    actions = _METRIC_ACTIONS.get(metric_id, {})
    action = actions.get(band, "routine development check-in")

    if value is None:
        finding = (
            f"This operator's {decision_name} could not be measured "
            f"(insufficient data for this metric)."
        )
        action = "data completeness review"
        action_detail = (
            "Ensure sufficient telemetry is collected before drawing "
            "developmental conclusions."
        )
    elif band == "low":
        pct_str = f"bottom {int(percentile)}%" if percentile is not None else "the lower range"
        finding = (
            f"This operator's {decision_name} is in the {pct_str} of "
            f"the cohort."
        )
        action_detail = (
            f"A {action} can help identify structural barriers and "
            f"build effective habits. This is a developmental "
            f"opportunity, not a performance judgment."
        )
    elif band == "high":
        pct_str = f"top {100 - int(percentile)}%" if percentile is not None else "the upper range"
        finding = (
            f"This operator's {decision_name} is in the {pct_str} of "
            f"the cohort."
        )
        action_detail = (
            f"This is a developmental strength. A {action} can help "
            f"diffuse these effective patterns across the cohort."
        )
    else:
        finding = (
            f"This operator's {decision_name} is within the typical "
            f"cohort range."
        )
        action_detail = (
            f"A {action} can help maintain and refine this level. "
            f"No urgent developmental action is indicated."
        )

    return {
        "metric_id": metric_id,
        "decision_name": decision_name,
        "raw_value": value,
        "percentile": percentile,
        "band": band,
        "finding": finding,
        "recommended_action": action,
        "action_detail": action_detail,
        "claim_type": "ASSOCIATION",
    }


def _divergence_finding(divergence_class: str) -> Dict[str, str]:
    """Translate a divergence class into decision vocabulary."""
    decision = _DIVERGENCE_DECISIONS.get(
        divergence_class,
        _DIVERGENCE_DECISIONS["MIXED"],
    )
    return {
        "divergence_class": divergence_class,
        "finding": decision["finding"],
        "recommended_action": decision["action"],
        "action_detail": decision["action_detail"],
        "claim_type": "ASSOCIATION",
    }


def build_operator_decision_report(
    svc: "PilotService",
    operator_id: str,
) -> dict:
    """Build a decision-oriented report for a single operator.

    Translates the operator's canonical metrics, percentiles, and
    divergence class into actionable developmental language.
    """
    op = svc.get_operator(operator_id)
    if op is None:
        return {"error": f"Unknown operator {operator_id}"}

    ms = svc.score_operator(operator_id)
    pcts = svc.percentiles().get(operator_id, {})
    div_map = {r.operator_id: r for r in svc.divergence()}
    div = div_map.get(operator_id)

    metric_findings: List[dict] = []
    for m in ms:
        pct_m = pcts.get(f"{m.metric_id}_percentile")
        percentile = pct_m.value if pct_m else None
        metric_findings.append(
            _metric_finding(m.metric_id, m.value, percentile)
        )

    divergence_finding = None
    if div is not None:
        divergence_finding = _divergence_finding(div.divergence_class)
        divergence_finding["usage_percentile"] = div.usage_percentile
        divergence_finding["yield_percentile"] = div.yield_percentile

    return {
        "operator_id": operator_id,
        "report_type": "decision_report",
        "metric_findings": metric_findings,
        "divergence_finding": divergence_finding,
        "label": (
            "DEVELOPMENTAL — decision-oriented recommendations for "
            "coaching and enablement; not a personnel evaluation"
        ),
        "claim_type": "ASSOCIATION",
        "governance_note": (
            "All recommendations are developmental (coaching, workshops, "
            "reviews). Outcome claims are ASSOCIATION, never CAUSATION. "
            "No punitive labels. No comparative ranking of individuals."
        ),
        "synthetic": True,
    }


def build_cohort_decision_report(svc: "PilotService") -> dict:
    """Build a cohort-level decision-oriented summary.

    Aggregates decision recommendations across the cohort without
    ranking individual operators. Surfaces the most common developmental
    actions needed so enablement leads can plan cohort-wide coaching.
    """
    from collections import Counter

    div_counts = svc.divergence_counts()
    div_findings: List[dict] = []
    for div_class, count in sorted(div_counts.items()):
        decision = _divergence_decisions(div_class)
        div_findings.append({
            "divergence_class": div_class,
            "operator_count": count,
            "finding": decision["finding"],
            "recommended_action": decision["action"],
            "action_detail": decision["action_detail"],
            "claim_type": "ASSOCIATION",
        })

    # Aggregate metric-band counts across the cohort (no ranking).
    band_counts: Dict[str, Dict[str, int]] = {}
    pcts = svc.percentiles()
    for oid in svc.operator_ids:
        ms = svc.score_operator(oid)
        op_pcts = pcts.get(oid, {})
        for m in ms:
            if m.metric_id not in _METRIC_DECISION_NAMES:
                continue
            pct_m = op_pcts.get(f"{m.metric_id}_percentile")
            band = _band_for_percentile(pct_m.value if pct_m else None)
            band_counts.setdefault(m.metric_id, {"low": 0, "medium": 0, "high": 0, "unknown": 0})
            band_counts[m.metric_id][band] = band_counts[m.metric_id].get(band, 0) + 1

    # Identify the most common developmental actions needed (cohort-wide).
    action_demand: Counter = Counter()
    for metric_id, bands in band_counts.items():
        actions = _METRIC_ACTIONS.get(metric_id, {})
        for band, count in bands.items():
            if band in ("low", "medium") and count > 0:
                action = actions.get(band, "routine development check-in")
                action_demand[action] += count

    top_actions = [
        {"recommended_action": action, "operators_indicated": count}
        for action, count in action_demand.most_common(5)
    ]

    return {
        "report_type": "cohort_decision_report",
        "cohort_id": svc.cohort.cohort_id,
        "divergence_findings": div_findings,
        "metric_band_counts": band_counts,
        "top_developmental_actions": top_actions,
        "label": (
            "DEVELOPMENTAL — cohort-level enablement planning; "
            "not an individual ranking"
        ),
        "claim_type": "ASSOCIATION",
        "governance_note": (
            "All recommendations are developmental (coaching, workshops, "
            "reviews). No punitive labels. No comparative ranking of individuals. Aggregate "
            "counts only — individual operators are not ranked."
        ),
        "synthetic": True,
    }


def _divergence_decisions(divergence_class: str) -> Dict[str, str]:
    """Helper to get the decision dict for a divergence class."""
    return _DIVERGENCE_DECISIONS.get(
        divergence_class, _DIVERGENCE_DECISIONS["MIXED"]
    )


def build_decision_report(
    svc: "PilotService",
    operator_id: str = "",
) -> dict:
    """Build a decision-oriented report.

    Per Gap 8: translates measurement vocabulary to decision vocabulary.

    Args:
        svc: The PilotService.
        operator_id: If provided, build a per-operator report. If empty,
            build a cohort-level summary.

    Returns:
        A dict with decision-oriented findings and developmental action
        recommendations.
    """
    if operator_id:
        return build_operator_decision_report(svc, operator_id)
    return build_cohort_decision_report(svc)


def export_decision_report_markdown(svc: "PilotService", operator_id: str = "") -> str:
    """Export the decision report as Markdown.

    Uses decision vocabulary throughout. Every recommendation is
    developmental. No punitive labels. No comparative ranking of individuals.
    """
    report = build_decision_report(svc, operator_id=operator_id)

    if "error" in report:
        return f"# Decision Report\n\n**[LIMITATION]** {report['error']}\n"

    lines = [
        "# Decision Report",
        "",
        f"**[DEVELOPMENTAL]** {report['label']}",
        f"**[GOVERNANCE]** {report['governance_note']}",
        "",
    ]

    if report["report_type"] == "decision_report":
        lines.extend([
            f"**[FACT]** Operator: {report['operator_id']}",
            "",
            "## Metric Findings",
            "",
        ])
        for f in report["metric_findings"]:
            lines.extend([
                f"### {f['decision_name'].title()} ({f['metric_id']})",
                "",
                f"**[MEASUREMENT]** {f['finding']}",
                f"**[RECOMMENDATION]** Recommended action: {f['recommended_action']}.",
                f"**[DEVELOPMENTAL]** {f['action_detail']}",
                "",
            ])
        if report.get("divergence_finding"):
            df = report["divergence_finding"]
            lines.extend([
                "## Usage vs Output Divergence",
                "",
                f"**[MEASUREMENT]** {df['finding']}",
                f"**[RECOMMENDATION]** Recommended action: {df['recommended_action']}.",
                f"**[DEVELOPMENTAL]** {df['action_detail']}",
                "",
            ])
    else:
        lines.extend([
            f"**[FACT]** Cohort: {report['cohort_id']}",
            "",
            "## Cohort Divergence Findings",
            "",
        ])
        for df in report["divergence_findings"]:
            lines.extend([
                f"### {df['divergence_class']} ({df['operator_count']} operators)",
                "",
                f"**[MEASUREMENT]** {df['finding']}",
                f"**[RECOMMENDATION]** Recommended action: {df['recommended_action']}.",
                f"**[DEVELOPMENTAL]** {df['action_detail']}",
                "",
            ])
        lines.extend([
            "## Top Developmental Actions (cohort-wide)",
            "",
            "| Recommended Action | Operators Indicated |",
            "|--------------------|---------------------|",
        ])
        for ta in report["top_developmental_actions"]:
            lines.append(f"| {ta['recommended_action']} | {ta['operators_indicated']} |")
        lines.append("")

    lines.extend([
        "---",
        "*All recommendations are developmental (coaching, workshops, reviews). "
        "Outcome claims are ASSOCIATION, never CAUSATION. No punitive labels. "
        "No comparative ranking of individuals.*",
    ])
    return "\n".join(lines) + "\n"
