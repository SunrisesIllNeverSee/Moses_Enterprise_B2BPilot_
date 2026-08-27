#!/usr/bin/env python3
"""
MOSES Enterprise Pilot Readiness — Q14 Gap Closure Generator

Closes the 3 GAPs + remaining PARTIALs from 08_PROOF_DEMO.md S17.3:
  GAP 1: artifacts.jsonl (200 synthetic artifacts linked to observations)
  GAP 2: lineages.jsonl (50 synthetic lineages linking obs -> artifacts -> outcomes)
  GAP 3: 2-3 additional workflows + stage events
  PARTIAL 5: teams.json (explicit team structure modeling)
  outcomes.json (structured outcome objects linked to artifacts)

Uses the same seed (50030) as the existing demo data for determinism.
All records carry synthetic=true per the data containment policy.

Usage:
  python3 generate_extensions.py
"""

import json
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

SEED = 50030
DEMO_DIR = Path(__file__).parent
random.seed(SEED)

# ---------------------------------------------------------------------------
# Load existing data
# ---------------------------------------------------------------------------

def load_json(name):
    with open(DEMO_DIR / name) as f:
        return json.load(f)

def load_jsonl(name):
    records = []
    with open(DEMO_DIR / name) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

operators = load_json("operators.json")
observations = load_jsonl("observations.jsonl")
existing_workflows = load_json("workflows.json")
interventions = load_json("interventions.json")
results = load_json("results.json")

# Index observations by operator
obs_by_op = {}
for o in observations:
    obs_by_op.setdefault(o["operator_id"], []).append(o)

# Team structure from operators
teams_map = {}
for op in operators:
    team = op["team"]
    teams_map.setdefault(team, []).append(op)

# ---------------------------------------------------------------------------
# GAP 1: artifacts.jsonl — 200 synthetic artifacts
# ---------------------------------------------------------------------------

ARTIFACT_TYPES = [
    "code_file", "code_file", "code_file", "code_file",  # weighted toward code
    "document", "config", "test_file", "design_doc", "data_file", "script",
]

FILE_PATHS_BY_TYPE = {
    "code_file": [
        "src/api/orders.py", "src/api/users.py", "src/api/auth.py",
        "src/lib/utils.py", "src/lib/cascade.py", "src/lib/metrics.py",
        "src/models/operator.py", "src/models/observation.py",
        "src/ingest/adapter.py", "src/ingest/normalize.py",
        "src/reporting/brief.py", "src/reporting/operator.py",
        "src/diagnostics/patterns.py", "src/diagnostics/burn.py",
        "src/governance/consent.py", "src/governance/audit.py",
    ],
    "test_file": [
        "tests/test_api.py", "tests/test_metrics.py", "tests/test_cascade.py",
        "tests/test_ingest.py", "tests/test_reporting.py",
    ],
    "document": [
        "docs/architecture.md", "docs/api_spec.md", "docs/runbook.md",
        "docs/pilot_playbook.md", "docs/methodology.md",
    ],
    "config": [
        "config/settings.yaml", "config/metrics.json", ".github/workflows/ci.yml",
        "deploy/docker-compose.yml", "config/tenants/acme.yaml",
    ],
    "design_doc": [
        "design/operator_eval.md", "design/benchmark_engine.md",
        "design/canonical_model.md", "design/evidence_grades.md",
    ],
    "data_file": [
        "data/reference_field.json", "data/metric_registry.json",
        "data/demo_manifest.json", "data/cohort_summary.json",
    ],
    "script": [
        "scripts/generate_demo.py", "scripts/validate_demo.py",
        "scripts/export_report.py", "scripts/run_pilot.py",
    ],
}

