"""SQLiteRepository — persistent storage for cohort/operator/observation data.

Drop-in replacement for DemoRepository that persists to SQLite. Supports:
    - Seeding from demo_data/ on first init
    - CRUD for operators, observations, cohorts, interventions,
      workflow_observations, experiments
    - Write operations that survive across sessions (unlike the
      in-memory DemoRepository)

The schema mirrors the domain model. All tables use TEXT primary keys
except observations (composite natural key operator_id + timestamp).

Usage:
    repo = SQLiteRepository("pilot.db")          # creates + seeds
    repo = SQLiteRepository("pilot.db", seed=False)  # existing db only
    repo = SQLiteRepository(":memory:")              # in-memory (tests)
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain import (
    Cohort, Diagnosis, DiagnosisStatus, DiagnosticLevel,
    Intervention, InterventionOutcome,
    Observation, Operator, ReferencePopulation,
    Workflow, WorkflowObservation,
)
from domain.provenance import Provenance


_SCHEMA = """
CREATE TABLE IF NOT EXISTS operators (
    operator_id       TEXT PRIMARY KEY,
    tenant_id         TEXT NOT NULL DEFAULT '',
    pseudonym         TEXT NOT NULL,
    cohort_id         TEXT NOT NULL DEFAULT '',
    team              TEXT,
    role_family       TEXT,
    level             TEXT,
    active            INTEGER NOT NULL DEFAULT 1,
    consent_state     TEXT NOT NULL DEFAULT 'granted',
    synthetic         INTEGER NOT NULL DEFAULT 0,
    primary_platform  TEXT,
    pattern_demo      TEXT
);

CREATE TABLE IF NOT EXISTS observations (
    observation_id      TEXT PRIMARY KEY,
    operator_id         TEXT NOT NULL,
    timestamp           TEXT NOT NULL,
    input_tokens        INTEGER NOT NULL,
    output_tokens       INTEGER NOT NULL,
    cache_read_tokens   INTEGER NOT NULL,
    cache_write_tokens  INTEGER NOT NULL,
    synthetic           INTEGER NOT NULL DEFAULT 0,
    platform            TEXT,
    model               TEXT,
    session_id          TEXT,
    provenance_json     TEXT,
    source_confidence   TEXT,
    raw_source_reference TEXT
);
CREATE INDEX IF NOT EXISTS idx_obs_operator ON observations(operator_id);

CREATE TABLE IF NOT EXISTS cohorts (
    cohort_id     TEXT PRIMARY KEY,
    tenant_id     TEXT NOT NULL DEFAULT '',
    name          TEXT NOT NULL,
    window_start  TEXT NOT NULL,
    window_end    TEXT NOT NULL,
    operator_ids_json TEXT NOT NULL DEFAULT '[]',
    synthetic     INTEGER NOT NULL DEFAULT 0,
    description   TEXT
);

