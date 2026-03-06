"""Simple rule-based disease prediction (no ML libraries required)."""

from typing import Iterable

# Fixed symptom order used when input is a binary 0/1 vector.
FEATURE_SYMPTOMS = [
    "fever",
    "cough",
    "fatigue",
    "headache",
    "nausea",
    "vomiting",
    "chest pain",
    "dizziness",
    "sore throat",
    "runny nose",
    "abdominal pain",
    "diarrhea",
    "rash",
    "joint pain",
    "chills",
    "sweating",
    "weight loss",
    "anxiety",
    "depression",
    "blurred vision",
    "shortness of breath",
    "muscle pain",
    "weakness",
    "insomnia",
    "loss of appetite",
]

# Rule base: each disease maps to common symptoms.
DISEASE_SYMPTOMS = {
    "Flu": {"fever", "cough", "fatigue", "headache", "chills", "muscle pain"},
    "Common Cold": {"cough", "sore throat", "runny nose", "fatigue"},
    "Malaria": {"fever", "chills", "sweating", "headache", "nausea", "weakness"},
    "Food Poisoning": {
        "nausea",
        "vomiting",
        "abdominal pain",
        "diarrhea",
        "fever",
    },
    "Heart Disease": {
        "chest pain",
        "shortness of breath",
        "fatigue",
        "sweating",
        "dizziness",
    },
    "Dengue": {"fever", "rash", "joint pain", "headache", "muscle pain"},
    "Typhoid": {"fever", "abdominal pain", "loss of appetite", "weakness", "headache"},
    "Migraine": {"headache", "nausea", "vomiting", "dizziness", "blurred vision"},
}


def _normalize_symptom_name(value):
    return str(value or "").strip().lower().replace("_", " ")


def _from_binary_vector(values: Iterable[int]):
    values = list(values)
    if len(values) != len(FEATURE_SYMPTOMS):
        raise ValueError(
            f"Expected {len(FEATURE_SYMPTOMS)} binary symptom values, got {len(values)}."
        )
    return {
        FEATURE_SYMPTOMS[index]
        for index, value in enumerate(values)
        if int(value) == 1
    }


def predict_disease(symptoms):
    """
    Predict a disease using rule-based symptom matching.

    `symptoms` can be:
    - a list of 0/1 values in FEATURE_SYMPTOMS order, or
    - a list of symptom names.
    """
    if not isinstance(symptoms, (list, tuple)):
        raise ValueError("symptoms must be provided as a list or tuple.")

    if not symptoms:
        return "No clear match"

    # Accept binary vectors (0/1) as requested.
    if all(str(value).strip() in {"0", "1"} for value in symptoms):
        selected = _from_binary_vector([int(value) for value in symptoms])
    else:
        selected = {
            _normalize_symptom_name(value)
            for value in symptoms
            if _normalize_symptom_name(value)
        }

    best_disease = "No clear match"
    best_match_count = 0
    best_coverage = 0.0

    for disease, disease_symptoms in DISEASE_SYMPTOMS.items():
        matches = len(selected.intersection(disease_symptoms))
        if matches == 0:
            continue

        coverage = matches / len(disease_symptoms)
        if matches > best_match_count or (
            matches == best_match_count and coverage > best_coverage
        ):
            best_disease = disease
            best_match_count = matches
            best_coverage = coverage

    return best_disease

