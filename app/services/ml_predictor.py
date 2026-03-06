import pickle
from pathlib import Path

_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    project_root = Path(__file__).resolve().parents[2]
    model_path = project_root / "model.pkl"
    if not model_path.exists():
        fallback_path = project_root / "model" / "model.pkl"
        model_path = fallback_path if fallback_path.exists() else model_path

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    with model_path.open("rb") as model_file:
        _MODEL = pickle.load(model_file)
    return _MODEL


def predict_disease(symptoms):
    """Predict disease label from a list of binary symptom values."""
    if not isinstance(symptoms, (list, tuple)):
        raise ValueError("symptoms must be a list or tuple of 0/1 values.")
    if not symptoms:
        raise ValueError("symptoms cannot be empty.")

    try:
        values = [int(item) for item in symptoms]
    except (TypeError, ValueError) as error:
        raise ValueError("symptoms must contain numeric 0/1 values.") from error

    if any(value not in (0, 1) for value in values):
        raise ValueError("Each symptom value must be 0 or 1.")

    model = _load_model()
    if hasattr(model, "n_features_in_") and len(values) != int(model.n_features_in_):
        raise ValueError(
            f"Expected {model.n_features_in_} symptom values, got {len(values)}."
        )

    prediction = model.predict([values])[0]
    return str(prediction)

