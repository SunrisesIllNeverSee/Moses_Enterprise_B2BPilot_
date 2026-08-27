"""Tests for the OperatorIdentity cross-system mapping module (Gap 5).

Verifies:
  - OperatorIdentity registry maps canonical operator to multiple
    system-specific IDs (e.g. "alice" → "alice@company.com" in ChatGPT,
    "alice_chen" in Claude, "achen" in Copilot)
  - resolve() returns the canonical operator given (system, system_id)
  - add_mapping() supports adding new identity mappings
  - Conflict detection: same (system, system_id) mapped to different
    canonical operators raises IdentityConflictError
  - Idempotent re-mapping to the same canonical operator is allowed
  - systems_for() returns all system-specific IDs for a canonical operator
  - to_dict / from_dict round-trips (rebuilds the reverse index)
  - Service-level resolve_operator_identity and add_operator_identity
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestOperatorIdentity(unittest.TestCase):
    """Tests for the OperatorIdentity registry."""

    def test_add_and_resolve_single_mapping(self):
        from domain import OperatorIdentity
        reg = OperatorIdentity()
        reg.add_mapping("alice", "chatgpt", "alice@company.com")
        self.assertEqual(reg.resolve("chatgpt", "alice@company.com"), "alice")

    def test_multiple_systems_for_one_operator(self):
        """operator 'alice' → 'alice@company.com' in ChatGPT, 'alice_chen' in Claude, 'achen' in Copilot."""
        from domain import OperatorIdentity
        reg = OperatorIdentity()
        reg.add_mapping("alice", "chatgpt", "alice@company.com")
        reg.add_mapping("alice", "claude", "alice_chen")
        reg.add_mapping("alice", "copilot", "achen")
        self.assertEqual(reg.resolve("chatgpt", "alice@company.com"), "alice")
        self.assertEqual(reg.resolve("claude", "alice_chen"), "alice")
        self.assertEqual(reg.resolve("copilot", "achen"), "alice")
        systems = reg.systems_for("alice")
        self.assertEqual(systems["chatgpt"], "alice@company.com")
        self.assertEqual(systems["claude"], "alice_chen")
        self.assertEqual(systems["copilot"], "achen")

    def test_resolve_unknown_returns_none(self):
        from domain import OperatorIdentity
        reg = OperatorIdentity()
        reg.add_mapping("alice", "chatgpt", "alice@company.com")
        self.assertIsNone(reg.resolve("claude", "nobody"))
        self.assertIsNone(reg.resolve("chatgpt", "nobody"))

    def test_conflict_raises(self):
        """Same (system, system_id) mapped to different canonical operators → error."""
        from domain import OperatorIdentity, IdentityConflictError
        reg = OperatorIdentity()
        reg.add_mapping("alice", "chatgpt", "shared_id")
        with self.assertRaises(IdentityConflictError) as cm:
            reg.add_mapping("bob", "chatgpt", "shared_id")
        self.assertEqual(cm.exception.system, "chatgpt")
        self.assertEqual(cm.exception.system_id, "shared_id")
        self.assertEqual(cm.exception.existing_canonical, "alice")
        self.assertEqual(cm.exception.new_canonical, "bob")

    def test_idempotent_remap_same_canonical(self):
        """Re-mapping to the same canonical operator is idempotent (no error)."""
        from domain import OperatorIdentity
        reg = OperatorIdentity()
        reg.add_mapping("alice", "chatgpt", "alice@company.com")
        # Should not raise
        reg.add_mapping("alice", "chatgpt", "alice@company.com")
        self.assertEqual(reg.resolve("chatgpt", "alice@company.com"), "alice")

    def test_has_conflict(self):
        from domain import OperatorIdentity
        reg = OperatorIdentity()
        reg.add_mapping("alice", "chatgpt", "shared_id")
        self.assertTrue(reg.has_conflict("bob", "chatgpt", "shared_id"))
        self.assertFalse(reg.has_conflict("alice", "chatgpt", "shared_id"))
        self.assertFalse(reg.has_conflict("carol", "chatgpt", "different_id"))

    def test_canonical_ids(self):
        from domain import OperatorIdentity
        reg = OperatorIdentity()
        reg.add_mapping("alice", "chatgpt", "alice@company.com")
        reg.add_mapping("bob", "claude", "bob_smith")
        self.assertEqual(set(reg.canonical_ids()), {"alice", "bob"})

    def test_systems_for_unknown_operator(self):
        from domain import OperatorIdentity
        reg = OperatorIdentity()
        self.assertEqual(reg.systems_for("nobody"), {})

    def test_to_dict_from_dict_round_trip(self):
        from domain import OperatorIdentity
        reg = OperatorIdentity()
        reg.add_mapping("alice", "chatgpt", "alice@company.com")
        reg.add_mapping("alice", "claude", "alice_chen")
        reg.add_mapping("bob", "copilot", "bob_c")
        d = reg.to_dict()
        restored = OperatorIdentity.from_dict(d)
        self.assertEqual(restored.resolve("chatgpt", "alice@company.com"), "alice")
        self.assertEqual(restored.resolve("claude", "alice_chen"), "alice")
        self.assertEqual(restored.resolve("copilot", "bob_c"), "bob")
        self.assertEqual(set(restored.canonical_ids()), {"alice", "bob"})

    def test_from_dict_rebuilds_reverse_index(self):
        """from_dict must rebuild the (system, system_id) → canonical reverse index."""
        from domain import OperatorIdentity
        d = {
            "canonical_to_systems": {
                "alice": {"chatgpt": "alice@company.com", "claude": "alice_chen"},
            },
        }
        reg = OperatorIdentity.from_dict(d)
        # Reverse index must work
        self.assertEqual(reg.resolve("chatgpt", "alice@company.com"), "alice")
        self.assertEqual(reg.resolve("claude", "alice_chen"), "alice")

    def test_exported_from_domain_package(self):
        import domain
        self.assertTrue(hasattr(domain, "OperatorIdentity"))
        self.assertTrue(hasattr(domain, "IdentityConflictError"))


class TestServiceOperatorIdentity(unittest.TestCase):
    """Tests for the PilotService identity methods."""

    def test_add_and_resolve_via_service(self):
        from service import PilotService
        svc = PilotService()
        result = svc.add_operator_identity("op_001", "chatgpt", "alice@company.com")
        self.assertEqual(result["status"], "added")
        resolved = svc.resolve_operator_identity("chatgpt", "alice@company.com")
        self.assertTrue(resolved["resolved"])
        self.assertEqual(resolved["canonical_operator_id"], "op_001")

    def test_resolve_unknown_via_service(self):
        from service import PilotService
        svc = PilotService()
        resolved = svc.resolve_operator_identity("unknown_system", "nobody")
        self.assertFalse(resolved["resolved"])
        self.assertIsNone(resolved["canonical_operator_id"])

    def test_conflict_via_service_raises(self):
        from service import PilotService
        from domain import IdentityConflictError
        svc = PilotService()
        svc.add_operator_identity("op_001", "chatgpt", "shared_id")
        with self.assertRaises(IdentityConflictError):
            svc.add_operator_identity("op_002", "chatgpt", "shared_id")

    def test_multiple_systems_via_service(self):
        from service import PilotService
        svc = PilotService()
        svc.add_operator_identity("op_001", "chatgpt", "alice@company.com")
        svc.add_operator_identity("op_001", "claude", "alice_chen")
        svc.add_operator_identity("op_001", "copilot", "achen")
        for system, system_id in [
            ("chatgpt", "alice@company.com"),
            ("claude", "alice_chen"),
            ("copilot", "achen"),
        ]:
            resolved = svc.resolve_operator_identity(system, system_id)
            self.assertEqual(resolved["canonical_operator_id"], "op_001")

    def test_identity_registry_property(self):
        from service import PilotService
        from domain import OperatorIdentity
        svc = PilotService()
        reg = svc.operator_identity_registry
        self.assertIsInstance(reg, OperatorIdentity)


if __name__ == "__main__":
    unittest.main()
