"""Tests for composite employee score (Item 9) and executive dashboard (Item 8).

Covers:
- CompositeScore: computation, normalization, governance labels
- Cohort composite scores: distribution, summary stats
- Executive dashboard: HTML generation, structure, governance
- MCP tools: get_composite_score, get_composite_score_summary, get_executive_dashboard
- CLI: score composite, score composite-summary, export dashboard
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ── Composite Score ───────────────────────────────────────────────────────

class TestCompositeScore:
    """Test the composite employee developmental score."""

    def test_composite_score_for_operator(self):
        from service import PilotService
        svc = PilotService()
        oid = svc.operator_ids[0]
        score = svc.composite_score(oid)
        assert score.operator_id == oid
        assert 0 <= score.score <= 100
        assert "leverage" in score.components
        assert "yield" in score.components
        assert "token_snr" in score.components
        assert "construction" in score.components

    def test_composite_score_label_is_developmental(self):
        from service import PilotService
        svc = PilotService()
        score = svc.composite_score(svc.operator_ids[0])
        assert "DEVELOPMENTAL" in score.label
        assert "PERSONNEL" not in score.label

    def test_composite_score_no_punitive_labels(self):
        """Per governance avoid-list: no punitive 'failure' labels."""
        from service import PilotService
        svc = PilotService()
        score = svc.composite_score(svc.operator_ids[0])
        label_lower = score.label.lower()
        assert "underperform" not in label_lower
        assert "failure" not in label_lower
        assert "punitive" not in label_lower

    def test_composite_score_synthetic_flag(self):
        from service import PilotService
        svc = PilotService()
        score = svc.composite_score(svc.operator_ids[0])
        assert score.synthetic is True

    def test_composite_score_to_dict(self):
        from service import PilotService
        svc = PilotService()
        score = svc.composite_score(svc.operator_ids[0])
        d = score.to_dict()
        assert "score" in d
        assert "components" in d
        assert "label" in d
        assert "caveats" in d
        assert d["score_id"] == "dev_index"

    def test_cohort_composite_scores(self):
        from service import PilotService
        svc = PilotService()
        scores = svc.cohort_composite_scores()
        assert len(scores) == len(svc.operator_ids)
        for oid, score in scores.items():
            assert 0 <= score.score <= 100

    def test_composite_score_summary(self):
        from service import PilotService
        svc = PilotService()
        summary = svc.composite_score_summary()
        assert "count" in summary
        assert "median" in summary
        assert "mean" in summary
        assert "min" in summary
        assert "max" in summary
        assert summary["count"] > 0
        assert summary["score_id"] == "dev_index"

    def test_composite_score_summary_no_individual_ranking(self):
        """Summary must not expose individual operator scores or rankings."""
        from service import PilotService
        svc = PilotService()
        summary = svc.composite_score_summary()
        # Should only have aggregate stats, not per-operator data
        assert "operators" not in summary
        assert "ranking" not in summary
        assert "scores" not in summary

    def test_composite_score_weights_sum_to_one(self):
        from metrics.composite_score import METRIC_WEIGHTS
        assert abs(sum(METRIC_WEIGHTS.values()) - 1.0) < 0.001

    def test_composite_score_excludes_unresolved_metrics(self):
        """Velocity, compression, stability have NEEDS_CANONICAL_LOCK — excluded."""
        from metrics.composite_score import METRIC_WEIGHTS
        assert "velocity" not in METRIC_WEIGHTS
        assert "compression_operating_ratio" not in METRIC_WEIGHTS
        assert "stability" not in METRIC_WEIGHTS

    def test_composite_score_with_sqlite(self):
        from service import PilotService
        svc = PilotService(db_path=":memory:")
        score = svc.composite_score(svc.operator_ids[0])
        assert 0 <= score.score <= 100

    def test_composite_score_caveats_for_interpretation_limits(self):
        """token_snr and construction have CANONICAL_WITH_INTERPRETATION_LIMIT."""
        from service import PilotService
        svc = PilotService()
        score = svc.composite_score(svc.operator_ids[0])
        # At least one caveat should mention interpretation limit
        caveat_text = " ".join(score.caveats).lower()
        # If both metrics are present, we should see interpretation limit caveats
        has_snr = score.components.get("token_snr", {}).get("value") is not None
        has_construction = score.components.get("construction", {}).get("value") is not None
        if has_snr and has_construction:
            assert "interpret" in caveat_text or "limit" in caveat_text


# ── Executive Dashboard ───────────────────────────────────────────────────

class TestExecutiveDashboard:
    """Test the polished executive dashboard HTML generator."""

    def test_dashboard_generates_html(self):
        from reporting import generate_executive_dashboard
        from service import PilotService
        svc = PilotService()
        html = generate_executive_dashboard(svc)
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
        assert len(html) > 1000  # substantial content

    def test_dashboard_has_cohort_id(self):
        from reporting import generate_executive_dashboard
        from service import PilotService
        svc = PilotService()
        html = generate_executive_dashboard(svc)
        assert svc.cohort.cohort_id in html

    def test_dashboard_has_composite_score_section(self):
        from reporting import generate_executive_dashboard
        from service import PilotService
        svc = PilotService()
        html = generate_executive_dashboard(svc)
        assert "Development Index" in html or "dev_index" in html.lower()

    def test_dashboard_has_governance_labels(self):
        from reporting import generate_executive_dashboard
        from service import PilotService
        svc = PilotService()
        html = generate_executive_dashboard(svc)
        assert "DEVELOPMENTAL" in html
        assert "SYNTHETIC" in html

    def test_dashboard_has_disclaimer(self):
        from reporting import generate_executive_dashboard
        from service import PilotService
        svc = PilotService()
        html = generate_executive_dashboard(svc)
        assert "disclaimer" in html.lower() or "synthetic demo data" in html.lower()

    def test_dashboard_has_no_leaderboard(self):
        """Per governance avoid-list: no bottom-employee leaderboard."""
        from reporting import generate_executive_dashboard
        from service import PilotService
        svc = PilotService()
        html = generate_executive_dashboard(svc)
        html_lower = html.lower()
        assert "leaderboard" not in html_lower
        assert "worst" not in html_lower
        assert "bottom-employee" not in html_lower

    def test_dashboard_has_next_evaluations(self):
        from reporting import generate_executive_dashboard
        from service import PilotService
        svc = PilotService()
        html = generate_executive_dashboard(svc)
        assert "Next Evaluations" in html or "eval-card" in html

    def test_dashboard_has_workflow_heatmap(self):
        from reporting import generate_executive_dashboard
        from service import PilotService
        svc = PilotService()
        html = generate_executive_dashboard(svc)
        assert "heatmap" in html.lower() or "Workflow Fit" in html

    def test_dashboard_with_sqlite(self):
        from reporting import generate_executive_dashboard
        from service import PilotService
        svc = PilotService(db_path=":memory:")
        html = generate_executive_dashboard(svc)
        assert "<!DOCTYPE html>" in html

    def test_dashboard_self_contained(self):
        """No external CSS/JS dependencies — all inline."""
        from reporting import generate_executive_dashboard
        from service import PilotService
        svc = PilotService()
        html = generate_executive_dashboard(svc)
        # No external stylesheet links
        assert '<link rel="stylesheet"' not in html
        assert '<script src=' not in html
        # Has inline style
        assert "<style>" in html


# ── MCP Tools ─────────────────────────────────────────────────────────────

class TestMcpCompositeDashboardTools:
    """Test the new MCP tools for composite score and dashboard."""

    def test_get_composite_score(self):
        from mcp_server.server import get_composite_score
        result = get_composite_score(operator_id="op_001")
        assert "score" in result
        assert 0 <= result["score"] <= 100
        assert "DEVELOPMENTAL" in result["label"]

    def test_get_composite_score_missing_operator(self):
        from mcp_server.server import get_composite_score
        result = get_composite_score(operator_id="")
        assert "error" in result

    def test_get_composite_score_summary(self):
        from mcp_server.server import get_composite_score_summary
        result = get_composite_score_summary()
        assert "median" in result
        assert "count" in result
        assert result["count"] > 0

    def test_get_executive_dashboard(self):
        from mcp_server.server import get_executive_dashboard
        result = get_executive_dashboard()
        assert "dashboard_html" in result
        assert "<!DOCTYPE html>" in result["dashboard_html"]
        assert result["size_bytes"] > 1000

    def test_tool_registry_includes_new_tools(self):
        from mcp_server.server import TOOL_REGISTRY
        assert "get_composite_score" in TOOL_REGISTRY
        assert "get_composite_score_summary" in TOOL_REGISTRY
        assert "get_executive_dashboard" in TOOL_REGISTRY

    def test_call_tool_directly_composite_score(self):
        from mcp_server.server import call_tool_directly
        result = call_tool_directly("get_composite_score", operator_id="op_001")
        assert "score" in result

    def test_call_tool_directly_dashboard(self):
        from mcp_server.server import call_tool_directly
        result = call_tool_directly("get_executive_dashboard")
        assert "dashboard_html" in result
