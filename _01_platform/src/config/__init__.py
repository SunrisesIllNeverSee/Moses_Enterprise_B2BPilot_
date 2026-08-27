"""Configuration package — bespoke pilot menu system."""
from __future__ import annotations
from .eval_registry import EvalFamily, EVAL_FAMILIES, get_eval, all_eval_ids, implemented_eval_ids
from .pilot_registry import CommercialPilot, COMMERCIAL_PILOTS, get_pilot, all_pilot_ids
from .configurator import PilotConfigurator
from .validation import ConfigValidator, ValidationResult
__all__ = [
    "EvalFamily", "EVAL_FAMILIES", "get_eval", "all_eval_ids", "implemented_eval_ids",
    "CommercialPilot", "COMMERCIAL_PILOTS", "get_pilot", "all_pilot_ids",
    "PilotConfigurator", "ConfigValidator", "ValidationResult",
]
