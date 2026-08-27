"""Conformance tests for the ScoringEngine (P0-B).

These tests verify that the engine produces exact, deterministic metric values
from known observation fixtures. The same fixtures must produce the same values
in every interface (P0 acceptance: "same fixture produces same metric values
in every interface").

Also tests:
    - I=0 domain restrictions handled explicitly
    - unknown metric version fails loudly
    - synthetic marker survives scoring
    - measurement object contract fields are all present
"""
import math
import unittest
from datetime import date, datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from domain.observation import Observation
from domain.measurement import Measurement, MetricStatus
from metrics.engine import ScoringEngine
from metrics.registry import load_registry


class TestScoringEngineConformance(unittest.TestCase):
    """Deterministic fixtures with known input → expected output."""

    def setUp(self):
        self.engine = ScoringEngine()
        self.window_start = date(2026, 7, 1)
        self.window_end = date(2026, 7, 30)

    def _make_obs(self, operator_id, n_days, I, O, R, W):
        """Create n_days of identical daily observations."""
        return [
            Observation(
                observation_id=f"{operator_id}_day_{i}",
                operator_id=operator_id,
                timestamp=datetime(2026, 7, 1 + i, 10, 0, 0),
                input_tokens=I, output_tokens=O,
                cache_read_tokens=R, cache_write_tokens=W,
                synthetic=True,
            )
            for i in range(n_days)
        ]

    def test_leverage_known_value(self):
        """Leverage = R/I. For I=10000, R=150000 → L=15.0."""
        obs = self._make_obs("op_test", 30, 10000, 5000, 150000, 30000)
        ms = self.engine.score_operator("op_test", obs, self.window_start, self.window_end)
        lev = next(m for m in ms if m.metric_id == "leverage")
        self.assertAlmostEqual(lev.value, 15.0, places=6)
        self.assertEqual(lev.status, MetricStatus.CANONICAL)
        self.assertEqual(lev.eligibility, "I>0")

    def test_yield_known_value(self):
        """Yield = (R*O)/I^2. For I=10000, O=5000, R=150000 → Y=7.5."""
        obs = self._make_obs("op_test", 30, 10000, 5000, 150000, 30000)
        ms = self.engine.score_operator("op_test", obs, self.window_start, self.window_end)
        yld = next(m for m in ms if m.metric_id == "yield")
        self.assertAlmostEqual(yld.value, 7.5, places=6)

    def test_token_snr_known_value(self):
        """SNR = O/(I+O). For I=10000, O=5000 → S=1/3."""
        obs = self._make_obs("op_test", 30, 10000, 5000, 150000, 30000)
        ms = self.engine.score_operator("op_test", obs, self.window_start, self.window_end)
        snr = next(m for m in ms if m.metric_id == "token_snr")
        self.assertAlmostEqual(snr.value, 1.0 / 3.0, places=6)

    def test_log_leverage_known_value(self):
        """Log Leverage = log10(R/I). For L=15.0 → D=log10(15)."""
        obs = self._make_obs("op_test", 30, 10000, 5000, 150000, 30000)
        ms = self.engine.score_operator("op_test", obs, self.window_start, self.window_end)
        log_lev = next(m for m in ms if m.metric_id == "log_leverage")
        self.assertAlmostEqual(log_lev.value, math.log10(15.0), places=6)

    def test_construction_known_value(self):
        """Construction = W/R. For R=150000, W=30000 → C=0.2."""
        obs = self._make_obs("op_test", 30, 10000, 5000, 150000, 30000)
        ms = self.engine.score_operator("op_test", obs, self.window_start, self.window_end)
        con = next(m for m in ms if m.metric_id == "construction")
        self.assertAlmostEqual(con.value, 0.2, places=6)

    def test_I_zero_domain_guard(self):
        """I=0 → leverage and yield are None with FAILED eligibility."""
        obs = self._make_obs("op_zero", 30, 0, 100, 500, 50)
        ms = self.engine.score_operator("op_zero", obs, self.window_start, self.window_end)
        lev = next(m for m in ms if m.metric_id == "leverage")
        yld = next(m for m in ms if m.metric_id == "yield")
        self.assertIsNone(lev.value)
        self.assertIn("FAILED", lev.eligibility)
        self.assertIsNone(yld.value)
        self.assertIn("FAILED", yld.eligibility)

    def test_R_zero_construction_guard(self):
        """R=0 → construction is None with FAILED eligibility."""
        obs = self._make_obs("op_no_cache", 30, 10000, 5000, 0, 0)
        ms = self.engine.score_operator("op_no_cache", obs, self.window_start, self.window_end)
        con = next(m for m in ms if m.metric_id == "construction")
        self.assertIsNone(con.value)
        self.assertIn("FAILED", con.eligibility)

    def test_synthetic_marker_survives(self):
        """Synthetic flag from observations propagates to measurements."""
        obs = self._make_obs("op_synth", 30, 10000, 5000, 150000, 30000)
        ms = self.engine.score_operator("op_synth", obs, self.window_start, self.window_end)
        for m in ms:
            self.assertTrue(m.synthetic, f"{m.metric_id} should carry synthetic=True")

    def test_measurement_contract_fields(self):
        """Every measurement has all contract fields from `03`."""
        obs = self._make_obs("op_contract", 30, 10000, 5000, 150000, 30000)
        ms = self.engine.score_operator("op_contract", obs, self.window_start, self.window_end)
        for m in ms:
            d = m.to_dict()
            for field in ("metric_id", "metric_version", "value", "unit",
                          "window_start", "window_end", "source", "status", "eligibility"):
                self.assertIn(field, d, f"{m.metric_id} missing {field}")
            self.assertEqual(m.metric_version, "1.0")
            self.assertEqual(m.source, "canonical_token_telemetry")

    def test_unknown_metric_fails_loudly(self):
        """Registry.get() raises KeyError for unknown metric_id."""
        with self.assertRaises(KeyError):
            self.engine.registry.get("nonexistent_metric")

    def test_same_fixture_same_values(self):
        """Same observations produce same measurements every time."""
        obs = self._make_obs("op_repro", 30, 10000, 5000, 150000, 30000)
        ms1 = self.engine.score_operator("op_repro", obs, self.window_start, self.window_end)
        ms2 = self.engine.score_operator("op_repro", obs, self.window_start, self.window_end)
        for m1, m2 in zip(ms1, ms2):
            self.assertEqual(m1, m2)

    def test_window_filtering(self):
        """Observations outside the window are excluded."""
        obs = self._make_obs("op_window", 30, 10000, 5000, 150000, 30000)
        # Add an out-of-window observation with very different values.
        obs.append(Observation(
            observation_id="op_window_extra",
            operator_id="op_window",
            timestamp=datetime(2026, 8, 15, 10, 0, 0),
            input_tokens=100000, output_tokens=100000,
            cache_read_tokens=100000, cache_write_tokens=100000,
            synthetic=True,
        ))
        ms = self.engine.score_operator("op_window", obs, self.window_start, self.window_end)
        lev = next(m for m in ms if m.metric_id == "leverage")
        # Should still be 15.0 — the August observation is outside the July window.
        self.assertAlmostEqual(lev.value, 15.0, places=6)


