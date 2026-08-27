"""Integration tests for A+B+C: canonical class wiring, benchmark engine, connectors.

Verifies the full end-to-end integration:
  A) New canonical classes are loaded by DemoRepository and accessible via PilotService
  B) Benchmark engine is wired into PilotService and CLI
  C) Ingest adapters emit full canonical objects in --full mode
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestCanonicalClassWiring(unittest.TestCase):
    """A: New canonical classes are wired into DemoRepository and PilotService."""

    def setUp(self):
        from service import PilotService
        self.svc = PilotService()

    def test_artifacts_loaded(self):
        """DemoRepository loads 200 artifacts."""
        self.assertEqual(len(self.svc.artifacts), 200)

    def test_lineages_loaded(self):
        """DemoRepository loads 50 lineages."""
        self.assertEqual(len(self.svc.lineages), 50)

    def test_outcomes_loaded(self):
        """DemoRepository loads 50 outcomes."""
        self.assertEqual(len(self.svc.outcomes), 50)

    def test_teams_loaded(self):
        """DemoRepository loads 6 teams."""
        self.assertEqual(len(self.svc.teams), 6)

    def test_workflows_loaded(self):
        """DemoRepository loads 4 workflows."""
        self.assertEqual(len(self.svc.workflows), 4)

    def test_systems_loaded(self):
        """DemoRepository provides 5 systems."""
        self.assertEqual(len(self.svc.systems), 5)

    def test_observations_full_loaded(self):
        """DemoRepository loads 1668 observations from observations.jsonl."""
        self.assertEqual(len(self.svc.observations_full), 1668)

    def test_artifacts_for_operator(self):
        """artifacts_for returns artifacts linked to a specific operator."""
        arts = self.svc.artifacts_for("op_031")
        self.assertIsInstance(arts, list)
        # op_031 should have at least 1 artifact
        self.assertGreater(len(arts), 0)
        for a in arts:
            self.assertEqual(a.operator_id, "op_031")

    def test_lineages_for_operator(self):
        """lineages_for returns lineages linked to a specific operator."""
        lins = self.svc.lineages_for("op_031")
        self.assertIsInstance(lins, list)
        for l in lins:
            self.assertEqual(l.operator_id, "op_031")

    def test_lineage_summary(self):
        """lineage_summary returns a summary dict."""
        summary = self.svc.lineage_summary()
        self.assertIn("total", summary)
        self.assertEqual(summary["total"], 50)

    def test_canonical_inventory_export(self):
        """export_canonical_inventory returns counts for all object types."""
        from reporting import export_canonical_inventory
        inv = export_canonical_inventory(self.svc)
        self.assertIn("artifacts", inv)
        self.assertIn("lineages", inv)
        self.assertIn("operators", inv)
        self.assertIn("observations", inv)
        self.assertEqual(inv["artifacts"], 200)
        self.assertEqual(inv["lineages"], 50)


class TestBenchmarkIntegration(unittest.TestCase):
    """B: Benchmark engine is wired into PilotService."""

    def setUp(self):
        from service import PilotService
        self.svc = PilotService()

    def test_benchmark_operator_returns_result(self):
        """benchmark_operator returns a benchmark result for a single operator."""
        result = self.svc.benchmark_operator("op_031", "leverage")
        self.assertIn("selected_benchmark", result)
        self.assertIn("benchmark", result)
        self.assertIsNotNone(result["selected_benchmark"])

    def test_benchmark_operator_includes_uncertainty(self):
        """benchmark_operator result includes CI and sample size."""
        result = self.svc.benchmark_operator("op_031", "leverage")
        bench = result["benchmark"]
        self.assertIn("result", bench)
        res = bench["result"]
        self.assertIn("percentile_rank", res)
        self.assertIn("percentile_ci_95", res)
        self.assertIn("sample_size", bench)

    def test_benchmark_cohort_returns_all_operators(self):
        """benchmark_cohort returns one result per operator."""
        results = self.svc.benchmark_cohort("leverage")
        self.assertEqual(len(results), 50)

    def test_benchmark_summary_no_leaderboard(self):
        """benchmark_summary does not produce a ranked leaderboard."""
        summary = self.svc.benchmark_summary("leverage")
        self.assertIn("no_false_leaderboards", summary)
        self.assertTrue(summary["no_false_leaderboards"])
        # Should have class counts, not individual rankings
        self.assertIn("benchmark_classes_selected", summary)
        self.assertNotIn("ranked_operators", summary)

    def test_benchmark_summary_percentile_distribution(self):
        """benchmark_summary includes percentile rank distribution stats."""
        summary = self.svc.benchmark_summary("leverage")
        dist = summary["percentile_rank_distribution"]
        self.assertIn("min", dist)
        self.assertIn("median", dist)
        self.assertIn("max", dist)
        self.assertEqual(dist["count"], 50)

    def test_benchmark_cli_command(self):
        """`enterprise benchmark summary` CLI command works."""
        from cli.main import main
        rc = main(["--json", "benchmark", "summary"])
        self.assertEqual(rc, 0)

    def test_benchmark_cli_operator(self):
        """`enterprise benchmark operator <id>` CLI command works."""
        from cli.main import main
        rc = main(["--json", "benchmark", "operator", "op_031"])
        self.assertEqual(rc, 0)


class TestIngestFullMode(unittest.TestCase):
    """C: Ingest adapters emit full canonical objects in --full mode."""

    def test_claude_adapter_ingest_full(self):
        """ClaudeAdapter.ingest_full() emits System + SystemVersion + Sessions."""
        from ingest.claude import ClaudeAdapter
        adapter = ClaudeAdapter()

        # Create a minimal Claude export file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([
                {
                    "operator_id": "op_001",
                    "timestamp": "2026-07-15T10:00:00Z",
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "cache_read_tokens": 2000,
                    "cache_write_tokens": 100,
                    "platform": "claude",
                    "model": "claude-sonnet-4",
                    "session_id": "sess_001",
                },
                {
                    "operator_id": "op_001",
                    "timestamp": "2026-07-15T11:00:00Z",
                    "input_tokens": 800,
                    "output_tokens": 300,
                    "cache_read_tokens": 1500,
                    "cache_write_tokens": 50,
                    "platform": "claude",
                    "model": "claude-sonnet-4",
                    "session_id": "sess_001",
                },
                {
                    "operator_id": "op_002",
                    "timestamp": "2026-07-15T10:00:00Z",
                    "input_tokens": 1200,
                    "output_tokens": 600,
                    "cache_read_tokens": 3000,
                    "cache_write_tokens": 200,
                    "platform": "claude",
                    "model": "claude-opus-4",
                    "session_id": "sess_002",
                },
            ], f)
            f.flush()

            result = adapter.ingest_full(f.name)

        import os
        os.unlink(f.name)

        self.assertEqual(result.source, "claude")
        self.assertEqual(len(result.observations), 3)
        # Should emit at least 1 system
        self.assertGreater(len(result.systems), 0)
        self.assertEqual(result.systems[0].system_id, "claude")
        # Should emit system versions (one per model)
        self.assertGreater(len(result.system_versions), 0)
        # Should emit sessions
        self.assertGreater(len(result.sessions), 0)
        # canonical_object_count should be > 0
        self.assertGreater(result.canonical_object_count(), 0)

    def test_codex_adapter_ingest_full(self):
        """CodexAdapter.ingest_full() emits System + SystemVersion + Sessions."""
        from ingest.codex import CodexAdapter
        adapter = CodexAdapter()

        # Create a minimal Codex export file (CSV format)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("operator_id,timestamp,input_tokens,output_tokens,cache_read_tokens,cache_write_tokens,platform,model,session_id\n")
            f.write("op_001,2026-07-15T10:00:00Z,1000,500,2000,100,codex,gpt-4-codex,sess_001\n")
            f.write("op_002,2026-07-15T10:00:00Z,1200,600,3000,200,codex,gpt-4-codex,sess_002\n")
            f.flush()

            result = adapter.ingest_full(f.name)

        import os
        os.unlink(f.name)

        self.assertEqual(result.source, "codex")
        self.assertGreater(len(result.observations), 0)
        self.assertGreater(len(result.systems), 0)
        self.assertEqual(result.systems[0].system_id, "codex")

    def test_github_adapter_exists(self):
        """GitHubAdapter is importable and registered."""
        from ingest.github import GitHubAdapter
        adapter = GitHubAdapter()
        self.assertEqual(adapter.name, "github-copilot")

    def test_github_adapter_ingest(self):
        """GitHubAdapter.ingest() parses Copilot usage CSV."""
        from ingest.github import GitHubAdapter
        adapter = GitHubAdapter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("date,user_id,suggestions_shown,suggestions_accepted,lines_accepted,lines_rejected,language,repo\n")
            f.write("2026-07-15,op_001,50,30,120,20,python,myrepo\n")
            f.write("2026-07-15,op_002,40,25,80,15,typescript,myrepo\n")
            f.flush()

            result = adapter.ingest(f.name)

        import os
        os.unlink(f.name)

        self.assertEqual(result.source, "github-copilot")
        self.assertEqual(len(result.observations), 2)
        # Should estimate tokens from lines
        for obs in result.observations:
            self.assertGreater(obs.output_tokens, 0)

    def test_github_adapter_ingest_full(self):
        """GitHubAdapter.ingest_full() emits System + Sessions + Artifacts."""
        from ingest.github import GitHubAdapter
        adapter = GitHubAdapter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("date,user_id,suggestions_shown,suggestions_accepted,lines_accepted,lines_rejected,language,repo\n")
            f.write("2026-07-15,op_001,50,30,120,20,python,myrepo\n")
            f.write("2026-07-16,op_001,40,25,80,15,python,myrepo\n")
            f.flush()

            result = adapter.ingest_full(f.name)

        import os
        os.unlink(f.name)

        self.assertGreater(len(result.systems), 0)
        self.assertEqual(result.systems[0].system_id, "copilot")
        self.assertGreater(len(result.sessions), 0)
        self.assertGreater(result.canonical_object_count(), 0)

    def test_ingest_result_helpers(self):
        """IngestResult.canonical_object_count() and total_object_count() work."""
        from ingest.base import IngestResult
        from domain.observation import Observation
        from domain.system import System, SystemType

        obs = Observation(
            observation_id="obs_001",
            operator_id="op_001",
            timestamp=datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc),
            input_tokens=100, output_tokens=50,
            cache_read_tokens=200, cache_write_tokens=10,
            synthetic=True,
        )
        sys_obj = System(
            system_id="test", tenant_id="t1", name="Test",
            system_type=SystemType.AI_PLATFORM,
        )
        result = IngestResult(
            source="test",
            observations=[obs],
            systems=[sys_obj],
        )
        self.assertEqual(result.count, 1)
        self.assertEqual(result.canonical_object_count(), 1)
        self.assertEqual(result.total_object_count(), 2)

    def test_ingest_cli_full_flag(self):
        """`enterprise ingest claude --full` CLI command works."""
        from cli.main import main

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([
                {
                    "operator_id": "op_001",
                    "timestamp": "2026-07-15T10:00:00Z",
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "cache_read_tokens": 2000,
                    "cache_write_tokens": 100,
                    "platform": "claude",
                    "model": "claude-sonnet-4",
                    "session_id": "sess_001",
                },
            ], f)
            f.flush()

            rc = main(["--json", "ingest", "claude", "--full", "--file", f.name])

        import os
        os.unlink(f.name)

        self.assertEqual(rc, 0)


class TestEndToEndDemo(unittest.TestCase):
    """Full end-to-end: demo full command runs with all new wiring."""

    def test_demo_full_complete(self):
        """`enterprise demo full` still completes with all new wiring."""
        from cli.main import main
        rc = main(["--json", "demo", "full"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
