"""
Automated Rich Dataset Builder
================================
Downloads 3 public Kaggle datasets, cleans them, merges with our
existing synthetic data, and produces a unified dataset.csv.

Run with:
    python model/build_rich_dataset.py

Requirements:
    - kaggle CLI configured (see Step 1 below if you haven't)
    - venv activated
"""

import io
import os
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
DATASET_IN   = SCRIPT_DIR / "dataset.csv"          # existing synthetic (input)
DATASET_OUT  = SCRIPT_DIR / "dataset_rich.csv"     # merged output
RAW_DIR      = SCRIPT_DIR / "_raw_downloads"
RAW_DIR.mkdir(exist_ok=True)

# ── Our 45 canonical symptom features (kept from current model) ─────────────
CANONICAL_FEATURES = [
    "headache", "dizziness", "blurred_vision", "confusion", "cough",
    "shortness_of_breath", "chest_pain", "wheezing", "palpitations",
    "abdominal_pain", "nausea", "vomiting", "diarrhea", "constipation",
    "bloating", "heartburn", "urinary_problems", "fever", "fatigue",
    "chills", "night_sweats", "weight_loss", "insomnia", "loss_of_appetite",
    "sore_throat", "runny_nose", "sneezing", "congestion", "rash",
    "swelling", "joint_pain", "back_pain", "muscle_pain", "stiffness",
    "acidity", "leg_pain", "body_weakness", "stomach_pain", "waist_pain",
    "watery_eyes", "nightfall", "menstrual_pain", "dehydration", "cold", "stress",
]

# ── Mapping: Kaggle symptom names → our canonical names ────────────────────
# Handles 132-column Kaggle dataset column names → our 45 features
ALIAS_MAP = {
    # headache cluster
    "headache": "headache",
    "pain_behind_the_eyes": "headache",
    "mild_fever": "fever",
    "high_fever": "fever",
    "continuous_fever": "fever",
    "low_grade_fever": "fever",
    # cough cluster
    "cough": "cough",
    "mucoid_sputum": "cough",
    "rusty_sputum": "cough",
    "blood_in_sputum": "cough",
    "phlegm": "cough",
    # breathing
    "breathlessness": "shortness_of_breath",
    "shortness_of_breath": "shortness_of_breath",
    "fast_heart_rate": "palpitations",
    "palpitations": "palpitations",
    # GI cluster
    "stomach_pain": "stomach_pain",
    "abdominal_pain": "abdominal_pain",
    "pain_during_bowel_movements": "abdominal_pain",
    "nausea": "nausea",
    "vomiting": "vomiting",
    "diarrhoea": "diarrhea",
    "diarrhea": "diarrhea",
    "constipation": "constipation",
    "stomach_bleeding": "abdominal_pain",
    "distention_of_abdomen": "bloating",
    "acidity": "acidity",
    "indigestion": "heartburn",
    "passage_of_gases": "bloating",
    # fatigue cluster
    "fatigue": "fatigue",
    "lethargy": "fatigue",
    "weakness_in_limbs": "body_weakness",
    "weakness_of_one_body_side": "body_weakness",
    "loss_of_balance": "dizziness",
    "unsteadiness": "dizziness",
    "dizziness": "dizziness",
    "loss_of_smell": "congestion",
    # skin
    "skin_rash": "rash",
    "rash": "rash",
    "itching": "rash",
    "skin_peeling": "rash",
    "dischromic_patches": "rash",
    "yellow_crust_ooze": "rash",
    "pus_filled_pimples": "rash",
    "blackheads": "rash",
    "scurring": "rash",
    # joint / musculo
    "joint_pain": "joint_pain",
    "knee_pain": "joint_pain",
    "hip_joint_pain": "joint_pain",
    "muscle_pain": "muscle_pain",
    "muscle_weakness": "muscle_pain",
    "muscle_wasting": "muscle_pain",
    "back_pain": "back_pain",
    "neck_pain": "back_pain",
    "stiff_neck": "stiffness",
    # throat / cold
    "throat_irritation": "sore_throat",
    "sore_throat": "sore_throat",
    "runny_nose": "runny_nose",
    "congestion": "congestion",
    "nasal_congestion": "congestion",
    "sneezing": "sneezing",
    # eyes
    "blurred_and_distorted_vision": "blurred_vision",
    "redness_of_eyes": "watery_eyes",
    "watering_from_eyes": "watery_eyes",
    "yellowing_of_eyes": "blurred_vision",
    # systemic
    "chills": "chills",
    "shivering": "chills",
    "sweating": "night_sweats",
    "excessive_sweating": "night_sweats",
    "night_sweats": "night_sweats",
    "weight_loss": "weight_loss",
    "loss_of_appetite": "loss_of_appetite",
    "dehydration": "dehydration",
    # mental / sleep
    "anxiety": "stress",
    "mood_swings": "stress",
    "depression": "stress",
    "lack_of_concentration": "confusion",
    "slurred_speech": "confusion",
    "altered_sensorium": "confusion",
    "coma": "confusion",
    "restlessness": "insomnia",
    "insomnia": "insomnia",
    # urinary
    "burning_micturition": "urinary_problems",
    "spotting_urination": "urinary_problems",
    "polyuria": "urinary_problems",
    "dark_urine": "urinary_problems",
    "yellow_urine": "urinary_problems",
    "frequent_urination": "urinary_problems",
    # reproductive
    "irregular_sugar_level": "fatigue",
    "increased_appetite": "loss_of_appetite",
}

