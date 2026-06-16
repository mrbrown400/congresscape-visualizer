"""Pydantic schemas for source-backed civic feed cards."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator

from app.models.update import BranchEnum

CivicCardType = Literal["bill", "vote", "hearing", "money", "alert"]
SourceTrailStatus = Literal["available", "pending", "unavailable"]
MoneyContextStatus = Literal["available", "not_applicable", "pending", "unavailable"]
MoneySourceRelationship = Literal[
    "direct_source",
    "related_entity",
    "topic_context",
    "unavailable",
]


class CivicEntity(BaseModel):
    """Person, organization, committee, agency, or bill involved in a card."""

    name: str
    entity_type: str
    role: str | None = None
    identifier: str | None = None
    url: HttpUrl | None = None


class CivicSource(BaseModel):
    """Official or supporting source used by one or more card claims."""

    label: str
    source: str
    url: HttpUrl
    published_at: datetime | None = None
    retrieved_at: datetime | None = None
    supports: list[str] = Field(default_factory=list)


class CivicClaim(BaseModel):
    """A factual claim on a card and its source support."""

    id: str
    text: str
    source_indexes: list[int] = Field(default_factory=list)
    unavailable_reason: str | None = None


class CivicMoneyContextItem(BaseModel):
    """Sourced money context, separated by source relationship strength."""

    label: str
    value: str | None = None
    source_relationship: MoneySourceRelationship
    source_indexes: list[int] = Field(default_factory=list)
    unavailable_reason: str | None = None
    note: str | None = Field(
        default=None,
        description=(
            "Neutral context copy. Must not infer corruption, motive, or intent."
        ),
    )


class CivicCard(BaseModel):
    """Shared backend/frontend contract for a primary-source civic feed card."""

    id: str
    card_type: CivicCardType
    branch: BranchEnum
    source: str
    headline: str
    summary: str
    what_happened: str
    published_at: datetime
    last_updated_at: datetime
    event_date: datetime | None = None
    primary_update_id: int | None = None
    why_it_matters: str | None = None
    involved: list[CivicEntity] = Field(default_factory=list)
    key_claims: list[CivicClaim] = Field(default_factory=list)
    money_context_status: MoneyContextStatus = "not_applicable"
    money_context_note: str | None = None
    money_context: list[CivicMoneyContextItem] = Field(default_factory=list)
    source_trail_status: SourceTrailStatus = "available"
    source_trail_note: str | None = None
    source_trail: list[CivicSource] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_provenance(self) -> "CivicCard":
        """Require explicit source support or clear unavailable states."""

        self._validate_source_trail_state()
        self._validate_claim_support()
        self._validate_money_context()
        return self

    def _validate_source_trail_state(self) -> None:
        if self.source_trail_status == "available" and not self.source_trail:
            raise ValueError(
                "source_trail_status='available' requires at least one source"
            )

        if self.source_trail_status != "available" and not self.source_trail_note:
            raise ValueError(
                "source_trail_note is required when sources are pending or unavailable"
            )

    def _validate_claim_support(self) -> None:
        for claim in self.key_claims:
            self._validate_indexes(claim.source_indexes, f"key_claims.{claim.id}")
            if not claim.source_indexes and not claim.unavailable_reason:
                raise ValueError(
                    f"key_claims.{claim.id} needs source indexes or an "
                    "unavailable_reason"
                )

    def _validate_money_context(self) -> None:
        if self.money_context_status == "available" and not self.money_context:
            raise ValueError(
                "money_context_status='available' requires at least one money item"
            )

        if (
            self.money_context_status in {"pending", "unavailable"}
            and not self.money_context_note
        ):
            raise ValueError(
                "money_context_note is required when money context is pending "
                "or unavailable"
            )

        for item in self.money_context:
            location = f"money_context.{item.label}"
            self._validate_indexes(item.source_indexes, location)

            if item.source_relationship == "unavailable":
                if not item.unavailable_reason:
                    raise ValueError(
                        f"{location} needs unavailable_reason for unavailable "
                        "money context"
                    )
                continue

            if not item.source_indexes and not item.unavailable_reason:
                raise ValueError(
                    f"{location} needs source indexes or an unavailable_reason"
                )

    def _validate_indexes(self, indexes: list[int], location: str) -> None:
        source_count = len(self.source_trail)
        for index in indexes:
            if index < 0 or index >= source_count:
                raise ValueError(
                    f"{location} references source index {index}, but "
                    f"source_trail has {source_count} sources"
                )
