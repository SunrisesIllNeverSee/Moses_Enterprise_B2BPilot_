"""Diagnostics — pattern engine + diagnosis engine.

P1: Pattern engine → diagnosis objects → intervention registry → pre/post verifier.

Architecture:
    diagnostics/pattern_engine.py  — detects patterns from measurements
    diagnostics/diagnosis_engine.py — generates Diagnosis objects from patterns
"""
from __future__ import annotations

from .pattern_engine import PatternEngine, DetectedPattern, PatternThresholds
from .diagnosis_engine import DiagnosisEngine

__all__ = ["PatternEngine", "DetectedPattern", "PatternThresholds", "DiagnosisEngine"]
