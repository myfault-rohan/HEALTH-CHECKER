"""Run with: python model/train_model.py"""

import pickle

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Load dataset
data = pd.read_csv("dataset.csv")

# Separate features and label
X = data.drop("disease", axis=1)
y = data["disease"]

# Create model
model = RandomForestClassifier()

# Train model
model.fit(X, y)

# Save model
pickle.dump(model, open("model.pkl", "wb"))

print("Model trained successfully!")
