"""Commercial pilot registry — codifies the 12 commercial pilot products."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass(frozen=True, slots=True)
class CommercialPilot:
    pilot_id: str
    name: str
    question: str
    best_buyer: str
    when_to_pitch: str
    eval_families: List[str]
    deployment_level: int
    description: str = ""
    deliverables: List[str] = field(default_factory=list)

COMMERCIAL_PILOTS: Dict[str, CommercialPilot] = {
    "1": CommercialPilot("1","AI Workforce Operating Baseline","What does our AI workforce actually look like?","Head of AI / Transformation","Best first wedge when AI is already deployed but capability is invisible.",["EVAL-001","EVAL-002","EVAL-003","EVAL-004","EVAL-006"],1,"The foundational baseline pilot."),
    "2": CommercialPilot("2","AI Capability Distribution","Do we have organizational capability or a few power users?","Head of AI / Transformation / BU leader","When leadership suspects the AI program depends on a few people.",["EVAL-006","EVAL-010"],1,"Reveals whether capability is distributed or concentrated."),
    "3": CommercialPilot("3","AI Adoption & Adaptation","Are people adapting, or simply using the tools?","Transformation / AI Enablement / L&D","Best after a recent AI rollout or mandate.",["EVAL-004","EVAL-015"],1,"Distinguishes adoption from adaptation."),
    "4": CommercialPilot("4","AI Training Evaluation","Did our training actually change how people operate AI?","L&D / AI Enablement / Transformation","Shows operating change, not unvalidated productivity lift.",["EVAL-007","EVAL-011"],2,"Measures whether training changed operating behavior."),
    "5": CommercialPilot("5","Model / Tool Evaluation","What changes when we introduce Model A, Model B or Tool X?","Head of AI / CIO / IT / Procurement","For model selection, tool consolidation and rollout decisions.",["EVAL-005","EVAL-012"],2,"Compares models and tools through operator metrics."),
    "6": CommercialPilot("6","Agent Adoption","Is agent capability becoming organizational or staying concentrated?","Head of AI / Automation / Transformation","For companies moving from chat to agentic workflows.",["EVAL-010","EVAL-013"],2,"Assesses whether agent capability is spreading."),
    "7": CommercialPilot("7","Workflow Diagnostic","Is the constraint the operator, the tool or the workflow?","Operations / Transformation / BU leader","If strong operators stall at the same stage, investigate workflow.",["EVAL-008","EVAL-002"],1,"Diagnoses whether constraints are operator, tool, or workflow."),
    "8": CommercialPilot("8","Team AI Operating Comparison","Why do teams using the same AI stack operate differently?","Transformation / Operations / BU leadership","For cross-team standardization and enablement planning.",["EVAL-006","EVAL-009","EVAL-013"],1,"Compares team-level operating patterns."),
    "9": CommercialPilot("9","Experiments","What changed when we introduced X?","Head of AI / Innovation / Transformation","Fits models, tools, training, agents, workflows.",["EVAL-007","EVAL-012"],2,"Predeclared experiments with governed measurement."),
    "10": CommercialPilot("10","Monitor","How is our AI operating population changing month over month?","Head of AI / CIO / Transformation","Natural recurring extension after a successful baseline pilot.",["EVAL-004","EVAL-006","EVAL-010"],1,"Continuous monitoring over time."),
    "11": CommercialPilot("11","Meta-Pilot (Validation, not deployment)","Does this metric predict something we already care about?","Head of AI / CIO / Transformation","Pre-sale wedge for skeptical buyers.",["EVAL-002","EVAL-004"],1,"Lightweight correlation study. ASSOCIATION — never CAUSATION.",["Correlation report","Threshold recommendations","ROI estimate"]),
    "12": CommercialPilot("12","Vendor / Consultancy Verification","Are our outsourced AI vendors actually delivering quality?","Procurement / CIO / Head of AI","When evaluating multiple AI vendors.",["EVAL-005","EVAL-006","EVAL-012"],2,"Independent telemetry on vendor delivery.",["Vendor comparison report","Threshold-gate recommendations","Delivery quality assessment"]),
}

def get_pilot(pilot_id: str) -> CommercialPilot:
    return COMMERCIAL_PILOTS[pilot_id]

def all_pilot_ids() -> List[str]:
    return list(COMMERCIAL_PILOTS.keys())
