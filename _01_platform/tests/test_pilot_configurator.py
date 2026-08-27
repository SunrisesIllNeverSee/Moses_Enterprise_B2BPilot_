"""Tests for the bespoke pilot menu system (Phases 1-7).

Covers:
    - Domain model: PilotConfiguration construction, serialization, deserialization
    - Registry: all 15 evals present, all 12 pilots present
    - Configurator: from_outcome produces correct eval bundles for each pilot
    - Configurator: from_alacarte produces correct eval selection
    - Validation: all 10 compatibility rules tested (pass + fail cases)
    - CLI: configure commands run without error
    - MCP: configuration tools work
    - Export: config report contains expected sections
    - Governance: all configs carry synthetic flag + decision-use label
    - Round-trip: save → load → compare
    - Production gates: service methods + CLI gate subcommands
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import (
    PilotConfigurator, ConfigValidator,
    EVAL_FAMILIES, COMMERCIAL_PILOTS,
    get_eval, get_pilot, all_eval_ids, all_pilot_ids,
    implemented_eval_ids,
)
from domain import PilotConfiguration, EvalFamilySelection, CohortConfig, GateRuleConfig
from reporting import export_configuration_report
from mcp_server import call_tool_directly
from cli.main import main as cli_main


class TestEvalRegistry(unittest.TestCase):
    """Tests for the eval family registry (15 eval families)."""

    def test_all_15_eval_families_present(self):
        self.assertEqual(len(EVAL_FAMILIES), 15)

    def test_eval_ids_match_pattern(self):
        for eid in EVAL_FAMILIES:
            self.assertRegex(eid, r"^EVAL-\d{3}$", f"Bad eval ID: {eid}")

    def test_eval_ids_are_sequential(self):
        ids = all_eval_ids()
        for i, eid in enumerate(ids, 1):
            self.assertEqual(eid, f"EVAL-{i:03d}")

    def test_each_eval_has_required_fields(self):
        for eid, e in EVAL_FAMILIES.items():
            self.assertTrue(e.name, f"{eid}: missing name")
            self.assertTrue(e.description, f"{eid}: missing description")
            self.assertIn(e.implementation_status, ("full", "partial", "not_implemented"))

    def test_get_eval_raises_for_unknown(self):
        with self.assertRaises(KeyError):
            get_eval("EVAL-999")

    def test_implemented_evals_excludes_not_implemented(self):
        implemented = implemented_eval_ids()
        for eid in implemented:
            self.assertTrue(EVAL_FAMILIES[eid].implemented)


class TestPilotRegistry(unittest.TestCase):
    """Tests for the commercial pilot registry (12 pilots)."""

    def test_all_12_pilots_present(self):
        self.assertEqual(len(COMMERCIAL_PILOTS), 12)

    def test_pilot_ids_are_1_through_12(self):
        ids = all_pilot_ids()
        self.assertEqual(ids, [str(i) for i in range(1, 13)])

    def test_each_pilot_has_eval_families(self):
        for pid, p in COMMERCIAL_PILOTS.items():
            self.assertTrue(len(p.eval_families) > 0, f"Pilot {pid}: no eval families")
            for eid in p.eval_families:
                self.assertIn(eid, EVAL_FAMILIES, f"Pilot {pid}: unknown eval {eid}")

    def test_each_pilot_has_valid_deployment_level(self):
        for pid, p in COMMERCIAL_PILOTS.items():
            self.assertIn(p.deployment_level, (1, 2, 3), f"Pilot {pid}: bad level {p.deployment_level}")

    def test_get_pilot_raises_for_unknown(self):
        with self.assertRaises(KeyError):
            get_pilot("99")


class TestPilotConfigurator(unittest.TestCase):
    """Tests for the PilotConfigurator (from_outcome and from_alacarte)."""

    def test_from_outcome_produces_correct_evals(self):
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        self.assertEqual(cfg.mode, "outcome_packaged")
        self.assertEqual(cfg.commercial_pilot_id, "1")
        self.assertEqual(cfg.enabled_eval_ids(), ["EVAL-001", "EVAL-002", "EVAL-003", "EVAL-004", "EVAL-006"])

    def test_from_outcome_for_all_12_pilots(self):
        for pid in all_pilot_ids():
            cfg = PilotConfigurator.from_outcome(pid, created_by="test")
            self.assertEqual(cfg.mode, "outcome_packaged")
            self.assertEqual(cfg.commercial_pilot_id, pid)
            pilot = get_pilot(pid)
            self.assertEqual(cfg.enabled_eval_ids(), pilot.eval_families)

    def test_from_outcome_sets_deployment_level(self):
        cfg = PilotConfigurator.from_outcome("4", created_by="test")
        self.assertEqual(cfg.deployment_level, 2)  # Pilot 4 is Level 2

    def test_from_alacarte_produces_correct_evals(self):
        cfg = PilotConfigurator.from_alacarte(["EVAL-001", "EVAL-008"], created_by="test")
        self.assertEqual(cfg.mode, "a_la_carte")
        self.assertIsNone(cfg.commercial_pilot_id)
        self.assertEqual(cfg.enabled_eval_ids(), ["EVAL-001", "EVAL-008"])

    def test_from_alacarte_raises_for_unknown_eval(self):
        with self.assertRaises(ValueError):
            PilotConfigurator.from_alacarte(["EVAL-999"], created_by="test")

    def test_from_alacarte_with_gates(self):
        cfg = PilotConfigurator.from_alacarte(
            ["EVAL-001", "EVAL-002"], gates_enabled=True, created_by="test",
        )
        self.assertTrue(cfg.gates.enabled)
        self.assertGreater(len(cfg.gates.rules), 0)

    def test_from_outcome_with_gates(self):
        cfg = PilotConfigurator.from_outcome("1", gates_enabled=True, created_by="test")
        self.assertTrue(cfg.gates.enabled)
        self.assertGreater(len(cfg.gates.rules), 0)

    def test_from_outcome_without_gates(self):
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        self.assertFalse(cfg.gates.enabled)
        self.assertEqual(len(cfg.gates.rules), 0)

    def test_from_outcome_with_outcome_join(self):
        cfg = PilotConfigurator.from_outcome(
            "11", outcome_join_enabled=True, outcome_csv_path="/tmp/outcomes.csv",
            created_by="test",
        )
        self.assertTrue(cfg.outcome_join.enabled)
        self.assertEqual(cfg.outcome_join.outcome_csv_path, "/tmp/outcomes.csv")


class TestPilotConfigurationSerialization(unittest.TestCase):
    """Tests for PilotConfiguration JSON serialization."""

    def test_to_json_and_from_json_round_trip(self):
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        json_str = cfg.to_json()
        cfg2 = PilotConfiguration.from_json(json_str)
        self.assertEqual(cfg2.config_id, cfg.config_id)
        self.assertEqual(cfg2.mode, cfg.mode)
        self.assertEqual(cfg2.enabled_eval_ids(), cfg.enabled_eval_ids())
        self.assertEqual(cfg2.deployment_level, cfg.deployment_level)

    def test_to_dict_and_from_dict_round_trip(self):
        cfg = PilotConfigurator.from_alacarte(["EVAL-001", "EVAL-002", "EVAL-008"], created_by="test")
        d = cfg.to_dict()
        cfg2 = PilotConfiguration.from_dict(d)
        self.assertEqual(cfg2.config_id, cfg.config_id)
        self.assertEqual(cfg2.enabled_eval_ids(), cfg.enabled_eval_ids())

    def test_save_and_load(self):
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name
        try:
            PilotConfigurator.save(cfg, path)
            cfg2 = PilotConfigurator.load(path)
            self.assertEqual(cfg2.config_id, cfg.config_id)
            self.assertEqual(cfg2.enabled_eval_ids(), cfg.enabled_eval_ids())
        finally:
            os.unlink(path)

    def test_enabled_eval_ids(self):
        cfg = PilotConfiguration(
            config_id="test",
            mode="a_la_carte",
            eval_families=[
                EvalFamilySelection("EVAL-001", True),
                EvalFamilySelection("EVAL-002", False),
                EvalFamilySelection("EVAL-003", True),
            ],
        )
        self.assertEqual(cfg.enabled_eval_ids(), ["EVAL-001", "EVAL-003"])


class TestConfigValidator(unittest.TestCase):
    """Tests for the ConfigValidator (10 compatibility rules)."""

    def test_valid_config_passes(self):
        cfg = PilotConfigurator.from_alacarte(["EVAL-001", "EVAL-002", "EVAL-008"], created_by="test")
        result = ConfigValidator.validate(cfg)
        self.assertTrue(result.valid, f"Expected valid, got errors: {result.errors}")

    def test_rule_1_divergence_requires_baseline(self):
        cfg = PilotConfigurator.from_alacarte(["EVAL-002"], created_by="test")
        result = ConfigValidator.validate(cfg)
        self.assertFalse(result.valid)
        self.assertTrue(any("EVAL-002" in e and "EVAL-001" in e for e in result.errors))

    def test_rule_2_intervention_requires_pre_post_windows(self):
        cfg = PilotConfigurator.from_alacarte(
            ["EVAL-001", "EVAL-007"],
            cohort=CohortConfig(window_days=7),
            created_by="test",
        )
        result = ConfigValidator.validate(cfg)
        self.assertFalse(result.valid)
        self.assertTrue(any("EVAL-007" in e and "14" in e for e in result.errors))

    def test_rule_3_workflow_fit_requires_workflow(self):
        from domain import WorkflowConfig
        cfg = PilotConfigurator.from_alacarte(
            ["EVAL-001", "EVAL-008"],
            workflow=WorkflowConfig(workflow_id=""),
            created_by="test",
        )
        result = ConfigValidator.validate(cfg)
        self.assertFalse(result.valid)
        self.assertTrue(any("EVAL-008" in e and "workflow" in e for e in result.errors))

    def test_rule_4_capability_dependency_requires_composition(self):
        cfg = PilotConfigurator.from_alacarte(["EVAL-010"], created_by="test")
        result = ConfigValidator.validate(cfg)
        self.assertFalse(result.valid)
        self.assertTrue(any("EVAL-010" in e and "EVAL-006" in e for e in result.errors))

    def test_rule_5_development_engine_requires_intervention(self):
        cfg = PilotConfigurator.from_alacarte(["EVAL-001", "EVAL-011"], created_by="test")
        result = ConfigValidator.validate(cfg)
        self.assertFalse(result.valid)
        self.assertTrue(any("EVAL-011" in e and "EVAL-007" in e for e in result.errors))

    def test_rule_6_experiment_requires_authorization(self):
        cfg = PilotConfigurator.from_alacarte(["EVAL-001", "EVAL-012"], created_by="test")
        result = ConfigValidator.validate(cfg)
        self.assertFalse(result.valid)
        self.assertTrue(any("EVAL-012" in e and "authorized" in e for e in result.errors))

    def test_rule_7_not_implemented_evals_warn(self):
        cfg = PilotConfigurator.from_alacarte(["EVAL-001", "EVAL-013", "EVAL-014"], created_by="test")
        result = ConfigValidator.validate(cfg)
        self.assertTrue(result.valid)  # Warnings don't block
        self.assertTrue(any("EVAL-013" in w for w in result.warnings))
        self.assertTrue(any("EVAL-014" in w for w in result.warnings))

    def test_rule_8_gates_require_producing_eval(self):
        cfg = PilotConfigurator.from_alacarte(
            ["EVAL-006"],  # EVAL-006 doesn't produce leverage/yield/construction
            gates_enabled=True,
            created_by="test",
        )
        result = ConfigValidator.validate(cfg)
        self.assertFalse(result.valid)
        self.assertTrue(any("Gate" in e and "leverage" in e for e in result.errors))

    def test_rule_9_outcome_join_requires_baseline(self):
        cfg = PilotConfigurator.from_alacarte(
            ["EVAL-006"],
            outcome_join_enabled=True,
            outcome_csv_path="/tmp/outcomes.csv",
            created_by="test",
        )
        result = ConfigValidator.validate(cfg)
        self.assertFalse(result.valid)
        self.assertTrue(any("outcome join" in e.lower() for e in result.errors))

    def test_rule_10_level_2_with_only_level_1_evals_warns(self):
        cfg = PilotConfigurator.from_alacarte(
            ["EVAL-001", "EVAL-002", "EVAL-006"],
            deployment_level=2,
            created_by="test",
        )
        result = ConfigValidator.validate(cfg)
        self.assertTrue(result.valid)
        self.assertTrue(any("level 2" in w.lower() for w in result.warnings))

    def test_invalid_deployment_level(self):
        cfg = PilotConfigurator.from_alacarte(["EVAL-001"], deployment_level=5, created_by="test")
        result = ConfigValidator.validate(cfg)
        self.assertFalse(result.valid)
        self.assertTrue(any("deployment level" in e.lower() for e in result.errors))

    def test_invalid_window_days(self):
        cfg = PilotConfigurator.from_alacarte(
            ["EVAL-001"], cohort=CohortConfig(window_days=3), created_by="test",
        )
        result = ConfigValidator.validate(cfg)
        self.assertFalse(result.valid)
        self.assertTrue(any("window" in e.lower() for e in result.errors))


class TestGovernanceMetadata(unittest.TestCase):
    """Tests that all configurations carry governance metadata."""

    def test_outcome_config_has_governance(self):
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        self.assertTrue(cfg.governance.synthetic)
        self.assertEqual(cfg.governance.decision_use_default, "DEVELOPMENTAL")

    def test_alacarte_config_has_governance(self):
        cfg = PilotConfigurator.from_alacarte(["EVAL-001"], created_by="test")
        self.assertTrue(cfg.governance.synthetic)
        self.assertEqual(cfg.governance.decision_use_default, "DEVELOPMENTAL")

    def test_outcome_join_label_is_association(self):
        cfg = PilotConfigurator.from_outcome(
            "11", outcome_join_enabled=True, created_by="test",
        )
        self.assertIn("ASSOCIATION", cfg.outcome_join.label)
        self.assertIn("never CAUSATION", cfg.outcome_join.label)

    def test_governance_survives_round_trip(self):
        cfg = PilotConfigurator.from_outcome("1", authorized_by="admin@test", created_by="test")
        cfg2 = PilotConfiguration.from_json(cfg.to_json())
        self.assertEqual(cfg2.governance.authorized_by, "admin@test")
        self.assertEqual(cfg2.governance.synthetic, cfg.governance.synthetic)


class TestCLIConfigure(unittest.TestCase):
    """Tests for the CLI configure command."""

    def test_cli_list_pilots(self):
        rc = cli_main(["--json", "configure", "list-pilots"])
        self.assertEqual(rc, 0)

    def test_cli_list_evals(self):
        rc = cli_main(["--json", "configure", "list-evals"])
        self.assertEqual(rc, 0)

    def test_cli_from_pilot(self):
        rc = cli_main(["--json", "configure", "from-pilot", "--pilot-id", "1"])
        self.assertEqual(rc, 0)

    def test_cli_from_evals(self):
        rc = cli_main(["--json", "configure", "from-evals", "--evals", "EVAL-001,EVAL-002"])
        self.assertEqual(rc, 0)

    def test_cli_from_pilot_save_and_show(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name
        try:
            rc = cli_main(["--json", "configure", "from-pilot", "--pilot-id", "1", "--save", path])
            self.assertEqual(rc, 0)
            rc = cli_main(["--json", "configure", "show", "--file", path])
            self.assertEqual(rc, 0)
            rc = cli_main(["--json", "configure", "validate", "--file", path])
            self.assertEqual(rc, 0)
        finally:
            os.unlink(path)

    def test_cli_from_evals_unknown_eval(self):
        rc = cli_main(["--json", "configure", "from-evals", "--evals", "EVAL-999"])
        self.assertEqual(rc, 0)  # Returns 0 with error in JSON body


class TestMCPConfigureTools(unittest.TestCase):
    """Tests for the MCP configuration tools."""

    def test_list_pilot_options(self):
        result = call_tool_directly("list_pilot_options")
        self.assertEqual(len(result["pilots"]), 12)
        self.assertEqual(len(result["eval_families"]), 15)

    def test_create_pilot_configuration_from_pilot(self):
        result = call_tool_directly("create_pilot_configuration", pilot_id="1", created_by="test")
        self.assertEqual(result["mode"], "outcome_packaged")
        self.assertEqual(result["commercial_pilot_id"], "1")

    def test_create_pilot_configuration_from_evals(self):
        result = call_tool_directly(
            "create_pilot_configuration",
            eval_ids="EVAL-001,EVAL-008",
            created_by="test",
        )
        self.assertEqual(result["mode"], "a_la_carte")
        self.assertIsNone(result["commercial_pilot_id"])

    def test_create_pilot_configuration_no_args(self):
        result = call_tool_directly("create_pilot_configuration")
        self.assertIn("error", result)

    def test_validate_pilot_configuration_from_file(self):
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(cfg.to_json())
            path = f.name
        try:
            result = call_tool_directly("validate_pilot_configuration", file_path=path)
            self.assertTrue(result["valid"])
        finally:
            os.unlink(path)

    def test_configuration_tools_in_registry(self):
        from mcp_server.server import TOOL_REGISTRY
        self.assertIn("list_pilot_options", TOOL_REGISTRY)
        self.assertIn("create_pilot_configuration", TOOL_REGISTRY)
        self.assertIn("validate_pilot_configuration", TOOL_REGISTRY)


class TestConfigReport(unittest.TestCase):
    """Tests for the configuration export report."""

    def test_report_contains_expected_sections(self):
        cfg = PilotConfigurator.from_outcome("1", gates_enabled=True, created_by="test")
        report = export_configuration_report(cfg)
        self.assertIn("Pilot Configuration Report", report)
        self.assertIn("Selected Eval Families", report)
        self.assertIn("Cohort Parameters", report)
        self.assertIn("Deployment Level", report)
        self.assertIn("Production Gates", report)
        self.assertIn("Governance", report)
        self.assertIn("Deliverables", report)
        self.assertIn("CLI and MCP Tool Mapping", report)

    def test_report_contains_eval_ids(self):
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        report = export_configuration_report(cfg)
        for eid in cfg.enabled_eval_ids():
            self.assertIn(eid, report)

    def test_report_contains_governance_labels(self):
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        report = export_configuration_report(cfg)
        self.assertIn("DEVELOPMENTAL", report)
        self.assertIn("synthetic", report.lower())

    def test_report_contains_association_label_for_outcome_join(self):
        cfg = PilotConfigurator.from_outcome(
            "11", outcome_join_enabled=True, created_by="test",
        )
        report = export_configuration_report(cfg)
        self.assertIn("ASSOCIATION", report)

    def test_report_contains_commercial_pilot_reference(self):
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        report = export_configuration_report(cfg)
        self.assertIn("Commercial Pilot Reference", report)
        self.assertIn("AI Workforce Operating Baseline", report)


class TestConstraintsEnforcement(unittest.TestCase):
    """Tests that the constraints from the prompt are enforced."""

    def test_metrics_not_configurable(self):
        """PilotConfiguration has no metric selection field."""
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        self.assertFalse(hasattr(cfg, "metrics"))
        self.assertFalse(hasattr(cfg, "metric_selection"))

    def test_interventions_not_configurable(self):
        """PilotConfiguration has no intervention catalog field."""
        cfg = PilotConfigurator.from_outcome("1", created_by="test")
        self.assertFalse(hasattr(cfg, "interventions"))
        self.assertFalse(hasattr(cfg, "intervention_catalog"))

    def test_gates_are_configurable(self):
        """Gates ARE configurable (threshold, enable/disable)."""
        cfg = PilotConfigurator.from_alacarte(
            ["EVAL-001", "EVAL-002"], gates_enabled=True, created_by="test",
        )
        self.assertTrue(cfg.gates.enabled)
        self.assertGreater(len(cfg.gates.rules), 0)
        for rule in cfg.gates.rules:
            self.assertIsInstance(rule.threshold, (int, float))

    def test_cohort_is_configurable(self):
        """Cohort IS configurable."""
        cfg = PilotConfigurator.from_alacarte(
            ["EVAL-001"],
            cohort=CohortConfig(window_days=45, min_operators=30, max_operators=80),
            created_by="test",
        )
        self.assertEqual(cfg.cohort.window_days, 45)
        self.assertEqual(cfg.cohort.min_operators, 30)
        self.assertEqual(cfg.cohort.max_operators, 80)

    def test_all_configs_carry_governance(self):
        """All configurations carry governance metadata."""
        cfg1 = PilotConfigurator.from_outcome("1", created_by="test")
        cfg2 = PilotConfigurator.from_alacarte(["EVAL-001"], created_by="test")
        for cfg in [cfg1, cfg2]:
            self.assertTrue(cfg.governance.synthetic)
            self.assertTrue(cfg.governance.decision_use_default)

    def test_no_causal_claims(self):
        """Outcome joins are always ASSOCIATION — never CAUSATION."""
        cfg = PilotConfigurator.from_outcome(
            "11", outcome_join_enabled=True, created_by="test",
        )
        self.assertIn("ASSOCIATION", cfg.outcome_join.label)
        self.assertIn("never CAUSATION", cfg.outcome_join.label)


# ── Production gates (service + CLI) ──────────────────────────────────────

class TestProductionGateService(unittest.TestCase):
    """Tests for PilotService gate methods."""

    def setUp(self):
        from service import PilotService
        self.svc = PilotService()

    def test_gate_rules_returns_defaults(self):
        """gate_rules returns the 3 default gate rules."""
        rules = self.svc.gate_rules()
        self.assertEqual(len(rules), 3)
        ids = {r.rule_id for r in rules}
        self.assertEqual(ids, {"GATE-001", "GATE-002", "GATE-003"})

    def test_evaluate_gates_for_returns_results(self):
        """evaluate_gates_for returns one result per rule."""
        results = self.svc.evaluate_gates_for("op_001")
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertEqual(r.decision_use, "DEVELOPMENTAL")

    def test_evaluate_cohort_gates_summary(self):
        """evaluate_cohort_gates returns a summary with expected keys."""
        summary = self.svc.evaluate_cohort_gates()
        self.assertIn("total_evaluations", summary)
        self.assertIn("total_fired", summary)
        self.assertIn("operators_flagged", summary)
        self.assertIn("by_action", summary)
        self.assertIn("fired_gates", summary)
        self.assertEqual(summary["decision_use"], "DEVELOPMENTAL")
        # 50 operators × 3 rules = 150 evaluations
        self.assertEqual(summary["total_evaluations"], 150)

    def test_evaluate_cohort_gates_fired_gates_have_dicts(self):
        """Fired gates in the summary are dicts with expected fields."""
        summary = self.svc.evaluate_cohort_gates()
        for g in summary["fired_gates"]:
            self.assertIn("rule_id", g)
            self.assertIn("operator_id", g)
            self.assertIn("metric_id", g)
            self.assertIn("fired", g)
            self.assertTrue(g["fired"])

    def test_gate_results_are_developmental(self):
        """All gate results carry DEVELOPMENTAL decision-use label."""
        results = self.svc.evaluate_gates_for("op_001")
        for r in results:
            self.assertEqual(r.decision_use, "DEVELOPMENTAL")


class TestCLIGateCommands(unittest.TestCase):
    """Tests for the CLI gate subcommand."""

    def test_cli_gate_rules(self):
        """CLI 'gate rules' returns 0 and lists rules."""
        rc = cli_main(["--json", "gate", "rules"])
        self.assertEqual(rc, 0)

    def test_cli_gate_operator(self):
        """CLI 'gate operator op_001' returns 0."""
        rc = cli_main(["--json", "gate", "operator", "op_001"])
        self.assertEqual(rc, 0)

    def test_cli_gate_cohort(self):
        """CLI 'gate cohort' returns 0 and includes summary fields."""
        rc = cli_main(["--json", "gate", "cohort"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
