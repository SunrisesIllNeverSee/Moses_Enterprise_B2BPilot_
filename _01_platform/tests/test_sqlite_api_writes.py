"""Tests for SQLiteRepository, API ingest adapters, and new MCP write tools.

Covers:
- SQLiteRepository: schema init, seeding, CRUD, persistence across sessions
- API adapters: stub mode, deterministic data, observation normalization
- MCP write tools: record_workflow_observation, attach_outcome_dataset
- PilotService with SQLite backend
"""
import json
import os
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ── SQLiteRepository ──────────────────────────────────────────────────────

class TestSQLiteRepository:
    """Test the SQLite persistent repository."""

    def test_in_memory_seed(self):
        """In-memory DB seeds from demo_data and has data."""
        from repository import SQLiteRepository
        repo = SQLiteRepository(":memory:")
        assert len(repo.operators) > 0
        assert len(repo.observations) > 0
        assert repo.cohort.cohort_id == "acme_50"
        repo.close()

    def test_operator_lookup(self):
        from repository import SQLiteRepository
        repo = SQLiteRepository(":memory:")
        first_op = repo.operators[0]
        found = repo.get_operator(first_op.operator_id)
        assert found is not None
        assert found.operator_id == first_op.operator_id
        assert repo.get_operator("nonexistent") is None
        repo.close()

    def test_observations_for_operator(self):
        from repository import SQLiteRepository
        repo = SQLiteRepository(":memory:")
        first_op = repo.operators[0]
        obs = repo.observations_for(first_op.operator_id)
        assert len(obs) > 0
        assert all(o.operator_id == first_op.operator_id for o in obs)
        repo.close()

    def test_intervention_insert_and_update(self):
        from repository import SQLiteRepository
        from domain import Intervention, InterventionOutcome
        repo = SQLiteRepository(":memory:")
        iv = Intervention(
            intervention_id="test_iv_001",
            operator_id=repo.operator_ids[0],
            catalog_id="CTX-001",
            reason_pattern="test",
            target_metric="yield",
            start_date=date(2026, 8, 21),
            followup_days=14,
        )
        repo.insert_intervention(iv)
        ivs = [i for i in repo.interventions if i.intervention_id == "test_iv_001"]
        assert len(ivs) == 1
        assert ivs[0].synthetic_outcome == InterventionOutcome.PENDING

        repo.update_intervention_outcome("test_iv_001", "SUCCESS")
        ivs = [i for i in repo.interventions if i.intervention_id == "test_iv_001"]
        assert ivs[0].synthetic_outcome == InterventionOutcome.SUCCESS
        repo.close()

    def test_workflow_observation_insert(self):
        from repository import SQLiteRepository
        from domain import WorkflowObservation
        repo = SQLiteRepository(":memory:")
        wobs = WorkflowObservation(
            operator_id=repo.operator_ids[0],
            workflow_id="software_dev_v1",
            stage_id="discovery",
            date=date(2026, 8, 21),
            provisional_fit=0.8,
            evidence_count=3,
            status="provisional",
            synthetic=True,
        )
        row_id = repo.insert_workflow_observation(wobs)
        assert row_id > 0
        all_wobs = repo.workflow_observations
        # Should have the original seeded ones plus our new one
        assert len(all_wobs) > 0
        repo.close()

    def test_experiment_insert_and_query(self):
        from repository import SQLiteRepository
        repo = SQLiteRepository(":memory:")
        experiment = {
            "experiment_id": "exp_test_001",
            "operator_id": repo.operator_ids[0],
            "target_metric": "yield",
            "window_days": 30,
            "description": "Test experiment",
            "start_date": "2026-08-21",
            "label": "EXPERIMENT",
        }
        repo.insert_experiment(experiment)
        exps = repo.experiments
        assert any(e["experiment_id"] == "exp_test_001" for e in exps)
        repo.close()

    def test_outcome_dataset_attach(self):
        from repository import SQLiteRepository
        repo = SQLiteRepository(":memory:")
        dataset_id = repo.attach_outcome_dataset(
            source_path="/tmp/test_outcomes.csv",
            record_count=50,
            attached_by="test_admin",
            operator_id="op_001",
        )
        assert dataset_id > 0
        datasets = repo.outcome_datasets
        assert len(datasets) == 1
        assert datasets[0]["source_path"] == "/tmp/test_outcomes.csv"
        assert datasets[0]["record_count"] == 50
        repo.close()

    def test_persistence_across_connections(self):
        """Data survives when the connection is closed and reopened."""
        from repository import SQLiteRepository
        from domain import Intervention
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo1 = SQLiteRepository(db_path)
            iv = Intervention(
                intervention_id="persist_test_001",
                operator_id=repo1.operator_ids[0],
                catalog_id="CTX-001",
                reason_pattern="persistence test",
                target_metric="yield",
                start_date=date(2026, 8, 21),
                followup_days=14,
            )
            repo1.insert_intervention(iv)
            repo1.close()

            # Reopen — data should still be there
            repo2 = SQLiteRepository(db_path, seed=False)
            ivs = [i for i in repo2.interventions if i.intervention_id == "persist_test_001"]
            assert len(ivs) == 1
            repo2.close()
        finally:
            os.unlink(db_path)

    def test_observation_insert(self):
        from repository import SQLiteRepository
        from domain import Observation
        from domain.provenance import Provenance
        repo = SQLiteRepository(":memory:")
        obs = Observation(
            observation_id="test_obs_001",
            operator_id=repo.operator_ids[0],
            timestamp=datetime(2026, 8, 21, 12, 0, 0),
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=200,
            cache_write_tokens=50,
            synthetic=True,
            platform="test",
            provenance=Provenance(
                source_provider="test",
                collection_method="unit_test",
                collector_version="test_v1",
                ingestion_timestamp="2026-08-21T12:00:00",
                synthetic=True,
            ),
        )
        repo.insert_observation(obs)
        found = [o for o in repo.observations if o.observation_id == "test_obs_001"]
        assert len(found) == 1
        assert found[0].input_tokens == 1000
        repo.close()


