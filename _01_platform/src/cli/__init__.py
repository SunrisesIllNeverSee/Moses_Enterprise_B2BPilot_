"""Enterprise CLI — command-line interface per `07_CLI_COMMAND_SPEC.md`.

The CLI is a thin wrapper over PilotService. It does NOT implement business
logic. All commands call the service layer.

Commands (per `07`):
    enterprise pilot init/status
    enterprise cohort list/show
    enterprise ingest claude/codex/fixture/validate
    enterprise score cohort/operator
    enterprise metrics explain/registry
    enterprise compare cohort/usage-operation/teams/models
    enterprise diagnose cohort/operator
    enterprise workflow show/fit
    enterprise intervention catalog/recommend
    enterprise verify operator/intervention
    enterprise export cohort/operator/pilot
    enterprise validate outcomes

All commands support --json for agent/MCP composition.
Every result declares metric-registry version.
Every comparison declares reference population/window.
Diagnostics label hypotheses.
Synthetic data labels remain visible.
"""
from __future__ import annotations

from .main import main

__all__ = ["main"]
