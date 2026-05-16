"""Run with: python model/train_model.py"""

import os
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold

# Resolve paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, "dataset.csv")
MODEL_PATH = os.path.join(SCRIPT_DIR, "model.pkl")

# Load dataset
data = pd.read_csv(DATASET_PATH)
print(f"Dataset loaded: {data.shape[0]} samples, {data.shape[1] - 1} features")
print(f"Disease classes: {data['disease'].nunique()}")
print(f"Class distribution:\n{data['disease'].value_counts().head(5)} ...\n")

# Separate features and label
X = data.drop("disease", axis=1)
y = data["disease"]

# Using HistGradientBoostingClassifier for highest accuracy on tabular data
# It natively handles missing values and is highly optimized.
best_model = HistGradientBoostingClassifier(
    max_iter=300,
    learning_rate=0.1,
    max_depth=15,
    random_state=42,
    class_weight="balanced"
)

print("Training Advanced HistGradientBoostingClassifier Model for maximum accuracy...")
best_model.fit(X, y)

# Full training report
y_pred = best_model.predict(X)
print(f"\nTraining Classification Report:")
print(classification_report(y, y_pred))

# Save model
with open(MODEL_PATH, "wb") as f:
    pickle.dump(best_model, f)

print(f"\nModel saved to {MODEL_PATH}")
print("Model trained successfully with High Accuracy enhancements!")
