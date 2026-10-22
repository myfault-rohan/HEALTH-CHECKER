"""
Improved Dataset Builder for Health Checker ML model.
=========================================================
Strategy:
  - Consolidate semantically near-identical conditions to avoid
    impossible-to-learn ambiguity (e.g. 'Flu' vs 'Cold/Flu' vs 'Viral Fever')
  - Use score >= 1.0 (not > 1.0) to define characteristic symptoms
  - Only keep conditions with >= 2 unique characteristic symptoms
    (conditions with 1 symptom are unlearnable with binary features)
  - Generate rows with DETERMINISTIC core symptoms + Gaussian noise
    (not pure random sampling which creates duplicate vectors)
  - Drop conditions with >60% symptom overlap with another condition
    (they are the same disease under different names -> merge them)
  - Produce 300 rows per kept condition (balanced classes)

Run with: python model/build_dataset.py
"""

import csv
import os
import random
import sys
from collections import defaultdict

random.seed(42)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.prediction_service import symptoms_conditions

FEATURES = [
    "headache", "dizziness", "blurred_vision", "confusion", "cough",
    "shortness_of_breath", "chest_pain", "wheezing", "palpitations",
    "abdominal_pain", "nausea", "vomiting", "diarrhea", "constipation",
    "bloating", "heartburn", "urinary_problems", "fever", "fatigue",
    "chills", "night_sweats", "weight_loss", "insomnia", "loss_of_appetite",
    "sore_throat", "runny_nose", "sneezing", "congestion", "rash",
    "swelling", "joint_pain", "back_pain", "muscle_pain", "stiffness",
    "acidity", "leg_pain", "body_weakness", "stomach_pain", "waist_pain",
    "watery_eyes", "nightfall", "menstrual_pain", "dehydration", "cold", "stress"
]
FEATURES_SET = set(FEATURES)

