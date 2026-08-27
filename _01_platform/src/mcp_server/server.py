"""MCP server implementation — resources + read tools per `08`.

Uses FastMCP from the MCP Python SDK if available. If not, falls back to
a direct-call mode where tool functions can be invoked programmatically.

All tools call PilotService — no business logic in the MCP layer.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import the MCP SDK. The local package is named `mcp_server` (not `mcp`)
# to avoid shadowing the installed `mcp` SDK package.
# MCP SDK v2.0.0 uses MCPServer; v1.x uses FastMCP.
try:
    from mcp.server import MCPServer as _MCPBase
    _HAS_MCP_SDK = True
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as _MCPBase  # type: ignore
        _HAS_MCP_SDK = True
    except ImportError:
        _HAS_MCP_SDK = False
        _MCPBase = None  # type: ignore

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from service import PilotService
from governance import (
    decision_use_for_diagnosis,
    decision_use_for_intervention,
)

# Singleton service instance
_svc: Optional[PilotService] = None


def _get_service() -> PilotService:
    global _svc
    if _svc is None:
        _svc = PilotService()
    return _svc


def _governance(svc: PilotService) -> dict:
    """Governance annotations required by `08` for every tool response."""
    return {
        "synthetic": True,
        "metric_registry_version": svc.engine.registry.registry_version,
        "data_window": {
            "start": svc.cohort.window_start.isoformat(),
            "end": svc.cohort.window_end.isoformat(),
        },
        "reference_version": svc.reference_population.version,
        "privacy_class": "pseudonymous_synthetic",
        "validation_status": "synthetic_demo",
    }


def _decision_use_developmental() -> str:
    """Decision-use label for diagnostic surfaces (DEVELOPMENTAL).

    Delegates to the canonical governance helper so the mapping lives
    in one place (src/governance/decision_use.py).
    """
    return decision_use_for_diagnosis(None).label()


def _decision_use_workflow() -> str:
    """Decision-use label for intervention/experiment surfaces (WORKFLOW_EXPERIMENTATION).

    Delegates to the canonical governance helper so the mapping lives
    in one place (src/governance/decision_use.py).
    """
    return decision_use_for_intervention(None).label()


# ── Tool implementations (pure functions, callable without MCP SDK) ──────

def get_pilot_status(cohort_id: str = "acme_50") -> dict:
    """Returns collection window, eligibility, providers, quality flags, registry versions."""
    svc = _get_service()
    data = svc.pilot_status()
    data.update(_governance(svc))
    return data


def get_operator_profile(operator_id: str, window: str = "30d") -> dict:
    """Returns raw totals, canonical measurements, percentiles, patterns, interventions."""
    svc = _get_service()
    profile = svc.operator_profile(operator_id)
    elig = svc.operator_eligibility(operator_id)
    profile["eligibility"] = elig.to_dict()
    profile.update(_governance(svc))
    profile["decision_use"] = _decision_use_developmental()
    return profile


def compare_operator_to_reference(
    operator_id: str, metric_ids: Optional[List[str]] = None, reference_id: str = "public-field-v1"
) -> dict:
    """Compare an operator's metrics to the reference population."""
    svc = _get_service()
    data = svc.compare_operator_to_reference(operator_id, metric_ids)
    data.update(_governance(svc))
    return data


def get_cohort_distribution(cohort_id: str = "acme_50", metric_id: str = "leverage") -> dict:
    """Get the distribution of a metric across the cohort."""
    svc = _get_service()
    dist = svc.cohort_distribution_for_metric(metric_id)
    if dist is None:
        return {"error": f"Unknown metric: {metric_id}", **_governance(svc)}
    return {"distribution": dist.to_dict(), **_governance(svc)}


def find_usage_operation_divergence(
    cohort_id: str = "acme_50", operation_metric: str = "yield"
) -> dict:
    """Find operators with usage-vs-operation divergence."""
    svc = _get_service()
    results = svc.divergence()
    return {
        "divergence": [
            {
                "operator_id": r.operator_id,
                "usage_percentile": r.usage_percentile,
                "yield_percentile": r.yield_percentile,
                "leverage_percentile": r.leverage_percentile,
                "divergence_pp": r.divergence_pp,
                "divergence_class": r.divergence_class,
            }
            for r in results
        ],
        "counts": svc.divergence_counts(),
        **_governance(svc),
    }


