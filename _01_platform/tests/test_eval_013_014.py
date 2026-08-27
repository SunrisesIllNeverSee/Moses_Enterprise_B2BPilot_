"""Tests for EVAL-013 (Org AI Topology) and EVAL-014 (Operator Similarity Search).

These are the two eval families that were previously unimplemented.
"""
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from service import PilotService
from analysis.org_topology import (
    compute_org_topology, OrgTopology, TeamTopology,
    CapabilityConcentration, PlatformAdoption, SinglePointOfFailure,
    _gini, _median, _iqr, _share_of_total,
)
from analysis.similarity import (
    compute_operator_similarity, SimilarityResult, SimilarityMatch,
    _percentile_rank, _euclidean,
)
from domain.operator import Operator
from domain.measurement import Measurement, MetricStatus


# ─── Helpers ─────────────────────────────────────────────────────────

def _make_operator(oid: str, team: str = "Engineering", role: str = "Software Engineering",
                   level: str = "Mid", platform: str = "claude") -> Operator:
    return Operator(
        operator_id=oid, tenant_id="test", pseudonym=f"Test {oid}",
        cohort_id="test_cohort", team=team, role_family=role,
        level=level, primary_platform=platform, synthetic=True,
    )


def _make_measurement(oid: str, metric: str, value: float) -> Measurement:
    return Measurement(
        metric_id=metric, metric_version="1.0", operator_id=oid,
        value=value, unit="ratio", window_start="2026-07-01", window_end="2026-07-30",
        source="canonical_token_telemetry", status=MetricStatus.CANONICAL,
        eligibility="I>0", synthetic=True,
    )


METRICS = ["leverage", "yield", "token_snr", "log_leverage", "construction"]


# ─── EVAL-013: Org AI Topology ───────────────────────────────────────

class TestOrgTopologyBasics:
    def test_empty_cohort(self):
        topo = compute_org_topology([], [], METRICS)
        assert topo.total_operators == 0
        assert topo.total_teams == 0

    def test_single_operator(self):
        ops = [_make_operator("op_1")]
        ms = [_make_measurement("op_1", "leverage", 10.0)]
        topo = compute_org_topology(ops, ms, METRICS)
        assert topo.total_operators == 1
        assert topo.total_teams == 1
        assert len(topo.team_topologies) == 1

    def test_demo_cohort(self):
        svc = PilotService()
        topo = svc.org_topology()
        assert topo["total_operators"] == 50
        assert topo["total_teams"] == 6
        assert len(topo["team_topologies"]) == 6
        assert len(topo["capability_concentration"]) == 5
        assert len(topo["platform_adoption"]) == 3
        assert topo["summary"] != ""


class TestTeamTopology:
    def test_team_breakdown(self):
        ops = [
            _make_operator("op_1", team="Engineering"),
            _make_operator("op_2", team="Engineering"),
            _make_operator("op_3", team="Sales"),
        ]
        ms = [
            _make_measurement("op_1", "leverage", 10.0),
            _make_measurement("op_2", "leverage", 20.0),
            _make_measurement("op_3", "leverage", 15.0),
        ]
        topo = compute_org_topology(ops, ms, ["leverage"])
        teams = {t.team: t for t in topo.team_topologies}
        assert teams["Engineering"].operator_count == 2
        assert teams["Sales"].operator_count == 1
        assert teams["Engineering"].median_metrics["leverage"] == 15.0

    def test_platform_and_role_composition(self):
        ops = [
            _make_operator("op_1", team="Eng", role="Software Engineering", platform="claude"),
            _make_operator("op_2", team="Eng", role="Data Engineering", platform="codex"),
        ]
        topo = compute_org_topology(ops, [], METRICS)
        eng = next(t for t in topo.team_topologies if t.team == "Eng")
        assert "claude" in eng.platforms_used
        assert "codex" in eng.platforms_used
        assert eng.role_composition["Software Engineering"] == 1
        assert eng.role_composition["Data Engineering"] == 1


