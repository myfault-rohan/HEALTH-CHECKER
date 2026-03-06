disease_symptoms = {
    "Flu": ["fever", "cough", "fatigue", "sore_throat"],
    "Cold": ["cough", "runny_nose", "sore_throat"],
    "Malaria": ["fever", "headache", "fatigue", "chills"],
    "Food Poisoning": ["nausea", "vomiting", "diarrhea"],
    "Heart Disease": ["chest_pain", "shortness_of_breath", "fatigue"]
}

def predict_disease(selected_symptoms):

    scores = {}

    for disease, symptoms in disease_symptoms.items():
        score = 0
        for symptom in selected_symptoms:
            if symptom in symptoms:
                score += 1

        scores[disease] = score

    predicted = max(scores, key=scores.get)

    return predicted