def get_diagnostics(operator_id: str = "") -> dict:
    """Returns hypotheses with supporting measurements and confidence.

    MUST never return them as proven causes.
    """
    svc = _get_service()
    if operator_id:
        diags = svc.diagnoses_for(operator_id)
    else:
        diags = svc.diagnoses
    return {
        "diagnostics": [d.to_dict() for d in diags],
        "label": "HYPOTHESIS — these are not causal findings",
        "decision_use": _decision_use_developmental(),
        **_governance(svc),
    }


def get_workflow_fit(
    cohort_id: str = "acme_50", workflow_id: str = "software_dev_v1", operator_id: str = ""
) -> dict:
    """Returns workflow stage observations, sample sizes, uncertainty."""
    svc = _get_service()
    by_stage = svc.workflow_fit_by_stage()
    if operator_id:
        by_stage = {
            stage: [w for w in wobs if w.operator_id == operator_id]
            for stage, wobs in by_stage.items()
        }
    return {
        "workflow_id": svc.workflow.workflow_id,
        "stages": {
            stage: [
                {
                    "operator_id": w.operator_id,
                    "provisional_fit": w.provisional_fit,
                    "evidence_count": w.evidence_count,
                    "status": w.status,
                }
                for w in wobs
            ]
            for stage, wobs in by_stage.items()
        },
        **_governance(svc),
    }


def get_intervention_status(intervention_id: str = "") -> dict:
    """Returns assigned intervention and before/after state."""
    svc = _get_service()
    ivs = svc.interventions
    if intervention_id:
        ivs = [i for i in ivs if i.intervention_id == intervention_id]
    return {
        "interventions": [iv.to_dict() for iv in ivs],
        "decision_use": _decision_use_workflow(),
        **_governance(svc),
    }


def verify_change(operator_id: str = "", intervention_id: str = "") -> dict:
    """Computes declared pre/post metric deltas and optional outcome deltas."""
    svc = _get_service()
    if intervention_id:
        ivs = [i for i in svc.interventions if i.intervention_id == intervention_id]
        if not ivs:
            return {"error": f"Unknown intervention {intervention_id}", **_governance(svc)}
        operator_id = ivs[0].operator_id
    if not operator_id:
        return {"error": "Must specify operator_id or intervention_id", **_governance(svc)}

    ms = svc.score_operator(operator_id)
    elig = svc.operator_eligibility(operator_id)
    return {
        "operator_id": operator_id,
        "eligible": elig.passed,
        "eligibility_reason": elig.reason,
        "measurements": [m.to_dict() for m in ms],
        "decision_use": _decision_use_workflow(),
        **_governance(svc),
    }


def get_data_quality(cohort_id: str = "acme_50") -> dict:
    """Returns missingness, schema warnings, eligibility, provenance issues."""
    svc = _get_service()
    dq = svc.data_quality()
    summary = svc.data_quality_summary()
    return {
        "summary": summary,
        "checks": {
            check: [r.to_dict() for r in results[:20]]  # cap at 20 per check for response size
            for check, results in dq.items()
        },
        **_governance(svc),
    }


def get_composite_score(operator_id: str = "") -> dict:
    """Return the composite developmental score for an operator.

    Per `21` §8: "one proprietary composite employee score."
    Combines canonical metrics into a 0-100 developmental index.
    Labeled DEVELOPMENTAL - never PERSONNEL.
    """
    svc = _get_service()
    if not operator_id:
        return {"error": "operator_id is required", **_governance(svc)}
    try:
        score = svc.composite_score(operator_id)
        return {
            **score.to_dict(),
            **_governance(svc),
        }
    except Exception as e:
        return {"error": str(e), **_governance(svc)}


def get_composite_score_summary() -> dict:
    """Return cohort-level composite score distribution statistics.

    Returns aggregate stats (min, max, median, mean, quartiles) without
    individual operator rankings. Per governance: cohort-level only.
    """
    svc = _get_service()
    summary = svc.composite_score_summary()
    return {
        **summary,
        **_governance(svc),
    }


def get_executive_dashboard() -> dict:
    """Return the executive dashboard as self-contained HTML.

    Per `21` §8: "polished executive dashboard."
    Returns HTML with embedded CSS/JS - no external dependencies.
    """
    svc = _get_service()
    from reporting import generate_executive_dashboard
    html = generate_executive_dashboard(svc)
    return {
        "dashboard_html": html,
        "size_bytes": len(html),
        "label": "DEVELOPMENTAL - executive dashboard from synthetic demo data",
        **_governance(svc),
    }


