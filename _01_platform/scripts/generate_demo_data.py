#!/usr/bin/env python3
"""Regenerate demo_data/ to match `02` §26 file layout.

Converts the existing CSV-based demo data to the spec's JSON/JSONL layout
and adds the missing files:
    - observations.jsonl (from daily_telemetry.csv, expanded to observation schema)
    - workflows.json (7-stage software_dev_v1)
    - stage_events.jsonl (from workflow_fit_observations.csv)
    - reference_field.json (computed from cohort metric distributions)
    - demo_manifest.json (per `02` §27)
    - metric_registry.json (copy of schemas/metric_registry.json)
    - cohort.json (from cohort_summary.json + computed medians)
    - results.json (from post_intervention_results.csv, recomputed)
    - external_outcomes.csv (extracted from post_intervention_results.csv)
    - operators.json (from operators.csv)
    - diagnoses.json (already JSON, reformatted)
    - interventions.json (from interventions.csv)

Keeps the 50-operator cohort and the 7 canonical workflow stages.
All values are synthetic placeholders — structure matters more than values.
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain import Workflow, Observation, Intervention, InterventionOutcome
from metrics.engine import ScoringEngine

BUILD_ROOT = Path(__file__).resolve().parents[1]
DATA = BUILD_ROOT / "demo_data"
SCHEMAS = BUILD_ROOT / "schemas"


def load_csv(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


def load_json(name):
    with open(DATA / name) as f:
        return json.load(f)


def write_json(name, obj):
    with open(DATA / name, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_jsonl(name, items):
    with open(DATA / name, "w") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_csv(name, header, rows):
    with open(DATA / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def main():
    print(f"Regenerating demo data in {DATA}...")

    # ── operators.json ──────────────────────────────────────────────────
    ops = load_csv("operators.csv")
    operators_json = [
        {
            "operator_id": r["operator_id"],
            "pseudonym": r["pseudonym"],
            "team": r.get("team"),
            "role_family": r.get("role_family"),
            "level": r.get("level"),
            "cohort_id": "acme_50",
            "active": True,
            "primary_platform": r.get("primary_platform"),
            "pattern_demo": r.get("pattern_demo"),
            "synthetic": True,
        }
        for r in ops
    ]
    write_json("operators.json", operators_json)
    print(f"  operators.json: {len(operators_json)} operators")

    # ── observations.jsonl (from daily_telemetry.csv) ───────────────────
    telemetry = load_csv("daily_telemetry.csv")
    observations = []
    obs_counter = 0
    for row in telemetry:
        obs_counter += 1
        observations.append({
            "observation_id": f"obs_{obs_counter:06d}",
            "operator_id": row["operator_id"],
            "timestamp": f"{row['date']}T12:00:00Z",
            "platform": row.get("platform"),
            "model": row.get("model"),
            "input_tokens": int(row["input_tokens"]),
            "output_tokens": int(row["output_tokens"]),
            "cache_read_tokens": int(row["cache_read_tokens"]),
            "cache_write_tokens": int(row["cache_write_tokens"]),
            "synthetic": True,
            "provenance": "synthetic_v1",
        })
    write_jsonl("observations.jsonl", observations)
    print(f"  observations.jsonl: {len(observations)} observations")

    # ── daily_aggregates.csv (keep the existing daily_telemetry.csv data) ──
    # The spec calls for daily_aggregates.csv — rename the existing file.
    daily_aggregates = [
        {
            "date": r["date"],
            "operator_id": r["operator_id"],
            "input_tokens": int(r["input_tokens"]),
            "output_tokens": int(r["output_tokens"]),
            "cache_read_tokens": int(r["cache_read_tokens"]),
            "cache_write_tokens": int(r["cache_write_tokens"]),
            "sessions": 1,
            "active": True,
            "synthetic": True,
        }
        for r in telemetry
    ]
    write_csv("daily_aggregates.csv",
              ["date", "operator_id", "input_tokens", "output_tokens",
               "cache_read_tokens", "cache_write_tokens", "sessions", "active", "synthetic"],
              daily_aggregates)
    print(f"  daily_aggregates.csv: {len(daily_aggregates)} rows")

    # ── workflows.json (7-stage software_dev_v1) ────────────────────────
    wf = Workflow.software_dev_v1()
    write_json("workflows.json", [wf.to_dict()])
    print(f"  workflows.json: {len(wf.stages)} stages")

    # ── stage_events.jsonl (from workflow_fit_observations.csv) ─────────
    wf_obs = load_csv("workflow_fit_observations.csv")
    stage_events = [
        {
            "workflow_id": r["workflow_id"],
            "stage_id": r["stage_id"],
            "operator_id": r["operator_id"],
            "date": "2026-07-15",
            "time_spent_minutes": int(r.get("observations", 0)) * 30,  # placeholder
            "tasks_completed": int(r.get("observations", 0)),
            "external_quality_score": None,
            "provisional_fit_demo": float(r.get("provisional_fit_demo", 0)),
            "evidence_count": int(r.get("observations", 0)),
            "status": r.get("status", "synthetic_provisional"),
            "synthetic": True,
        }
        for r in wf_obs
    ]
    write_jsonl("stage_events.jsonl", stage_events)
    print(f"  stage_events.jsonl: {len(stage_events)} events")

    # ── diagnoses.json (reformat existing) ──────────────────────────────
    diagnoses = load_json("diagnostics.json")
    formatted_diagnoses = [
        {
            "diagnosis_id": f"diag_{i:03d}",
            "operator_id": d["operator_id"],
            "pattern_id": d["pattern_id"],
            "hypothesis": d.get("evidence", ""),
            "confidence": d.get("confidence_demo", 0),
            "status": d.get("status", "hypothesis").lower(),
            "evidence": d.get("evidence", ""),
            "alternatives": [],
            "recommended_interventions": d.get("recommended", []),
            "synthetic": d.get("synthetic", True),
        }
        for i, d in enumerate(diagnoses)
    ]
    write_json("diagnoses.json", formatted_diagnoses)
    print(f"  diagnoses.json: {len(formatted_diagnoses)} diagnoses")

    # ── interventions.json (from interventions.csv) ─────────────────────
    ivs = load_csv("interventions.csv")
    interventions_json = [
        {
            "intervention_id": r["intervention_id"],
            "operator_id": r["operator_id"],
            "catalog_id": r["catalog_id"],
            "reason_pattern": r["reason_pattern"],
            "target_metric": r["target_metric"],
            "start_date": r["start_date"],
            "followup_days": int(r["followup_days"]),
            "synthetic_outcome": r["synthetic_outcome"],
            "synthetic": True,
        }
        for r in ivs
    ]
    write_json("interventions.json", interventions_json)
    print(f"  interventions.json: {len(interventions_json)} interventions")

    # ── results.json (from post_intervention_results.csv, recomputed) ───
    post = load_csv("post_intervention_results.csv")
    # Join with interventions to get the synthetic_outcome.
    iv_outcomes = {r["intervention_id"]: r["synthetic_outcome"] for r in ivs}
    results_json = [
        {
            "result_id": f"res_{i+1:03d}",
            "operator_id": r["operator_id"],
            "intervention_id": r["intervention_id"],
            "baseline_window": "2026-07-01/2026-07-30",
            "post_window": "2026-08-01/2026-08-14",
            "internal_deltas": {
                "leverage_pct": _pct_change(float(r["baseline_leverage"]), float(r["followup_leverage"])),
                "yield_pct": _pct_change(float(r["baseline_yield"]), float(r["followup_yield"])),
            },
            "external_deltas": {
                "cycle_time_pct": float(r["external_cycle_time_change_pct"]),
                "quality_pct": float(r["external_quality_change_pct"]),
            },
            "classification": _classify_result(iv_outcomes.get(r["intervention_id"], "NO_EFFECT")),
            "status": "synthetic_demo",
        }
        for i, r in enumerate(post)
    ]
    write_json("results.json", results_json)
    print(f"  results.json: {len(results_json)} results")

    # ── external_outcomes.csv ───────────────────────────────────────────
    external_rows = [
        {
            "operator_id": r["operator_id"],
            "intervention_id": r["intervention_id"],
            "window_start": "2026-08-01",
            "window_end": "2026-08-14",
            "cycle_time_change_pct": r["external_cycle_time_change_pct"],
            "quality_change_pct": r["external_quality_change_pct"],
            "source": "synthetic_customer_provided",
            "synthetic": True,
        }
        for r in post
    ]
    write_csv("external_outcomes.csv",
              ["operator_id", "intervention_id", "window_start", "window_end",
               "cycle_time_change_pct", "quality_change_pct", "source", "synthetic"],
              external_rows)
    print(f"  external_outcomes.csv: {len(external_rows)} rows")

    # ── reference_field.json (computed from cohort) ─────────────────────
    engine = ScoringEngine()
    op_ids = [o["operator_id"] for o in operators_json]
    obs_objects = [Observation.from_dict(o) for o in observations]
    cohort_ms = engine.score_cohort(op_ids, obs_objects, date(2026, 7, 1), date(2026, 7, 30))
    distributions = {}
    for metric_id in ("leverage", "yield", "token_snr", "construction", "log_leverage"):
        values = sorted(
            m.value for ms in cohort_ms.values() for m in ms
            if m.metric_id == metric_id and m.value is not None
        )
        if values:
            n = len(values)
            distributions[metric_id] = {
                f"p{p}": round(values[min(int(n * p / 100), n - 1)], 4)
                for p in (0, 10, 25, 50, 75, 90, 100)
            }
    reference_field = {
        "reference_id": "public_field",
        "version": "public_field_2026-08-17",
        "date": "2026-08-17",
        "description": "Synthetic reference field distribution derived from the acme_50 cohort. Placeholder — replace with a real external reference field before production use.",
        "distributions": distributions,
        "synthetic": True,
    }
    write_json("reference_field.json", reference_field)
    print(f"  reference_field.json: {len(distributions)} metric distributions")

    # ── metric_registry.json (copy from schemas/) ───────────────────────
    shutil.copy2(SCHEMAS / "metric_registry.json", DATA / "metric_registry.json")
    print(f"  metric_registry.json: copied from schemas/")

    # ── cohort.json (from cohort_summary.json + computed medians) ───────
    summary = load_json("cohort_summary.json")
    medians = {}
    for metric_id in ("leverage", "yield", "token_snr", "construction"):
        values = sorted(
            m.value for ms in cohort_ms.values() for m in ms
            if m.metric_id == metric_id and m.value is not None
        )
        if values:
            n = len(values)
            medians[metric_id] = round(values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2, 4)
    cohort_json = {
        "cohort_id": summary["cohort_id"],
        "tenant_id": "acme",
        "name": "Acme 50",
        "window_start": summary["window"].split("/")[0],
        "window_end": summary["window"].split("/")[1],
        "operator_ids": op_ids,
        "operators": len(op_ids),
        "synthetic": True,
        "median_leverage": medians.get("leverage"),
        "median_yield": medians.get("yield"),
        "median_token_snr": medians.get("token_snr"),
        "median_construction": medians.get("construction"),
        "metric_registry_version": summary.get("metric_registry_version", "0.2"),
    }
    write_json("cohort.json", cohort_json)
    print(f"  cohort.json: {len(op_ids)} operators, medians computed")

    # ── demo_manifest.json (per `02` §27) ───────────────────────────────
    manifest = {
        "demo_id": "acme_50_v1",
        "synthetic": True,
        "operators": 50,
        "baseline_days": 30,
        "post_days": 14,
        "reference_field_version": "public_field_2026-08-17",
        "metric_registry_version": "0.2",
        "seed": 50030,
        "files": [
            "cohort.json",
            "operators.json",
            "observations.jsonl",
            "daily_aggregates.csv",
            "workflows.json",
            "stage_events.jsonl",
            "diagnoses.json",
            "interventions.json",
            "results.json",
            "external_outcomes.csv",
            "reference_field.json",
            "metric_registry.json",
            "demo_manifest.json",
        ],
    }
    write_json("demo_manifest.json", manifest)
    print(f"  demo_manifest.json: manifest written")

    # ── Update README.md to reflect the new layout ──────────────────────
    print("\nDemo data regeneration complete.")
    print(f"Files in {DATA}:")
    for f in sorted(DATA.glob("*")):
        if f.name == "README.md":
            continue
        print(f"  {f.name}")


def _pct_change(baseline, followup):
    if baseline == 0:
        return 0.0
    return round((followup - baseline) / baseline * 100, 2)


def _classify_result(outcome):
    mapping = {
        "SUCCESS": "improved_internal_and_external",
        "PARTIAL": "improved_internal_only",
        "NO_EFFECT": "no_change",
        "NEGATIVE": "degraded",
    }
    return mapping.get(outcome, "no_change")


if __name__ == "__main__":
    main()
