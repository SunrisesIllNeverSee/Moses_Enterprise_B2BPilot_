"""Tests for Operator×System decomposition, Outcome domain object,
lineage chain reconstruction, and outcome correlation.

Covers:
- Outcome dataclass (from_dict, to_dict, round-trip)
- Lineage flat-field loading and link conversion
- Operator×System decomposition (two-way ANOVA-style)
- Outcome correlation (Pearson r, interpretation)
- Service methods (operator_system_decomposition, lineage_chain, outcome_correlation)
- MCP tools (get_operator_system_decomposition, get_lineage_chain, get_outcome_correlation)
"""
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest
from domain import Outcome, OutcomeType, OutcomeStatus, Lineage, LinkType
from analysis.operator_system import (
    compute_operator_system_decomposition,
    MetricDecomposition, OperatorEffect, SystemEffect, InteractionCell,
    OperatorSystemDecomposition,
)
from analysis.outcome_correlation import (
    compute_outcome_correlation,
    OutcomeCorrelationResult, MetricOutcomeCorrelation,
)


class TestOutcomeDomain:
    """Test the Outcome domain object."""

    def test_outcome_creation(self):
        o = Outcome(
            outcome_id="out_001",
            lineage_id="lin_001",
            operator_id="op_001",
            outcome_type=OutcomeType.PR_MERGED,
            outcome_status=OutcomeStatus.SUCCESS,
            synthetic=True,
            external_quality_score=0.85,
            cycle_time_minutes=120,
        )
        assert o.outcome_id == "out_001"
        assert o.outcome_type == OutcomeType.PR_MERGED
        assert o.outcome_status == OutcomeStatus.SUCCESS
        assert o.external_quality_score == 0.85

    def test_outcome_from_dict(self):
        d = {
            "outcome_id": "out_002",
            "lineage_id": "lin_002",
            "operator_id": "op_002",
            "outcome_type": "bug_fixed",
            "outcome_status": "partial",
            "synthetic": True,
            "external_quality_score": 0.6,
            "cycle_time_minutes": 240,
        }
        o = Outcome.from_dict(d)
        assert o.outcome_id == "out_002"
        assert o.outcome_type == OutcomeType.BUG_FIXED
        assert o.outcome_status == OutcomeStatus.PARTIAL

    def test_outcome_to_dict_round_trip(self):
        o = Outcome(
            outcome_id="out_003",
            lineage_id="lin_003",
            operator_id="op_003",
            outcome_type=OutcomeType.FEATURE_SHIPPED,
            outcome_status=OutcomeStatus.SUCCESS,
            synthetic=False,
        )
        d = o.to_dict()
        o2 = Outcome.from_dict(d)
        assert o2.outcome_id == o.outcome_id
        assert o2.outcome_type == o.outcome_type
        assert o2.outcome_status == o.outcome_status
        assert o2.synthetic == o.synthetic

    def test_outcome_unknown_type_kept_as_string(self):
        d = {
            "outcome_id": "out_004",
            "lineage_id": "lin_004",
            "operator_id": "op_004",
            "outcome_type": "custom_outcome",
            "outcome_status": "success",
            "synthetic": True,
        }
        o = Outcome.from_dict(d)
        assert o.outcome_type == "custom_outcome"


class TestLineageFlatFields:
    """Test that Lineage loads flat fields from demo JSONL format."""

    def test_lineage_loads_flat_fields(self):
        d = {
            "lineage_id": "lin_test",
            "operator_id": "op_test",
            "synthetic": True,
            "workflow_id": "software_dev_v1",
            "workflow_stage": "architecture",
            "state_a_observation_id": "obs_001",
            "bi_action_observation_id": "obs_002",
            "aai_transformation_observation_id": "obs_003",
            "committed_artifact_id": "art_001",
            "outcome_id": "out_001",
            "micro_eval": {"leverage": 0.5, "yield": 0.4},
        }
        lin = Lineage.from_dict(d)
        assert lin.state_a_observation_id == "obs_001"
        assert lin.bi_action_observation_id == "obs_002"
        assert lin.aai_transformation_observation_id == "obs_003"
        assert lin.committed_artifact_id == "art_001"
        assert lin.outcome_id == "out_001"
        # Links should be built from flat fields
        assert len(lin.links) >= 4  # state_a, bi_action, aai_trans, committed
        link_types = [l.link_type for l in lin.links]
        assert LinkType.STATE_A in link_types
        assert LinkType.BI_ACTION in link_types
        assert LinkType.AAI_TRANSFORMATION in link_types
        assert LinkType.COMMITTED_STATE in link_types
        assert LinkType.OUTCOME in link_types

    def test_lineage_to_dict_preserves_flat_fields(self):
        d = {
            "lineage_id": "lin_test2",
            "operator_id": "op_test2",
            "synthetic": True,
            "state_a_observation_id": "obs_010",
            "outcome_id": "out_010",
        }
        lin = Lineage.from_dict(d)
        out = lin.to_dict()
        assert out["state_a_observation_id"] == "obs_010"
        assert out["outcome_id"] == "out_010"