# ── API Adapters ──────────────────────────────────────────────────────────

class TestApiAdapters:
    """Test the API-based ingest adapters in stub mode."""

    def test_groq_stub_mode(self):
        from ingest import GroqApiAdapter
        adapter = GroqApiAdapter(stub=True)
        assert adapter.is_stub is True
        result = adapter.fetch("op_001", days=7)
        assert result.ok
        assert result.count == 7
        assert all(o.platform == "groq" for o in result.observations)
        assert all(o.synthetic for o in result.observations)
        assert any("STUB" in w for w in result.warnings)

    def test_claude_stub_mode(self):
        from ingest import ClaudeApiAdapter
        adapter = ClaudeApiAdapter(stub=True)
        assert adapter.is_stub is True
        result = adapter.fetch("op_002", days=14)
        assert result.ok
        assert result.count == 14
        assert all(o.platform == "claude" for o in result.observations)

    def test_codex_stub_mode(self):
        from ingest import CodexApiAdapter
        adapter = CodexApiAdapter(stub=True)
        assert adapter.is_stub is True
        result = adapter.fetch("op_003", days=30)
        assert result.ok
        assert result.count == 30
        assert all(o.platform == "codex" for o in result.observations)

    def test_stub_deterministic(self):
        """Same operator + days produces same data every time."""
        from ingest import GroqApiAdapter
        adapter = GroqApiAdapter(stub=True)
        r1 = adapter.fetch("op_001", days=5)
        r2 = adapter.fetch("op_001", days=5)
        assert len(r1.observations) == len(r2.observations)
        for o1, o2 in zip(r1.observations, r2.observations):
            assert o1.input_tokens == o2.input_tokens
            assert o1.output_tokens == o2.output_tokens

    def test_different_operators_different_data(self):
        from ingest import GroqApiAdapter
        adapter = GroqApiAdapter(stub=True)
        r1 = adapter.fetch("op_001", days=5)
        r2 = adapter.fetch("op_002", days=5)
        # Different operators should (very likely) have different token counts
        assert r1.observations[0].input_tokens != r2.observations[0].input_tokens

    def test_no_key_defaults_to_stub(self):
        """Without an API key, adapter defaults to stub mode."""
        from ingest import GroqApiAdapter
        # Ensure env var is not set
        old = os.environ.pop("GROQ_API_KEY", None)
        try:
            adapter = GroqApiAdapter()
            assert adapter.is_stub is True
        finally:
            if old:
                os.environ["GROQ_API_KEY"] = old

    def test_key_enables_live_mode(self):
        """With an API key, adapter switches to live mode."""
        from ingest import GroqApiAdapter
        adapter = GroqApiAdapter(api_key="fake_key_12345")
        assert adapter.is_stub is False

    def test_ingest_path_returns_error(self):
        """API adapters should reject file-based ingest()."""
        from ingest import GroqApiAdapter
        adapter = GroqApiAdapter(stub=True)
        result = adapter.ingest("some/path.json")
        assert not result.ok
        assert "fetch(" in result.errors[0]

    def test_fetch_and_persist_to_sqlite(self):
        from ingest import GroqApiAdapter
        from repository import SQLiteRepository
        repo = SQLiteRepository(":memory:")
        adapter = GroqApiAdapter(stub=True)
        result = adapter.fetch_and_persist("op_999", repo, days=5)
        assert result.ok
        assert result.count == 5
        # Verify observations were persisted
        obs = [o for o in repo.observations if o.operator_id == "op_999"]
        assert len(obs) == 5
        repo.close()