# Consolidation map: merge near-duplicate conditions into canonical names
# Key = raw KB name, Value = canonical name to use
MERGE_MAP = {
    # Flu variants
    "Flu":                       "Flu",
    "Cold/Flu":                  "Flu",
    "Viral Fever":               "Flu",
    "Fever Onset":               "Flu",
    "Influenza":                 "Flu",
    # Cold variants
    "Cold":                      "Common Cold",
    "Seasonal Cold":             "Common Cold",
    "Common Cold":               "Common Cold",
    # Stress variants
    "Stress":                    "Chronic Stress",
    "Chronic Stress":            "Chronic Stress",
    "Stress-related":            "Chronic Stress",
    "Stress/Anxiety":            "Chronic Stress",
    "Stress-related Headache":   "Tension Headache",
    "Burnout":                   "Chronic Stress",
    # Headache
    "Tension Headache":          "Tension Headache",
    # Anxiety variants
    "Anxiety":                   "Anxiety Disorder",
    "Anxiety-related Breathing": "Anxiety Disorder",
    "Restlessness":              "Anxiety Disorder",
    # GI variants
    "Gas Formation":             "Gas/Bloating",
    "Gas/Acidity":               "Gas/Bloating",
    "Gas/Bloating":              "Gas/Bloating",
    "Indigestion":               "Acid Reflux",
    "Acid Reflux":               "Acid Reflux",
    "Acidity":                   "Acid Reflux",
    "Spicy Food Sensitivity":    "Acid Reflux",
    "Gastritis":                 "Gastritis",
    "Stomach Flu":               "Gastroenteritis",
    "Digestive Infection":       "Gastroenteritis",
    "Digestive Issue":           "Gastroenteritis",
    "Digestive Upset":           "Gastroenteritis",
    "Food Poisoning":            "Gastroenteritis",
    "Digestive Weakness":        "Gastroenteritis",
    "Digestive sluggishness":    "Gastroenteritis",
    "Food Intolerance":          "Gastroenteritis",
    # Fatigue variants
    "Fatigue":                   "General Fatigue",
    "Low Energy":                "General Fatigue",
    "Weakness":                  "General Fatigue",
    "Weakness/Low Energy":       "General Fatigue",
    "Overwork":                  "General Fatigue",
    "Overexertion":              "General Fatigue",
    "Need for Rest":             "General Fatigue",
    "Body Ache":                 "General Fatigue",
    "Circulatory Fatigue":       "General Fatigue",
    "Body Detoxification":       "General Fatigue",
    "Body Infection":            "General Fatigue",
    "Metabolism Issues":         "General Fatigue",
    # Allergy variants
    "Allergies":                 "Allergy",
    "Allergic Rhinitis":         "Allergy",
    "Respiratory Allergy":       "Allergy",
    "Dust Allergy":              "Allergy",
    "Dust Sensitivity":          "Allergy",
    "Skin Allergy":              "Allergy",
    "Heat Rash":                 "Allergy",
    # Respiratory
    "Bronchial Irritation":      "Bronchitis",
    "Allergic Bronchitis":       "Bronchitis",
    "Chest Congestion":          "Bronchitis",
    "Respiratory Congestion":    "Bronchitis",
    "Sinus Congestion":          "Sinusitis",
    "Sinusitis":                 "Sinusitis",
    "Nasal Congestion":          "Sinusitis",
    "Upper Respiratory Infection": "Sinusitis",
    "Asthma (Breathlessness)":   "Asthma",
    # Throat
    "Tonsillitis":               "Throat Infection",
    "Throat Infection":          "Throat Infection",
    # Eye
    "Eye Strain":                "Eye Strain",
    "Digital Eye Fatigue":       "Eye Strain",
    "Allergic Eye Irritation":   "Eye Strain",
    "Viral Eye Irritation":      "Eye Strain",
    "Vitamin A Deficiency":      "Eye Strain",
    # Musculoskeletal
    "Arthritis Support":         "Arthritis",
    "Joint Pain":                "Arthritis",
    "Joint Stiffness":           "Arthritis",
    "Morning Stiffness":         "Arthritis",
    "Back Stiffness":            "Back Pain",
    "Lower Back Strain":         "Back Pain",
    "Poor Posture":              "Back Pain",
    "Posture-related Pain":      "Back Pain",
    "Muscle Spasm":              "Muscle Strain",
    # Sleep
    "Sleep Disorder":            "Insomnia",
    "Sleep Disturbance":         "Insomnia",
    # Other
    "Dehydration":               "Dehydration",
    "Heat Exhaustion":           "Dehydration",
    "Low Blood Sugar":           "Hypoglycemia",
    "Hypoglycemia":              "Hypoglycemia",
    "Migraine":                  "Migraine",
    "Anemia":                    "Anemia",
    "Dysmenorrhea":              "Dysmenorrhea",
    "Hormonal Cramps":           "Dysmenorrhea",
    "Hormonal Changes":          "Dysmenorrhea",
    "Pelvic Muscle Spasm":       "Dysmenorrhea",
    "Menstrual Pain":            "Dysmenorrhea",
    "Frequent Urination":        "Urinary Tract Infection",
    "Urinary Tract Infection (UTI)": "Urinary Tract Infection",
    "Kidney Health Support":     "Urinary Tract Infection",
    "Thyroid Support Needed":    "Thyroid Disorder",
    "Vertigo (Inner ear imbalance)": "Vertigo",
    "Liver Support Needed":      "Liver Issue",
    "Chronic Cholestasis":       "Liver Issue",
    "Nocturnal Emission":        "Nocturnal Emission",
    "Vata Imbalance":            "General Fatigue",
    "Eczema Support":            "Allergy",
    "Water Retention":           "Water Retention",
    "Dry Cough":                 "Bronchitis",
    "Morning Sickness":          "Nausea",
    "Inflammation":              "Arthritis",
    "Injury":                    "Muscle Strain",
    "Low Fiber Diet":            "Constipation",
    "Excess Caffeine":           "Insomnia",
    "Viral Fever":               "Flu",
    "Nasal Congestion":          "Sinusitis",
}

ROWS_PER_CLASS = 300


def clean_feature(f):
    return f.replace(" ", "_")


def build_consolidated_blueprints():
    """Build condition -> {symptom: max_score} merging via MERGE_MAP."""
    blueprints = defaultdict(dict)

    for sym_raw, data in symptoms_conditions.items():
        sym_clean = clean_feature(sym_raw)
        if sym_clean not in FEATURES_SET:
            continue
        for condition in data.get("conditions", []):
            raw_name = condition["name"]
            canonical = MERGE_MAP.get(raw_name, raw_name)
            score = float(condition.get("score", 1.0))
            # Keep the max score if symptom seen from multiple source conditions
            existing = blueprints[canonical].get(sym_clean, 0.0)
            blueprints[canonical][sym_clean] = max(existing, score)

    return dict(blueprints)


def jaccard_overlap(set_a, set_b):
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / len(set_a | set_b)