class TestCapabilityConcentration:
    def test_gini_uniform(self):
        """Perfectly uniform distribution → gini near 0."""
        assert _gini([10, 10, 10, 10, 10]) < 0.05

    def test_gini_concentrated(self):
        """One operator has everything → gini near 1."""
        assert _gini([0, 0, 0, 0, 100]) > 0.7

    def test_gini_empty(self):
        assert _gini([]) == 0.0

    def test_gini_negative_filtered(self):
        # Negative values should be filtered
        assert _gini([-1, -2, 10, 10]) < 0.1

    def test_concentration_in_demo(self):
        svc = PilotService()
        topo = svc.org_topology()
        for c in topo["capability_concentration"]:
            assert 0 <= c["gini"] <= 1
            assert c["interpretation"] != ""

    def test_share_of_total(self):
        vals = [1, 2, 3, 4, 10]
        # top 20% = [10], total = 20, share = 0.5
        assert abs(_share_of_total(vals, 0.2) - 0.5) < 0.01


class TestPlatformAdoption:
    def test_platform_shares(self):
        ops = [
            _make_operator("op_1", platform="claude"),
            _make_operator("op_2", platform="claude"),
            _make_operator("op_3", platform="codex"),
            _make_operator("op_4", platform="chatgpt"),
        ]
        topo = compute_org_topology(ops, [], METRICS)
        plats = {p.platform: p for p in topo.platform_adoption}
        assert plats["claude"].share == 0.5
        assert plats["codex"].share == 0.25
        assert plats["chatgpt"].share == 0.25
        assert sum(p.share for p in topo.platform_adoption) == 1.0


class TestSinglePointOfFailure:
    def test_detects_concentrated_capability(self):
        """One operator with much higher leverage than rest of team."""
        ops = [_make_operator(f"op_{i}", team="Eng") for i in range(5)]
        ms = [
            _make_measurement("op_0", "leverage", 100.0),
            _make_measurement("op_1", "leverage", 1.0),
            _make_measurement("op_2", "leverage", 1.0),
            _make_measurement("op_3", "leverage", 1.0),
            _make_measurement("op_4", "leverage", 1.0),
        ]
        topo = compute_org_topology(ops, ms, ["leverage"])
        spofs = [s for s in topo.single_points_of_failure if s.capability == "leverage"]
        assert len(spofs) > 0
        assert spofs[0].risk_level == "high"

    def test_no_spof_when_distributed(self):
        ops = [_make_operator(f"op_{i}", team="Eng") for i in range(5)]
        ms = [_make_measurement(f"op_{i}", "leverage", 10.0 + i) for i in range(5)]
        topo = compute_org_topology(ops, ms, ["leverage"])
        spofs = [s for s in topo.single_points_of_failure if s.capability == "leverage"]
        assert len(spofs) == 0


class TestComplementarity:
    def test_complementary_teams(self):
        """Team A high on leverage, low on yield. Team B opposite."""
        ops = []
        ms = []
        for i in range(5):
            ops.append(_make_operator(f"a_{i}", team="TeamA"))
            ms.append(_make_measurement(f"a_{i}", "leverage", 50.0))
            ms.append(_make_measurement(f"a_{i}", "yield", 1.0))
        for i in range(5):
            ops.append(_make_operator(f"b_{i}", team="TeamB"))
            ms.append(_make_measurement(f"b_{i}", "leverage", 1.0))
            ms.append(_make_measurement(f"b_{i}", "yield", 50.0))
        topo = compute_org_topology(ops, ms, ["leverage", "yield"])
        assert len(topo.cross_team_complementarity) > 0


# ─── EVAL-014: Operator Similarity Search ────────────────────────────

