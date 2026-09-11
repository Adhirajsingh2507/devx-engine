"""Strict Pydantic models for the canonical input contract (doc 05).

Mirrors contracts/core.schema.json. `extra="forbid"` matches the schema's
additionalProperties:false, so unknown properties are structural (422) errors.
Domain rules that JSON Schema cannot express (cross-field, physical
applicability) live in validation.py, not here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, conlist

# --- shared constrained types (schema patterns) ---
IdStr = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}$")]
ShortStr = Annotated[str, StringConstraints(min_length=1, max_length=240)]
Utc = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")]
MoneyAmount = Annotated[str, StringConstraints(pattern=r"^(0|[1-9][0-9]*)(\.[0-9]+)?$", max_length=40)]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Prob = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
NonNeg = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Num = Annotated[float, Field(allow_inf_nan=False)]
Vec3 = conlist(Num, min_length=3, max_length=3)
Mat3 = conlist(conlist(Num, min_length=3, max_length=3), min_length=3, max_length=3)
Lon = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
Coord = conlist(Lon, min_length=2, max_length=2)


def parse_utc(value: str) -> datetime:
    """Parse a canonical `...Z` timestamp to an aware UTC datetime (3.10-safe)."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Provenanced(Strict):
    schema_version: Literal["2.0"]
    provenance_kind: Literal["synthetic", "historical", "operator_supplied"]
    source_name: ShortStr
    source_revision: ShortStr


class ObjectState(Strict):
    object_id: IdStr
    position_m: Vec3
    velocity_m_s: Vec3
    position_covariance_m2: Mat3
    hard_body_radius_m: Annotated[float, Field(gt=0, allow_inf_nan=False)]


class ModelDomain(Strict):
    linear_relative_motion: Literal[True]
    gaussian_position_error: Literal[True]
    constant_covariance: Literal[True]
    velocity_uncertainty_neglected: Literal[True]
    cross_object_dependence: Literal["independent", "supplied_cross_covariance"]


class Encounter(Strict):
    epoch: Utc
    frame: Literal["GCRF", "synthetic_inertial"]
    interval_start_offset_s: Num
    interval_end_offset_s: Num
    primary: ObjectState
    secondary: ObjectState
    domain: ModelDomain
    cross_covariance_ps_m2: Optional[Mat3] = None


class Planning(Strict):
    latest_command_at: Optional[Utc]
    review_allowance_s: Optional[NonNeg]
    maneuver_context_known: bool


class EvidenceMetadata(Strict):
    primary_solution_epoch: Optional[Utc]
    secondary_solution_epoch: Optional[Utc]
    primary_last_observation_at: Optional[Utc]
    secondary_last_observation_at: Optional[Utc]
    covariance_realism_basis: Literal["synthetic_assumption", "operator_declared", "unverified"]
    maneuver_information_status: Literal["supplied_none", "supplied_update", "unknown"]


class Report(Provenanced):
    bundle_kind: Literal["encounter_report"]
    event_key: IdStr
    report_id: IdStr
    primary_object_id: IdStr
    secondary_object_id: IdStr
    created_at: Utc
    reported_tca: Utc
    reported_pc: Optional[Prob]
    encounter: Optional[Encounter]
    planning: Planning
    notes: Optional[Annotated[str, StringConstraints(max_length=2000)]] = None
    evidence_metadata: EvidenceMetadata


class Money(Strict):
    amount: MoneyAmount
    currency: Currency


class Candidate(Strict):
    candidate_id: IdStr
    selected_object_state: ObjectState
    delta_v_m_s: Optional[NonNeg]
    response_cost: Optional[Money]
    feasible: Optional[bool]
    feasibility_basis: Literal["supplied_assumption"]


class CandidateSet(Provenanced):
    bundle_kind: Literal["candidate_set"]
    candidate_set_id: IdStr
    catalogue_revision: ShortStr
    epoch: Utc
    frame: Literal["GCRF", "synthetic_inertial"]
    interval_start_offset_s: Num
    interval_end_offset_s: Num
    domain: ModelDomain
    selected_object_id: IdStr
    objects: conlist(ObjectState, min_length=2, max_length=20)
    alternatives: conlist(Candidate, min_length=1, max_length=3)
    selected_object_maneuver_capable: Optional[bool]
    planning: Planning
    policy_threshold: Prob


