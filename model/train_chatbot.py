import os
import pickle
import random
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline

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

SYMPTOM_PHRASES = {
    "headache": ["my head hurts", "throbbing head", "head is pounding", "headache", "pain in my head", "migraine", "head feels heavy", "head ache"],
    "nausea": ["feel sick", "feel like throwing up", "nauseous", "nausea", "queasy", "sick to my stomach", "want to vomit", "nauseated"],
    "fever": ["running a temperature", "feel hot", "fever", "feverish", "high temp", "burning up", "temperature"],
    "cough": ["hacking cough", "keep coughing", "dry cough", "coughing up", "cough", "throat tickle"],
    "fatigue": ["so tired", "exhausted", "no energy", "fatigue", "feel weak", "worn out", "drained", "very tired"],
    "chest_pain": ["chest hurts", "pain in chest", "chest pain", "tightness in chest", "chest pressure", "heavy chest"],
    "dizziness": ["dizzy", "lightheaded", "room is spinning", "faint", "dizziness", "spinning sensation"],
    "shortness_of_breath": ["can't breathe", "hard to breathe", "short of breath", "shortness of breath", "breathless", "gasping for air"],
    "stomach_pain": ["stomach hurts", "belly ache", "stomach ache", "tummy hurts", "stomach pain", "abdomen hurts"],
    "runny_nose": ["nose is running", "runny nose", "snotty", "dripping nose"],
    "sore_throat": ["throat hurts", "scratchy throat", "sore throat", "pain swallowing", "throat is sore"],
    "diarrhea": ["the runs", "loose stool", "diarrhea", "watery stool"],
    "vomiting": ["throwing up", "vomiting", "puking", "barfing", "threw up"],
    "muscle_pain": ["muscles ache", "muscle pain", "body aches", "sore muscles", "body ache"],
    "joint_pain": ["joints hurt", "joint pain", "knees ache", "aching joints"],
    "stress": ["feeling stressed", "stressed out", "anxious", "stress", "too much tension"],
    "insomnia": ["can't sleep", "trouble sleeping", "insomnia", "waking up at night", "no sleep"],
    "cold": ["caught a cold", "feeling cold", "have a cold", "cold"],
}

# Fill defaults
for f in FEATURES:
    if f not in SYMPTOM_PHRASES:
        name = f.replace("_", " ")
        SYMPTOM_PHRASES[f] = [f"I have {name}", f"experiencing {name}", f"my {name} is bad", name, f"suffering from {name}"]

def generate_nlp_dataset(num_samples=5000):
    texts = []
    labels = []
    for _ in range(num_samples):
        num_sym = random.randint(1, 4)
        chosen_syms = random.sample(FEATURES, num_sym)
        
        phrase_parts = [random.choice(SYMPTOM_PHRASES[sym]) for sym in chosen_syms]
        
        joiners = [" and ", ", also ", ". I also have ", " with ", ", "]
        
        text = phrase_parts[0]
        for part in phrase_parts[1:]:
            text += random.choice(joiners) + part
            
        texts.append(text)
        labels.append([1 if f in chosen_syms else 0 for f in FEATURES])
        
    return texts, np.array(labels)

def train_chatbot_model():
    print("Generating synthetic NLP dataset...")
    texts, y = generate_nlp_dataset(6000)
    
    # Add pure single-phrase rows
    extra_labels = []
    for sym in FEATURES:
        for phrase in SYMPTOM_PHRASES[sym]:
            for _ in range(20):
                texts.append(phrase)
                row = [1 if f == sym else 0 for f in FEATURES]
                extra_labels.append(row)
                
    if extra_labels:
        y = np.vstack([y, np.array(extra_labels)])

    print(f"Dataset generated. Total rows: {len(texts)}")
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=5000)),
        ('clf', MultiOutputClassifier(LogisticRegression(class_weight='balanced', max_iter=1000)))
    ])
    
    print("Training the NLP Chatbot model...")
    pipeline.fit(texts, y)
    
    model_path = os.path.join(os.path.dirname(__file__), "chatbot_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(pipeline, f)
        
    print(f"Chatbot ML Model saved to {model_path}")

if __name__ == "__main__":
    train_chatbot_model()
