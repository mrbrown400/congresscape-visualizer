from __future__ import annotations

from decimal import Decimal

import pytest

from app.ingest.city_finance import normalize_rows, paginate_rows, reconciliation_groups


def test_all_six_datasets_normalize_and_retain_raw_rows() -> None:
    datasets = ("pggv-e4fn", "5662-zu2k", "uyzw-yi8n", "hfus-a659", "ej7u-di9z", "ebs9-fdwv")
    rows = [{"row_id": "r1", "amount": "10.00", "vendor_id": "v1", "vendor_name": "Same Vendor"}]

    records = [normalize_rows(dataset, rows, {"rowsUpdatedAt": "2026-07-14T00:00:00Z"})[0] for dataset in datasets]

    assert {record.dataset_id for record in records} == set(datasets)
    assert all(record.raw["row_id"] == "r1" for record in records)
    assert all(record.amount == Decimal("10.00") for record in records)


def test_checkbook_composite_and_discretionary_row_keys() -> None:
    checkbook = normalize_rows(
        "pggv-e4fn",
        [{"data_source": "ERP", "transaction_id": "t1", "invoice": "i1", "purchase_order": "p1"}],
        {},
    )[0]
    discretionary = normalize_rows("ebs9-fdwv", [{"row_id": "stable-row"}], {})[0]

    assert checkbook.source_key == "ERP:t1:i1:p1"
    assert discretionary.source_key == "stable-row"
    assert checkbook.stale_metadata is True


def test_negative_and_missing_amounts_are_preserved_without_reconciliation_mix() -> None:
    records = normalize_rows(
        "pggv-e4fn",
        [{"transaction_id": "reversal", "amount": "-4.00"}, {"transaction_id": "missing"}],
        {"rowsUpdatedAt": "2026-07-14T00:00:00Z"},
    ) + normalize_rows("ej7u-di9z", [{"row_id": "balance", "amount": "100.00"}], {"rowsUpdatedAt": "2026-07-14T00:00:00Z"})

    groups = reconciliation_groups(records)
    assert groups["payment"][0].amount == Decimal("-4.00")
    assert groups["payment"][1].amount_state == "missing"
    assert set(groups) == {"payment", "balance"}


def test_pagination_is_deterministic_and_unknown_sources_fail() -> None:
    rows = ({"id": index} for index in range(5))
    assert paginate_rows(rows, page_size=2) == (({"id": 0}, {"id": 1}), ({"id": 2}, {"id": 3}), ({"id": 4},))
    with pytest.raises(ValueError, match="Unsupported"):
        normalize_rows("unknown", [], {})