def get_cohort_overview(cohort_id: str = "acme_50") -> dict:
    """Cohort-level overview: distributions, medians, divergence counts.

    Per `08` resource `enterprise://cohort/{cohort_id}`: returns
    cohort-level distributions, medians, and divergence class counts.
    """
    svc = _get_service()
    dists = svc.cohort_distributions()
    medians = svc.cohort_medians()
    div_counts = svc.divergence_counts()
    return {
        "cohort_id": svc.cohort.cohort_id,
        "medians": medians,
        "distributions": {k: v.to_dict() for k, v in dists.items()},
        "divergence_counts": div_counts,
        **_governance(svc),
    }


# ── Write tools (P1+) — require authorization ────────────────────────────

def assign_intervention(
    operator_id: str,
    catalog_id: str,
    target_metric: str,
    followup_days: int,
    authorized_by: str = "",
    reason_pattern: str = "",
    intervention_id: str = "",
) -> dict:
    """Assign a new intervention to an operator.

    Per `08` §Write tools (P1+): requires explicit target and authorization.
    Refuses to execute without `authorized_by` parameter.

    Per P1: intervention declares target metric/window before follow-up.
    Delegates to PilotService.assign_intervention which persists the
    intervention in service state so subsequent read tools observe it.
    """
    svc = _get_service()
    if not authorized_by:
        return {
            "error": "authorized_by is required for write tools (P1+: no unauthorized writes)",
            "label": "BLOCKED — authorization required",
            **_governance(svc),
        }
    if not target_metric:
        return {
            "error": "target_metric is required (P1: intervention declares target metric before follow-up)",
            **_governance(svc),
        }
    if not followup_days or followup_days <= 0:
        return {
            "error": "followup_days must be > 0 (P1: intervention declares window before follow-up)",
            **_governance(svc),
        }

    try:
        iv = svc.assign_intervention(
            operator_id=operator_id,
            catalog_id=catalog_id,
            target_metric=target_metric,
            followup_days=followup_days,
            reason_pattern=reason_pattern,
            intervention_id=intervention_id,
        )
        return {
            "intervention": iv.to_dict(),
            "authorized_by": authorized_by,
            "label": "EXPERIMENT — requires human approval before execution",
            "decision_use": _decision_use_workflow(),
            **_governance(svc),
        }
    except Exception as e:
        return {"error": str(e), **_governance(svc)}


def close_intervention(
    intervention_id: str,
    outcome: str,
    authorized_by: str = "",
) -> dict:
    """Close an intervention with a declared outcome.

    Per `08` §Write tools (P1+): requires authorization.
    Per P1: "intervention failure is representable and reportable."

    Outcome must be one of: SUCCESS, PARTIAL, NO_EFFECT, NEGATIVE.
    Delegates to PilotService.close_intervention which persists the
    closure in service state so subsequent read tools observe it.
    """
    svc = _get_service()
    if not authorized_by:
        return {
            "error": "authorized_by is required for write tools (P1+: no unauthorized writes)",
            "label": "BLOCKED — authorization required",
            **_governance(svc),
        }

    valid_outcomes = {"SUCCESS", "PARTIAL", "NO_EFFECT", "NEGATIVE"}
    if outcome not in valid_outcomes:
        return {
            "error": f"outcome must be one of {sorted(valid_outcomes)}, got: {outcome}",
            **_governance(svc),
        }

    try:
        closed = svc.close_intervention(intervention_id, outcome)
        return {
            "intervention": closed.to_dict(),
            "authorized_by": authorized_by,
            "label": "CLOSED — outcome recorded",
            "decision_use": _decision_use_workflow(),
            **_governance(svc),
        }
    except ValueError as e:
        return {"error": str(e), **_governance(svc)}
    except Exception as e:
        return {"error": str(e), **_governance(svc)}


