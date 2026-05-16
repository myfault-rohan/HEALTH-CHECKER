import csv
import os
import random
import sys

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

def clean_feature(f): return f.replace(" ", "_")

def generate_dynamic_dataset():
    dataset_rows = []
    
    # 1. Reverse Engineer the map: Condition -> {Symptom: Score}
    condition_blueprints = {}
    for sym_raw, data in symptoms_conditions.items():
        sym_clean = clean_feature(sym_raw)
        if sym_clean not in FEATURES:
            continue
            
        for condition in data.get("conditions", []):
            name = condition["name"]
            score = float(condition.get("score", 1.0))
            if name not in condition_blueprints:
                condition_blueprints[name] = {}
            condition_blueprints[name][sym_clean] = score
            
    # 2. Add some "Combo Safety Features" that overrule anything else.
    # The UI defines "Potential Cardiac Concern" explicitly for chest pain + breathing
    # We will inject heavy rows just for this to ensure it works.
    
    print(f"Extracted {len(condition_blueprints)} unique clinical conditions from internal logic.")
    
    # 3. Generate 50 rows per specific clinical condition
    for disease, symptom_scores in condition_blueprints.items():
        # Sort symptoms by score so higher scores are "core"
        sorted_syms = sorted(symptom_scores.items(), key=lambda x: x[1], reverse=True)
        core_syms = [s[0] for s in sorted_syms if s[1] > 1.0]
        opt_syms = [s[0] for s in sorted_syms if s[1] <= 1.0]
        
        # If no core symptoms, promote top optional to core
        if not core_syms and opt_syms:
            core_syms = [opt_syms.pop(0)]
            
        for i in range(500):
            row = {f: 0 for f in FEATURES}
            row["disease"] = disease
            
            # Select core
            if core_syms:
                num_core = max(1, int(len(core_syms) * random.uniform(0.7, 1.0)))
                selected_core = random.sample(core_syms, num_core)
                for sym in selected_core: row[sym] = 1
                
            # Select optional
            if opt_syms:
                num_optional = int(len(opt_syms) * random.uniform(0.0, 0.8))
                selected_opt = random.sample(opt_syms, num_optional)
                for sym in selected_opt: row[sym] = 1
                
            dataset_rows.append(row)
            
    # 4. Generate pure 1-to-1 symptom rows. 
    # For every symptom, we isolate its highest scoring condition from prediction_service
    # and create 20 pure rows. (E.g. blurred_vision -> Eye Strain)
    for sym_clean in FEATURES:
        sym_raw = sym_clean.replace("_", " ")
        if sym_raw in symptoms_conditions:
            conditions = symptoms_conditions[sym_raw].get("conditions", [])
            if conditions:
                # Find the top condition by score and lowest severity
                # If they have same score, sort by severity (low first) to ensure safest fallback
                def sort_key(c):
                    sev_map = {"low": 3, "medium": 2, "high": 1}
                    return (float(c.get("score", 1.0)), sev_map.get(c.get("severity", "medium"), 2))
                
                best_condition = sorted(conditions, key=sort_key, reverse=True)[0]["name"]
                
                for _ in range(100):
                    row = {f: 0 for f in FEATURES}
                    row[sym_clean] = 1
                    row["disease"] = best_condition
                    dataset_rows.append(row)

    # 5. Save the ML logic
    csv_out = os.path.join(os.path.dirname(__file__), "dataset.csv")
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FEATURES + ["disease"])
        writer.writeheader()
        for r in dataset_rows:
            writer.writerow(r)

    print(f"Dynamically aligned Dataset generated at {csv_out} with {len(dataset_rows)} rows.")

if __name__ == "__main__":
    generate_dynamic_dataset()
