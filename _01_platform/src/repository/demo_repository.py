"""DemoRepository — loads the synthetic demo dataset into domain objects.

Reads the demo_data/ directory and provides:
    - operators (list[Operator])
    - observations (list[Observation])
    - cohort (Cohort)
    - workflow (Workflow)
    - workflow_observations (list[WorkflowObservation])
    - diagnoses (list[Diagnosis])
    - interventions (list[Intervention])
    - reference_population (ReferencePopulation)

The repository does NOT compute metrics — that's the ScoringEngine's job.
The repository provides observations; the engine computes measurements.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

# Ensure src/ is on the path for domain imports.
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain import (
    Cohort, Diagnosis, DiagnosisStatus, Intervention, InterventionOutcome,
    Observation, Operator, ReferencePopulation, Workflow, WorkflowObservation,
    Artifact, Lineage, System, SystemType, SystemVersion,
    Outcome,
)


class DemoRepository:
    """Loads the synthetic demo dataset from demo_data/."""

    def __init__(self, data_dir: Optional[str] = None) -> None:
        if data_dir is None:
            # src/repository/demo_repository.py → src/ → build_package_root/demo_data/
            root = Path(__file__).resolve().parents[2]
            self.data_dir = root / "demo_data"
        else:
            self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"demo_data directory not found: {self.data_dir}")

        self._operators: Optional[List[Operator]] = None
        self._observations: Optional[List[Observation]] = None
        self._cohort: Optional[Cohort] = None
        self._workflow: Optional[Workflow] = None
        self._workflow_observations: Optional[List[WorkflowObservation]] = None
        self._diagnoses: Optional[List[Diagnosis]] = None
        self._interventions: Optional[List[Intervention]] = None
        self._reference_population: Optional[ReferencePopulation] = None
        # New canonical domain objects (lazy-loaded).
        self._artifacts: Optional[List[Artifact]] = None
        self._lineages: Optional[List[Lineage]] = None
        self._outcomes: Optional[list] = None
        self._teams: Optional[list] = None
        self._workflows: Optional[List[Workflow]] = None
        self._systems: Optional[List[System]] = None
        self._observations_jsonl: Optional[List[Observation]] = None

    # ── Operators ────────────────────────────────────────────────────────

    @property
    def operators(self) -> List[Operator]:
        if self._operators is None:
            self._operators = self._load_operators()
        return self._operators

    def _load_operators(self) -> List[Operator]:
        path = self.data_dir / "operators.csv"
        ops: List[Operator] = []
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                ops.append(Operator(
                    operator_id=row["operator_id"],
                    tenant_id="acme",
                    pseudonym=row["pseudonym"],
                    cohort_id="acme_50",
                    team=row.get("team"),
                    role_family=row.get("role_family"),
                    level=row.get("level"),
                    active=True,
                    synthetic=row.get("synthetic", "").lower() == "true",
                    primary_platform=row.get("primary_platform"),
                    pattern_demo=row.get("pattern_demo"),
                ))
        return ops

    def get_operator(self, operator_id: str) -> Optional[Operator]:
        return next((o for o in self.operators if o.operator_id == operator_id), None)

    @property
    def operator_ids(self) -> List[str]:
        return [o.operator_id for o in self.operators]

    # ── Observations ─────────────────────────────────────────────────────

    @property
    def observations(self) -> List[Observation]:
        if self._observations is None:
            self._observations = self._load_observations()
        return self._observations

    def _load_observations(self) -> List[Observation]:
        """Loads daily telemetry as daily-aggregate observations.

        Each row in daily_telemetry.csv becomes one Observation representing
        that day's aggregated token counts. The observation_id is derived
        from operator_id + date for determinism. Structured provenance is
        populated per `12` §Provenance.
        """
        from domain.provenance import Provenance
        path = self.data_dir / "daily_telemetry.csv"
        obs: List[Observation] = []
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                d = date.fromisoformat(row["date"])
                is_synthetic = row.get("synthetic", "").lower() == "true"
                obs.append(Observation(
                    observation_id=f"{row['operator_id']}_{row['date']}",
                    operator_id=row["operator_id"],
                    timestamp=datetime(d.year, d.month, d.day, 12, 0, 0),
                    input_tokens=int(row["input_tokens"]),
                    output_tokens=int(row["output_tokens"]),
                    cache_read_tokens=int(row["cache_read_tokens"]),
                    cache_write_tokens=int(row["cache_write_tokens"]),
                    synthetic=is_synthetic,
                    platform=row.get("platform"),
                    model=row.get("model"),
                    provenance=Provenance(
                        source_provider="demo_fixture:daily_telemetry",
                        collection_method="daily_telemetry_csv",
                        collector_version="demo_repository_v1",
                        ingestion_timestamp=datetime.now().isoformat(),
                        original_time_window=(row["date"], row["date"]),
                        synthetic=is_synthetic,
                    ),
                ))
        return obs

    def observations_for(self, operator_id: str) -> List[Observation]:
        return [o for o in self.observations if o.operator_id == operator_id]

    # ── Cohort ───────────────────────────────────────────────────────────

    @property
    def cohort(self) -> Cohort:
        if self._cohort is None:
            path = self.data_dir / "cohort_summary.json"
            with open(path) as f:
                s = json.load(f)
            window = s["window"]  # "2026-07-01/2026-07-30"
            ws, we = window.split("/")
            self._cohort = Cohort(
                cohort_id=s["cohort_id"],
                tenant_id="acme",
                name="Acme 50",
                window_start=date.fromisoformat(ws),
                window_end=date.fromisoformat(we),
                operator_ids=self.operator_ids,
                synthetic=s.get("synthetic", True),
            )
        return self._cohort

    # ── Workflow ─────────────────────────────────────────────────────────

    @property
    def workflow(self) -> Workflow:
        if self._workflow is None:
            self._workflow = Workflow.software_dev_v1()
        return self._workflow

    @property
    def workflow_observations(self) -> List[WorkflowObservation]:
        if self._workflow_observations is None:
            self._workflow_observations = self._load_workflow_observations()
        return self._workflow_observations

    def _load_workflow_observations(self) -> List[WorkflowObservation]:
        path = self.data_dir / "workflow_fit_observations.csv"
        wobs: List[WorkflowObservation] = []
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                wobs.append(WorkflowObservation(
                    operator_id=row["operator_id"],
                    workflow_id=row["workflow_id"],
                    stage_id=row["stage_id"],
                    date=date(2026, 7, 15),  # mid-window nominal date
                    provisional_fit=float(row.get("provisional_fit_demo", 0)),
                    evidence_count=int(row.get("observations", 0)),
                    status=row.get("status", "synthetic_provisional"),
                    synthetic=row.get("synthetic", "").lower() == "true",
                ))
        return wobs

    # ── Diagnoses ────────────────────────────────────────────────────────

    @property
    def diagnoses(self) -> List[Diagnosis]:
        if self._diagnoses is None:
            path = self.data_dir / "diagnostics.json"
            with open(path) as f:
                raw = json.load(f)
            self._diagnoses = [
                Diagnosis(
                    diagnosis_id=f"diag_{i:03d}",
                    operator_id=d["operator_id"],
                    pattern_id=d["pattern_id"],
                    hypothesis=d.get("evidence", ""),
                    confidence=float(d.get("confidence_demo", 0)),
                    status=DiagnosisStatus(d.get("status", "hypothesis").lower()),
                    evidence=d.get("evidence", ""),
                    alternatives=[],
                    recommended_interventions=d.get("recommended", []),
                    synthetic=d.get("synthetic", True),
                )
                for i, d in enumerate(raw)
            ]
        return self._diagnoses

    def diagnoses_for(self, operator_id: str) -> List[Diagnosis]:
        return [d for d in self.diagnoses if d.operator_id == operator_id]

    # ── Interventions ────────────────────────────────────────────────────

    @property
    def interventions(self) -> List[Intervention]:
        if self._interventions is None:
            path = self.data_dir / "interventions.csv"
            ivs: List[Intervention] = []
            with open(path, newline="") as f:
                for row in csv.DictReader(f):
                    outcome = row.get("synthetic_outcome", "PENDING")
                    try:
                        outcome = InterventionOutcome(outcome)
                    except ValueError:
                        outcome = InterventionOutcome.PENDING
                    ivs.append(Intervention(
                        intervention_id=row["intervention_id"],
                        operator_id=row["operator_id"],
                        catalog_id=row["catalog_id"],
                        reason_pattern=row["reason_pattern"],
                        target_metric=row["target_metric"],
                        start_date=date.fromisoformat(row["start_date"]),
                        followup_days=int(row["followup_days"]),
                        synthetic_outcome=outcome,
                        synthetic=row.get("synthetic", "").lower() == "true",
                    ))
            self._interventions = ivs
        return self._interventions

    # ── Reference Population ─────────────────────────────────────────────

    @property
    def reference_population(self) -> ReferencePopulation:
        if self._reference_population is None:
            # Try to load a separate reference_field file; fall back to embedded.
            ref_path = self.data_dir / "reference_field.json"
            if ref_path.exists():
                with open(ref_path) as f:
                    raw = json.load(f)
                self._reference_population = ReferencePopulation.from_dict(raw)
            else:
                # Derive a synthetic reference from the cohort's metric distributions.
                self._reference_population = self._derive_reference_population()
        return self._reference_population

    def _derive_reference_population(self) -> ReferencePopulation:
        """Build a fallback reference population from cohort metric distributions."""
        from metrics.engine import ScoringEngine
        engine = ScoringEngine()
        c = self.cohort
        all_ms = engine.score_cohort(self.operator_ids, self.observations, c.window_start, c.window_end)
        distributions: Dict[str, dict] = {}
        for metric_id in ("leverage", "yield", "token_snr", "construction"):
            values = sorted(
                m.value for ms in all_ms.values() for m in ms
                if m.metric_id == metric_id and m.value is not None
            )
            if values:
                n = len(values)
                distributions[metric_id] = {
                    f"p{p}": values[min(int(n * p / 100), n - 1)]
                    for p in (0, 10, 25, 50, 75, 90, 100)
                }
        return ReferencePopulation(
            reference_id="acme_50_derived",
            version="derived_v1",
            date=date(2026, 7, 30),
            description="Derived from acme_50 cohort (fallback — no external reference_field.json)",
            distributions=distributions,
            synthetic=True,
        )

    # ── Cohort summary ───────────────────────────────────────────────────

    @property
    def cohort_summary(self) -> dict:
        path = self.data_dir / "cohort_summary.json"
        with open(path) as f:
            return json.load(f)

    # ── Artifacts ────────────────────────────────────────────────────────

    @property
    def artifacts(self) -> List[Artifact]:
        if self._artifacts is None:
            self._artifacts = self._load_artifacts()
        return self._artifacts

    def _load_artifacts(self) -> List[Artifact]:
        path = self.data_dir / "artifacts.jsonl"
        arts: List[Artifact] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                arts.append(Artifact.from_dict(json.loads(line)))
        return arts

    def artifacts_for(self, operator_id: str) -> List[Artifact]:
        return [a for a in self.artifacts if a.operator_id == operator_id]

    # ── Lineages ─────────────────────────────────────────────────────────

    @property
    def lineages(self) -> List[Lineage]:
        if self._lineages is None:
            self._lineages = self._load_lineages()
        return self._lineages

    def _load_lineages(self) -> List[Lineage]:
        path = self.data_dir / "lineages.jsonl"
        lins: List[Lineage] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                lins.append(Lineage.from_dict(json.loads(line)))
        return lins

    def lineages_for(self, operator_id: str) -> List[Lineage]:
        return [l for l in self.lineages if l.operator_id == operator_id]

    # ── Outcomes (raw records) ───────────────────────────────────────────

    @property
    def outcomes(self) -> list:
        if self._outcomes is None:
            path = self.data_dir / "outcomes.json"
            with open(path) as f:
                raw = json.load(f)
            self._outcomes = [Outcome.from_dict(d) for d in raw]
        return self._outcomes

    # ── Teams (raw records) ──────────────────────────────────────────────

    @property
    def teams(self) -> list:
        if self._teams is None:
            path = self.data_dir / "teams.json"
            with open(path) as f:
                self._teams = json.load(f)
        return self._teams

    # ── Workflows (all 4 from JSON) ──────────────────────────────────────

    @property
    def workflows(self) -> List[Workflow]:
        if self._workflows is None:
            path = self.data_dir / "workflows.json"
            with open(path) as f:
                raw = json.load(f)
            self._workflows = [Workflow.from_dict(w) for w in raw]
        return self._workflows

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return next((w for w in self.workflows if w.workflow_id == workflow_id), None)

    # ── Systems (derived static list) ────────────────────────────────────

    @property
    def systems(self) -> List[System]:
        if self._systems is None:
            self._systems = [
                System(
                    system_id="claude",
                    tenant_id="acme",
                    name="Claude",
                    system_type=SystemType.AI_PLATFORM,
                    synthetic=True,
                ),
                System(
                    system_id="codex",
                    tenant_id="acme",
                    name="Codex",
                    system_type=SystemType.AI_PLATFORM,
                    synthetic=True,
                ),
                System(
                    system_id="chatgpt",
                    tenant_id="acme",
                    name="ChatGPT",
                    system_type=SystemType.AI_PLATFORM,
                    synthetic=True,
                ),
                System(
                    system_id="cursor",
                    tenant_id="acme",
                    name="Cursor",
                    system_type=SystemType.AI_PLATFORM,
                    synthetic=True,
                ),
                System(
                    system_id="copilot",
                    tenant_id="acme",
                    name="Copilot",
                    system_type=SystemType.AI_PLATFORM,
                    synthetic=True,
                ),
            ]
        return self._systems

    # ── Full observations from observations.jsonl ────────────────────────

    @property
    def observations_jsonl(self) -> List[Observation]:
        if self._observations_jsonl is None:
            self._observations_jsonl = self._load_observations_jsonl()
        return self._observations_jsonl

    def _load_observations_jsonl(self) -> List[Observation]:
        path = self.data_dir / "observations.jsonl"
        obs: List[Observation] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obs.append(Observation.from_dict(json.loads(line)))
        return obs