# ── PilotService with SQLite ──────────────────────────────────────────────

class TestPilotServiceSQLite:
    """Test PilotService backed by SQLiteRepository."""

    def test_service_with_sqlite(self):
        from service import PilotService
        svc = PilotService(db_path=":memory:")
        assert len(svc.operators) > 0
        assert len(svc.observations) > 0
        status = svc.pilot_status()
        assert status["cohort_id"] == "acme_50"

    def test_service_score_with_sqlite(self):
        from service import PilotService
        svc = PilotService(db_path=":memory:")
        ms = svc.score_operator(svc.operator_ids[0])
        assert len(ms) > 0

    def test_service_ingest_api(self):
        from service import PilotService
        svc = PilotService(db_path=":memory:")
        result = svc.ingest_api("groq", "test_op", days=5, skip_governance=True)
        assert result.ok
        assert result.count == 5

    def test_service_ingest_api_persist(self):
        from service import PilotService
        svc = PilotService(db_path=":memory:")
        result = svc.ingest_api("groq", "persist_op", days=3, persist=True, skip_governance=True)
        assert result.ok
        # Verify persisted to SQLite
        obs = [o for o in svc.repo.observations if o.operator_id == "persist_op"]
        assert len(obs) == 3

    def test_service_record_workflow_observation(self):
        from service import PilotService
        svc = PilotService(db_path=":memory:")
        wobs = svc.record_workflow_observation(
            operator_id=svc.operator_ids[0],
            stage_id="discovery",
            provisional_fit=0.85,
            evidence_count=5,
        )
        assert wobs.operator_id == svc.operator_ids[0]
        assert wobs.stage_id == "discovery"
        assert wobs.provisional_fit == 0.85
        # Verify persisted
        all_wobs = svc.repo.workflow_observations
        assert any(w.operator_id == svc.operator_ids[0] and w.stage_id == "discovery" and w.provisional_fit == 0.85 for w in all_wobs)

    def test_service_attach_outcome_dataset(self):
        from service import PilotService
        svc = PilotService(db_path=":memory:")
        # Create a temp CSV file
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False, newline="") as f:
            f.write("operator_id,outcome_metric,outcome_value\n")
            f.write("op_001,revenue,1000\n")
            f.write("op_002,revenue,2000\n")
            csv_path = f.name

        try:
            result = svc.attach_outcome_dataset(
                source_path=csv_path,
                attached_by="test_admin",
            )
            assert result["record_count"] == 2
            assert result["claim_type"] == "ASSOCIATION"
            assert result["attached_by"] == "test_admin"
            # Verify persisted
            datasets = svc.outcome_datasets
            assert len(datasets) == 1
        finally:
            os.unlink(csv_path)

    def test_service_attach_outcome_missing_file(self):
        from service import PilotService
        svc = PilotService(db_path=":memory:")
        with pytest.raises(FileNotFoundError):
            svc.attach_outcome_dataset(source_path="/nonexistent/path.csv")