class LossItem(Strict):
    item_id: IdStr
    description: ShortStr
    money: Money


class EconomicScenario(Provenanced):
    bundle_kind: Literal["economic_scenario"]
    scenario_id: IdStr
    case_event_key: IdStr
    before_probability: Optional[Prob]
    after_probability: Optional[Prob]
    probability_basis: Literal["synthetic_supplied", "supported_calculation", "reported_scenario"]
    before_probability_ref: IdStr
    after_probability_ref: IdStr
    loss_items_before: conlist(LossItem, min_length=1, max_length=20)
    loss_items_after: conlist(LossItem, min_length=1, max_length=20)
    response_cost: Money


class PolygonGeometry(Strict):
    type: Literal["Polygon"]
    coordinates: conlist(conlist(Coord, min_length=4, max_length=1000), min_length=1, max_length=20)


class MultiPolygonGeometry(Strict):
    type: Literal["MultiPolygon"]
    coordinates: conlist(
        conlist(conlist(Coord, min_length=4, max_length=1000), min_length=1, max_length=20),
        min_length=1,
        max_length=20,
    )


Geometry = Annotated[Union[PolygonGeometry, MultiPolygonGeometry], Field(discriminator="type")]


class PopulationPoint(Strict):
    sample_id: IdStr
    coordinates: Coord
    represented_population: Annotated[int, Field(ge=0)]


class AssetPoint(Strict):
    asset_id: IdStr
    asset_type: ShortStr
    coordinates: Coord
    replacement_value: Optional[Money]
    probability_of_damage: Optional[Prob]
    mean_loss_fraction: Optional[Prob]


class ReentryScenario(Provenanced):
    bundle_kind: Literal["reentry_scenario"]
    scenario_id: IdStr
    window_start: Utc
    window_end: Utc
    footprint: Geometry
    population_points: conlist(PopulationPoint, min_length=0, max_length=1000)
    asset_points: conlist(AssetPoint, min_length=0, max_length=1000)
    coverage_note: ShortStr
    layer_revision: ShortStr


class CommunicationScenario(Provenanced):
    bundle_kind: Literal["communication_scenario"]
    scenario_id: IdStr
    candidate_id: IdStr
    comparison_ref: IdStr
    now: Utc
    contact_start: Optional[Utc]
    contact_end: Optional[Utc]
    action_deadline: Optional[Utc]
    packet_expires_at: Utc
    uplink_s: Optional[NonNeg]
    ack_allowance_s: Optional[NonNeg]
    action_lead_s: Optional[NonNeg]


Record = Annotated[
    Union[Report, CandidateSet, EconomicScenario, ReentryScenario, CommunicationScenario],
    Field(discriminator="bundle_kind"),
]


class ImportBatch(Strict):
    schema_version: Literal["2.0"]
    expected_workspace_revision: Annotated[int, Field(ge=0)]
    records: conlist(Record, min_length=1, max_length=500)


class AgentSelection(Strict):
    assessment_id: IdStr
    ordered_finding_ids: conlist(IdStr, min_length=0, max_length=50)
    selected_fact_ids: conlist(IdStr, min_length=0, max_length=50)
    summary_template_code: Literal[
        "REVIEW_DUE_TO_RISK",
        "REVIEW_DUE_TO_MISSING_EVIDENCE",
        "REVIEW_DUE_TO_CONFLICT",
        "MONITOR_SUPPORTED",
        "CALCULATION_UNSUPPORTED",
    ]
    request_template_code: Optional[
        Literal["REQUEST_STATE_COVARIANCE", "REQUEST_FRAME_EPOCH", "REQUEST_MANEUVER_CONTEXT", "REQUEST_DEADLINE"]
    ]
    question_to_analyst_code: Optional[Literal["CONFIRM_SOURCE", "CONFIRM_DEADLINE", "CONFIRM_ASSUMPTION"]]
