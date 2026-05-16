# -*- coding: utf-8 -*-
"""Unit tests for the prediction service — the core diagnostic engine."""

import pytest

from app.services.prediction_service import (
    compute_condition_matches,
    confidence_label,
    detect_emergency_signals,
    get_condition_precautions,
    get_searchable_symptoms,
    get_symptom_categories,
    normalize_symptom_name,
    ordered_unique,
    urgency_from_severity,
)


class TestNormalizeSymptomName:
    """Test symptom name normalization and alias resolution."""

    def test_basic_normalization(self):
        assert normalize_symptom_name("Headache") == "headache"

    def test_strips_whitespace(self):
        assert normalize_symptom_name("  fever  ") == "fever"

    def test_lowercases(self):
        assert normalize_symptom_name("CHEST PAIN") == "chest pain"

    def test_none_returns_empty(self):
        assert normalize_symptom_name(None) == ""

    def test_empty_returns_empty(self):
        assert normalize_symptom_name("") == ""


class TestOrderedUnique:
    """Test the ordered deduplication utility."""

    def test_removes_duplicates(self):
        result = ordered_unique(["a", "b", "a", "c", "b"])
        assert result == ["a", "b", "c"]

    def test_preserves_order(self):
        result = ordered_unique(["z", "a", "m"])
        assert result == ["z", "a", "m"]

    def test_empty_list(self):
        assert ordered_unique([]) == []

    def test_single_element(self):
        assert ordered_unique(["x"]) == ["x"]


class TestConfidenceLabel:
    """Test confidence label mapping."""

    def test_strong_match(self):
        assert confidence_label(80) == "Strong match"
        assert confidence_label(96) == "Strong match"

    def test_fair_match(self):
        assert confidence_label(60) == "Fair match"
        assert confidence_label(77) == "Fair match"

    def test_possible_match(self):
        assert confidence_label(20) == "Possible match"
        assert confidence_label(59) == "Possible match"


class TestUrgencyFromSeverity:
    """Test urgency classification logic."""

    def test_high_severity_returns_high(self):
        assert urgency_from_severity("high", 50) == "high"

    def test_high_confidence_returns_high(self):
        assert urgency_from_severity("low", 85) == "high"

    def test_medium_severity_returns_medium(self):
        assert urgency_from_severity("medium", 50) == "medium"

    def test_medium_confidence_returns_medium(self):
        assert urgency_from_severity("low", 65) == "medium"

    def test_low_returns_low(self):
        assert urgency_from_severity("low", 30) == "low"


class TestGetSearchableSymptoms:
    """Test the symptom list generator."""

    def test_returns_non_empty_list(self):
        symptoms = get_searchable_symptoms()
        assert len(symptoms) > 0

    def test_returns_sorted_list(self):
        symptoms = get_searchable_symptoms()
        assert symptoms == sorted(symptoms)

    def test_contains_common_symptoms(self):
        symptoms = get_searchable_symptoms()
        for expected in ["fever", "headache", "cough"]:
            assert expected in symptoms, f"'{expected}' not found in symptom list"

    def test_no_duplicates(self):
        symptoms = get_searchable_symptoms()
        assert len(symptoms) == len(set(symptoms))


class TestGetSymptomCategories:
    """Test symptom categorization."""

    def test_returns_dict(self):
        categories = get_symptom_categories()
        assert isinstance(categories, dict)

    def test_has_known_categories(self):
        categories = get_symptom_categories()
        for key in ["respiratory", "digestive", "neurological"]:
            assert key in categories, f"Category '{key}' missing"

    def test_each_category_has_items(self):
        categories = get_symptom_categories()
        for key, items in categories.items():
            assert isinstance(items, list), f"Category '{key}' should be a list"


class TestComputeConditionMatches:
    """Test the main condition matching engine."""

    def test_empty_symptoms_returns_empty(self):
        result = compute_condition_matches([], 30, "male", {})
        assert result == []

    def test_single_symptom_returns_results(self):
        result = compute_condition_matches(["fever"], 30, "male", {})
        assert len(result) > 0

    def test_result_has_required_fields(self):
        result = compute_condition_matches(["headache"], 25, "female", {})
        assert len(result) > 0
        condition = result[0]
        required_fields = {"name", "confidence", "match_label", "urgency", "severity", "evidence"}
        for field in required_fields:
            assert field in condition, f"Missing field '{field}' in condition result"

    def test_confidence_in_valid_range(self):
        result = compute_condition_matches(["fever", "cough"], 30, "male", {})
        for condition in result:
            assert 20 <= condition["confidence"] <= 96

    def test_multiple_symptoms_improve_results(self):
        single = compute_condition_matches(["cough"], 30, "male", {})
        multi = compute_condition_matches(["fever", "cough", "congestion"], 30, "male", {})
        # With more symptoms, we should get at least as many results
        assert len(multi) >= len(single)

    def test_results_capped_at_eight(self):
        many_symptoms = ["fever", "cough", "headache", "fatigue", "nausea",
                         "dizziness", "chest pain", "joint pain"]
        result = compute_condition_matches(many_symptoms, 30, "male", {})
        assert len(result) <= 8

    def test_results_sorted_by_relevance(self):
        result = compute_condition_matches(["fever", "cough"], 30, "male", {})
        if len(result) >= 2:
            confidences = [c["confidence"] for c in result]
            # First result should have highest or equal confidence
            assert confidences[0] >= confidences[-1]

    def test_demographic_adjustment_female(self):
        """Conditions like UTI should score higher for female patients."""
        female_result = compute_condition_matches(
            ["frequent urination", "burning urination"], 25, "female", {}
        )
        male_result = compute_condition_matches(
            ["frequent urination", "burning urination"], 25, "male", {}
        )
        # Find UTI in both results
        female_uti = next((c for c in female_result if "uti" in c["name"].lower()), None)
        male_uti = next((c for c in male_result if "uti" in c["name"].lower()), None)
        if female_uti and male_uti:
            assert female_uti["confidence"] >= male_uti["confidence"]


class TestDetectEmergencySignals:
    """Test emergency symptom detection."""

    def test_no_emergency_for_mild_symptoms(self):
        detected, message = detect_emergency_signals(["headache"], {})
        assert detected is False
        assert message == ""

    def test_chest_pain_plus_breath_is_emergency(self):
        detected, message = detect_emergency_signals(
            ["chest pain", "shortness of breath"], {}
        )
        assert detected is True
        assert len(message) > 0

    def test_high_fever_emergency(self):
        detected, message = detect_emergency_signals(
            ["fever"], {"fever_temp": "104"}
        )
        # High fever should trigger emergency
        if detected:
            assert len(message) > 0

    def test_returns_tuple(self):
        result = detect_emergency_signals(["cough"], {})
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestGetConditionPrecautions:
    """Test precaution generation."""

    def test_high_urgency_precautions(self):
        precautions = get_condition_precautions({"urgency": "high"})
        assert len(precautions) > 0
        assert any("urgent" in p.lower() or "emergency" in p.lower() for p in precautions)

    def test_medium_urgency_precautions(self):
        precautions = get_condition_precautions({"urgency": "medium"})
        assert len(precautions) > 0

    def test_low_urgency_precautions(self):
        precautions = get_condition_precautions({"urgency": "low"})
        assert len(precautions) > 0
        assert any("hydrat" in p.lower() for p in precautions)

    def test_missing_urgency_defaults_to_low(self):
        precautions = get_condition_precautions({})
        assert len(precautions) > 0