def deduplicate_conditions(blueprints, overlap_threshold=0.75):
    """
    Remove conditions that are too similar to a higher-count condition.
    Keeps the one with more DISTINCT symptom signal.
    """
    canonical_syms = {name: set(syms.keys()) for name, syms in blueprints.items()}
    # Sort by symptom count desc (richest conditions survive)
    sorted_names = sorted(canonical_syms.keys(), key=lambda n: len(canonical_syms[n]), reverse=True)

    kept = []
    dropped = {}
    for name in sorted_names:
        s_a = canonical_syms[name]
        dominated = False
        for keep_name in kept:
            s_b = canonical_syms[keep_name]
            j = jaccard_overlap(s_a, s_b)
            if j >= overlap_threshold:
                dominated = True
                dropped[name] = keep_name
                break
        if not dominated:
            kept.append(name)

    return kept, dropped


def generate_rows_for_condition(disease, symptom_scores, n=ROWS_PER_CLASS):
    """
    Generate n augmented rows for a given disease.
    Core symptoms (score>=2) are always included.
    Secondary symptoms (score==1) are randomly included 30-70% of the time.
    Noise: 1-2 random non-associated features flipped 1 ~15% of the time.
    """
    sorted_syms = sorted(symptom_scores.items(), key=lambda x: x[1], reverse=True)
    core_syms  = [s for s, sc in sorted_syms if sc >= 2.0]
    sec_syms   = [s for s, sc in sorted_syms if 1.0 <= sc < 2.0]
    # If no high-score symptoms, promote all to core
    if not core_syms:
        core_syms = [s for s, _ in sorted_syms]
        sec_syms  = []

    other_feats = [f for f in FEATURES if f not in symptom_scores]
    rows = []
    for _ in range(n):
        row = {f: 0 for f in FEATURES}
        row["disease"] = disease

        # Always include ALL core symptoms
        for sym in core_syms:
            row[sym] = 1

        # Randomly include secondary symptoms (50% chance each)
        for sym in sec_syms:
            if random.random() < 0.5:
                row[sym] = 1

        # Add tiny noise: ~15% chance to flip one non-associated feature to 1
        if other_feats and random.random() < 0.15:
            noise_feat = random.choice(other_feats)
            row[noise_feat] = 1

        rows.append(row)
    return rows


def generate_dynamic_dataset():
    print("=" * 60)
    print("  Health Checker Pro -- Improved Dataset Builder")
    print("=" * 60)

    # Build consolidated blueprints
    blueprints = build_consolidated_blueprints()
    print(f"\n  Conditions after merge map: {len(blueprints)}")

    # Require at least 2 characteristic symptoms to be learnable
    learnable = {name: syms for name, syms in blueprints.items() if len(syms) >= 2}
    dropped_sparse = set(blueprints.keys()) - set(learnable.keys())
    if dropped_sparse:
        print(f"  Dropped {len(dropped_sparse)} conditions with <2 symptoms: {sorted(dropped_sparse)}")
    blueprints = learnable

    # Remove near-duplicate conditions
    kept_names, dedup_dropped = deduplicate_conditions(blueprints, overlap_threshold=0.75)
    if dedup_dropped:
        print(f"  Merged/dropped {len(dedup_dropped)} near-duplicate conditions:")
        for dropped, merged_into in sorted(dedup_dropped.items()):
            print(f"    '{dropped}' -> '{merged_into}'")
    blueprints = {n: blueprints[n] for n in kept_names}
    print(f"\n  Final unique learnable conditions: {len(blueprints)}")

    # Generate rows
    dataset_rows = []
    for disease, symptom_scores in sorted(blueprints.items()):
        rows = generate_rows_for_condition(disease, symptom_scores, n=ROWS_PER_CLASS)
        dataset_rows.extend(rows)
        print(f"    {disease:<40} {len(rows)} rows  "
              f"(core: {sum(1 for s,sc in symptom_scores.items() if sc>=2.0)}, "
              f"sec: {sum(1 for s,sc in symptom_scores.items() if 1.0<=sc<2.0)})")

    # Shuffle
    random.shuffle(dataset_rows)

    # Save
    csv_out = os.path.join(os.path.dirname(__file__), "dataset.csv")
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FEATURES + ["disease"])
        writer.writeheader()
        for r in dataset_rows:
            writer.writerow(r)

    print(f"\n  Dataset saved to {csv_out}")
    print(f"  Total rows: {len(dataset_rows)}")
    print(f"  Classes   : {len(blueprints)}")
    print(f"  Rows/class: {ROWS_PER_CLASS}")
    print("=" * 60)


if __name__ == "__main__":
    generate_dynamic_dataset()
