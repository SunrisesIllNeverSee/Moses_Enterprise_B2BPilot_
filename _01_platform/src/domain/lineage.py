"""Lineage — the chain linking states, actions, transformations, artifacts, and outcomes.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 17: A first-class object recording
the chain of transformations from raw observation to derived measurement to
pattern to diagnosis to intervention to re-measurement to outcome validation.

LineageLink represents a single node in the chain, referencing the underlying
canonical object (observation, artifact, or outcome) and its role in the
BI → AAI → committed-state → outcome sequence.

Required Lineage fields: lineage_id, operator_id, synthetic.
Optional Lineage fields: workflow_id, workflow_stage, links, micro_eval.

Required LineageLink fields: link_id, lineage_id, link_type, order.
Optional LineageLink fields: observation_id, artifact_id, outcome_id.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class LinkType(str, Enum):
    """Lineage link types per `03` §5.6 Object 17.

    The chain follows the BI → AAI → committed-state → outcome sequence:
        state_a          — the prior state (before input)
        bi_action        — the operator's before-input action
        aai_transformation — the AI-assisted action transformation
        bi_redirection   — an operator redirection during the chain
        aai_extension    — a system extension during the chain
        committed_state  — the final committed resulting state
        outcome          — the external outcome validating the chain
    """
    STATE_A = "state_a"
    BI_ACTION = "bi_action"
    AAI_TRANSFORMATION = "aai_transformation"
    BI_REDIRECTION = "bi_redirection"
    AAI_EXTENSION = "aai_extension"
    COMMITTED_STATE = "committed_state"
    OUTCOME = "outcome"


@dataclass(frozen=True, slots=True)
class LineageLink:
    """A single link in a lineage chain.

    References one canonical object (observation_id, artifact_id, or
    outcome_id) and its role in the chain via `link_type`.
    """
    link_id: str
    lineage_id: str
    link_type: LinkType
    order: int
    observation_id: Optional[str] = None
    artifact_id: Optional[str] = None
    outcome_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "link_id": self.link_id,
            "lineage_id": self.lineage_id,
            "link_type": self.link_type.value,
            "order": self.order,
            "observation_id": self.observation_id,
            "artifact_id": self.artifact_id,
            "outcome_id": self.outcome_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LineageLink":
        link_type = d["link_type"]
        if isinstance(link_type, str):
            link_type = LinkType(link_type)
        return cls(
            link_id=d["link_id"],
            lineage_id=d["lineage_id"],
            link_type=link_type,
            order=int(d["order"]),
            observation_id=d.get("observation_id"),
            artifact_id=d.get("artifact_id"),
            outcome_id=d.get("outcome_id"),
        )


@dataclass(frozen=True, slots=True)
class Lineage:
    """A lineage chain linking states, actions, transformations, artifacts,
    and outcomes.

    The `links` list is an ordered chain of LineageLink objects. The
    `micro_eval` dict carries aggregate micro-evaluation scores for the
    entire chain.

    Flat fields (state_a_observation_id, bi_action_observation_id, etc.)
    are loaded from the demo JSONL format and also exposed as convenience
    attributes. If `links` is empty but flat fields are present, they
    are converted to links on load.

    The `synthetic` flag must survive import/export.
    """
    lineage_id: str
    operator_id: str
    synthetic: bool = False
    workflow_id: Optional[str] = None
    workflow_stage: Optional[str] = None
    links: List[LineageLink] = field(default_factory=list)
    micro_eval: dict = field(default_factory=dict)
    # Flat fields from demo JSONL format
    state_a_observation_id: Optional[str] = None
    bi_action_observation_id: Optional[str] = None
    aai_transformation_observation_id: Optional[str] = None
    bi_redirection_observation_id: Optional[str] = None
    aai_extension_observation_id: Optional[str] = None
    committed_artifact_id: Optional[str] = None
    outcome_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "lineage_id": self.lineage_id,
            "operator_id": self.operator_id,
            "synthetic": self.synthetic,
            "workflow_id": self.workflow_id,
            "workflow_stage": self.workflow_stage,
            "links": [link.to_dict() for link in self.links],
            "micro_eval": dict(self.micro_eval),
        }
        # Preserve flat fields if present
        if self.state_a_observation_id:
            d["state_a_observation_id"] = self.state_a_observation_id
        if self.bi_action_observation_id:
            d["bi_action_observation_id"] = self.bi_action_observation_id
        if self.aai_transformation_observation_id:
            d["aai_transformation_observation_id"] = self.aai_transformation_observation_id
        if self.bi_redirection_observation_id:
            d["bi_redirection_observation_id"] = self.bi_redirection_observation_id
        if self.aai_extension_observation_id:
            d["aai_extension_observation_id"] = self.aai_extension_observation_id
        if self.committed_artifact_id:
            d["committed_artifact_id"] = self.committed_artifact_id
        if self.outcome_id:
            d["outcome_id"] = self.outcome_id
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Lineage":
        # Load flat fields from demo JSONL format
        state_a = d.get("state_a_observation_id")
        bi_action = d.get("bi_action_observation_id")
        aai_trans = d.get("aai_transformation_observation_id")
        bi_redir = d.get("bi_redirection_observation_id")
        aai_ext = d.get("aai_extension_observation_id")
        committed_art = d.get("committed_artifact_id")
        outcome = d.get("outcome_id")

        # Build links from flat fields if no explicit links list
        raw_links = d.get("links", [])
        if not raw_links:
            order = 0
            for obs_id, lt in [
                (state_a, LinkType.STATE_A),
                (bi_action, LinkType.BI_ACTION),
                (aai_trans, LinkType.AAI_TRANSFORMATION),
                (bi_redir, LinkType.BI_REDIRECTION),
                (aai_ext, LinkType.AAI_EXTENSION),
            ]:
                if obs_id:
                    raw_links.append({
                        "link_id": f"{d['lineage_id']}_link_{order}",
                        "lineage_id": d["lineage_id"],
                        "link_type": lt.value,
                        "order": order,
                        "observation_id": obs_id,
                    })
                    order += 1
            if committed_art:
                raw_links.append({
                    "link_id": f"{d['lineage_id']}_link_{order}",
                    "lineage_id": d["lineage_id"],
                    "link_type": LinkType.COMMITTED_STATE.value,
                    "order": order,
                    "artifact_id": committed_art,
                })
                order += 1
            if outcome:
                raw_links.append({
                    "link_id": f"{d['lineage_id']}_link_{order}",
                    "lineage_id": d["lineage_id"],
                    "link_type": LinkType.OUTCOME.value,
                    "order": order,
                    "outcome_id": outcome,
                })

        return cls(
            lineage_id=d["lineage_id"],
            operator_id=d["operator_id"],
            synthetic=bool(d["synthetic"]),
            workflow_id=d.get("workflow_id"),
            workflow_stage=d.get("workflow_stage"),
            links=[LineageLink.from_dict(link) for link in raw_links],
            micro_eval=dict(d.get("micro_eval", {})),
            state_a_observation_id=state_a,
            bi_action_observation_id=bi_action,
            aai_transformation_observation_id=aai_trans,
            bi_redirection_observation_id=bi_redir,
            aai_extension_observation_id=aai_ext,
            committed_artifact_id=committed_art,
            outcome_id=outcome,
        )