# ── MCP Write Tools ───────────────────────────────────────────────────────

class TestMcpWriteTools:
    """Test the new MCP write tools via direct invocation."""

    def test_record_workflow_observation_blocked_without_auth(self):
        from mcp_server.server import record_workflow_observation
        result = record_workflow_observation(
            operator_id="op_001",
            stage_id="discovery",
        )
        assert "error" in result
        assert "authorized_by" in result["error"]

    def test_record_workflow_observation_with_auth(self):
        from mcp_server.server import record_workflow_observation
        result = record_workflow_observation(
            operator_id="op_001",
            stage_id="discovery",
            authorized_by="admin@test.com",
            provisional_fit=0.9,
            evidence_count=4,
        )
        assert "observation" in result
        assert result["observation"]["operator_id"] == "op_001"
        assert result["observation"]["stage_id"] == "discovery"
        assert result["authorized_by"] == "admin@test.com"

    def test_attach_outcome_dataset_blocked_without_auth(self):
        from mcp_server.server import attach_outcome_dataset
        result = attach_outcome_dataset(source_path="/tmp/test.csv")
        assert "error" in result
        assert "authorized_by" in result["error"]

    def test_attach_outcome_dataset_with_auth(self):
        from mcp_server.server import attach_outcome_dataset
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False, newline="") as f:
            f.write("operator_id,score\n")
            f.write("op_001,85\n")
            csv_path = f.name
        try:
            result = attach_outcome_dataset(
                source_path=csv_path,
                authorized_by="admin@test.com",
            )
            assert result["record_count"] == 1
            assert result["claim_type"] == "ASSOCIATION"
        finally:
            os.unlink(csv_path)

    def test_attach_outcome_dataset_missing_file(self):
        from mcp_server.server import attach_outcome_dataset
        result = attach_outcome_dataset(
            source_path="/nonexistent/file.csv",
            authorized_by="admin@test.com",
        )
        assert "error" in result

    def test_tool_registry_includes_new_tools(self):
        from mcp_server.server import TOOL_REGISTRY
        assert "record_workflow_observation" in TOOL_REGISTRY
        assert "attach_outcome_dataset" in TOOL_REGISTRY

    def test_call_tool_directly_record_workflow(self):
        from mcp_server.server import call_tool_directly
        result = call_tool_directly(
            "record_workflow_observation",
            operator_id="op_001",
            stage_id="testing",
            authorized_by="admin@test.com",
        )
        assert "observation" in result


# ── Executive Brief ───────────────────────────────────────────────────────

class TestExecutiveBrief:
    """Verify the executive brief is already implemented and works."""

    def test_executive_brief_generates(self):
        from service import PilotService
        svc = PilotService()
        brief = svc.executive_brief()
        assert "Executive Solution Brief" in brief
        assert "FACT" in brief
        assert "Next Evaluations" in brief

    def test_executive_brief_with_sqlite(self):
        from service import PilotService
        svc = PilotService(db_path=":memory:")
        brief = svc.executive_brief()
        assert "Executive Solution Brief" in brief