def create_experiment(
    operator_id: str,
    target_metric: str,
    window_days: int,
    authorized_by: str = "",
    description: str = "",
) -> dict:
    """Create a predeclared experiment with target metric and window.

    Per `08` §Write tools (P1+): requires authorization.
    Per P2: experiments are predeclared with metrics before execution.
    Delegates to PilotService.create_experiment which persists the
    experiment in service state so subsequent read tools can enumerate it.
    """
    svc = _get_service()
    if not authorized_by:
        return {
            "error": "authorized_by is required for write tools (P1+: no unauthorized writes)",
            "label": "BLOCKED — authorization required",
            **_governance(svc),
        }
    if not target_metric:
        return {
            "error": "target_metric is required (experiment must predeclare target metric)",
            **_governance(svc),
        }
    if not window_days or window_days <= 0:
        return {
            "error": "window_days must be > 0",
            **_governance(svc),
        }

    experiment = svc.create_experiment(
        operator_id=operator_id,
        target_metric=target_metric,
        window_days=window_days,
        description=description,
    )
    return {
        **experiment,
        "authorized_by": authorized_by,
        "decision_use": _decision_use_workflow(),
        **_governance(svc),
    }


def record_workflow_observation(
    operator_id: str,
    stage_id: str,
    authorized_by: str = "",
    workflow_id: str = "",
    provisional_fit: float = 0.0,
    evidence_count: int = 0,
    time_spent_minutes: float = 0.0,
    tasks_completed: int = 0,
    external_quality_score: float = 0.0,
    status: str = "provisional",
) -> dict:
    """Record a workflow stage observation for an operator.

    Per `08` §Write tools (P1+): requires authorization.
    The observation is persisted so subsequent read tools (get_workflow_fit)
    observe it.
    """
    svc = _get_service()
    if not authorized_by:
        return {
            "error": "authorized_by is required for write tools (P1+: no unauthorized writes)",
            "label": "BLOCKED — authorization required",
            **_governance(svc),
        }
    if not operator_id:
        return {"error": "operator_id is required", **_governance(svc)}
    if not stage_id:
        return {"error": "stage_id is required", **_governance(svc)}

    try:
        wobs = svc.record_workflow_observation(
            operator_id=operator_id,
            stage_id=stage_id,
            workflow_id=workflow_id,
            provisional_fit=provisional_fit if provisional_fit else None,
            evidence_count=evidence_count,
            time_spent_minutes=time_spent_minutes,
            tasks_completed=tasks_completed,
            external_quality_score=external_quality_score if external_quality_score else None,
            status=status,
        )
        return {
            "observation": wobs.to_dict(),
            "authorized_by": authorized_by,
            "label": "EXPERIMENT — workflow stage observation recorded",
            "decision_use": _decision_use_workflow(),
            **_governance(svc),
        }
    except Exception as e:
        return {"error": str(e), **_governance(svc)}


def attach_outcome_dataset(
    source_path: str,
    authorized_by: str = "",
    operator_id: str = "",
) -> dict:
    """Attach an external outcome dataset for association analysis.

    Per `08` §Write tools (P1+): requires authorization.
    Per P2: outcome joins remain separately governed and labeled
    ASSOCIATION, never CAUSATION.
    """
    svc = _get_service()
    if not authorized_by:
        return {
            "error": "authorized_by is required for write tools (P1+: no unauthorized writes)",
            "label": "BLOCKED — authorization required",
            **_governance(svc),
        }
    if not source_path:
        return {"error": "source_path is required", **_governance(svc)}

    try:
        result = svc.attach_outcome_dataset(
            source_path=source_path,
            attached_by=authorized_by,
            operator_id=operator_id or None,
        )
        return {
            **result,
            "authorized_by": authorized_by,
            "decision_use": _decision_use_workflow(),
            **_governance(svc),
        }
    except FileNotFoundError as e:
        return {"error": str(e), **_governance(svc)}
    except Exception as e:
        return {"error": str(e), **_governance(svc)}


# ── Configuration tools (bespoke pilot menu system) ──────────────────────

def list_pilot_options() -> dict:
    """List all 12 commercial pilots and 15 eval families for configuration."""
    from config import COMMERCIAL_PILOTS, EVAL_FAMILIES
    pilots = [
        {
            "pilot_id": pid, "name": p.name, "question": p.question,
            "best_buyer": p.best_buyer, "eval_families": p.eval_families,
            "deployment_level": p.deployment_level,
        }
        for pid, p in COMMERCIAL_PILOTS.items()
    ]
    evals = [
        {
            "eval_id": eid, "name": e.name, "description": e.description,
            "implemented": e.implemented, "implementation_status": e.implementation_status,
        }
        for eid, e in EVAL_FAMILIES.items()
    ]
    return {"pilots": pilots, "eval_families": evals}