CREATE TABLE IF NOT EXISTS interventions (
    intervention_id   TEXT PRIMARY KEY,
    operator_id       TEXT NOT NULL,
    catalog_id        TEXT NOT NULL,
    reason_pattern    TEXT NOT NULL,
    target_metric     TEXT NOT NULL,
    start_date        TEXT NOT NULL,
    followup_days     INTEGER NOT NULL,
    synthetic_outcome TEXT NOT NULL DEFAULT 'PENDING',
    synthetic         INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_int_operator ON interventions(operator_id);

CREATE TABLE IF NOT EXISTS workflow_observations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id     TEXT NOT NULL,
    workflow_id     TEXT NOT NULL,
    stage_id        TEXT NOT NULL,
    date            TEXT NOT NULL,
    time_spent_minutes   REAL NOT NULL DEFAULT 0,
    tasks_completed      INTEGER NOT NULL DEFAULT 0,
    external_quality_score REAL,
    provisional_fit      REAL,
    evidence_count       INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'synthetic_provisional',
    synthetic       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_wobs_operator ON workflow_observations(operator_id);

CREATE TABLE IF NOT EXISTS reference_populations (
    reference_id    TEXT PRIMARY KEY,
    version         TEXT NOT NULL,
    date            TEXT NOT NULL,
    description     TEXT NOT NULL,
    distributions_json TEXT NOT NULL DEFAULT '{}',
    synthetic       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id   TEXT PRIMARY KEY,
    operator_id     TEXT NOT NULL,
    target_metric   TEXT NOT NULL,
    window_days     INTEGER NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    start_date      TEXT NOT NULL,
    label           TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS outcome_datasets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id     TEXT,
    source_path     TEXT NOT NULL,
    record_count    INTEGER NOT NULL DEFAULT 0,
    attached_by     TEXT NOT NULL DEFAULT '',
    attached_at     TEXT NOT NULL,
    claim_type      TEXT NOT NULL DEFAULT 'ASSOCIATION',
    metadata_json   TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);
INSERT OR IGNORE INTO schema_version VALUES ('1', datetime('now'));
"""


class SQLiteRepository:
    """SQLite-backed persistent repository.

    Implements the same read interface as DemoRepository plus write
    methods for interventions, workflow observations, experiments,
    and outcome dataset attachments.
    """

    def __init__(self, db_path: str = "pilot.db", data_dir: Optional[str] = None, seed: bool = True) -> None:
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

        if data_dir is None:
            root = Path(__file__).resolve().parents[2]
            self.data_dir = root / "demo_data"
        else:
            self.data_dir = Path(data_dir)

        self._init_schema()
        if seed and not self._has_data():
            self._seed_from_demo_data()

    # ── Connection management ────────────────────────────────────────────

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.executescript(_SCHEMA)

    def _has_data(self) -> bool:
        row = self.conn.execute("SELECT COUNT(*) as c FROM operators").fetchone()
        return row["c"] > 0

    # ── Seeding ──────────────────────────────────────────────────────────

    def _seed_from_demo_data(self) -> None:
        """Seed all tables from demo_data/ CSV/JSON files."""
        if not self.data_dir.exists():
            raise FileNotFoundError(f"demo_data directory not found: {self.data_dir}")

        self._seed_operators()
        self._seed_observations()
        self._seed_cohort()
        self._seed_interventions()
        self._seed_workflow_observations()
        self._seed_reference_population()

    def _seed_operators(self) -> None:
        path = self.data_dir / "operators.csv"
        if not path.exists():
            return
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                self.conn.execute(
                    """INSERT OR REPLACE INTO operators
                    (operator_id, tenant_id, pseudonym, cohort_id, team, role_family,
                     level, active, consent_state, synthetic, primary_platform, pattern_demo)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        row["operator_id"], "acme", row["pseudonym"], "acme_50",
                        row.get("team"), row.get("role_family"), row.get("level"),
                        1, "granted",
                        1 if row.get("synthetic", "").lower() == "true" else 0,
                        row.get("primary_platform"), row.get("pattern_demo"),
                    ),
                )
        self.conn.commit()

    def _seed_observations(self) -> None:
        path = self.data_dir / "daily_telemetry.csv"
        if not path.exists():
            return
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                d = row["date"]
                ts = f"{d}T12:00:00+00:00"
                is_synth = 1 if row.get("synthetic", "").lower() == "true" else 0
                prov = Provenance(
                    source_provider="demo_fixture:daily_telemetry",
                    collection_method="daily_telemetry_csv",
                    collector_version="sqlite_seed_v1",
                    ingestion_timestamp=datetime.now().isoformat(),
                    original_time_window=(d, d),
                    synthetic=bool(is_synth),
                )
                self.conn.execute(
                    """INSERT OR REPLACE INTO observations
                    (observation_id, operator_id, timestamp, input_tokens, output_tokens,
                     cache_read_tokens, cache_write_tokens, synthetic, platform, model,
                     session_id, provenance_json, source_confidence, raw_source_reference)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        f"{row['operator_id']}_{d}", row["operator_id"], ts,
                        int(row["input_tokens"]), int(row["output_tokens"]),
                        int(row["cache_read_tokens"]), int(row["cache_write_tokens"]),
                        is_synth, row.get("platform"), row.get("model"),
                        None, json.dumps(prov.to_dict()), None, None,
                    ),
                )
        self.conn.commit()

    def _seed_cohort(self) -> None:
        path = self.data_dir / "cohort_summary.json"
        if not path.exists():
            return
        with open(path) as f:
            s = json.load(f)
        window = s["window"]
        ws, we = window.split("/")
        op_ids = [r["operator_id"] for r in self.conn.execute("SELECT operator_id FROM operators").fetchall()]
        self.conn.execute(
            """INSERT OR REPLACE INTO cohorts
            (cohort_id, tenant_id, name, window_start, window_end, operator_ids_json, synthetic, description)
            VALUES (?,?,?,?,?,?,?,?)""",
            (
                s["cohort_id"], "acme", "Acme 50", ws, we,
                json.dumps(op_ids),
                1 if s.get("synthetic", True) else 0, None,
            ),
        )
        self.conn.commit()

    def _seed_interventions(self) -> None:
        path = self.data_dir / "interventions.csv"
        if not path.exists():
            return
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                outcome = row.get("synthetic_outcome", "PENDING")
                try:
                    InterventionOutcome(outcome)
                except ValueError:
                    outcome = "PENDING"
                self.conn.execute(
                    """INSERT OR REPLACE INTO interventions
                    (intervention_id, operator_id, catalog_id, reason_pattern, target_metric,
                     start_date, followup_days, synthetic_outcome, synthetic)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        row["intervention_id"], row["operator_id"], row["catalog_id"],
                        row["reason_pattern"], row["target_metric"], row["start_date"],
                        int(row["followup_days"]), outcome,
                        1 if row.get("synthetic", "").lower() == "true" else 0,
                    ),
                )
        self.conn.commit()

    def _seed_workflow_observations(self) -> None:
        path = self.data_dir / "workflow_fit_observations.csv"
        if not path.exists():
            return
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                self.conn.execute(
                    """INSERT INTO workflow_observations
                    (operator_id, workflow_id, stage_id, date, time_spent_minutes,
                     tasks_completed, external_quality_score, provisional_fit,
                     evidence_count, status, synthetic)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        row["operator_id"], row.get("workflow_id", "software_dev_v1"),
                        row["stage_id"], "2026-07-15",
                        0, 0, None,
                        float(row.get("provisional_fit_demo", 0) or 0),
                        int(row.get("observations", 0) or 0),
                        row.get("status", "synthetic_provisional"),
                        1 if row.get("synthetic", "").lower() == "true" else 0,
                    ),
                )
        self.conn.commit()

    def _seed_reference_population(self) -> None:
        path = self.data_dir / "reference_field.json"
        if not path.exists():
            return
        with open(path) as f:
            raw = json.load(f)
        ref = ReferencePopulation.from_dict(raw)
        self.conn.execute(
            """INSERT OR REPLACE INTO reference_populations
            (reference_id, version, date, description, distributions_json, synthetic)
            VALUES (?,?,?,?,?,?)""",
            (
                ref.reference_id, ref.version, ref.date.isoformat(),
                ref.description, json.dumps(ref.distributions),
                1 if ref.synthetic else 0,
            ),
        )
        self.conn.commit()

    # ── Operators ────────────────────────────────────────────────────────

    @property
    def operators(self) -> List[Operator]:
        rows = self.conn.execute("SELECT * FROM operators ORDER BY operator_id").fetchall()
        return [self._row_to_operator(r) for r in rows]

    def get_operator(self, operator_id: str) -> Optional[Operator]:
        row = self.conn.execute(
            "SELECT * FROM operators WHERE operator_id = ?", (operator_id,)
        ).fetchone()
        return self._row_to_operator(row) if row else None

    @property
    def operator_ids(self) -> List[str]:
        rows = self.conn.execute("SELECT operator_id FROM operators ORDER BY operator_id").fetchall()
        return [r["operator_id"] for r in rows]

    def upsert_operator(self, op: Operator) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO operators
            (operator_id, tenant_id, pseudonym, cohort_id, team, role_family,
             level, active, consent_state, synthetic, primary_platform, pattern_demo)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                op.operator_id, op.tenant_id, op.pseudonym, op.cohort_id,
                op.team, op.role_family, op.level,
                1 if op.active else 0, op.consent_state,
                1 if op.synthetic else 0, op.primary_platform, op.pattern_demo,
            ),
        )
        self.conn.commit()

    @staticmethod
    def _row_to_operator(r: sqlite3.Row) -> Operator:
        return Operator(
            operator_id=r["operator_id"], tenant_id=r["tenant_id"],
            pseudonym=r["pseudonym"], cohort_id=r["cohort_id"],
            team=r["team"], role_family=r["role_family"], level=r["level"],
            active=bool(r["active"]), consent_state=r["consent_state"],
            synthetic=bool(r["synthetic"]),
            primary_platform=r["primary_platform"], pattern_demo=r["pattern_demo"],
        )

    # ── Observations ─────────────────────────────────────────────────────

    @property
    def observations(self) -> List[Observation]:
        rows = self.conn.execute("SELECT * FROM observations ORDER BY operator_id, timestamp").fetchall()
        return [self._row_to_observation(r) for r in rows]

    def observations_for(self, operator_id: str) -> List[Observation]:
        rows = self.conn.execute(
            "SELECT * FROM observations WHERE operator_id = ? ORDER BY timestamp",
            (operator_id,),
        ).fetchall()
        return [self._row_to_observation(r) for r in rows]

    def insert_observation(self, obs: Observation) -> None:
        prov_json = json.dumps(obs.provenance.to_dict()) if obs.provenance else None
        self.conn.execute(
            """INSERT OR REPLACE INTO observations
            (observation_id, operator_id, timestamp, input_tokens, output_tokens,
             cache_read_tokens, cache_write_tokens, synthetic, platform, model,
             session_id, provenance_json, source_confidence, raw_source_reference)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                obs.observation_id, obs.operator_id, obs.timestamp.isoformat(),
                obs.input_tokens, obs.output_tokens,
                obs.cache_read_tokens, obs.cache_write_tokens,
                1 if obs.synthetic else 0, obs.platform, obs.model,
                obs.session_id, prov_json, obs.source_confidence, obs.raw_source_reference,
            ),
        )
        self.conn.commit()

    def insert_observations(self, observations: List[Observation]) -> int:
        count = 0
        for obs in observations:
            prov_json = json.dumps(obs.provenance.to_dict()) if obs.provenance else None
            self.conn.execute(
                """INSERT OR REPLACE INTO observations
                (observation_id, operator_id, timestamp, input_tokens, output_tokens,
                 cache_read_tokens, cache_write_tokens, synthetic, platform, model,
                 session_id, provenance_json, source_confidence, raw_source_reference)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    obs.observation_id, obs.operator_id, obs.timestamp.isoformat(),
                    obs.input_tokens, obs.output_tokens,
                    obs.cache_read_tokens, obs.cache_write_tokens,
                    1 if obs.synthetic else 0, obs.platform, obs.model,
                    obs.session_id, prov_json, obs.source_confidence, obs.raw_source_reference,
                ),
            )
            count += 1
        self.conn.commit()
        return count

    @staticmethod
    def _row_to_observation(r: sqlite3.Row) -> Observation:
        ts = datetime.fromisoformat(r["timestamp"])
        prov = None
        if r["provenance_json"]:
            prov = Provenance.from_dict(json.loads(r["provenance_json"]))
        return Observation(
            observation_id=r["observation_id"], operator_id=r["operator_id"],
            timestamp=ts, input_tokens=r["input_tokens"], output_tokens=r["output_tokens"],
            cache_read_tokens=r["cache_read_tokens"], cache_write_tokens=r["cache_write_tokens"],
            synthetic=bool(r["synthetic"]), platform=r["platform"], model=r["model"],
            session_id=r["session_id"], provenance=prov,
            source_confidence=r["source_confidence"], raw_source_reference=r["raw_source_reference"],
        )

    # ── Cohort ───────────────────────────────────────────────────────────

    @property
    def cohort(self) -> Cohort:
        row = self.conn.execute("SELECT * FROM cohorts LIMIT 1").fetchone()
        if row is None:
            raise RuntimeError("No cohort in database. Seed first or use DemoRepository.")
        return Cohort(
            cohort_id=row["cohort_id"], tenant_id=row["tenant_id"], name=row["name"],
            window_start=date.fromisoformat(row["window_start"]),
            window_end=date.fromisoformat(row["window_end"]),
            operator_ids=json.loads(row["operator_ids_json"]),
            synthetic=bool(row["synthetic"]), description=row["description"],
        )

    # ── Interventions ────────────────────────────────────────────────────

    @property
    def interventions(self) -> List[Intervention]:
        rows = self.conn.execute("SELECT * FROM interventions ORDER BY intervention_id").fetchall()
        return [self._row_to_intervention(r) for r in rows]

    def insert_intervention(self, iv: Intervention) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO interventions
            (intervention_id, operator_id, catalog_id, reason_pattern, target_metric,
             start_date, followup_days, synthetic_outcome, synthetic)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                iv.intervention_id, iv.operator_id, iv.catalog_id, iv.reason_pattern,
                iv.target_metric, iv.start_date.isoformat(), iv.followup_days,
                iv.synthetic_outcome.value, 1 if iv.synthetic else 0,
            ),
        )
        self.conn.commit()

    def update_intervention_outcome(self, intervention_id: str, outcome: str) -> None:
        self.conn.execute(
            "UPDATE interventions SET synthetic_outcome = ? WHERE intervention_id = ?",
            (outcome, intervention_id),
        )
        self.conn.commit()

    @staticmethod
    def _row_to_intervention(r: sqlite3.Row) -> Intervention:
        return Intervention(
            intervention_id=r["intervention_id"], operator_id=r["operator_id"],
            catalog_id=r["catalog_id"], reason_pattern=r["reason_pattern"],
            target_metric=r["target_metric"],
            start_date=date.fromisoformat(r["start_date"]),
            followup_days=r["followup_days"],
            synthetic_outcome=InterventionOutcome(r["synthetic_outcome"]),
            synthetic=bool(r["synthetic"]),
        )

    # ── Workflow observations ────────────────────────────────────────────

    @property
    def workflow(self) -> Workflow:
        return Workflow.software_dev_v1()

    @property
    def workflow_observations(self) -> List[WorkflowObservation]:
        rows = self.conn.execute("SELECT * FROM workflow_observations ORDER BY operator_id, stage_id").fetchall()
        return [self._row_to_workflow_obs(r) for r in rows]

    def insert_workflow_observation(self, wobs: WorkflowObservation) -> int:
        cur = self.conn.execute(
            """INSERT INTO workflow_observations
            (operator_id, workflow_id, stage_id, date, time_spent_minutes,
             tasks_completed, external_quality_score, provisional_fit,
             evidence_count, status, synthetic)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                wobs.operator_id, wobs.workflow_id, wobs.stage_id,
                wobs.date.isoformat(), wobs.time_spent_minutes,
                wobs.tasks_completed, wobs.external_quality_score,
                wobs.provisional_fit, wobs.evidence_count,
                wobs.status, 1 if wobs.synthetic else 0,
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    @staticmethod
    def _row_to_workflow_obs(r: sqlite3.Row) -> WorkflowObservation:
        return WorkflowObservation(
            operator_id=r["operator_id"], workflow_id=r["workflow_id"],
            stage_id=r["stage_id"], date=date.fromisoformat(r["date"]),
            time_spent_minutes=r["time_spent_minutes"],
            tasks_completed=r["tasks_completed"],
            external_quality_score=r["external_quality_score"],
            provisional_fit=r["provisional_fit"],
            evidence_count=r["evidence_count"],
            status=r["status"], synthetic=bool(r["synthetic"]),
        )

    # ── Reference population ─────────────────────────────────────────────

    @property
    def reference_population(self) -> ReferencePopulation:
        row = self.conn.execute("SELECT * FROM reference_populations LIMIT 1").fetchone()
        if row is None:
            raise RuntimeError("No reference population in database.")
        return ReferencePopulation(
            reference_id=row["reference_id"], version=row["version"],
            date=date.fromisoformat(row["date"]),
            description=row["description"],
            distributions=json.loads(row["distributions_json"]),
            synthetic=bool(row["synthetic"]),
        )

    # ── Experiments ──────────────────────────────────────────────────────

    @property
    def experiments(self) -> List[dict]:
        rows = self.conn.execute("SELECT * FROM experiments ORDER BY experiment_id").fetchall()
        return [dict(r) for r in rows]

    def insert_experiment(self, experiment: dict) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO experiments
            (experiment_id, operator_id, target_metric, window_days, description, start_date, label)
            VALUES (?,?,?,?,?,?,?)""",
            (
                experiment["experiment_id"], experiment["operator_id"],
                experiment["target_metric"], experiment["window_days"],
                experiment.get("description", ""), experiment["start_date"],
                experiment.get("label", ""),
            ),
        )
        self.conn.commit()

    # ── Outcome datasets ─────────────────────────────────────────────────

    @property
    def outcome_datasets(self) -> List[dict]:
        rows = self.conn.execute("SELECT * FROM outcome_datasets ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def attach_outcome_dataset(
        self, source_path: str, record_count: int, attached_by: str,
        operator_id: Optional[str] = None, metadata: Optional[dict] = None,
    ) -> int:
        cur = self.conn.execute(
            """INSERT INTO outcome_datasets
            (operator_id, source_path, record_count, attached_by, attached_at, claim_type, metadata_json)
            VALUES (?,?,?,?,?,?,?)""",
            (
                operator_id, source_path, record_count, attached_by,
                datetime.now().isoformat(), "ASSOCIATION",
                json.dumps(metadata or {}),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    # ── Diagnoses (read-only, loaded from demo data) ─────────────────────

    @property
    def diagnoses(self) -> List[Diagnosis]:
        path = self.data_dir / "diagnostics.json"
        if not path.exists():
            return []
        with open(path) as f:
            raw = json.load(f)
        return [
            Diagnosis(
                diagnosis_id=f"diag_{i:03d}",
                operator_id=d["operator_id"], pattern_id=d["pattern_id"],
                hypothesis=d.get("evidence", ""),
                confidence=float(d.get("confidence_demo", 0)),
                status=DiagnosisStatus(d.get("status", "hypothesis").lower()),
                evidence=d.get("evidence", ""),
                alternatives=[],
                recommended_interventions=d.get("recommended", []),
                synthetic=d.get("synthetic", True),
                level=DiagnosticLevel.OPERATOR,
            )
            for i, d in enumerate(raw)
        ]

    def diagnoses_for(self, operator_id: str) -> List[Diagnosis]:
        return [d for d in self.diagnoses if d.operator_id == operator_id]

    # ── Cohort summary ───────────────────────────────────────────────────

    @property
    def cohort_summary(self) -> dict:
        path = self.data_dir / "cohort_summary.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return self.cohort.to_dict()
