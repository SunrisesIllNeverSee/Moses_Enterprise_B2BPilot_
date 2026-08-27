"""MCP server — exposes pilot data to AI clients per `08_MCP_TOOL_SPEC.md`.

Resources:
    enterprise://pilot/{cohort_id}
    enterprise://cohort/{cohort_id}
    enterprise://operator/{operator_id}
    enterprise://metrics/registry
    enterprise://interventions/catalog
    enterprise://workflow/{workflow_id}

Read tools:
    get_pilot_status, get_operator_profile, compare_operator_to_reference,
    get_cohort_distribution, find_usage_operation_divergence, get_diagnostics,
    get_workflow_fit, get_intervention_status, verify_change, get_data_quality

Every tool response carries governance annotations (per `08` §Safety):
    synthetic/production marker, metric registry version, data window,
    reference version, privacy class, validation status.

The MCP server uses the FastMCP pattern from the MCP Python SDK.
If the SDK is not installed, the server can still be imported and the tool
functions called directly (useful for testing).
"""
from __future__ import annotations

from .server import mcp, main, call_tool_directly

__all__ = ["mcp", "main", "call_tool_directly"]
