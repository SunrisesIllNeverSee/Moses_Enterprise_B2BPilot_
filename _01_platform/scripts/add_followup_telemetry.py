#!/usr/bin/env python3
"""Generate follow-up telemetry (Aug 1-15) for intervention operators.

The demo data has 30 days of July telemetry (the baseline window) but no
August data. Interventions start Aug 1 with 14-day follow-up windows, so
the pre/post verifier finds no follow-up observations and returns None
deltas. This script generates synthetic August telemetry for the 12
intervention operators, using the target follow-up metrics from
post_intervention_results.csv to derive token counts that produce those
metrics.

Metric formulas (from src/metrics/formulas.py):
    leverage = R / I
    yield    = (R * O) / (I^2)

Given target followup_leverage (L_f) and followup_yield (Y_f), and
keeping total input tokens I_f = I_baseline:
    R_f = L_f * I_f
    O_f = Y_f * I_f^2 / R_f = Y_f * I_f / L_f
    W_f = (W_b / R_b) * R_f   (preserve construction ratio)

Token totals are distributed across 14 daily rows using the same daily
proportion as the operator's July data (same platform/model per day).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "demo_data"


def main() -> int:
    # Load intervention operators + target follow-up metrics
    with open(DATA / "post_intervention_results.csv") as f:
        post_rows = list(csv.DictReader(f))
    with open(DATA / "interventions.csv") as f:
        iv_rows = list(csv.DictReader(f))

    iv_ops = {r["operator_id"] for r in iv_rows}
    target_metrics = {}
    for r in post_rows:
        target_metrics[r["operator_id"]] = {
            "followup_leverage": float(r["followup_leverage"]),
            "followup_yield": float(r["followup_yield"]),
        }

    # Load existing July telemetry
    with open(DATA / "daily_telemetry.csv") as f:
        telemetry = list(csv.DictReader(f))

    # Group July telemetry by operator
    by_op = defaultdict(list)
    for row in telemetry:
        by_op[row["operator_id"]].append(row)

    # Generate Aug 1-15 follow-up rows for each intervention operator
    followup_start = date(2026, 8, 1)
    followup_days = 14
    new_rows = []

    for op_id in sorted(iv_ops):
        july_rows = by_op.get(op_id, [])
        if not july_rows:
            print(f"  WARNING: no July telemetry for {op_id}, skipping")
            continue

        # July totals
        I_b = sum(int(r["input_tokens"]) for r in july_rows)
        O_b = sum(int(r["output_tokens"]) for r in july_rows)
        R_b = sum(int(r["cache_read_tokens"]) for r in july_rows)
        W_b = sum(int(r["cache_write_tokens"]) for r in july_rows)

        if I_b <= 0 or R_b <= 0:
            print(f"  WARNING: zero totals for {op_id}, skipping")
            continue

        targets = target_metrics.get(op_id)
        if not targets:
            print(f"  WARNING: no target metrics for {op_id}, skipping")
            continue

        L_f = targets["followup_leverage"]
        Y_f = targets["followup_yield"]

        # Compute follow-up totals
        I_f = I_b  # keep same total input
        R_f = L_f * I_f
        O_f = (Y_f * I_f) / L_f if L_f != 0 else O_b
        W_f = (W_b / R_b) * R_f if R_b > 0 else W_b

        # Round to integers
        I_f, O_f, R_f, W_f = int(round(I_f)), int(round(O_f)), int(round(R_f)), int(round(W_f))

        # Distribute across 14 days using July's daily proportions
        n_july = len(july_rows)
        # Use the first 14 July rows as the daily pattern (cycle if fewer)
        pattern_rows = july_rows[:followup_days]
        while len(pattern_rows) < followup_days:
            pattern_rows.extend(july_rows[:followup_days - len(pattern_rows)])

        # Compute daily fractions from the pattern
        pattern_I = [int(r["input_tokens"]) for r in pattern_rows]
        pattern_total_I = sum(pattern_I)
        if pattern_total_I == 0:
            pattern_total_I = 1

        for i in range(followup_days):
            d = followup_start.replace(day=i + 1)
            frac = pattern_I[i] / pattern_total_I
            row = {
                "date": d.isoformat(),
                "operator_id": op_id,
                "platform": pattern_rows[i]["platform"],
                "model": pattern_rows[i]["model"],
                "input_tokens": max(1, int(round(I_f * frac))),
                "output_tokens": max(1, int(round(O_f * frac))),
                "cache_read_tokens": max(1, int(round(R_f * frac))),
                "cache_write_tokens": max(1, int(round(W_f * frac))),
                "synthetic": "True",
            }
            new_rows.append(row)

    # Append to daily_telemetry.csv
    fieldnames = ["date", "operator_id", "platform", "model",
                  "input_tokens", "output_tokens", "cache_read_tokens",
                  "cache_write_tokens", "synthetic"]
    with open(DATA / "daily_telemetry.csv", "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        for row in new_rows:
            w.writerow(row)
    print(f"  Appended {len(new_rows)} follow-up rows to daily_telemetry.csv")

    # Regenerate observations.jsonl (full rewrite from daily_telemetry.csv)
    with open(DATA / "daily_telemetry.csv") as f:
        all_telemetry = list(csv.DictReader(f))

    obs_lines = []
    for idx, row in enumerate(all_telemetry, 1):
        obs = {
            "observation_id": f"obs_{idx:06d}",
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
        }
        obs_lines.append(json.dumps(obs, ensure_ascii=False))

    with open(DATA / "observations.jsonl", "w") as f:
        f.write("\n".join(obs_lines) + "\n")
    print(f"  Regenerated observations.jsonl: {len(obs_lines)} observations")

    # Regenerate daily_aggregates.csv
    daily_agg_rows = []
    for row in all_telemetry:
        daily_agg_rows.append({
            "date": row["date"],
            "operator_id": row["operator_id"],
            "input_tokens": int(row["input_tokens"]),
            "output_tokens": int(row["output_tokens"]),
            "cache_read_tokens": int(row["cache_read_tokens"]),
            "cache_write_tokens": int(row["cache_write_tokens"]),
            "sessions": 1,
            "active": True,
            "synthetic": True,
        })
    with open(DATA / "daily_aggregates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "operator_id", "input_tokens",
                          "output_tokens", "cache_read_tokens", "cache_write_tokens",
                          "sessions", "active", "synthetic"])
        w.writeheader()
        w.writerows(daily_agg_rows)
    print(f"  Regenerated daily_aggregates.csv: {len(daily_agg_rows)} rows")

    return 0


if __name__ == "__main__":
    sys.exit(main())
