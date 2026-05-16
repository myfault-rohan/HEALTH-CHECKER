# -*- coding: utf-8 -*-
"""Unit tests for the SHAP explainability service."""

import pytest


class TestSHAPServiceStructure:
    """Test SHAP service output format without loading the actual ML model."""

    def test_unavailable_dict_shape(self):
        from app.services.shap_service import _unavailable
        result = _unavailable()
        assert result["available"] is False
        assert result["features"] == []
        assert result["predicted_disease"] == ""
        assert "base_value" in result

    def test_format_explanation_empty_features(self):
        from app.services.shap_service import _format_explanation
        result = _format_explanation({
            "predicted_disease": "Fever",
            "features": [],
            "base_value": 0.5,
        })
        assert result["available"] is True
        assert result["predicted_disease"] == "Fever"
        assert result["features"] == []

    def test_format_explanation_filters_near_zero(self):
        from app.services.shap_service import _format_explanation
        features = [
            {"name": "cough", "display_name": "Cough", "value": 1, "shap_value": 0.5},
            {"name": "rash", "display_name": "Rash", "value": 0, "shap_value": 0.0005},  # tiny
            {"name": "fever", "display_name": "Fever", "value": 1, "shap_value": -0.3},
        ]
        result = _format_explanation({
            "predicted_disease": "Flu",
            "features": features,
            "base_value": 0.0,
        })
        # near-zero rash should be filtered
        names = [f["name"] for f in result["features"]]
        assert "rash" not in names
        assert "cough" in names
        assert "fever" in names

    def test_format_explanation_sorts_by_magnitude(self):
        from app.services.shap_service import _format_explanation
        features = [
            {"name": "runny_nose", "display_name": "Runny Nose", "value": 1, "shap_value": 0.1},
            {"name": "cough",      "display_name": "Cough",      "value": 1, "shap_value": 0.9},
            {"name": "headache",   "display_name": "Headache",   "value": 1, "shap_value": -0.4},
        ]
        result = _format_explanation({
            "predicted_disease": "Cold",
            "features": features,
            "base_value": 0.0,
        })
        assert result["features"][0]["name"] == "cough"   # highest magnitude first

    def test_format_explanation_bar_pct_range(self):
        from app.services.shap_service import _format_explanation
        features = [
            {"name": "fever",   "display_name": "Fever",   "value": 1, "shap_value": 0.8},
            {"name": "fatigue", "display_name": "Fatigue", "value": 1, "shap_value": 0.4},
        ]
        result = _format_explanation({
            "predicted_disease": "Flu",
            "features": features,
            "base_value": 0.0,
        })
        for feat in result["features"]:
            assert 0 <= feat["bar_pct"] <= 100

    def test_format_explanation_top_feature_is_100pct(self):
        from app.services.shap_service import _format_explanation
        features = [
            {"name": "fever",   "display_name": "Fever",   "value": 1, "shap_value": 0.8},
            {"name": "fatigue", "display_name": "Fatigue", "value": 1, "shap_value": 0.4},
        ]
        result = _format_explanation({
            "predicted_disease": "Flu",
            "features": features,
            "base_value": 0.0,
        })
        assert result["features"][0]["bar_pct"] == 100.0

    def test_format_explanation_direction_labels(self):
        from app.services.shap_service import _format_explanation
        features = [
            {"name": "fever",     "display_name": "Fever",     "value": 1, "shap_value":  0.5},
            {"name": "headache",  "display_name": "Headache",  "value": 1, "shap_value": -0.3},
        ]
        result = _format_explanation({
            "predicted_disease": "Flu",
            "features": features,
            "base_value": 0.0,
        })
        directions = {f["name"]: f["direction"] for f in result["features"]}
        assert directions["fever"] == "positive"
        assert directions["headache"] == "negative"

    def test_format_explanation_present_flag(self):
        from app.services.shap_service import _format_explanation
        features = [
            {"name": "fever",  "display_name": "Fever",  "value": 1, "shap_value": 0.5},
            {"name": "rash",   "display_name": "Rash",   "value": 0, "shap_value": 0.2},
        ]
        result = _format_explanation({
            "predicted_disease": "Flu",
            "features": features,
            "base_value": 0.0,
        })
        fever_feat = next(f for f in result["features"] if f["name"] == "fever")
        rash_feat  = next(f for f in result["features"] if f["name"] == "rash")
        assert fever_feat["present"] is True
        assert rash_feat["present"] is False

    def test_format_explanation_caps_at_10_features(self):
        from app.services.shap_service import _format_explanation
        features = [
            {"name": f"sym_{i}", "display_name": f"Sym {i}", "value": 1, "shap_value": float(i) / 10}
            for i in range(1, 16)  # 15 features
        ]
        result = _format_explanation({
            "predicted_disease": "X",
            "features": features,
            "base_value": 0.0,
        })
        assert len(result["features"]) <= 10


@pytest.mark.slow
class TestSHAPLocalExplanation:
    """Integration test — loads model.pkl and runs real SHAP values.

    Marked slow because TreeExplainer initialisation takes ~2-5 seconds.
    """

    def test_returns_available_true(self):
        from app.services.shap_service import get_local_shap_explanation
        result = get_local_shap_explanation(["fever", "cough"])
        assert result["available"] is True

    def test_has_features(self):
        from app.services.shap_service import get_local_shap_explanation
        result = get_local_shap_explanation(["fever", "cough"])
        assert len(result["features"]) > 0

    def test_predicted_disease_is_string(self):
        from app.services.shap_service import get_local_shap_explanation
        result = get_local_shap_explanation(["headache", "dizziness"])
        assert isinstance(result["predicted_disease"], str)
        assert len(result["predicted_disease"]) > 0

    def test_empty_symptoms_returns_unavailable(self):
        from app.services.shap_service import get_local_shap_explanation
        result = get_local_shap_explanation([])
        assert result["available"] is False