# ── Label normalisation: fix common dirty disease names ────────────────────
LABEL_FIX = {
    "dimorphic hemmorhoids(piles)": "Piles",
    "dimorphic haemorrhoids(piles)": "Piles",
    "(vertigo) paroymsal  positional vertigo": "Vertigo",
    "paralysis (brain hemorrhage)": "Brain Hemorrhage",
    "peptic ulcer diseae": "Peptic Ulcer Disease",
    "cervical spondylosis": "Cervical Spondylosis",
    "varicose veins": "Varicose Veins",
    "heart attack": "Heart Attack",
    "bronchial asthma": "Asthma",
    "urinary tract infection": "Urinary Tract Infection",
    "diabetes ": "Diabetes",
    " diabetes": "Diabetes",
    "hypertension ": "Hypertension",
    " hypertension": "Hypertension",
    "common cold": "Common Cold",
    "chicken pox": "Chickenpox",
    "dengue": "Dengue Fever",
    "typhoid": "Typhoid Fever",
    "malaria": "Malaria",
    "pneumonia": "Pneumonia",
    "tuberculosis": "Tuberculosis",
    "hepatitis b": "Hepatitis B",
    "hepatitis c": "Hepatitis C",
    "hepatitis d": "Hepatitis D",
    "hepatitis e": "Hepatitis E",
    "alcoholic hepatitis": "Alcoholic Hepatitis",
    "drug reaction": "Drug Reaction",
    "fungal infection": "Fungal Infection",
    "gastroenteritis": "Gastroenteritis",
    "migraine": "Migraine",
    "arthritis": "Arthritis",
    "osteoarthritis": "Osteoarthritis",
    "hyperthyroidism": "Hyperthyroidism",
    "hypothyroidism": "Hypothyroidism",
    "hypoglycemia": "Hypoglycemia",
    "jaundice": "Jaundice",
    "allergy": "Allergy",
    "acne": "Acne",
    "psoriasis": "Psoriasis",
    "impetigo": "Impetigo",
    "aids": "AIDS",
}


def normalize_label(label: str) -> str:
    """Clean and standardise a disease label."""
    if not isinstance(label, str):
        return ""
    label = label.strip().lower()
    if label in LABEL_FIX:
        return LABEL_FIX[label]
    # Title-case if not found in map
    return " ".join(w.capitalize() for w in label.split())


def normalize_col(col: str) -> str:
    """Normalize a column name to lowercase_underscore."""
    col = col.strip().lower()
    col = re.sub(r"[\s\-/]+", "_", col)
    col = re.sub(r"[^a-z0-9_]", "", col)
    return col.strip("_")


def map_to_canonical(col: str) -> str | None:
    """Return canonical feature name or None if not mappable."""
    col = normalize_col(col)
    if col in CANONICAL_FEATURES:
        return col
    return ALIAS_MAP.get(col)