def generate_artifacts():
    """Generate 200 synthetic artifacts linked to observations."""
    artifacts = []
    # Select 200 observations spread across operators
    candidate_ops = [op["operator_id"] for op in operators]
    random.shuffle(candidate_ops)

    obs_pool = []
    for op_id in candidate_ops:
        obs_pool.extend(obs_by_op.get(op_id, []))
    random.shuffle(obs_pool)
    selected_obs = obs_pool[:200]

    for i, obs in enumerate(selected_obs, 1):
        artifact_type = random.choice(ARTIFACT_TYPES)
        file_path = random.choice(FILE_PATHS_BY_TYPE[artifact_type])
        lines_added = random.randint(5, 120)
        lines_removed = random.randint(0, lines_added // 3)
        commit_sha = hashlib.sha256(f"{obs['observation_id']}-{i}".encode()).hexdigest()[:7]

        artifact = {
            "artifact_id": f"art_{i:03d}",
            "operator_id": obs["operator_id"],
            "observation_id": obs["observation_id"],
            "artifact_type": artifact_type,
            "file_path": file_path,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "commit_sha": commit_sha,
            "created_at": obs["timestamp"],
            "synthetic": True,
        }
        artifacts.append(artifact)

    artifacts.sort(key=lambda a: a["artifact_id"])
    return artifacts

# ---------------------------------------------------------------------------
# GAP 2: lineages.jsonl — 50 synthetic lineages
# ---------------------------------------------------------------------------

def compute_micro_eval(obs):
    """Compute Leverage, Yield, Token SNR, Construction, Upsilon from observation."""
    I = obs.get("input_tokens", 0) or 0
    O = obs.get("output_tokens", 0) or 0
    CR = obs.get("cache_read_tokens", 0) or 0
    CW = obs.get("cache_write_tokens", 0) or 0

    safe_I = I if I > 0 else 1
    leverage = O / safe_I
    yield_val = O / safe_I  # Yield = output / input (same as leverage at obs level)
    token_snr = O / (I + O) if (I + O) > 0 else 0.0
    construction = CW / O if O > 0 else 0.0
    upsilon = (CR * O) / (safe_I ** 2) if safe_I > 0 else 0.0
    log_leverage = 0.0
    if leverage > 0:
        import math
        log_leverage = math.log10(leverage)

    return {
        "leverage": round(leverage, 4),
        "yield": round(yield_val, 4),
        "token_snr": round(token_snr, 4),
        "construction": round(construction, 4),
        "upsilon": round(upsilon, 4),
        "log_leverage": round(log_leverage, 4),
    }

WORKFLOW_STAGES = ["discovery", "requirements", "architecture", "implementation", "testing", "review", "release"]

def generate_lineages(artifacts):
    """Generate 50 synthetic lineages linking observations -> artifacts -> outcomes."""
    # Group artifacts by operator
    artifacts_by_op = {}
    for a in artifacts:
        artifacts_by_op.setdefault(a["operator_id"], []).append(a)

    lineages = []
    lineage_ops = [op["operator_id"] for op in operators if op["operator_id"] in artifacts_by_op]
    random.shuffle(lineage_ops)
    lineage_ops = lineage_ops[:50]

    for i, op_id in enumerate(lineage_ops, 1):
        op_obs = obs_by_op.get(op_id, [])
        if len(op_obs) < 5:
            continue
        op_arts = artifacts_by_op.get(op_id, [])
        if not op_arts:
            continue

        # Pick 5 consecutive observations for the lineage chain
        start_idx = random.randint(0, max(0, len(op_obs) - 5))
        chain_obs = op_obs[start_idx:start_idx + 5]
        while len(chain_obs) < 5:
            chain_obs.append(op_obs[-1])

        # Pick an artifact from this operator
        artifact = random.choice(op_arts)

        # Compute micro eval from the transformation observation (3rd in chain)
        micro_eval = compute_micro_eval(chain_obs[2])

        outcome_id = f"out_{i:03d}"

        lineage = {
            "lineage_id": f"lin_{i:03d}",
            "operator_id": op_id,
            "workflow_id": "software_dev_v1",
            "workflow_stage": random.choice(WORKFLOW_STAGES),
            "state_a_observation_id": chain_obs[0]["observation_id"],
            "bi_action_observation_id": chain_obs[1]["observation_id"],
            "aai_transformation_observation_id": chain_obs[2]["observation_id"],
            "bi_redirection_observation_id": chain_obs[3]["observation_id"],
            "aai_extension_observation_id": chain_obs[4]["observation_id"],
            "committed_artifact_id": artifact["artifact_id"],
            "outcome_id": outcome_id,
            "micro_eval": micro_eval,
            "synthetic": True,
        }
        lineages.append(lineage)

    lineages.sort(key=lambda l: l["lineage_id"])
    return lineages

# ---------------------------------------------------------------------------
# outcomes.json — structured outcome objects
# ---------------------------------------------------------------------------

OUTCOME_TYPES = ["task_completed", "pr_merged", "bug_fixed", "feature_shipped", "doc_published", "test_passed"]
OUTCOME_STATUSES = ["success", "success", "success", "partial", "failure"]

def generate_outcomes(lineages):
    """Generate outcome objects linked to lineage artifacts."""
    outcomes = []
    for i, lin in enumerate(lineages, 1):
        outcome = {
            "outcome_id": lin["outcome_id"],
            "lineage_id": lin["lineage_id"],
            "operator_id": lin["operator_id"],
            "artifact_id": lin["committed_artifact_id"],
            "outcome_type": random.choice(OUTCOME_TYPES),
            "outcome_status": random.choice(OUTCOME_STATUSES),
            "external_quality_score": round(random.uniform(0.6, 0.98), 3),
            "cycle_time_minutes": random.randint(15, 480),
            "recorded_at": "2026-07-30T18:00:00Z",
            "synthetic": True,
        }
        outcomes.append(outcome)
    return outcomes

# ---------------------------------------------------------------------------
# GAP 3: Additional workflows + stage events
# ---------------------------------------------------------------------------

NEW_WORKFLOWS = [
    {
        "workflow_id": "design_sprint_v1",
        "name": "Design Sprint",
        "stages": [
            {"stage_id": "discover", "order": 1, "name": "discover"},
            {"stage_id": "define", "order": 2, "name": "define"},
            {"stage_id": "ideate", "order": 3, "name": "ideate"},
            {"stage_id": "prototype", "order": 4, "name": "prototype"},
            {"stage_id": "test", "order": 5, "name": "test"},
        ],
        "applicable_teams": ["Product / Design", "Product Engineering"],
    },
    {
        "workflow_id": "data_analysis_v1",
        "name": "Data Analysis",
        "stages": [
            {"stage_id": "question", "order": 1, "name": "question"},
            {"stage_id": "query", "order": 2, "name": "query"},
            {"stage_id": "analyze", "order": 3, "name": "analyze"},
            {"stage_id": "visualize", "order": 4, "name": "visualize"},
            {"stage_id": "communicate", "order": 5, "name": "communicate"},
        ],
        "applicable_teams": ["Data / Analytics", "Operations / GTM"],
    },
    {
        "workflow_id": "incident_response_v1",
        "name": "Incident Response",
        "stages": [
            {"stage_id": "detect", "order": 1, "name": "detect"},
            {"stage_id": "triage", "order": 2, "name": "triage"},
            {"stage_id": "resolve", "order": 3, "name": "resolve"},
            {"stage_id": "postmortem", "order": 4, "name": "postmortem"},
        ],
        "applicable_teams": ["Platform / Infrastructure", "Customer Engineering / Support"],
    },
]

def generate_new_workflows():
    """Return updated workflows.json content (existing + new)."""
    all_workflows = list(existing_workflows)
    for wf in NEW_WORKFLOWS:
        wf_entry = {
            "workflow_id": wf["workflow_id"],
            "name": wf["name"],
            "stages": wf["stages"],
        }
        all_workflows.append(wf_entry)
    return all_workflows

def generate_new_stage_events():
    """Generate stage events for the new workflows."""
    events = []
    for wf in NEW_WORKFLOWS:
        # Select operators from applicable teams
        applicable_ops = [
            op for op in operators
            if op["team"] in wf["applicable_teams"]
        ]
        # Each operator gets 3-7 stage events spread across the 30-day window
        for op in applicable_ops:
            num_events = random.randint(3, 7)
            stages = wf["stages"]
            for _ in range(num_events):
                stage = random.choice(stages)
                day = random.randint(1, 30)
                date_str = f"2026-07-{day:02d}"
                events.append({
                    "workflow_id": wf["workflow_id"],
                    "stage_id": stage["stage_id"],
                    "operator_id": op["operator_id"],
                    "date": date_str,
                    "time_spent_minutes": random.randint(30, 360),
                    "tasks_completed": random.randint(1, 12),
                    "external_quality_score": None,
                    "provisional_fit_demo": round(random.uniform(0.5, 0.95), 3),
                    "evidence_count": random.randint(1, 10),
                    "status": "SYNTHETIC_PROVISIONAL",
                    "synthetic": True,
                })
    return events

# ---------------------------------------------------------------------------
# PARTIAL 5: teams.json — explicit team structure
# ---------------------------------------------------------------------------

def generate_teams():
    """Generate explicit team structure with metadata."""
    teams = []
    for team_name, members in teams_map.items():
        # Derive a team_id from the team name
        team_id = team_name.lower().replace(" / ", "_").replace(" ", "_").replace("/", "_")
        platforms = {}
        for m in members:
            p = m["primary_platform"]
            platforms[p] = platforms.get(p, 0) + 1

        teams.append({
            "team_id": team_id,
            "name": team_name,
            "operator_count": len(members),
            "operator_ids": [m["operator_id"] for m in members],
            "primary_platforms": platforms,
            "synthetic": True,
        })
    return teams

# ---------------------------------------------------------------------------
# Write all files
# ---------------------------------------------------------------------------

def write_json(name, data):
    with open(DEMO_DIR / name, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  wrote {name} ({len(data) if isinstance(data, list) else 'object'})")

def write_jsonl(name, records):
    with open(DEMO_DIR / name, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"  wrote {name} ({len(records)} records)")

def append_jsonl(name, records):
    with open(DEMO_DIR / name, "a") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"  appended {len(records)} records to {name}")

def main():
    print("MOSES Enterprise Pilot Readiness — Q14 Gap Closure Generator")
    print(f"Seed: {SEED}")
    print()

    # GAP 1: artifacts
    print("GAP 1: Generating artifacts.jsonl (200 records)...")
    artifacts = generate_artifacts()
    write_jsonl("artifacts.jsonl", artifacts)

    # GAP 2: lineages
    print("GAP 2: Generating lineages.jsonl (50 records)...")
    lineages = generate_lineages(artifacts)
    write_jsonl("lineages.jsonl", lineages)

    # outcomes
    print("Generating outcomes.json...")
    outcomes = generate_outcomes(lineages)
    write_json("outcomes.json", outcomes)

    # GAP 3: workflows
    print("GAP 3: Updating workflows.json with 3 new workflows...")
    all_workflows = generate_new_workflows()
    write_json("workflows.json", all_workflows)

    print("GAP 3: Appending new stage events to stage_events.jsonl...")
    new_events = generate_new_stage_events()
    append_jsonl("stage_events.jsonl", new_events)

    # PARTIAL 5: teams
    print("PARTIAL 5: Generating teams.json...")
    teams = generate_teams()
    write_json("teams.json", teams)

    print()
    print("Done. All gap-closure data generated.")
    print(f"  artifacts: {len(artifacts)}")
    print(f"  lineages: {len(lineages)}")
    print(f"  outcomes: {len(outcomes)}")
    print(f"  workflows: {len(all_workflows)} (was {len(existing_workflows)}, +{len(NEW_WORKFLOWS)})")
    print(f"  new stage events: {len(new_events)}")
    print(f"  teams: {len(teams)}")

if __name__ == "__main__":
    main()