class TestOperatorSimilarity:
    def test_finds_self_excluded(self):
        """The query operator should not appear in its own neighbors."""
        svc = PilotService()
        sim = svc.operator_similarity("op_001")
        neighbor_ids = [n["operator_id"] for n in sim["nearest_neighbors"]]
        assert "op_001" not in neighbor_ids

    def test_returns_correct_count(self):
        svc = PilotService()
        sim = svc.operator_similarity("op_001", n_neighbors=5)
        assert len(sim["nearest_neighbors"]) <= 5

    def test_distances_sorted_ascending(self):
        """Nearest neighbors should be sorted by distance ascending."""
        svc = PilotService()
        sim = svc.operator_similarity("op_001")
        distances = [n["distance"] for n in sim["nearest_neighbors"]]
        assert distances == sorted(distances)

    def test_similarity_decreases_with_distance(self):
        """Higher distance = lower similarity."""
        svc = PilotService()
        sim = svc.operator_similarity("op_001")
        for n in sim["nearest_neighbors"]:
            assert n["similarity"] >= 0
            assert n["similarity"] <= 1

    def test_cluster_quality_assessed(self):
        svc = PilotService()
        sim = svc.operator_similarity("op_001")
        assert sim["cluster_quality"] in ("tight", "moderate", "dispersed", "insufficient", "unknown")
        assert sim["cluster_description"] != ""

    def test_note_present(self):
        """The 'not a personality match' note must be present."""
        svc = PilotService()
        sim = svc.operator_similarity("op_001")
        assert "personality" in sim["note"].lower()

    def test_normalization_method(self):
        svc = PilotService()
        sim = svc.operator_similarity("op_001")
        assert sim["normalization"] == "percentile_rank"
        assert sim["distance_metric"] == "euclidean"

    def test_unknown_operator(self):
        svc = PilotService()
        sim = svc.operator_similarity("nonexistent_op")
        assert sim["cluster_quality"] == "unknown"
        assert len(sim["nearest_neighbors"]) == 0


class TestSimilarityInternals:
    def test_percentile_rank(self):
        vals = [1, 2, 3, 4, 5]
        # 3 is the median → ~50th percentile
        assert 40 < _percentile_rank(3, vals) < 60
        # 5 is the max → ~90th+ percentile
        assert _percentile_rank(5, vals) > 80
        # 1 is the min → ~10th- percentile
        assert _percentile_rank(1, vals) < 20

    def test_percentile_rank_empty(self):
        assert _percentile_rank(5, []) == 0.0

    def test_euclidean(self):
        assert _euclidean([0, 0], [3, 4]) == 5.0
        assert _euclidean([1, 1], [1, 1]) == 0.0

    def test_euclidean_mismatched_length(self):
        try:
            _euclidean([1, 2], [1])
            assert False, "Should raise"
        except ValueError:
            pass


class TestSimilarityWithSyntheticData:
    def test_identical_operators_are_close(self):
        """Two operators with identical metrics should have distance 0."""
        ops = [_make_operator("op_1"), _make_operator("op_2")]
        ms = []
        for mid in METRICS:
            ms.append(_make_measurement("op_1", mid, 10.0))
            ms.append(_make_measurement("op_2", mid, 10.0))
        result = compute_operator_similarity("op_1", ops, ms, METRICS, n_neighbors=1)
        assert len(result.nearest_neighbors) == 1
        assert result.nearest_neighbors[0].operator_id == "op_2"
        assert result.nearest_neighbors[0].distance < 0.01

    def test_opposite_operators_are_far(self):
        """Operators at opposite ends of the distribution should be far apart."""
        ops = [_make_operator("op_1"), _make_operator("op_2")]
        ms = []
        for mid in METRICS:
            ms.append(_make_measurement("op_1", mid, 1.0))
            ms.append(_make_measurement("op_2", mid, 100.0))
        result = compute_operator_similarity("op_1", ops, ms, METRICS, n_neighbors=1)
        assert result.nearest_neighbors[0].distance > 50  # large in percentile space


# ─── Serialization ───────────────────────────────────────────────────

class TestSerialization:
    def test_topology_to_dict(self):
        ops = [_make_operator("op_1")]
        ms = [_make_measurement("op_1", "leverage", 10.0)]
        topo = compute_org_topology(ops, ms, ["leverage"])
        d = topo.to_dict()
        assert "total_operators" in d
        assert "team_topologies" in d
        assert "capability_concentration" in d
        assert "platform_adoption" in d
        assert "single_points_of_failure" in d
        assert "cross_team_complementarity" in d
        assert "summary" in d

    def test_similarity_to_dict(self):
        ops = [_make_operator("op_1"), _make_operator("op_2")]
        ms = [_make_measurement("op_1", "leverage", 10.0),
              _make_measurement("op_2", "leverage", 12.0)]
        result = compute_operator_similarity("op_1", ops, ms, ["leverage"], n_neighbors=1)
        d = result.to_dict()
        assert "query_operator_id" in d
        assert "nearest_neighbors" in d
        assert "normalization" in d
        assert "note" in d
