"""Persistence helpers for canonical legislative records."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legislative import (
    BillAction,
    BillTextVersion,
    CongressionalBill,
    CongressionalCommittee,
    CongressionalHearing,
    CongressionalMember,
    CongressionalVote,
    DistrictLookupResult,
    LegislativeSourceLink,
    MemberVotePosition,
    bill_committee_association,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_datetime(value: Any) -> datetime | None:
    """Parse Congress.gov/Census timestamps without making callers care."""

    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        sanitized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(sanitized)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                return datetime.strptime(sanitized, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                return None
    return None


def canonical_bill_id(congress: int | str, bill_type: str, number: str | int) -> str:
    return f"{congress}-{bill_type.lower()}-{number}".replace(" ", "-")


def canonical_vote_id(chamber: str, congress: int | str, session: str | None, roll_number: str | int) -> str:
    session_part = session or "unknown-session"
    return f"vote-{chamber.lower()}-{congress}-{session_part}-{roll_number}".replace(" ", "-")


def canonical_hearing_id(congress: int | str | None, chamber: str, event_id: str | int) -> str:
    congress_part = congress or "unknown-congress"
    return f"hearing-{congress_part}-{chamber.lower()}-{event_id}".replace(" ", "-")


def _json_list(value: Any) -> list[dict]:
    return value if isinstance(value, list) else []


def _json_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _url(value: Any) -> str | None:
    return str(value) if value else None


class LegislativeDataService:
    """Idempotent writer for Congress.gov-backed domain records."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_bill(self, payload: dict[str, Any]) -> CongressionalBill:
        congress = int(payload["congress"])
        bill_type = str(payload["bill_type"]).lower()
        number = str(payload["number"])
        canonical_id = payload.get("canonical_id") or canonical_bill_id(congress, bill_type, number)

        bill = await self._get_by_canonical_id(CongressionalBill, canonical_id)
        if bill is None:
            bill = CongressionalBill(canonical_id=canonical_id, congress=congress, bill_type=bill_type, number=number, title="")
            self.session.add(bill)

        bill.congress = congress
        bill.bill_type = bill_type
        bill.number = number
        bill.origin_chamber = payload.get("origin_chamber")
        bill.title = payload.get("title") or bill.title or f"{bill_type.upper()} {number}"
        bill.short_title = payload.get("short_title")
        bill.introduced_at = as_datetime(payload.get("introduced_at"))
        bill.latest_action_at = as_datetime(payload.get("latest_action_at"))
        bill.latest_action_text = payload.get("latest_action_text")
        bill.policy_area = payload.get("policy_area")
        bill.congress_url = _url(payload.get("congress_url"))
        bill.summaries = _json_list(payload.get("summaries"))
        bill.cosponsors = _json_list(payload.get("cosponsors"))
        bill.amendments = _json_list(payload.get("amendments"))
        bill.related_bills = _json_list(payload.get("related_bills"))
        bill.subjects = _json_list(payload.get("subjects"))
        bill.cbo_cost_estimates = _json_list(payload.get("cbo_cost_estimates"))
        bill.crs_reports = _json_list(payload.get("crs_reports"))
        bill.metadata_json = _json_dict(payload.get("metadata"))
        await self.session.flush()

        for source_link in payload.get("source_links", []):
            await self.upsert_source_link(source_link, bill_id=bill.id)
        for committee_payload in payload.get("committees", []):
            committee = await self.upsert_committee(committee_payload)
            await self._link_bill_committee(bill.id, committee.id)
        for action_payload in payload.get("actions", []):
            await self.upsert_bill_action(bill, action_payload)
        for text_payload in payload.get("text_versions", []):
            await self.upsert_bill_text_version(bill, text_payload)

        await self.session.flush()
        return bill

    async def upsert_bill_action(self, bill: CongressionalBill, payload: dict[str, Any]) -> BillAction:
        acted_at = as_datetime(payload.get("acted_at") or payload.get("action_date"))
        sequence = payload.get("sequence")
        suffix = sequence if sequence is not None else f"{acted_at.isoformat() if acted_at else 'undated'}-{hash(payload.get('text', ''))}"
        canonical_id = payload.get("canonical_id") or f"{bill.canonical_id}:action:{suffix}"

        action = await self._get_by_canonical_id(BillAction, canonical_id)
        if action is None:
            action = BillAction(canonical_id=canonical_id, bill_id=bill.id, text="")
            self.session.add(action)

        action.bill_id = bill.id
        action.action_code = payload.get("action_code")
        action.action_type = payload.get("action_type")
        action.text = payload.get("text") or action.text
        action.acted_at = acted_at
        action.chamber = payload.get("chamber")
        action.committee_code = payload.get("committee_code")
        action.source_url = _url(payload.get("source_url"))
        action.sequence = int(sequence) if sequence is not None else None
        action.metadata_json = _json_dict(payload.get("metadata"))
        await self.session.flush()

        for source_link in payload.get("source_links", []):
            await self.upsert_source_link(source_link, action_id=action.id)
        return action

    async def upsert_bill_text_version(self, bill: CongressionalBill, payload: dict[str, Any]) -> BillTextVersion:
        version_code = payload.get("version_code") or payload.get("type") or "unknown-version"
        canonical_id = payload.get("canonical_id") or f"{bill.canonical_id}:text:{version_code}"

        text_version = await self._get_by_canonical_id(BillTextVersion, canonical_id)
        if text_version is None:
            text_version = BillTextVersion(canonical_id=canonical_id, bill_id=bill.id)
            self.session.add(text_version)

        text_version.bill_id = bill.id
        text_version.version_code = str(version_code)
        text_version.version_name = payload.get("version_name") or payload.get("name")
        text_version.published_at = as_datetime(payload.get("published_at") or payload.get("date"))
        text_version.source_url = _url(payload.get("source_url") or payload.get("url"))
        text_version.formats = _json_list(payload.get("formats"))
        text_version.metadata_json = _json_dict(payload.get("metadata"))
        await self.session.flush()

        for source_link in payload.get("source_links", []):
            await self.upsert_source_link(source_link, text_version_id=text_version.id)
        return text_version

    async def upsert_committee(self, payload: dict[str, Any]) -> CongressionalCommittee:
        committee_code = str(payload.get("committee_code") or payload.get("system_code") or payload["name"]).lower()
        stmt = select(CongressionalCommittee).where(CongressionalCommittee.committee_code == committee_code)
        result = await self.session.execute(stmt)
        committee = result.scalar_one_or_none()
        if committee is None:
            committee = CongressionalCommittee(committee_code=committee_code, name=payload.get("name") or committee_code)
            self.session.add(committee)

        committee.name = payload.get("name") or committee.name
        committee.chamber = payload.get("chamber")
        committee.committee_type = payload.get("committee_type") or payload.get("type")
        committee.parent_committee_code = payload.get("parent_committee_code")
        committee.jurisdiction = payload.get("jurisdiction")
        committee.congress_url = _url(payload.get("congress_url") or payload.get("url"))
        committee.metadata_json = _json_dict(payload.get("metadata"))
        await self.session.flush()

        for source_link in payload.get("source_links", []):
            await self.upsert_source_link(source_link, committee_id=committee.id)
        return committee

    async def upsert_member(self, payload: dict[str, Any]) -> CongressionalMember:
        bioguide_id = str(payload.get("bioguide_id") or payload.get("bioguideId") or payload["id"])
        stmt = select(CongressionalMember).where(CongressionalMember.bioguide_id == bioguide_id)
        result = await self.session.execute(stmt)
        member = result.scalar_one_or_none()
        if member is None:
            member = CongressionalMember(bioguide_id=bioguide_id, name=payload.get("name") or bioguide_id)
            self.session.add(member)

        member.name = payload.get("name") or member.name
        member.party = payload.get("party")
        member.state = payload.get("state")
        district = payload.get("district")
        member.district = str(district).zfill(2) if district not in (None, "") else None
        member.chamber = payload.get("chamber")
        member.member_type = payload.get("member_type") or payload.get("type")
        member.current = bool(payload.get("current", True))
        member.congress_url = _url(payload.get("congress_url") or payload.get("url"))
        member.identifiers = _json_dict(payload.get("identifiers"))
        member.metadata_json = _json_dict(payload.get("metadata"))
        await self.session.flush()

        for source_link in payload.get("source_links", []):
            await self.upsert_source_link(source_link, member_id=member.id)
        return member

    async def upsert_vote(self, payload: dict[str, Any]) -> CongressionalVote:
        chamber = str(payload["chamber"])
        congress = int(payload["congress"])
        session = payload.get("session")
        roll_number = str(payload["roll_number"])
        canonical_id = payload.get("canonical_id") or canonical_vote_id(chamber, congress, session, roll_number)

        vote = await self._get_by_canonical_id(CongressionalVote, canonical_id)
        if vote is None:
            vote = CongressionalVote(
                canonical_id=canonical_id,
                chamber=chamber,
                congress=congress,
                roll_number=roll_number,
                question="",
            )
            self.session.add(vote)

        bill_id = payload.get("bill_id")
        bill_canonical_id = payload.get("bill_canonical_id")
        if bill_id is None and bill_canonical_id:
            bill = await self._get_by_canonical_id(CongressionalBill, str(bill_canonical_id))
            bill_id = bill.id if bill else None

        vote.chamber = chamber
        vote.congress = congress
        vote.session = session
        vote.roll_number = roll_number
        vote.vote_date = as_datetime(payload.get("vote_date") or payload.get("date"))
        vote.question = payload.get("question") or vote.question
        vote.result = payload.get("result")
        vote.bill_id = bill_id
        vote.source_url = _url(payload.get("source_url"))
        vote.totals = _json_dict(payload.get("totals"))
        vote.party_split = _json_dict(payload.get("party_split"))
        vote.metadata_json = _json_dict(payload.get("metadata"))
        await self.session.flush()

        for source_link in payload.get("source_links", []):
            await self.upsert_source_link(source_link, vote_id=vote.id)
        for position_payload in payload.get("positions", []):
            await self.upsert_member_vote_position(vote, position_payload)
        return vote

    async def upsert_member_vote_position(
        self, vote: CongressionalVote, payload: dict[str, Any]
    ) -> MemberVotePosition:
        member = None
        member_identifier = (
            payload.get("member_identifier")
            or payload.get("bioguide_id")
            or payload.get("bioguideId")
            or payload.get("name")
        )
        bioguide_id = payload.get("bioguide_id") or payload.get("bioguideId")
        if bioguide_id:
            stmt = select(CongressionalMember).where(CongressionalMember.bioguide_id == str(bioguide_id))
            result = await self.session.execute(stmt)
            member = result.scalar_one_or_none()

        stmt = select(MemberVotePosition).where(
            MemberVotePosition.vote_id == vote.id,
            MemberVotePosition.member_identifier == str(member_identifier),
        )
        result = await self.session.execute(stmt)
        position = result.scalar_one_or_none()
        if position is None:
            position = MemberVotePosition(
                vote_id=vote.id,
                member_identifier=str(member_identifier),
                member_name=payload.get("name") or str(member_identifier),
                position=payload.get("position") or "unknown",
            )
            self.session.add(position)

        position.member_id = member.id if member else None
        position.member_name = payload.get("name") or position.member_name
        position.party = payload.get("party")
        position.state = payload.get("state")
        position.position = payload.get("position") or position.position
        position.metadata_json = _json_dict(payload.get("metadata"))
        await self.session.flush()
        return position

    async def upsert_hearing(self, payload: dict[str, Any]) -> CongressionalHearing:
        chamber = str(payload["chamber"])
        event_id = str(payload["event_id"])
        congress = payload.get("congress")
        canonical_id = payload.get("canonical_id") or canonical_hearing_id(congress, chamber, event_id)

        committee_id = payload.get("committee_id")
        committee_payload = payload.get("committee")
        if committee_id is None and committee_payload:
            committee = await self.upsert_committee(committee_payload)
            committee_id = committee.id

        hearing = await self._get_by_canonical_id(CongressionalHearing, canonical_id)
        if hearing is None:
            hearing = CongressionalHearing(canonical_id=canonical_id, event_id=event_id, chamber=chamber, title="")
            self.session.add(hearing)

        hearing.event_id = event_id
        hearing.congress = int(congress) if congress is not None else None
        hearing.chamber = chamber
        hearing.committee_id = committee_id
        hearing.title = payload.get("title") or hearing.title
        hearing.meeting_type = payload.get("meeting_type")
        hearing.status = payload.get("status")
        hearing.scheduled_at = as_datetime(payload.get("scheduled_at") or payload.get("date"))
        hearing.location = payload.get("location")
        hearing.source_url = _url(payload.get("source_url"))
        hearing.witnesses = _json_list(payload.get("witnesses"))
        hearing.related_bills = _json_list(payload.get("related_bills"))
        hearing.videos = _json_list(payload.get("videos"))
        hearing.transcripts = _json_list(payload.get("transcripts"))
        hearing.metadata_json = _json_dict(payload.get("metadata"))
        await self.session.flush()

        for source_link in payload.get("source_links", []):
            await self.upsert_source_link(source_link, hearing_id=hearing.id)
        return hearing

    async def resolve_district_members(
        self,
        *,
        lookup_key: str,
        lookup_type: str,
        query: str,
        state: str | None,
        district: str | None,
        source: str,
        retrieved_at: datetime | None = None,
        raw_response: dict[str, Any] | None = None,
        ambiguity_reason: str | None = None,
    ) -> DistrictLookupResult:
        district_value = str(district).zfill(2) if district not in (None, "") else None
        representative = None
        senators: list[CongressionalMember] = []

        if state and district_value and not ambiguity_reason:
            representative_result = await self.session.execute(
                select(CongressionalMember).where(
                    CongressionalMember.current.is_(True),
                    CongressionalMember.chamber == "House",
                    CongressionalMember.state == state,
                    CongressionalMember.district == district_value,
                )
            )
            representative = representative_result.scalar_one_or_none()

        if state and not ambiguity_reason:
            senators_result = await self.session.execute(
                select(CongressionalMember).where(
                    CongressionalMember.current.is_(True),
                    CongressionalMember.chamber == "Senate",
                    CongressionalMember.state == state,
                )
            )
            senators = list(senators_result.scalars().all())

        if not ambiguity_reason and state and district_value and representative is None:
            ambiguity_reason = "No current House member is loaded for the resolved district."
        if not ambiguity_reason and state and len(senators) < 2:
            ambiguity_reason = "Fewer than two current senators are loaded for the resolved state."

        stmt = select(DistrictLookupResult).where(DistrictLookupResult.lookup_key == lookup_key)
        result = await self.session.execute(stmt)
        lookup = result.scalar_one_or_none()
        if lookup is None:
            lookup = DistrictLookupResult(
                lookup_key=lookup_key,
                lookup_type=lookup_type,
                query=query,
                source=source,
                retrieved_at=retrieved_at or utcnow(),
            )
            self.session.add(lookup)

        lookup.lookup_type = lookup_type
        lookup.query = query
        lookup.state = state
        lookup.district = district_value
        lookup.source = source
        lookup.retrieved_at = retrieved_at or utcnow()
        lookup.ambiguity_reason = ambiguity_reason
        lookup.representative_member_id = representative.id if representative else None
        lookup.senator_member_ids = [senator.id for senator in senators]
        lookup.raw_response = raw_response or {}
        await self.session.flush()
        return lookup

    async def upsert_source_link(self, payload: dict[str, Any], **parent_ids: int | None) -> LegislativeSourceLink:
        parent_ids = {key: value for key, value in parent_ids.items() if value is not None}
        source_system = payload.get("source_system") or payload.get("source") or "congress.gov"
        url = str(payload["url"])
        stmt = select(LegislativeSourceLink).where(
            LegislativeSourceLink.url == url,
            LegislativeSourceLink.source_system == source_system,
        )
        for key, value in parent_ids.items():
            stmt = stmt.where(getattr(LegislativeSourceLink, key) == value)
        result = await self.session.execute(stmt)
        source_link = result.scalar_one_or_none()
        if source_link is None:
            source_link = LegislativeSourceLink(
                label=payload.get("label") or source_system,
                url=url,
                source_system=source_system,
                retrieved_at=as_datetime(payload.get("retrieved_at")) or utcnow(),
            )
            self.session.add(source_link)

        source_link.label = payload.get("label") or source_link.label
        source_link.url = url
        source_link.source_system = source_system
        source_link.retrieved_at = as_datetime(payload.get("retrieved_at")) or source_link.retrieved_at or utcnow()
        source_link.published_at = as_datetime(payload.get("published_at"))
        source_link.confidence = payload.get("confidence") or "direct_source"
        source_link.source_category = payload.get("source_category") or "official"
        source_link.supports = payload.get("supports") if isinstance(payload.get("supports"), list) else []
        source_link.metadata_json = _json_dict(payload.get("metadata"))
        for key, value in parent_ids.items():
            setattr(source_link, key, value)
        await self.session.flush()
        return source_link

    async def _link_bill_committee(self, bill_id: int, committee_id: int) -> None:
        stmt = select(bill_committee_association).where(
            bill_committee_association.c.bill_id == bill_id,
            bill_committee_association.c.committee_id == committee_id,
        )
        result = await self.session.execute(stmt)
        if result.first() is None:
            await self.session.execute(
                insert(bill_committee_association).values(bill_id=bill_id, committee_id=committee_id)
            )

    async def _get_by_canonical_id(self, model: type, canonical_id: str):
        stmt = select(model).where(model.canonical_id == canonical_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