class TestDomainModelRoundTrip(unittest.TestCase):
    """All domain entities survive to_dict → from_dict round-trips."""

    def test_observation_round_trip(self):
        obs = Observation(
            observation_id="obs_001", operator_id="op_001",
            timestamp=datetime(2026, 7, 1, 14, 22, 9),
            input_tokens=10000, output_tokens=4200,
            cache_read_tokens=181000, cache_write_tokens=26000,
            synthetic=True, platform="claude", model="claude-code",
        )
        self.assertEqual(obs, Observation.from_dict(obs.to_dict()))

    def test_observation_source_confidence_round_trip(self):
        """source_confidence and raw_source_reference survive round-trip."""
        obs = Observation(
            observation_id="obs_sc", operator_id="op_001",
            timestamp=datetime(2026, 7, 1, 14, 22, 9),
            input_tokens=1000, output_tokens=500,
            cache_read_tokens=5000, cache_write_tokens=1000,
            synthetic=True, platform="claude",
            source_confidence="high",
            raw_source_reference="export.json:row42",
        )
        rt = Observation.from_dict(obs.to_dict())
        self.assertEqual(rt.source_confidence, "high")
        self.assertEqual(rt.raw_source_reference, "export.json:row42")
        self.assertEqual(obs, rt)

    def test_observation_backward_compat_no_source_confidence(self):
        """Old dicts without source_confidence still parse (None defaults)."""
        old = {
            "observation_id": "old_001", "operator_id": "op_001",
            "timestamp": "2026-07-01T12:00:00+00:00",
            "input_tokens": 1000, "output_tokens": 500,
            "cache_read_tokens": 5000, "cache_write_tokens": 1000,
            "synthetic": True,
        }
        obs = Observation.from_dict(old)
        self.assertIsNone(obs.source_confidence)
        self.assertIsNone(obs.raw_source_reference)

    def test_observation_negative_tokens_rejected(self):
        with self.assertRaises(ValueError):
            Observation(
                observation_id="x", operator_id="op",
                timestamp=datetime.now(), input_tokens=-1,
                output_tokens=0, cache_read_tokens=0, cache_write_tokens=0,
                synthetic=True,
            )

    def test_measurement_round_trip(self):
        from domain import Measurement, MetricStatus
        m = Measurement(
            metric_id="leverage", metric_version="1.0", operator_id="op_001",
            value=18.4, unit="ratio", window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30), source="canonical_token_telemetry",
            status=MetricStatus.CANONICAL, eligibility="I>0", synthetic=True,
        )
        self.assertEqual(m, Measurement.from_dict(m.to_dict()))


class TestRegistry(unittest.TestCase):
    """Metric registry loading and validation."""

    def test_load_default_registry(self):
        reg = load_registry()
        self.assertEqual(reg.registry_version, "0.2")
        self.assertIn("leverage", reg.metrics)
        self.assertIn("yield", reg.metrics)

    def test_canonical_metric_ids(self):
        reg = load_registry()
        canonical = reg.canonical_metric_ids()
        self.assertIn("leverage", canonical)
        self.assertIn("yield", canonical)
        self.assertIn("token_snr", canonical)
        self.assertIn("log_leverage", canonical)
        self.assertIn("construction", canonical)
        # Unlocked metrics should NOT be in canonical list.
        self.assertNotIn("velocity", canonical)


if __name__ == "__main__":
    unittest.main()
