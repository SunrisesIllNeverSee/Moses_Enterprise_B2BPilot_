"""Tests for the tool registration gate (HRN-008 governance).

Verifies:
    - Tools must be registered before invocation (deny-by-default)
    - Duplicate registration is rejected
    - Revoked tools are denied
    - Audit log records registration and revocation
    - Serialization round-trips
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from governance import (
    ToolBlastRadius,
    ToolRegistry,
    UnregisteredToolError,
    GovernanceAuditLog,
)


class TestToolRegistry(unittest.TestCase):

    def test_unregistered_tool_denied(self):
        """Deny-by-default: unregistered tools raise on invocation."""
        reg = ToolRegistry()
        with self.assertRaises(UnregisteredToolError):
            reg.check_invocation("tteop_scanner")

    def test_register_then_invoke(self):
        """Registered tools can be invoked."""
        reg = ToolRegistry()
        reg.register(
            tool_id="tteop_scanner",
            description="Collects TTEOP telemetry envelopes",
            data_classes=["telemetry"],
            blast_radius=ToolBlastRadius.READ_ONLY,
            approved_by="pilot_admin",
        )
        tool = reg.check_invocation("tteop_scanner")
        self.assertEqual(tool.tool_id, "tteop_scanner")
        self.assertEqual(tool.blast_radius, ToolBlastRadius.READ_ONLY)

    def test_duplicate_registration_rejected(self):
        """Cannot register the same tool_id twice without revoking first."""
        reg = ToolRegistry()
        reg.register(
            tool_id="tteop_scanner",
            description="v1",
            data_classes=["telemetry"],
            blast_radius=ToolBlastRadius.READ_ONLY,
            approved_by="admin",
        )
        with self.assertRaises(ValueError):
            reg.register(
                tool_id="tteop_scanner",
                description="v2",
                data_classes=["telemetry"],
                blast_radius=ToolBlastRadius.READ_ONLY,
                approved_by="admin",
            )

    def test_revoke_then_invoke_denied(self):
        """Revoked tools are denied on invocation."""
        reg = ToolRegistry()
        reg.register(
            tool_id="tteop_scanner",
            description="scanner",
            data_classes=["telemetry"],
            blast_radius=ToolBlastRadius.READ_ONLY,
            approved_by="admin",
        )
        reg.revoke("tteop_scanner", revoked_by="admin")
        with self.assertRaises(UnregisteredToolError):
            reg.check_invocation("tteop_scanner")

    def test_revoke_nonexistent_raises(self):
        """Cannot revoke a tool that was never registered."""
        reg = ToolRegistry()
        with self.assertRaises(KeyError):
            reg.revoke("nonexistent", revoked_by="admin")

    def test_reregister_after_revoke(self):
        """Can re-register a tool after it has been revoked."""
        reg = ToolRegistry()
        reg.register(
            tool_id="tteop_scanner",
            description="v1",
            data_classes=["telemetry"],
            blast_radius=ToolBlastRadius.READ_ONLY,
            approved_by="admin",
        )
        reg.revoke("tteop_scanner", revoked_by="admin")
        reg.register(
            tool_id="tteop_scanner",
            description="v2",
            data_classes=["telemetry", "identity"],
            blast_radius=ToolBlastRadius.WRITE_LOCAL,
            approved_by="admin",
        )
        tool = reg.check_invocation("tteop_scanner")
        self.assertEqual(tool.description, "v2")
        self.assertEqual(tool.blast_radius, ToolBlastRadius.WRITE_LOCAL)

    def test_audit_log_records_registration(self):
        """Registration is logged to the audit log."""
        log = GovernanceAuditLog()
        reg = ToolRegistry(audit_log=log)
        reg.register(
            tool_id="tteop_scanner",
            description="scanner",
            data_classes=["telemetry"],
            blast_radius=ToolBlastRadius.READ_ONLY,
            approved_by="admin",
        )
        entries = log.entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].action, "tool_registered")
        self.assertEqual(entries[0].target, "tteop_scanner")

    def test_audit_log_records_revocation(self):
        """Revocation is logged to the audit log."""
        log = GovernanceAuditLog()
        reg = ToolRegistry(audit_log=log)
        reg.register(
            tool_id="tteop_scanner",
            description="scanner",
            data_classes=["telemetry"],
            blast_radius=ToolBlastRadius.READ_ONLY,
            approved_by="admin",
        )
        reg.revoke("tteop_scanner", revoked_by="admin")
        entries = log.entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[1].action, "tool_revoked")

    def test_serialization_roundtrip(self):
        """Registry can be serialized and deserialized."""
        reg = ToolRegistry()
        reg.register(
            tool_id="tteop_scanner",
            description="scanner",
            data_classes=["telemetry"],
            blast_radius=ToolBlastRadius.READ_ONLY,
            approved_by="admin",
        )
        reg.register(
            tool_id="intervention_applier",
            description="Applies interventions",
            data_classes=["outcomes"],
            blast_radius=ToolBlastRadius.WRITE_LOCAL,
            approved_by="admin",
        )
        d = reg.to_dict()
        reg2 = ToolRegistry.from_dict(d)
        self.assertTrue(reg2.is_registered("tteop_scanner"))
        self.assertTrue(reg2.is_registered("intervention_applier"))
        tool = reg2.check_invocation("intervention_applier")
        self.assertEqual(tool.blast_radius, ToolBlastRadius.WRITE_LOCAL)

    def test_list_tools_excludes_revoked_by_default(self):
        """list_tools() excludes revoked tools by default."""
        reg = ToolRegistry()
        reg.register(
            tool_id="tool_a",
            description="a",
            data_classes=[],
            blast_radius=ToolBlastRadius.READ_ONLY,
            approved_by="admin",
        )
        reg.register(
            tool_id="tool_b",
            description="b",
            data_classes=[],
            blast_radius=ToolBlastRadius.READ_ONLY,
            approved_by="admin",
        )
        reg.revoke("tool_b", revoked_by="admin")
        active = reg.list_tools()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].tool_id, "tool_a")
        all_tools = reg.list_tools(include_revoked=True)
        self.assertEqual(len(all_tools), 2)


if __name__ == "__main__":
    unittest.main()