def create_pilot_configuration(
    pilot_id: str = "",
    eval_ids: str = "",
    name: str = "",
    description: str = "",
    deployment_level: int = 1,
    gates_enabled: bool = False,
    outcome_join_enabled: bool = False,
    outcome_csv_path: str = "",
    authorized_by: str = "",
    created_by: str = "",
) -> dict:
    """Create a pilot configuration from a commercial pilot ID or à la carte eval IDs.

    If pilot_id is provided, creates an outcome-packaged configuration.
    If eval_ids is provided (comma-separated), creates an à la carte configuration.
    """
    from config import PilotConfigurator
    if pilot_id:
        cfg = PilotConfigurator.from_outcome(
            pilot_id=pilot_id, name=name, description=description,
            gates_enabled=gates_enabled,
            outcome_join_enabled=outcome_join_enabled,
            outcome_csv_path=outcome_csv_path,
            authorized_by=authorized_by, created_by=created_by,
        )
    elif eval_ids:
        eid_list = [e.strip() for e in eval_ids.split(",") if e.strip()]
        cfg = PilotConfigurator.from_alacarte(
            eval_ids=eid_list, name=name, description=description,
            deployment_level=deployment_level, gates_enabled=gates_enabled,
            outcome_join_enabled=outcome_join_enabled,
            outcome_csv_path=outcome_csv_path,
            authorized_by=authorized_by, created_by=created_by,
        )
    else:
        return {"error": "Provide either pilot_id or eval_ids."}
    return cfg.to_dict()


def validate_pilot_configuration(config_json: str = "", file_path: str = "") -> dict:
    """Validate a pilot configuration from JSON string or file path."""
    from config import ConfigValidator, PilotConfigurator
    from domain import PilotConfiguration
    if file_path:
        cfg = PilotConfigurator.load(file_path)
    elif config_json:
        cfg = PilotConfiguration.from_json(config_json)
    else:
        return {"error": "Provide either config_json or file_path."}
    return ConfigValidator.validate(cfg).to_dict()


# ── Operator×System and Lineage/Outcome tools ────────────────────────────

def get_operator_system_decomposition(operator_id: str = "") -> dict:
    """Decompose observed metrics into operator/system/interaction effects.

    Per Jaimie's review §2: the deepest intellectual value. Decomposes
    each metric into operator effect, system effect, and the
    operator×system interaction residual.

    If operator_id is provided, highlights that operator. If empty,
    returns cohort-level decomposition.
    """
    svc = _get_service()
    data = svc.operator_system_decomposition(operator_id=operator_id)
    return {"decomposition": data, **_governance(svc)}


def get_lineage_chain(operator_id: str) -> dict:
    """Return the full lineage chain for an operator.

    Connects observations -> transformations -> artifact -> outcome
    per the BI -> AAI -> committed-state -> outcome sequence.
    """
    svc = _get_service()
    if not operator_id:
        return {"error": "operator_id is required", **_governance(svc)}
    data = svc.lineage_chain(operator_id)
    return {"lineage": data, **_governance(svc)}


def get_lineage_summary() -> dict:
    """Return cohort-level lineage summary."""
    svc = _get_service()
    data = svc.lineage_summary()
    return {"lineage_summary": data, **_governance(svc)}


def get_outcome_correlation() -> dict:
    """Correlate operating patterns (micro_eval) with outcomes.

    All results are labeled ASSOCIATION with evidence grade
    OBSERVATIONAL — never CAUSATION.
    """
    svc = _get_service()
    data = svc.outcome_correlation()
    return {"outcome_correlation": data, **_governance(svc)}


def get_org_topology() -> dict:
    """Return the organization-level AI topology map.

    Team-level metric distributions, capability concentration (Gini),
    platform adoption, single-point-of-failure detection, and
    cross-team complementarity. This is a structural map, NOT a ranking.
    """
    svc = _get_service()
    data = svc.org_topology()
    return {**data, **_governance(svc)}


def get_operator_similarity(operator_id: str, n_neighbors: int = 5) -> dict:
    """Find the nearest comparable operators by metric profile.

    Uses percentile-rank normalization and Euclidean distance across
    the 5 canonical metrics. This is metric similarity, NOT a
    personality match.
    """
    svc = _get_service()
    if not operator_id:
        return {"error": "operator_id is required", **_governance(svc)}
    data = svc.operator_similarity(operator_id, n_neighbors=n_neighbors)
    return {**data, **_governance(svc)}


