"""Unit tests for shared route helpers — utilities, formatters, session logic."""


from app.routes.helpers import (
    build_history_stats,
    classify_condition,
    clean_text,
    compute_check_streak,
    format_datetime_label,
    format_gender,
    highlight_match,
    parse_datetime_value,
    strip_icon_prefix,
)


class TestCleanText:
    def test_strips_whitespace(self):
        assert clean_text("  hello  ") == "hello"

    def test_enforces_max_length(self):
        assert len(clean_text("x" * 300, max_length=50)) == 50

    def test_none_returns_empty(self):
        assert clean_text(None) == ""

    def test_default_max_200(self):
        assert len(clean_text("a" * 250)) == 200


class TestStripIconPrefix:
    def test_strips_herb_icon(self):
        assert strip_icon_prefix("🌿 Turmeric tea") == "Turmeric tea"

    def test_strips_water_icon(self):
        assert strip_icon_prefix("💧 Drink water") == "Drink water"

    def test_no_icon_returns_original(self):
        assert strip_icon_prefix("Plain text") == "Plain text"

    def test_none_returns_empty(self):
        assert strip_icon_prefix(None) == ""


class TestParseDatetimeValue:
    def test_iso_format(self):
        result = parse_datetime_value("2024-06-15T10:30:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 6

    def test_short_format(self):
        result = parse_datetime_value("2024-06-15 10:30")
        assert result is not None
        assert result.hour == 10

    def test_none_returns_none(self):
        assert parse_datetime_value(None) is None

    def test_invalid_returns_none(self):
        assert parse_datetime_value("not-a-date") is None

    def test_empty_returns_none(self):
        assert parse_datetime_value("") is None


class TestFormatDatetimeLabel:
    def test_valid_iso(self):
        result = format_datetime_label("2024-06-15 10:30")
        assert "Jun" in result
        assert "2024" in result

    def test_none_returns_unknown(self):
        assert format_datetime_label(None) == "Unknown"

    def test_invalid_returns_original(self):
        assert format_datetime_label("garbage") == "garbage"


class TestFormatGender:
    def test_male(self):
        assert format_gender("male") == "Male"

    def test_female(self):
        assert format_gender("female") == "Female"

    def test_none(self):
        assert format_gender(None) == "Not set"

    def test_empty(self):
        assert format_gender("") == "Not set"


class TestClassifyCondition:
    def test_respiratory(self):
        condition = {"name": "Common Cold", "evidence": ["cough", "congestion"]}
        assert classify_condition(condition) == "Respiratory"

    def test_digestive(self):
        condition = {"name": "Digestive Infection", "evidence": ["nausea"]}
        assert classify_condition(condition) == "Digestive"

    def test_neurological(self):
        condition = {"name": "Migraine", "evidence": ["headache", "dizziness"]}
        assert classify_condition(condition) == "Neurological"

    def test_musculoskeletal(self):
        condition = {"name": "Joint Stiffness", "evidence": ["joint pain"]}
        assert classify_condition(condition) == "Musculoskeletal"

    def test_general_fallback(self):
        condition = {"name": "Unknown Thing", "evidence": []}
        assert classify_condition(condition) == "General"


class TestComputeCheckStreak:
    def test_empty_history(self):
        assert compute_check_streak([]) == 0

    def test_single_entry(self):
        entries = [{"checked_at": "2024-06-15 10:00"}]
        assert compute_check_streak(entries) == 1

    def test_consecutive_days(self):
        entries = [
            {"checked_at": "2024-06-15 10:00"},
            {"checked_at": "2024-06-14 09:00"},
            {"checked_at": "2024-06-13 11:00"},
        ]
        assert compute_check_streak(entries) == 3

    def test_gap_breaks_streak(self):
        entries = [
            {"checked_at": "2024-06-15 10:00"},
            {"checked_at": "2024-06-13 09:00"},  # gap on June 14
        ]
        assert compute_check_streak(entries) == 1


class TestBuildHistoryStats:
    def test_empty_history(self):
        stats = build_history_stats([])
        assert stats["total_checks"] == 0
        assert stats["health_score"] == 100
        assert stats["streak"] == 0

    def test_counts_symptoms(self):
        entries = [
            {"symptoms": ["fever", "cough"], "condition_summaries": [],
             "top_category": "General", "medium_high_condition_count": 0},
            {"symptoms": ["fever"], "condition_summaries": [],
             "top_category": "General", "medium_high_condition_count": 0},
        ]
        stats = build_history_stats(entries)
        assert stats["most_common_symptom"] == "Fever"
        assert stats["total_checks"] == 2

    def test_health_score_decreases_with_severity(self):
        entries = [
            {"symptoms": ["chest pain"], "condition_summaries": [],
             "top_category": "General", "medium_high_condition_count": 3},
        ]
        stats = build_history_stats(entries)
        assert stats["health_score"] < 100


class TestHighlightMatch:
    def test_highlights_match(self):
        from markupsafe import Markup
        result = highlight_match("Headache", "head")
        assert isinstance(result, Markup)
        assert "<strong>" in str(result)

    def test_no_query_returns_plain(self):
        result = highlight_match("Fever", "")
        assert "<strong>" not in str(result)