class TestOperatorSystemDecomposition:
    """Test the two-way ANOVA-style decomposition."""

    def test_operator_dominates(self):
        """When operators have consistent levels across systems,
        operator effect should dominate."""
        # op_a is always high, op_b is always low, regardless of system
        data = {
            "op_a": {"sys1": {"leverage": 10.0}, "sys2": {"leverage": 10.1}},
            "op_b": {"sys1": {"leverage": 2.0}, "sys2": {"leverage": 2.1}},
            "op_c": {"sys1": {"leverage": 5.0}, "sys2": {"leverage": 5.1}},
        }
        result = compute_operator_system_decomposition(data, metric_ids=["leverage"])
        assert len(result.metrics) == 1
        m = result.metrics[0]
        assert m.dominant_effect == "operator"
        assert m.pct_operator > 0.9  # operator explains >90% of variance

    def test_system_dominates(self):
        """When systems have large consistent shifts, system effect should dominate."""
        # All operators are similar, but sys1 always gives 10x more
        data = {
            "op_a": {"sys1": {"leverage": 50.0}, "sys2": {"leverage": 5.0}},
            "op_b": {"sys1": {"leverage": 51.0}, "sys2": {"leverage": 5.1}},
            "op_c": {"sys1": {"leverage": 49.0}, "sys2": {"leverage": 4.9}},
        }
        result = compute_operator_system_decomposition(data, metric_ids=["leverage"])
        m = result.metrics[0]
        assert m.dominant_effect == "system"
        assert m.pct_system > 0.9

    def test_interaction_dominates(self):
        """When specific pairings outperform, interaction should be significant."""
        # op_a is great on sys1 but terrible on sys2, op_b is the reverse
        data = {
            "op_a": {"sys1": {"leverage": 20.0}, "sys2": {"leverage": 2.0}},
            "op_b": {"sys1": {"leverage": 2.0}, "sys2": {"leverage": 20.0}},
        }
        result = compute_operator_system_decomposition(data, metric_ids=["leverage"])
        m = result.metrics[0]
        # With perfect crossover, operator and system effects cancel,
        # leaving interaction as the dominant component
        assert m.pct_interaction > 0.4

    def test_insufficient_data(self):
        """With only 1 operator, decomposition should return no metrics."""
        data = {
            "op_a": {"sys1": {"leverage": 10.0}, "sys2": {"leverage": 11.0}},
        }
        result = compute_operator_system_decomposition(data, metric_ids=["leverage"])
        assert len(result.metrics) == 0

    def test_single_system(self):
        """With only 1 system, decomposition should return no metrics."""
        data = {
            "op_a": {"sys1": {"leverage": 10.0}},
            "op_b": {"sys1": {"leverage": 5.0}},
        }
        result = compute_operator_system_decomposition(data, metric_ids=["leverage"])
        assert len(result.metrics) == 0

    def test_to_dict(self):
        data = {
            "op_a": {"sys1": {"leverage": 10.0}, "sys2": {"leverage": 2.0}},
            "op_b": {"sys1": {"leverage": 2.0}, "sys2": {"leverage": 10.0}},
        }
        result = compute_operator_system_decomposition(data, metric_ids=["leverage"])
        d = result.to_dict()
        assert "metrics" in d
        assert "systems_compared" in d
        assert len(d["metrics"]) == 1
        assert "variance_partition" in d["metrics"][0]

    def test_variance_partitions_sum_to_one(self):
        """pct_operator + pct_system + pct_interaction should ≈ 1.0."""
        data = {
            "op_a": {"sys1": {"leverage": 10.0}, "sys2": {"leverage": 8.0}},
            "op_b": {"sys1": {"leverage": 5.0}, "sys2": {"leverage": 7.0}},
            "op_c": {"sys1": {"leverage": 6.0}, "sys2": {"leverage": 9.0}},
        }
        result = compute_operator_system_decomposition(data, metric_ids=["leverage"])
        m = result.metrics[0]
        total = m.pct_operator + m.pct_system + m.pct_interaction
        assert abs(total - 1.0) < 0.01  # should sum to ~1.0