# ── Tool registry for direct invocation ──────────────────────────────────

TOOL_REGISTRY = {
    "get_pilot_status": get_pilot_status,
    "get_operator_profile": get_operator_profile,
    "compare_operator_to_reference": compare_operator_to_reference,
    "get_cohort_distribution": get_cohort_distribution,
    "find_usage_operation_divergence": find_usage_operation_divergence,
    "get_diagnostics": get_diagnostics,
    "get_workflow_fit": get_workflow_fit,
    "get_intervention_status": get_intervention_status,
    "verify_change": verify_change,
    "get_data_quality": get_data_quality,
    "get_composite_score": get_composite_score,
    "get_composite_score_summary": get_composite_score_summary,
    "get_executive_dashboard": get_executive_dashboard,
    "assign_intervention": assign_intervention,
    "close_intervention": close_intervention,
    "create_experiment": create_experiment,
    "record_workflow_observation": record_workflow_observation,
    "attach_outcome_dataset": attach_outcome_dataset,
    "list_pilot_options": list_pilot_options,
    "create_pilot_configuration": create_pilot_configuration,
    "validate_pilot_configuration": validate_pilot_configuration,
    # Operator×System and Lineage/Outcome
    "get_operator_system_decomposition": get_operator_system_decomposition,
    "get_lineage_chain": get_lineage_chain,
    "get_lineage_summary": get_lineage_summary,
    "get_outcome_correlation": get_outcome_correlation,
    # Org Topology and Operator Similarity
    "get_org_topology": get_org_topology,
    "get_operator_similarity": get_operator_similarity,
}


def call_tool_directly(tool_name: str, **kwargs) -> dict:
    """Call a tool function directly (without MCP SDK).

    Useful for testing and for environments without the MCP SDK.
    """
    fn = TOOL_REGISTRY.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool: {tool_name}. Available: {list(TOOL_REGISTRY)}"}
    return fn(**kwargs)


# ── MCP server (only if SDK is installed) ────────────────────────────────

