from app.services.check_service import (
    assess_quality,
    build_check_result,
    build_remedies,
    enrich_conditions,
    merge_ml_prediction,
)


class TestBuildRemedies:
    def test_empty_symptoms_returns_empty(self):
        remedies, suggestions = build_remedies([])
        assert remedies == []
        assert suggestions == []

    def test_known_symptom_returns_remedies_and_suggestions(self):
        remedies, suggestions = build_remedies(["headache"])
        assert len(remedies) > 0
        assert len(suggestions) > 0
        assert any("water" in item.lower() or "rest" in item.lower() for item in suggestions)


class TestMergeMLPrediction:
    def test_ignores_error_and_no_match(self):
        conditions = [{"name": "Flu", "confidence": 50}]
        res = merge_ml_prediction(conditions, "Prediction Error")
        assert res == conditions

        res2 = merge_ml_prediction(conditions, "No clear match")
        assert res2 == conditions

    def test_inserts_new_ml_prediction(self):
        conditions = [{"name": "Flu", "confidence": 50}]
        res = merge_ml_prediction(conditions, "Migraine")
        assert len(res) == 2
        assert res[0]["name"] == "Migraine"
        assert res[0]["confidence"] == 95
        assert res[0]["match_label"] == "Machine Learning Match"

    def test_boosts_existing_prediction(self):
        conditions = [{"name": "Migraine", "confidence": 50, "match_label": "Rule Match"}]
        res = merge_ml_prediction(conditions, "Migraine")
        assert len(res) == 1
        assert res[0]["name"] == "Migraine"
        assert res[0]["confidence"] == 70  # 50 + 20
        assert res[0]["match_label"] == "Verified by Machine Learning"


class TestEnrichConditions:
    def test_enriches_with_kb_details(self):
        conditions = [{"name": "Migraine", "confidence": 50, "evidence": ["headache"]}]
        res = enrich_conditions(conditions)
        assert len(res) == 1
        assert "description" in res[0]
        assert "ayurvedic_remedies" in res[0]
        assert "precautions" in res[0]
        assert res[0]["category"] == "Neurological"


class TestAssessQuality:
    def test_limited_quality(self):
        q, s = assess_quality(["fever"], "")
        assert q == "limited"
        assert "at least 2-3" in s.lower()

    def test_good_quality(self):
        q, s = assess_quality(["fever", "cough"], "")
        assert q == "good"
        assert "confidence improves" in s.lower()

    def test_high_quality(self):
        q, s = assess_quality(["fever", "cough", "headache", "fatigue", "chills"], "")
        assert q == "high"
        assert "good symptom coverage" in s.lower()

    def test_cough_type_appended(self):
        q, s = assess_quality(["cough", "fever"], "dry")
        assert "cough type noted as dry" in s.lower()


class TestBuildCheckResult:
    def test_assembles_correct_shape(self):
        res = build_check_result(
            checked_at="2026-05-24 12:00",
            selected_symptoms=["headache"],
            predicted_disease="Tension Headache",
            condition_details=[],
            remedies=["Rest"],
            emergency_detected=False,
            emergency_message="",
            quality="good",
            suggestion="Fine",
            lifestyle_suggestions=[],
            age=25,
            gender="male",
            shap_data={"available": False},
        )
        assert res["checked_at"] == "2026-05-24 12:00"
        assert res["selected_symptoms"] == ["headache"]
        assert res["predicted_disease"] == "Tension Headache"
        assert res["remedies"] == ["Rest"]
        assert res["analysis"]["quality"] == "good"
        assert res["patient"]["age"] == 25