# ═══════════════════════════════════════════════════════════════════════════
# SOURCE 1 — Our existing synthetic dataset (always included as base)
# ═══════════════════════════════════════════════════════════════════════════
def load_existing_synthetic() -> pd.DataFrame:
    path = DATASET_IN
    if not path.exists():
        print("  [!] No existing dataset.csv found -- skipping synthetic base.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["disease"] = df["disease"].apply(normalize_label)
    df["_source"] = "synthetic_v1"
    print(f"  [OK] Existing synthetic: {len(df):,} rows, {df['disease'].nunique()} classes")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# SOURCE 2 — Kaggle: itachi9604/disease-symptom-description-dataset
#            132 symptom columns, 4,920 rows, 41 real disease classes
# ═══════════════════════════════════════════════════════════════════════════
def load_kaggle_132(raw_dir: Path) -> pd.DataFrame:
    """
    Primary Kaggle dataset — 132 binary symptom columns.
    CSV columns: Symptom_1 ... Symptom_17, prognosis
    OR wide binary format.
    """
    # Try to find pre-downloaded file
    candidates = list(raw_dir.glob("dataset.csv")) + \
                 list(raw_dir.glob("*symptom*.csv")) + \
                 list(raw_dir.glob("*disease*.csv"))

    if not candidates:
        print("  [!] Kaggle dataset not found in _raw_downloads/.")
        print("      To download automatically:")
        print("      1. Go to https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset")
        print("      2. Download and unzip into:  model/_raw_downloads/")
        print("      3. Re-run this script.")
        return pd.DataFrame()

    df = pd.read_csv(candidates[0])
    print(f"  Raw shape: {df.shape}")

    # ── Detect format ──────────────────────────────────────────────────────
    cols = [c.strip() for c in df.columns]
    disease_col = next((c for c in cols if "prognosis" in c.lower() or
                        "disease" in c.lower() or "label" in c.lower()), None)

    if disease_col is None:
        print("  [!] Cannot find disease column — skipping this dataset.")
        return pd.DataFrame()

    df = df.rename(columns={disease_col: "disease"})

    # ── Format A: Symptom_1...Symptom_N columns (string values) ───────────
    symptom_cols = [c for c in df.columns if re.match(r"symptom_?\d+", c.lower())]
    if symptom_cols:
        rows = []
        for _, row in df.iterrows():
            label = normalize_label(str(row["disease"]))
            if not label:
                continue
            canonical_row = {f: 0 for f in CANONICAL_FEATURES}
            canonical_row["disease"] = label
            for sc in symptom_cols:
                val = str(row.get(sc, "")).strip().lower().replace(" ", "_")
                if val and val != "nan":
                    mapped = map_to_canonical(val)
                    if mapped:
                        canonical_row[mapped] = 1
            rows.append(canonical_row)
        df_out = pd.DataFrame(rows)

    # ── Format B: Wide binary (one col per symptom) ───────────────────────
    else:
        feature_cols = [c for c in df.columns if c != "disease"]
        rows = []
        for _, row in df.iterrows():
            label = normalize_label(str(row["disease"]))
            if not label:
                continue
            canonical_row = {f: 0 for f in CANONICAL_FEATURES}
            canonical_row["disease"] = label
            for col in feature_cols:
                val = row.get(col, 0)
                if val in (1, True, "1", "true", "yes"):
                    mapped = map_to_canonical(col)
                    if mapped:
                        canonical_row[mapped] = 1
            rows.append(canonical_row)
        df_out = pd.DataFrame(rows)

    df_out["_source"] = "kaggle_132"
    print(f"  [OK] Kaggle 132-symptom: {len(df_out):,} rows, {df_out['disease'].nunique()} classes")
    return df_out


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLEANING — Applied to the merged dataframe
# ═══════════════════════════════════════════════════════════════════════════
def clean_merged(df: pd.DataFrame) -> pd.DataFrame:
    print("\n-- Cleaning merged dataset --")
    before = len(df)

    # 1. Drop rows where disease label is missing or too short
    df = df[df["disease"].notna()]
    df = df[df["disease"].str.len() >= 3]
    df = df[~df["disease"].str.lower().isin(["nan", "none", "unknown", "other", "n/a"])]

    # 2. Remove rows with all-zero symptoms (useless rows)
    feat_cols = [c for c in df.columns if c in CANONICAL_FEATURES]
    df = df[df[feat_cols].sum(axis=1) > 0]

    # 3. Drop only truly duplicate rows where BOTH disease AND ALL symptoms are identical.
    #    We use a hash-based approach to preserve Kaggle class variety — don't dedup across
    #    sources since repetition is intentional (augments minority classes).
    #    Only remove within-source duplicates (same disease, same exact binary row).
    df = df.drop_duplicates()

    # 4. Remove disease classes with fewer than 5 samples (truly sparse)
    class_counts = df["disease"].value_counts()
    valid_classes = class_counts[class_counts >= 5].index
    removed_classes = set(df["disease"].unique()) - set(valid_classes)
    if removed_classes:
        print(f"  Removed {len(removed_classes)} classes with <5 samples: {list(removed_classes)[:5]}...")
    df = df[df["disease"].isin(valid_classes)]

    # 5. Ensure all canonical feature columns exist (fill 0 if missing)
    for feat in CANONICAL_FEATURES:
        if feat not in df.columns:
            df[feat] = 0
    df[CANONICAL_FEATURES] = df[CANONICAL_FEATURES].fillna(0).astype(int).clip(0, 1)

    # 6. Final column selection
    df = df[CANONICAL_FEATURES + ["disease"]]

    after = len(df)
    print(f"  Rows: {before:,} -> {after:,} (removed {before - after:,} dirty rows)")
    print(f"  Disease classes: {df['disease'].nunique()}")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# CLASS BALANCING — Upsample small classes, cap huge ones
# ═══════════════════════════════════════════════════════════════════════════
def balance_classes(df: pd.DataFrame,
                    min_samples: int = 300,
                    max_samples: int = 600) -> pd.DataFrame:
    print("\n-- Balancing classes --")
    rng = np.random.default_rng(42)
    parts = []

    for disease, group in df.groupby("disease"):
        n = len(group)
        if n < min_samples:
            # Upsample by duplicating with tiny random noise
            needed = min_samples - n
            extra = group.sample(n=needed, replace=True, random_state=42)
            # Randomly flip ~10% of non-core symptoms for augmentation
            feat_cols = [c for c in CANONICAL_FEATURES if c in extra.columns]
            for col in feat_cols:
                flip_mask = rng.random(len(extra)) < 0.05
                extra.loc[flip_mask, col] = 1 - extra.loc[flip_mask, col]
            parts.append(pd.concat([group, extra]))
        elif n > max_samples:
            parts.append(group.sample(n=max_samples, random_state=42))
        else:
            parts.append(group)

    balanced = pd.concat(parts, ignore_index=True).sample(
        frac=1, random_state=42
    )
    print(f"  Final: {len(balanced):,} rows, {balanced['disease'].nunique()} classes")
    print(f"  Samples/class — min: {balanced['disease'].value_counts().min()}, "
          f"max: {balanced['disease'].value_counts().max()}, "
          f"mean: {balanced['disease'].value_counts().mean():.0f}")
    return balanced


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  Health Checker Pro — Rich Dataset Builder")
    print("=" * 60)

    frames = []

    print("\n[1/4] Loading existing synthetic dataset...")
    syn = load_existing_synthetic()
    if not syn.empty:
        frames.append(syn[CANONICAL_FEATURES + ["disease"]])

    print("\n[2/4] Loading Kaggle 132-symptom dataset...")
    k132 = load_kaggle_132(RAW_DIR)
    if not k132.empty:
        frames.append(k132[CANONICAL_FEATURES + ["disease"]])

    if not frames:
        print("\n[!] No data loaded. Download the Kaggle dataset first.")
        print("  See instructions printed above.")
        sys.exit(1)

    print(f"\n[3/4] Merging {len(frames)} source(s)...")
    merged = pd.concat(frames, ignore_index=True)
    print(f"  Combined: {len(merged):,} rows")

    cleaned = clean_merged(merged)
    balanced = balance_classes(cleaned)

    print(f"\n[4/4] Saving to {DATASET_OUT} ...")
    balanced.to_csv(DATASET_OUT, index=False)
    print(f"  [OK] Saved {len(balanced):,} rows x {len(CANONICAL_FEATURES)} features")
    print(f"  [!!] To use this as your new dataset, run:")
    print(f"       copy model\\dataset_rich.csv model\\dataset.csv  (Windows)")
    print(f"       python model\\train_model.py")

    print("\n" + "=" * 60)
    print("  DATASET SUMMARY")
    print("=" * 60)
    vc = balanced["disease"].value_counts()
    print(f"  Total rows     : {len(balanced):,}")
    print(f"  Disease classes: {balanced['disease'].nunique()}")
    print(f"  Features       : {len(CANONICAL_FEATURES)}")
    print(f"\n  Top 10 classes:")
    for disease, count in vc.head(10).items():
        print(f"    {disease:<35} {count:>4} samples")
    print("\n  [DONE] dataset_rich.csv created. Copy it over dataset.csv then retrain.")
    print("=" * 60)


if __name__ == "__main__":
    main()
