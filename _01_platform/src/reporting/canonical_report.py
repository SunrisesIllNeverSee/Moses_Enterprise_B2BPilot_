"""CanonicalReport — one report model feeding Markdown, HTML, and PDF.

Per the deep-dive review §18 (Reporting Integrity Invariants):
    1. Every number in a pilot readout must originate from canonical
       pilot evidence or canonical pilot state.
    2. All presentation formats must derive from one report model.
    3. A handwritten or static sample report must never be an
       independent source for a customer-facing PDF.

This module implements the canonical report model. It collects pilot
evidence and state into a single data structure, then renders that
structure to Markdown, HTML, and PDF. No format has its own independent
data source.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from service import PilotService


@dataclass
class CanonicalReport:
    """The single canonical report model for a pilot readout.

    All numbers originate from PilotService (canonical pilot evidence
    and state). All presentation formats (Markdown, HTML, PDF) derive
    from this object — no format has an independent data source.
    """
    pilot_id: str = ""
    cohort_id: str = ""
    window_start: str = ""
    window_end: str = ""
    operator_count: int = 0
    eligible_operators: int = 0
    observation_count: int = 0
    providers: List[str] = field(default_factory=list)
    metric_registry_version: str = ""
    reference_field_version: str = ""
    active_interventions: int = 0
    data_quality: Dict[str, int] = field(default_factory=dict)
    divergence_counts: Dict[str, int] = field(default_factory=dict)
    cohort_medians: Dict[str, Optional[float]] = field(default_factory=dict)
    findings_count: int = 0
    verification_summary: Dict = field(default_factory=dict)
    engagement_status: Optional[Dict] = None
    synthetic: bool = True

    def to_dict(self) -> dict:
        return {
            "pilot_id": self.pilot_id,
            "cohort_id": self.cohort_id,
            "window": {"start": self.window_start, "end": self.window_end},
            "operator_count": self.operator_count,
            "eligible_operators": self.eligible_operators,
            "observation_count": self.observation_count,
            "providers": list(self.providers),
            "metric_registry_version": self.metric_registry_version,
            "reference_field_version": self.reference_field_version,
            "active_interventions": self.active_interventions,
            "data_quality": dict(self.data_quality),
            "divergence_counts": dict(self.divergence_counts),
            "cohort_medians": dict(self.cohort_medians),
            "findings_count": self.findings_count,
            "verification_summary": dict(self.verification_summary),
            "engagement_status": self.engagement_status,
            "synthetic": self.synthetic,
        }


def build_canonical_report(svc: "PilotService") -> CanonicalReport:
    """Build a CanonicalReport from PilotService (canonical pilot evidence).

    This is the single source of truth for all report formats. Every
    number originates from the service layer — no static or handwritten
    data is mixed in.
    """
    status = svc.pilot_status()
    run = svc.pilot_run
    engagement = run.engagement_status() if run else None
    return CanonicalReport(
        pilot_id=run.pilot_id if run else "",
        cohort_id=status.get("cohort_id", ""),
        window_start=status.get("window", {}).get("start", ""),
        window_end=status.get("window", {}).get("end", ""),
        operator_count=status.get("total_operators", 0),
        eligible_operators=status.get("eligible_operators", 0),
        observation_count=status.get("observation_count", 0),
        providers=status.get("providers", []),
        metric_registry_version=status.get("metric_registry_version", ""),
        reference_field_version=status.get("reference_field_version", ""),
        active_interventions=status.get("active_interventions", 0),
        data_quality=status.get("data_quality", {}),
        divergence_counts=svc.divergence_counts(),
        cohort_medians=svc.cohort_medians(),
        findings_count=len(svc.diagnoses),
        verification_summary={},
        engagement_status=engagement,
        synthetic=status.get("synthetic", True),
    )


def render_canonical_markdown(report: CanonicalReport) -> str:
    """Render the canonical report as Markdown."""
    lines = [
        f"# MO§ES™ Pilot Readout — {report.pilot_id or report.cohort_id}",
        "",
        f"**Window:** {report.window_start} to {report.window_end}",
        f"**Cohort:** {report.cohort_id} ({report.operator_count} operators, "
        f"{report.eligible_operators} eligible)",
        f"**Observations:** {report.observation_count}",
        f"**Providers:** {', '.join(report.providers) or '—'}",
        f"**Metric Registry:** {report.metric_registry_version}",
        f"**Reference Field:** {report.reference_field_version}",
        "",
        "## Data Quality",
        "",
    ]
    for sev, count in sorted(report.data_quality.items()):
        lines.append(f"- **{sev}:** {count}")
    lines.extend([
        "",
        "## Divergence Distribution",
        "",
    ])
    for cls, count in sorted(report.divergence_counts.items()):
        lines.append(f"- **{cls}:** {count}")
    lines.extend([
        "",
        "## Cohort Medians",
        "",
    ])
    for metric, val in sorted(report.cohort_medians.items()):
        lines.append(f"- **{metric}:** {val:.4f}" if val is not None else f"- **{metric}:** —")
    lines.extend([
        "",
        "## Findings",
        "",
        f"- **Diagnostic findings:** {report.findings_count}",
        f"- **Active interventions:** {report.active_interventions}",
        "",
    ])
    if report.engagement_status:
        es = report.engagement_status
        lines.extend([
            "## Engagement Status",
            "",
            f"- **Pilot ID:** {es.get('pilot_id', '—')}",
            f"- **Customer:** {es.get('customer', '—')}",
            f"- **Day:** {es.get('day', '—')}",
            f"- **Current Stage:** {es.get('current_stage', '—')}",
            f"- **Baseline:** {es.get('baseline', '—')}",
            f"- **Next Gate:** {es.get('next_gate', '—')}",
            f"- **Final Decision:** {es.get('final_decision', '—')}",
            "",
        ])
    if report.synthetic:
        lines.append("> **SYNTHETIC DEMONSTRATION** — not customer proof.")
    return "\n".join(lines)


def render_canonical_html(report: CanonicalReport) -> str:
    """Render the canonical report as HTML."""
    from .pdf import _markdown_to_html, _REPORT_CSS, _TITLE_HTML
    md = render_canonical_markdown(report)
    # Strip the top-level header (replaced by title block)
    lines = md.split("\n")
    skip = True
    content_lines = []
    for line in lines:
        if skip and (line.startswith("#") or line.startswith("===") or line.strip() == ""):
            continue
        skip = False
        content_lines.append(line)
    body_html = _markdown_to_html("\n".join(content_lines))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>MO§ES™ Pilot Readout</title>
<style>{_REPORT_CSS}</style>
</head>
<body>
{_TITLE_HTML}
{body_html}
</body>
</html>"""


def render_canonical_pdf(report: CanonicalReport, output_path: str) -> str:
    """Render the canonical report as PDF.

    Uses the runtime-generated Markdown from the canonical report model.
    This enforces the reporting invariant: the PDF derives from canonical
    pilot evidence, not from a stale static report.
    """
    from .pdf import render_sample_report_pdf
    md = render_canonical_markdown(report)
    return render_sample_report_pdf(
        output_path=output_path,
        runtime_markdown=md,
    )
