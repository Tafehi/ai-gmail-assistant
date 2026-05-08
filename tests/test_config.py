from datetime import date

import pytest

from src.gmail.config import parse_date_input
from src.gmail.delete import build_delete_query


class TestParseDateInput:
    def test_year_only(self):
        assert parse_date_input("2024") == date(2024, 1, 1)

    def test_year_month_dot(self):
        assert parse_date_input("03.2024") == date(2024, 3, 1)

    def test_day_month_year_dot(self):
        assert parse_date_input("15.03.2024") == date(2024, 3, 15)

    def test_year_month_dash(self):
        assert parse_date_input("2024-03") == date(2024, 3, 1)

    def test_year_month_day_dash(self):
        assert parse_date_input("2024-03-15") == date(2024, 3, 15)

    def test_year_month_day_slash(self):
        assert parse_date_input("2024/03/15") == date(2024, 3, 15)

    def test_whitespace_stripped(self):
        assert parse_date_input("  2024  ") == date(2024, 1, 1)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_date_input("not-a-date")


class TestBuildDeleteQuery:
    def test_basic_query(self):
        result = build_delete_query(date(2024, 3, 1))
        assert result == "before:2024/03/01 -label:Keep"

    def test_exclude_keep_false(self):
        result = build_delete_query(date(2024, 3, 1), exclude_keep=False)
        assert result == "before:2024/03/01"

    def test_different_date(self):
        result = build_delete_query(date(2023, 12, 15))
        assert result == "before:2023/12/15 -label:Keep"
