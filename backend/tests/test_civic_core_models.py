from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.db.base import Base


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


def test_civic_schema_creates_all_core_tables(session: Session) -> None:
    expected = {
        models.AgendaItem.__tablename__,
        models.DocumentVersion.__tablename__,
        models.ExtractedClaim.__tablename__,
        models.FundingEvent.__tablename__,
        models.Geography.__tablename__,
        models.GovernmentBody.__tablename__,
        models.Jurisdiction.__tablename__,
        models.Meeting.__tablename__,
        models.Official.__tablename__,
        models.PolicyAction.__tablename__,
        models.PolicyItem.__tablename__,
        models.Project.__tablename__,
        models.SourceLink.__tablename__,
        models.Vote.__tablename__,
        models.VotePosition.__tablename__,
    }

    assert expected.issubset(Base.metadata.tables)


def test_canonical_ids_are_unique(session: Session) -> None:
    session.add_all(
        [
            models.Jurisdiction(canonical_id="us.federal", name="United States", kind="federal"),
            models.Jurisdiction(canonical_id="us.federal", name="Duplicate", kind="federal"),
        ]
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_policy_item_source_identity_is_unique(session: Session) -> None:
    jurisdiction = models.Jurisdiction(canonical_id="la.metro", name="Metro", kind="service_area")
    session.add_all(
        [
            models.PolicyItem(
                canonical_id="la.metro:item:1",
                source_system="metro",
                source_native_id="item-1",
                jurisdiction=jurisdiction,
                item_type="board_report",
                title="First",
            ),
            models.PolicyItem(
                canonical_id="la.metro:item:2",
                source_system="metro",
                source_native_id="item-1",
                jurisdiction=jurisdiction,
                item_type="board_report",
                title="Duplicate",
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_set_null_official_relationship_preserves_vote_position(session: Session) -> None:
    jurisdiction = models.Jurisdiction(canonical_id="la.metro", name="Metro", kind="service_area")
    body = models.GovernmentBody(
        canonical_id="la.metro:body:board", name="Metro Board", body_type="board", jurisdiction=jurisdiction
    )
    official = models.Official(canonical_id="la.metro:official:1", name="A. Official", government_body=body)
    vote = models.Vote(canonical_id="la.metro:vote:1", question="Adopt?", voted_at=datetime.now(timezone.utc))
    position = models.VotePosition(
        canonical_id="la.metro:vote:1:position:1", vote=vote, official=official, position="yes"
    )
    session.add_all([jurisdiction, body, official, vote, position])
    session.commit()

    session.delete(official)
    session.commit()
    session.refresh(position)
    assert position.official_id is None


def test_foreign_keys_reject_orphan_policy_actions(session: Session) -> None:
    session.add(
        models.PolicyAction(
            canonical_id="la.metro:action:orphan",
            policy_item_id=999,
            action_type="published",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_core_relationships_preserve_typed_links(session: Session) -> None:
    jurisdiction = models.Jurisdiction(canonical_id="la.metro", name="Metro", kind="service_area")
    body = models.GovernmentBody(
        canonical_id="la.metro:body:board",
        name="Metro Board",
        body_type="board",
        jurisdiction=jurisdiction,
    )
    official = models.Official(
        canonical_id="la.metro:official:1",
        name="A. Official",
        role="board_member",
        government_body=body,
    )
    item = models.PolicyItem(
        canonical_id="la.metro:board-report:2026-0308",
        jurisdiction=jurisdiction,
        item_type="board_report",
        title="Service plan",
        lifecycle_phase="published",
    )
    action = models.PolicyAction(
        canonical_id="la.metro:board-report:2026-0308:action:1",
        policy_item=item,
        actor_body=body,
        action_type="published",
        sequence=1,
    )
    meeting = models.Meeting(
        canonical_id="la.metro:meeting:2026-03-08",
        government_body=body,
        meeting_type="board",
    )
    agenda = models.AgendaItem(
        canonical_id="la.metro:agenda:2026-03-08:1",
        meeting=meeting,
        policy_item=item,
        ordinal=1,
        title="Service plan",
    )
    vote = models.Vote(
        canonical_id="la.metro:vote:2026-03-08:1",
        policy_item=item,
        meeting=meeting,
        question="Adopt the plan?",
        result="passed",
        agenda_items=[agenda],
    )
    position = models.VotePosition(
        canonical_id="la.metro:vote:2026-03-08:1:official:1",
        vote=vote,
        official=official,
        position="yes",
    )
    project = models.Project(
        canonical_id="la.metro:project:service-plan",
        project_type="capital_program",
        name="Service plan implementation",
        owner_body=body,
    )
    geography = models.Geography(
        canonical_id="la.metro:route:20",
        geography_type="route",
        name="Route 20",
        jurisdiction=jurisdiction,
    )
    funding = models.FundingEvent(
        canonical_id="la.metro:funding:2026:1",
        event_type="authorization",
        amount=1000,
        currency="USD",
        policy_item=item,
        project=project,
    )
    item.projects.append(project)
    item.geographies.append(geography)
    project.geographies.append(geography)
    session.add_all([jurisdiction, item, action, meeting, vote, position, project, funding])
    session.commit()

    loaded = session.scalar(select(models.PolicyItem).where(models.PolicyItem.id == item.id))
    assert loaded is not None
    assert loaded.jurisdiction is jurisdiction
    assert loaded.actions[0].actor_body is body
    assert loaded.agenda_items[0].meeting is meeting
    assert loaded.votes[0].positions[0].official is official
    assert loaded.projects[0].geographies[0] is geography
    assert loaded.funding_events[0].project is project


def test_document_versions_keep_immutable_identity_and_hash_fields(session: Session) -> None:
    retrieved_at = datetime(2026, 7, 15, tzinfo=timezone.utc)
    document = models.DocumentVersion(
        canonical_id="la.metro:document:agenda:1:v1",
        source_system="metro",
        source_native_id="agenda-1",
        source_url="https://example.test/agenda-1.pdf",
        content_type="application/pdf",
        retrieved_at=retrieved_at,
        byte_hash="a" * 64,
        revision_key="v1",
    )
    session.add(document)
    session.commit()

    document.byte_hash = "b" * 64
    with pytest.raises(ValueError, match="immutable"):
        session.commit()
    session.rollback()
    session.refresh(document)
    assert document.byte_hash == "a" * 64
    assert document.revision_key == "v1"
    assert document.retrieved_at.replace(tzinfo=timezone.utc) == retrieved_at


def test_source_links_attach_claims_and_document_versions(session: Session) -> None:
    document = models.DocumentVersion(
        canonical_id="la.metro:document:agenda:2:v1",
        source_system="metro",
        source_native_id="agenda-2",
        source_url="https://example.test/agenda-2.pdf",
        content_type="application/pdf",
        retrieved_at=datetime(2026, 7, 15, tzinfo=timezone.utc),
        byte_hash="c" * 64,
        revision_key="v1",
    )
    claim = models.ExtractedClaim(
        canonical_id="la.metro:claim:2",
        subject="board",
        predicate="authorized",
        value="Service plan",
        extraction_version="claims-1",
        document_version=document,
    )
    source = models.SourceLink(
        label="Official agenda",
        url="https://example.test/agenda-2.pdf",
        source_system="metro",
        source_record_kind="agenda",
        source_native_id="agenda-2",
        retrieved_at=document.retrieved_at,
        document_version=document,
        claim=claim,
    )
    session.add(source)
    session.commit()

    loaded_claim = session.scalar(select(models.ExtractedClaim).where(models.ExtractedClaim.id == claim.id))
    assert loaded_claim is not None
    assert loaded_claim.document_version is document
    assert loaded_claim.source_links[0].url == source.url
    assert document.source_links[0].claim is claim


def test_source_links_require_one_subject_and_document(session: Session) -> None:
    document = models.DocumentVersion(
        canonical_id="la.metro:document:agenda:3:v1",
        source_system="metro",
        source_native_id="agenda-3",
        content_type="application/pdf",
        retrieved_at=datetime.now(timezone.utc),
        byte_hash="d" * 64,
        revision_key="v1",
    )
    invalid = models.SourceLink(
        label="Unattached",
        url="https://example.test/agenda-3.pdf",
        source_system="metro",
        source_record_kind="agenda",
        source_native_id="agenda-3",
        retrieved_at=document.retrieved_at,
        document_version=document,
    )
    session.add(invalid)
    with pytest.raises(IntegrityError):
        session.commit()
