import pickle
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier


def main():
    base_dir = Path(__file__).resolve().parent
    dataset_path = base_dir / "dataset.csv"
    if not dataset_path.exists():
        dataset_path = base_dir / "model" / "dataset.csv"

    data = pd.read_csv(dataset_path)
    features = data.drop(columns=["disease"])
    target = data["disease"]

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(features, target)

    model_path = base_dir / "model.pkl"
    with model_path.open("wb") as model_file:
        pickle.dump(model, model_file)

    print("Model trained successfully")


if __name__ == "__main__":
    main()