class TestOutcomeCorrelation:
    """Test outcome correlation through lineage."""

    def test_positive_correlation(self):
        """When higher metric values correlate with higher quality scores."""
        lineage_outcomes = []
        for i in range(20):
            me = {"leverage": float(i)}
            out = {"external_quality_score": float(i) * 0.05, "cycle_time_minutes": None}
            lineage_outcomes.append((me, out))
        result = compute_outcome_correlation(lineage_outcomes, metric_ids=["leverage"])
        assert len(result.correlations) >= 1
        corr = [c for c in result.correlations if c.outcome_metric == "external_quality_score"][0]
        assert corr.correlation > 0.9
        assert corr.direction == "positive"
        assert corr.strength == "strong"

    def test_negative_correlation(self):
        """When higher metric values correlate with lower cycle times (better)."""
        lineage_outcomes = []
        for i in range(20):
            me = {"leverage": float(i)}
            out = {"external_quality_score": None, "cycle_time_minutes": float(20 - i) * 10}
            lineage_outcomes.append((me, out))
        result = compute_outcome_correlation(lineage_outcomes, metric_ids=["leverage"])
        corr = [c for c in result.correlations if c.outcome_metric == "cycle_time_minutes"][0]
        assert corr.correlation < -0.9
        assert corr.direction == "negative"

    def test_no_correlation(self):
        """Random data should show no meaningful correlation."""
        import random
        random.seed(42)
        lineage_outcomes = []
        for i in range(20):
            me = {"leverage": random.random() * 100}
            out = {"external_quality_score": random.random(), "cycle_time_minutes": None}
            lineage_outcomes.append((me, out))
        result = compute_outcome_correlation(lineage_outcomes, metric_ids=["leverage"])
        corr = [c for c in result.correlations if c.outcome_metric == "external_quality_score"][0]
        assert abs(corr.correlation) < 0.5  # shouldn't be strongly correlated

    def test_insufficient_data(self):
        """With fewer than 3 pairs, should return empty correlations."""
        lineage_outcomes = [
            ({"leverage": 1.0}, {"external_quality_score": 0.5, "cycle_time_minutes": 100}),
            ({"leverage": 2.0}, {"external_quality_score": 0.6, "cycle_time_minutes": 90}),
        ]
        result = compute_outcome_correlation(lineage_outcomes, metric_ids=["leverage"])
        assert len(result.correlations) == 0
        assert "Insufficient" in result.summary

    def test_evidence_grade_is_observational(self):
        """All results should be labeled OBSERVATIONAL, never CAUSATION."""
        lineage_outcomes = []
        for i in range(10):
            me = {"leverage": float(i)}
            out = {"external_quality_score": float(i) * 0.1, "cycle_time_minutes": None}
            lineage_outcomes.append((me, out))
        result = compute_outcome_correlation(lineage_outcomes, metric_ids=["leverage"])
        assert result.evidence_grade == "OBSERVATIONAL"
        assert result.claim_status == "ASSOCIATION"

    def test_to_dict(self):
        lineage_outcomes = []
        for i in range(10):
            me = {"leverage": float(i)}
            out = {"external_quality_score": float(i) * 0.1, "cycle_time_minutes": None}
            lineage_outcomes.append((me, out))
        result = compute_outcome_correlation(lineage_outcomes, metric_ids=["leverage"])
        d = result.to_dict()
        assert "correlations" in d
        assert "evidence_grade" in d
        assert d["evidence_grade"] == "OBSERVATIONAL"


class TestServiceIntegration:
    """Test service-level integration with demo data."""

    def test_service_operator_system_decomposition(self):
        from service import PilotService
        svc = PilotService()
        result = svc.operator_system_decomposition()
        assert "metrics" in result
        assert len(result["metrics"]) > 0
        assert "systems_compared" in result
        assert len(result["systems_compared"]) >= 2

    def test_service_lineage_chain(self):
        from service import PilotService
        svc = PilotService()
        chain = svc.lineage_chain("op_046")
        assert chain["operator_id"] == "op_046"
        assert len(chain["chains"]) > 0
        # Should have links including OUTCOME
        first_chain = chain["chains"][0]
        link_types = [l["link_type"] for l in first_chain["links"]]
        assert "OUTCOME" in link_types

    def test_service_lineage_summary(self):
        from service import PilotService
        svc = PilotService()
        summary = svc.lineage_summary()
        assert summary["total"] > 0
        assert "outcomes_linked" in summary
        assert summary["outcomes_linked"] > 0

    def test_service_outcome_correlation(self):
        from service import PilotService
        svc = PilotService()
        result = svc.outcome_correlation()
        assert result["evidence_grade"] == "OBSERVATIONAL"
        assert result["claim_status"] == "ASSOCIATION"
        assert len(result["correlations"]) > 0

    def test_service_outcomes_for_operator(self):
        from service import PilotService
        svc = PilotService()
        outcomes = svc.outcomes_for("op_046")
        assert len(outcomes) > 0
        assert isinstance(outcomes[0], Outcome)


class TestMCPTools:
    """Test MCP tool direct invocation."""

    def test_mcp_operator_system_decomposition(self):
        from mcp_server.server import call_tool_directly
        r = call_tool_directly("get_operator_system_decomposition", operator_id="")
        assert "decomposition" in r
        assert len(r["decomposition"]["metrics"]) > 0

    def test_mcp_lineage_chain(self):
        from mcp_server.server import call_tool_directly
        r = call_tool_directly("get_lineage_chain", operator_id="op_046")
        assert "lineage" in r
        assert len(r["lineage"]["chains"]) > 0

    def test_mcp_lineage_summary(self):
        from mcp_server.server import call_tool_directly
        r = call_tool_directly("get_lineage_summary")
        assert "lineage_summary" in r
        assert r["lineage_summary"]["total"] > 0

    def test_mcp_outcome_correlation(self):
        from mcp_server.server import call_tool_directly
        r = call_tool_directly("get_outcome_correlation")
        assert "outcome_correlation" in r
        assert r["outcome_correlation"]["evidence_grade"] == "OBSERVATIONAL"
