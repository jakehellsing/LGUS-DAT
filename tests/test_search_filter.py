"""Tests for the search filter helper."""

from dataclasses import dataclass

from lgus_dat.ui.search_filter import filter_by_search, matches_search


@dataclass
class _Record:
    employee_id: str
    name: str | None = None


def test_matches_search_empty_query_returns_true() -> None:
    assert matches_search("", "any", "value") is True
    assert matches_search("   ", "any", "value") is True


def test_matches_search_case_insensitive() -> None:
    assert matches_search("foo", "Foo Bar") is True
    assert matches_search("FOO", "foo bar") is True
    assert matches_search("foo", "baz") is False


def test_matches_search_across_multiple_values() -> None:
    assert matches_search("2", "1", "2", "3") is True
    assert matches_search("test", "other", None, "TESTING") is True


def test_filter_by_search_ignores_empty_query() -> None:
    records = [_Record("1", "Alice"), _Record("2", "Bob")]
    assert filter_by_search(records, "", [lambda r: r.employee_id, lambda r: r.name]) == records


def test_filter_by_search_matches_any_accessor() -> None:
    records = [_Record("1", "Alice Smith"), _Record("2", "Bob Jones"), _Record("3", "Charlie")]
    result = filter_by_search(records, "smith", [lambda r: r.employee_id, lambda r: r.name])
    assert [r.employee_id for r in result] == ["1"]


def test_filter_by_search_matches_id() -> None:
    records = [_Record("100", "Alice"), _Record("101", "Bob")]
    result = filter_by_search(records, "101", [lambda r: r.employee_id, lambda r: r.name])
    assert [r.employee_id for r in result] == ["101"]
