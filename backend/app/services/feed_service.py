"""Feed querying and primary-source civic card assembly."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legislative import (
    BillAction,
    BillTextVersion,
    CongressionalBill,
    CongressionalCommittee,
    CongressionalHearing,
    CongressionalVote,
    LegislativeSourceLink,
    MemberVotePosition,
)
from app.models.update import GovernmentUpdate
from app.schemas.update import FeedQueryParams
from app.services.personalization import rank_updates, ranking_factors


class FeedService:
    """High-level feed operations for API layer."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _base_query(self) -> Select[tuple[GovernmentUpdate]]:
        return select(GovernmentUpdate).order_by(GovernmentUpdate.published_at.desc())

    def _apply_filters(self, query: Select, params: FeedQueryParams) -> Select:
        if params.branch:
            query = query.where(GovernmentUpdate.branch == params.branch)
        if params.source:
            query = query.where(GovernmentUpdate.source == params.source)
        if params.tag:
            query = query.where(GovernmentUpdate.tags.contains([params.tag]))
        if params.search:
            # Placeholder for vector search; fallback to case-insensitive headline match.
            pattern = f"%{params.search.lower()}%"
            query = query.where(func.lower(GovernmentUpdate.headline).like(pattern))
        if params.start_date:
            query = query.where(GovernmentUpdate.published_at >= params.start_date)
        if params.end_date:
            query = query.where(GovernmentUpdate.published_at <= params.end_date)
        return query

    async def list_updates(self, params: FeedQueryParams) -> tuple[List[dict[str, Any]], int]:
        query = self._apply_filters(self._base_query(), params)

        result = await self.session.execute(query)
        ranked = rank_updates(result.scalars().all(), context=self._ranking_context(params))
        feed_items = [self._to_feed_item(update, params) for update in ranked]

        if params.card_type:
            feed_items = [item for item in feed_items if item["card_type"] == params.card_type]

        total = len(feed_items)
        return feed_items[params.offset : params.offset + params.limit], total

    def _ranking_context(self, params: FeedQueryParams) -> dict[str, Any]:
        return params.model_dump(exclude_none=True)

    def _to_feed_item(self, update: GovernmentUpdate, params: FeedQueryParams) -> dict[str, Any]:
        metadata = update.metadata_json or {}
        card_type = self._card_type(update, metadata)
        source_trail = self._source_trail(update)
        source_trail_status = "available" if source_trail else "pending"
        source_trail_note = None if source_trail else "Official source link has not been published for this event yet."

        return {
            "id": update.id,
            "external_id": update.external_id,
            "source": update.source,
            "branch": update.branch,
            "headline": update.headline,
            "summary": update.summary,
            "full_text": update.full_text,
            "published_at": update.published_at,
            "event_date": update.event_date,
            "url": update.url,
            "bill_id": update.bill_id,
            "bill_action_id": update.bill_action_id,
            "vote_id": update.vote_id,
            "hearing_id": update.hearing_id,
            "tags": update.tags or [],
            "metadata": metadata,
            "entities": [
                {"id": entity.id, "name": entity.name, "type": entity.type, "slug": entity.slug}
                for entity in update.entities
            ],
            "card_type": card_type,
            "rank_context": self._rank_context(update, params, metadata),
            "involved": self._involved(update),
            "key_claims": self._key_claims(update, bool(source_trail)),
            "source_trail": source_trail,
            "source_trail_status": source_trail_status,
            "source_trail_note": source_trail_note,
            "detail": self._detail(update, params, card_type),
        }

    def _card_type(self, update: GovernmentUpdate, metadata: dict[str, Any]) -> str:
        metadata_type = metadata.get("card_type") or metadata.get("event_type")
        if isinstance(metadata_type, str) and metadata_type in {"bill", "vote", "hearing", "money", "alert"}:
            return metadata_type
        if update.vote_id:
            return "vote"
        if update.hearing_id:
            return "hearing"
        if update.bill_id or update.bill_action_id:
            return "bill"
        tags = {str(tag).lower() for tag in (update.tags or [])}
        if "vote" in tags:
            return "vote"
        if "hearing" in tags:
            return "hearing"
        return "bill" if "bill" in tags or "legislation" in tags else "alert"

    def _rank_context(self, update: GovernmentUpdate, params: FeedQueryParams, metadata: dict[str, Any]) -> dict[str, Any]:
        factors = ranking_factors(update, context=self._ranking_context(params))
        reasons: list[str] = []
        if update.vote_id:
            reasons.append("Roll-call votes are high-importance primary-source events.")
        if update.hearing_id:
            reasons.append("Hearings are ranked for schedule and oversight relevance.")
        if update.bill_action_id:
            reasons.append("Bill lifecycle actions are ranked by official action importance.")
        if params.followed_bills or params.followed_members or params.followed_topics:
            reasons.append("Followed bills, members, and topics raise relevant cards when they match.")
        if params.state or params.district:
            reasons.append("District and state context raise local representative activity when present.")
        if update.url or metadata.get("source_trail"):
            reasons.append("Official source links are available on the card.")

        return {
            "score": sum(factors.values()),
            "factors": factors,
            "reasons": reasons,
        }

    def _source_trail(self, update: GovernmentUpdate) -> list[dict[str, Any]]:
        metadata = update.metadata_json or {}
        metadata_trail = metadata.get("source_trail")
        if isinstance(metadata_trail, list) and metadata_trail:
            return [dict(item) for item in metadata_trail if isinstance(item, dict)]

        links: list[dict[str, Any]] = []
        for source_link in self._related_source_links(update):
            links.append(self._source_link_dict(source_link))

        if update.url and not any(link.get("url") == update.url for link in links):
            links.insert(
                0,
                {
                    "label": "Official source",
                    "source": update.source,
                    "url": update.url,
                    "published_at": _iso(update.published_at),
                    "retrieved_at": None,
                    "supports": ["headline", "summary"],
                },
            )
        return links

    def _related_source_links(self, update: GovernmentUpdate) -> list[LegislativeSourceLink]:
        links: list[LegislativeSourceLink] = []
        if update.bill:
            links.extend(update.bill.source_links)
        if update.bill_action:
            links.extend(update.bill_action.source_links)
        if update.vote:
            links.extend(update.vote.source_links)
        if update.hearing:
            links.extend(update.hearing.source_links)

        seen: set[tuple[str, str]] = set()
        deduped: list[LegislativeSourceLink] = []
        for link in links:
            key = (link.source_system, link.url)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(link)
        return deduped

    def _source_link_dict(self, link: LegislativeSourceLink) -> dict[str, Any]:
        return {
            "label": link.label,
            "source": link.source_system,
            "url": link.url,
            "published_at": _iso(link.published_at),
            "retrieved_at": _iso(link.retrieved_at),
            "supports": link.supports or [],
            "confidence": link.confidence,
            "source_category": link.source_category,
        }

    def _involved(self, update: GovernmentUpdate) -> list[dict[str, Any]]:
        involved = [
            {"name": entity.name, "entity_type": entity.type, "role": None, "identifier": entity.slug, "url": None}
            for entity in update.entities
        ]
        if update.bill:
            involved.append(
                {
                    "name": update.bill.short_title or update.bill.title,
                    "entity_type": "bill",
                    "role": "subject",
                    "identifier": update.bill.canonical_id,
                    "url": update.bill.congress_url,
                }
            )
            for committee in update.bill.committees:
                involved.append(self._committee_involved(committee, "committee"))
        if update.vote:
            involved.append(
                {
                    "name": f"{update.vote.chamber} roll call {update.vote.roll_number}",
                    "entity_type": "vote",
                    "role": "roll_call",
                    "identifier": update.vote.canonical_id,
                    "url": update.vote.source_url,
                }
            )
        if update.hearing:
            involved.append(
                {
                    "name": update.hearing.title,
                    "entity_type": "hearing",
                    "role": "committee_activity",
                    "identifier": update.hearing.canonical_id,
                    "url": update.hearing.source_url,
                }
            )
            if update.hearing.committee:
                involved.append(self._committee_involved(update.hearing.committee, "host_committee"))
        return involved

    def _committee_involved(self, committee: CongressionalCommittee, role: str) -> dict[str, Any]:
        return {
            "name": committee.name,
            "entity_type": "committee",
            "role": role,
            "identifier": committee.committee_code,
            "url": committee.congress_url,
        }

    def _key_claims(self, update: GovernmentUpdate, has_source: bool) -> list[dict[str, Any]]:
        source_indexes = [0] if has_source else []
        unavailable_reason = None if has_source else "Official source link has not been attached yet."
        claims = [
            {
                "id": "headline",
                "text": update.headline,
                "source_indexes": source_indexes,
                "unavailable_reason": unavailable_reason,
            }
        ]
        if update.summary:
            claims.append(
                {
                    "id": "summary",
                    "text": update.summary,
                    "source_indexes": source_indexes,
                    "unavailable_reason": unavailable_reason,
                }
            )
        return claims

    def _detail(self, update: GovernmentUpdate, params: FeedQueryParams, card_type: str) -> dict[str, Any]:
        if card_type == "vote" and update.vote:
            return {"vote": self._vote_detail(update.vote, params)}
        if card_type == "hearing" and update.hearing:
            return {"hearing": self._hearing_detail(update.hearing)}
        if update.bill:
            return {"bill": self._bill_detail(update.bill, update, params)}
        return {}

    def _bill_detail(self, bill: CongressionalBill, update: GovernmentUpdate, params: FeedQueryParams) -> dict[str, Any]:
        timeline = sorted(bill.actions, key=lambda action: _sortable_datetime(action.acted_at), reverse=True)
        text_versions = sorted(
            bill.text_versions,
            key=lambda text_version: _sortable_datetime(text_version.published_at),
            reverse=True,
        )
        eligible_vote = bool(bill.votes) or bool((update.metadata_json or {}).get("vote_eligible"))

        return {
            "canonical_id": bill.canonical_id,
            "display_number": f"{bill.bill_type.upper()} {bill.number}",
            "title": bill.title,
            "short_title": bill.short_title,
            "status": bill.latest_action_text or "Official lifecycle status has not been published yet.",
            "origin_chamber": bill.origin_chamber,
            "policy_area": bill.policy_area,
            "introduced_at": _iso(bill.introduced_at),
            "latest_action_at": _iso(bill.latest_action_at),
            "sponsors": _list_or_unavailable((bill.metadata_json or {}).get("sponsors")),
            "cosponsors": _list_or_unavailable(bill.cosponsors),
            "committees": [self._committee_detail(committee) for committee in bill.committees],
            "timeline": [self._action_detail(action) for action in timeline],
            "text_versions": [self._text_version_detail(text_version) for text_version in text_versions],
            "amendments": _list_or_unavailable(bill.amendments),
            "related_bills": _list_or_unavailable(bill.related_bills),
            "cbo_cost_estimates": _list_or_unavailable(bill.cbo_cost_estimates),
            "crs_reports": _list_or_unavailable(bill.crs_reports),
            "votes": [self._vote_summary(vote, params) for vote in bill.votes],
            "vote_eligible": eligible_vote,
            "user_position_prompt": (
                "Record a personal position for comparison. This is civic tracking, not an official congressional vote."
                if eligible_vote
                else None
            ),
            "source_url": bill.congress_url,
            "unavailable": {
                "committees": "No committee referrals are published yet." if not bill.committees else None,
                "text_versions": "No official bill text versions are published yet." if not bill.text_versions else None,
                "votes": "No roll-call vote is linked to this bill yet." if not bill.votes else None,
            },
        }

    def _vote_detail(self, vote: CongressionalVote, params: FeedQueryParams) -> dict[str, Any]:
        positions = [self._position_detail(position) for position in vote.positions]
        local_positions = [
            position
            for position in positions
            if _matches_local_context(position, params.state, params.district)
        ]

        return {
            "canonical_id": vote.canonical_id,
            "chamber": vote.chamber,
            "congress": vote.congress,
            "session": vote.session,
            "roll_number": vote.roll_number,
            "vote_date": _iso(vote.vote_date),
            "question": vote.question,
            "result": vote.result,
            "margin": _vote_margin(vote.totals),
            "totals": vote.totals or {},
            "party_split": vote.party_split or {},
            "positions": sorted(positions, key=lambda item: (item.get("state") or "", item["member_name"])),
            "local_representative_positions": local_positions,
            "linked_bill": self._bill_summary(vote.bill) if vote.bill else None,
            "source_url": vote.source_url,
            "unavailable": {
                "member_positions": "Official member vote positions have not been published yet." if not positions else None,
                "local_representatives": (
                    "No local representative match was available for this vote."
                    if (params.state or params.district) and not local_positions
                    else None
                ),
            },
        }

    def _hearing_detail(self, hearing: CongressionalHearing) -> dict[str, Any]:
        committee = self._committee_detail(hearing.committee) if hearing.committee else None
        return {
            "canonical_id": hearing.canonical_id,
            "event_id": hearing.event_id,
            "congress": hearing.congress,
            "chamber": hearing.chamber,
            "title": hearing.title,
            "meeting_type": hearing.meeting_type,
            "status": hearing.status,
            "scheduled_at": _iso(hearing.scheduled_at),
            "location": hearing.location,
            "committee": committee,
            "witnesses": _list_or_unavailable(hearing.witnesses),
            "related_bills": _list_or_unavailable(hearing.related_bills),
            "videos": _list_or_unavailable(hearing.videos),
            "transcripts": _list_or_unavailable(hearing.transcripts),
            "source_url": hearing.source_url,
            "follow_supported": bool(committee),
            "alert_affordance": "Follow this committee for hearing alerts." if committee else None,
            "unavailable": {
                "witnesses": "Official witness details are not published yet." if not hearing.witnesses else None,
                "videos": "Official video is not published yet." if not hearing.videos else None,
                "transcripts": "Official transcript is not published yet." if not hearing.transcripts else None,
            },
        }

    def _bill_summary(self, bill: CongressionalBill) -> dict[str, Any]:
        return {
            "id": bill.id,
            "canonical_id": bill.canonical_id,
            "display_number": f"{bill.bill_type.upper()} {bill.number}",
            "title": bill.short_title or bill.title,
            "source_url": bill.congress_url,
        }

    def _vote_summary(self, vote: CongressionalVote, params: FeedQueryParams | None = None) -> dict[str, Any]:
        positions = [self._position_detail(position) for position in vote.positions]
        return {
            "id": vote.id,
            "canonical_id": vote.canonical_id,
            "chamber": vote.chamber,
            "roll_number": vote.roll_number,
            "vote_date": _iso(vote.vote_date),
            "question": vote.question,
            "result": vote.result,
            "source_url": vote.source_url,
            "positions": positions,
            "local_representative_positions": (
                [
                    position
                    for position in positions
                    if _matches_local_context(position, params.state, params.district)
                ]
                if params
                else []
            ),
        }

    def _committee_detail(self, committee: CongressionalCommittee | None) -> dict[str, Any] | None:
        if committee is None:
            return None
        return {
            "id": committee.id,
            "committee_code": committee.committee_code,
            "name": committee.name,
            "chamber": committee.chamber,
            "committee_type": committee.committee_type,
            "jurisdiction": committee.jurisdiction,
            "source_url": committee.congress_url,
        }

    def _action_detail(self, action: BillAction) -> dict[str, Any]:
        return {
            "id": action.id,
            "action_type": action.action_type,
            "text": action.text,
            "acted_at": _iso(action.acted_at),
            "chamber": action.chamber,
            "source_url": action.source_url,
        }

    def _text_version_detail(self, text_version: BillTextVersion) -> dict[str, Any]:
        return {
            "id": text_version.id,
            "version_code": text_version.version_code,
            "version_name": text_version.version_name,
            "published_at": _iso(text_version.published_at),
            "source_url": text_version.source_url,
            "formats": text_version.formats or [],
        }

    def _position_detail(self, position: MemberVotePosition) -> dict[str, Any]:
        member = position.member
        return {
            "member_identifier": position.member_identifier,
            "member_name": position.member_name,
            "party": position.party,
            "state": position.state,
            "district": member.district if member else None,
            "position": position.position,
            "congress_url": member.congress_url if member else None,
            "is_current_member": member.current if member else None,
        }


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _sortable_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _list_or_unavailable(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _matches_local_context(position: dict[str, Any], state: str | None, district: str | None) -> bool:
    if state and str(position.get("state") or "").lower() != state.lower():
        return False
    if district and str(position.get("district") or "").zfill(2) != str(district).zfill(2):
        return False
    return bool(state or district)


def _vote_margin(totals: dict[str, Any] | None) -> str | None:
    if not totals:
        return None
    yea = _intish(totals.get("yea") or totals.get("yes"))
    nay = _intish(totals.get("nay") or totals.get("no"))
    if yea is None or nay is None:
        return None
    return str(abs(yea - nay))


def _intish(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