if _HAS_MCP_SDK:
    mcp = _MCPBase("Enterprise Operator Intelligence")

    @mcp.tool()
    def tool_get_pilot_status(cohort_id: str = "acme_50") -> str:
        """Returns collection window, eligibility, providers, quality flags, registry versions."""
        return json.dumps(get_pilot_status(cohort_id), indent=2)

    @mcp.tool()
    def tool_get_operator_profile(operator_id: str, window: str = "30d") -> str:
        """Returns raw totals, canonical measurements, percentiles, patterns, interventions."""
        return json.dumps(get_operator_profile(operator_id, window), indent=2)

    @mcp.tool()
    def tool_compare_operator_to_reference(
        operator_id: str, metric_ids: str = "", reference_id: str = "public-field-v1"
    ) -> str:
        """Compare an operator's metrics to the reference population."""
        ids = metric_ids.split(",") if metric_ids else None
        return json.dumps(compare_operator_to_reference(operator_id, ids, reference_id), indent=2)

    @mcp.tool()
    def tool_get_cohort_distribution(cohort_id: str = "acme_50", metric_id: str = "leverage") -> str:
        """Get the distribution of a metric across the cohort."""
        return json.dumps(get_cohort_distribution(cohort_id, metric_id), indent=2)

    @mcp.tool()
    def tool_find_usage_operation_divergence(
        cohort_id: str = "acme_50", operation_metric: str = "yield"
    ) -> str:
        """Find operators with usage-vs-operation divergence."""
        return json.dumps(find_usage_operation_divergence(cohort_id, operation_metric), indent=2)

    @mcp.tool()
    def tool_get_diagnostics(operator_id: str = "") -> str:
        """Returns hypotheses with supporting measurements and confidence."""
        return json.dumps(get_diagnostics(operator_id), indent=2)

    @mcp.tool()
    def tool_get_workflow_fit(
        cohort_id: str = "acme_50", workflow_id: str = "software_dev_v1", operator_id: str = ""
    ) -> str:
        """Returns workflow stage observations, sample sizes, uncertainty."""
        return json.dumps(get_workflow_fit(cohort_id, workflow_id, operator_id), indent=2)

    @mcp.tool()
    def tool_get_intervention_status(intervention_id: str = "") -> str:
        """Returns assigned intervention and before/after state."""
        return json.dumps(get_intervention_status(intervention_id), indent=2)

    @mcp.tool()
    def tool_verify_change(operator_id: str = "", intervention_id: str = "") -> str:
        """Computes declared pre/post metric deltas and optional outcome deltas."""
        return json.dumps(verify_change(operator_id, intervention_id), indent=2)

    @mcp.tool()
    def tool_get_data_quality(cohort_id: str = "acme_50") -> str:
        """Returns missingness, schema warnings, eligibility, provenance issues."""
        return json.dumps(get_data_quality(cohort_id), indent=2)

    @mcp.tool()
    def tool_get_composite_score(operator_id: str = "") -> str:
        """Return the composite developmental score (0-100) for an operator."""
        return json.dumps(get_composite_score(operator_id), indent=2)

    @mcp.tool()
    def tool_get_composite_score_summary() -> str:
        """Return cohort-level composite score distribution statistics."""
        return json.dumps(get_composite_score_summary(), indent=2)

    @mcp.tool()
    def tool_get_executive_dashboard() -> str:
        """Return the executive dashboard as self-contained HTML."""
        return json.dumps(get_executive_dashboard(), indent=2)

    # ── Write tools (P1+) — require authorization ────────────────────────

    @mcp.tool()
    def tool_assign_intervention(
        operator_id: str,
        catalog_id: str,
        target_metric: str,
        followup_days: int,
        authorized_by: str = "",
        reason_pattern: str = "",
        intervention_id: str = "",
    ) -> str:
        """Assign a new intervention to an operator. Requires authorized_by."""
        return json.dumps(
            assign_intervention(
                operator_id=operator_id,
                catalog_id=catalog_id,
                target_metric=target_metric,
                followup_days=followup_days,
                authorized_by=authorized_by,
                reason_pattern=reason_pattern,
                intervention_id=intervention_id,
            ),
            indent=2,
        )

    @mcp.tool()
    def tool_close_intervention(
        intervention_id: str,
        outcome: str,
        authorized_by: str = "",
    ) -> str:
        """Close an intervention with a declared outcome. Requires authorized_by."""
        return json.dumps(
            close_intervention(
                intervention_id=intervention_id,
                outcome=outcome,
                authorized_by=authorized_by,
            ),
            indent=2,
        )

    @mcp.tool()
    def tool_create_experiment(
        operator_id: str,
        target_metric: str,
        window_days: int,
        authorized_by: str = "",
        description: str = "",
    ) -> str:
        """Create a predeclared experiment. Requires authorized_by."""
        return json.dumps(
            create_experiment(
                operator_id=operator_id,
                target_metric=target_metric,
                window_days=window_days,
                authorized_by=authorized_by,
                description=description,
            ),
            indent=2,
        )

    @mcp.tool()
    def tool_record_workflow_observation(
        operator_id: str,
        stage_id: str,
        authorized_by: str = "",
        workflow_id: str = "",
        provisional_fit: float = 0.0,
        evidence_count: int = 0,
        time_spent_minutes: float = 0.0,
        tasks_completed: int = 0,
        external_quality_score: float = 0.0,
        status: str = "provisional",
    ) -> str:
        """Record a workflow stage observation. Requires authorized_by."""
        return json.dumps(
            record_workflow_observation(
                operator_id=operator_id,
                stage_id=stage_id,
                authorized_by=authorized_by,
                workflow_id=workflow_id,
                provisional_fit=provisional_fit,
                evidence_count=evidence_count,
                time_spent_minutes=time_spent_minutes,
                tasks_completed=tasks_completed,
                external_quality_score=external_quality_score,
                status=status,
            ),
            indent=2,
        )

    @mcp.tool()
    def tool_attach_outcome_dataset(
        source_path: str,
        authorized_by: str = "",
        operator_id: str = "",
    ) -> str:
        """Attach an external outcome dataset. Requires authorized_by."""
        return json.dumps(
            attach_outcome_dataset(
                source_path=source_path,
                authorized_by=authorized_by,
                operator_id=operator_id,
            ),
            indent=2,
        )

    # Configuration tools (bespoke pilot menu system)
    @mcp.tool()
    def tool_list_pilot_options() -> str:
        """List all 12 commercial pilots and 15 eval families for configuration."""
        return json.dumps(list_pilot_options(), indent=2)

    @mcp.tool()
    def tool_create_pilot_configuration(
        pilot_id: str = "",
        eval_ids: str = "",
        name: str = "",
        description: str = "",
        deployment_level: int = 1,
        gates_enabled: bool = False,
        outcome_join_enabled: bool = False,
        outcome_csv_path: str = "",
        authorized_by: str = "",
        created_by: str = "",
    ) -> str:
        """Create a pilot configuration from a commercial pilot ID or à la carte eval IDs."""
        return json.dumps(
            create_pilot_configuration(
                pilot_id=pilot_id, eval_ids=eval_ids, name=name, description=description,
                deployment_level=deployment_level, gates_enabled=gates_enabled,
                outcome_join_enabled=outcome_join_enabled, outcome_csv_path=outcome_csv_path,
                authorized_by=authorized_by, created_by=created_by,
            ),
            indent=2,
        )

    @mcp.tool()
    def tool_validate_pilot_configuration(
        config_json: str = "",
        file_path: str = "",
    ) -> str:
        """Validate a pilot configuration from JSON string or file path."""
        return json.dumps(
            validate_pilot_configuration(config_json=config_json, file_path=file_path),
            indent=2,
        )

    # Operator×System and Lineage/Outcome tools

    @mcp.tool()
    def tool_get_operator_system_decomposition(operator_id: str = "") -> str:
        """Decompose metrics into operator/system/interaction effects."""
        return json.dumps(get_operator_system_decomposition(operator_id=operator_id), indent=2)

    @mcp.tool()
    def tool_get_lineage_chain(operator_id: str) -> str:
        """Return the full lineage chain for an operator."""
        return json.dumps(get_lineage_chain(operator_id=operator_id), indent=2)

    @mcp.tool()
    def tool_get_lineage_summary() -> str:
        """Return cohort-level lineage summary."""
        return json.dumps(get_lineage_summary(), indent=2)

    @mcp.tool()
    def tool_get_outcome_correlation() -> str:
        """Correlate operating patterns with outcomes (ASSOCIATION, not causation)."""
        return json.dumps(get_outcome_correlation(), indent=2)

    @mcp.tool()
    def tool_get_org_topology() -> str:
        """Organization-level AI topology map — teams, concentration, platforms, SPOF."""
        return json.dumps(get_org_topology(), indent=2)

    @mcp.tool()
    def tool_get_operator_similarity(operator_id: str, n_neighbors: int = 5) -> str:
        """Find nearest comparable operators by metric profile (not personality match)."""
        return json.dumps(get_operator_similarity(operator_id, n_neighbors=n_neighbors), indent=2)

    # Resources
    @mcp.resource("enterprise://pilot/{cohort_id}")
    def resource_pilot(cohort_id: str) -> str:
        return json.dumps(get_pilot_status(cohort_id), indent=2)

    @mcp.resource("enterprise://cohort/{cohort_id}")
    def resource_cohort(cohort_id: str) -> str:
        """Cohort-level overview: distributions, medians, divergence counts."""
        return json.dumps(get_cohort_overview(cohort_id), indent=2)

    @mcp.resource("enterprise://operator/{operator_id}")
    def resource_operator(operator_id: str) -> str:
        return json.dumps(get_operator_profile(operator_id), indent=2)

    @mcp.resource("enterprise://metrics/registry")
    def resource_metrics_registry() -> str:
        svc = _get_service()
        reg = svc.engine.registry
        return json.dumps({
            "registry_version": reg.registry_version,
            "canonical_metric_ids": reg.canonical_metric_ids(),
        }, indent=2)

    @mcp.resource("enterprise://interventions/catalog")
    def resource_intervention_catalog() -> str:
        from domain.intervention import INTERVENTION_CATALOG
        return json.dumps(INTERVENTION_CATALOG, indent=2)

    @mcp.resource("enterprise://workflow/{workflow_id}")
    def resource_workflow(workflow_id: str) -> str:
        svc = _get_service()
        return json.dumps(svc.workflow.to_dict(), indent=2)

else:
    mcp = None  # type: ignore


def main():
    """Run the MCP server (requires MCP SDK)."""
    if not _HAS_MCP_SDK:
        print("MCP Python SDK not installed. Install with: pip install mcp", file=sys.stderr)
        print("Tools are still callable directly via call_tool_directly().", file=sys.stderr)
        sys.exit(1)
    mcp.run()


if __name__ == "__main__":
    main()
