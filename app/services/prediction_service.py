import json
from collections import defaultdict
from pathlib import Path

_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "symptoms_kb.json"
with open(_KB_PATH, encoding="utf-8") as f:
    symptoms_conditions = json.load(f)

SYMPTOM_CATEGORY_GROUPS = {
    "respiratory": [
        "cough",
        "cold",
        "shortness of breath",
        "chest pain",
        "wheezing",
        "sore throat",
        "runny nose",
        "sneezing",
        "congestion",
    ],
    "digestive": [
        "abdominal pain",
        "stomach pain",
        "nausea",
        "vomiting",
        "diarrhea",
        "constipation",
        "bloating",
        "heartburn",
        "acidity",
        "loss of appetite",
        "urinary problems",
    ],
    "neurological": [
        "headache",
        "dizziness",
        "blurred vision",
        "confusion",
        "insomnia",
        "fatigue",
        "chills",
        "stress",
        "palpitations",
    ],
    "musculoskeletal": [
        "joint pain",
        "back pain",
        "muscle pain",
        "stiffness",
        "leg pain",
        "waist pain",
        "body weakness",
        "swelling",
    ],
}

SYMPTOM_ALIASES = {
    "body weekness": "body weakness",
    "stomac pain": "stomach pain",
    "stoamac pain": "stomach pain",
    "head ace": "headache",
    "head ache": "headache",
    "water comig from eyes": "watery eyes",
    "water coming from eyes": "watery eyes",
    "pain in periods": "menstrual pain",
    "period pain": "menstrual pain",
    "dehaidrasion": "dehydration",
    "colds": "cold",
    "stressed": "stress",
    "tension": "stress",
    "mental stress": "stress",
    "anxious": "stress",
}


def normalize_symptom_name(symptom):
    normalized = (symptom or "").strip().lower()
    return SYMPTOM_ALIASES.get(normalized, normalized)


# Emergency symptoms
EMERGENCY_SYMPTOMS = {
    "chest pain": {
        "message": "If you experience severe chest pain, please consult a doctor immediately.",
        "triggers": ["crushing", "pressure", "severe"]
    },
    "shortness of breath": {
        "message": "If breathing difficulty persists, seek medical attention.",
        "triggers": ["severe", "sudden"]
    },
    "fever": {
        "message": "If fever persists above 103°F for more than 2 days, please see a doctor.",
        "triggers": [103]
    },
    "vomiting": {
        "message": "If vomiting persists for more than 24 hours, consult a healthcare provider.",
        "triggers": ["continuous"]
    }
}

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3}

CONDITION_DESCRIPTIONS = {
    "Migraine": "Neurological headache pattern often linked with light/noise sensitivity and nausea.",
    "Tension Headache": "Common stress-related headache with pressure or tightness around the head.",
    "Flu": "Viral infection often causing fever, chills, fatigue, and respiratory symptoms.",
    "Viral Fever": "Short-term fever pattern most commonly from viral causes.",
    "Digestive Infection": "Gastrointestinal infection pattern linked to vomiting or diarrhea.",
    "Acid Reflux": "Backflow of stomach acid causing heartburn and chest discomfort after meals.",
    "Asthma (Breathlessness)": "Airway narrowing that may cause breathlessness, chest tightness, or wheeze.",
    "Urinary Tract Infection (UTI)": "Urinary infection symptoms such as burning, urgency, or discomfort.",
    "Potential Cardiac Concern": "Chest pain with breathing distress can represent a serious heart/lung issue.",
    "Dysmenorrhea": "Painful menstrual cramps, often in lower abdomen or back during periods.",
    "Gastritis": "Stomach lining irritation that can cause pain, acidity, and bloating.",
    "Dehydration": "Fluid loss pattern causing weakness, dizziness, and low energy.",
    "Common Cold": "Viral infection of the upper respiratory tract causing sneezing, runny nose, and congestion.",
    "Seasonal Cold": "Recurring cold symptoms triggered by seasonal weather changes and weakened immunity.",
    "Upper Respiratory Infection": "Infection affecting nose, throat, or sinuses with congestion, sore throat, and cough.",
    "Chronic Stress": "Prolonged mental or emotional tension causing fatigue, headaches, and sleep disturbances.",
    "Burnout": "Physical and emotional exhaustion from prolonged stress, causing low motivation and fatigue.",
    "Stress-Weakened Immunity": "Chronic stress reducing immune function, making the body more susceptible to infections.",
    "Peptic Ulcer": "Sores that develop on the lining of the stomach, lower esophagus, or small intestine commonly causing severe heartburn.",
    "Food Poisoning": "Illness caused by eating contaminated food, resulting in nausea, vomiting, or diarrhea.",
    "Irritable Bowel Syndrome": "A common disorder that affects the large intestine causing abdominal pain, bloating, and irregular bowel habits.",
    "Influenza": "A viral infection that attacks the respiratory system, characterized by fever, chills, and muscle aches.",
    "Bronchitis": "Inflammation of the lining of bronchial tubes, which carry air to and from the lungs, often causing an intense cough.",
    "Anxiety Disorder": "A mental health disorder characterized by feelings of worry, anxiety, or fear that are strong enough to interfere with daily activities.",
    "Anemia": "A condition in which the blood doesn't have enough healthy red blood cells, causing severe body weakness and fatigue.",
    "Arthritis": "Inflammation of one or more joints, causing pain, leg pain, swelling, and stiffness.",
    "Gastroenteritis": "An intestinal infection marked by diarrhea, cramps, nausea, vomiting, and fever.",
    "Pneumonia": "Infection that inflames air sacs in one or both lungs, which may fill with fluid.",
    "Tuberculosis": "A potentially serious infectious bacterial disease that mainly affects the lungs.",
    "Asthma": "A condition in which a person's airways become inflamed, narrow and swell, and produce extra mucus.",
    "Dengue": "A mosquito-borne viral infection causing a severe flu-like illness.",
    "Malaria": "A disease caused by a plasmodium parasite, transmitted by the bite of infected mosquitoes.",
    "Typhoid": "A bacterial disease spread through contaminated food and water or close contact.",
    "COVID 19": "An infectious disease caused by the SARS-CoV-2 virus, primarily affecting the respiratory system.",
    "Diabetes": "A disease that occurs when your blood glucose, also called blood sugar, is too high.",
    "Hypertension": "A condition in which the force of the blood against the artery walls is too high.",
    "Depression Disorder": "A mood disorder that causes a persistent feeling of sadness and loss of interest."
}

CONDITION_DEMOGRAPHIC_HINTS = {
    "Urinary Tract Infection (UTI)": {"female_bonus": 0.6},
    "Arthritis Support": {"age_min": 40, "age_bonus": 0.6},
    "Joint Stiffness": {"age_min": 35, "age_bonus": 0.4},
    "Thyroid Support Needed": {"female_bonus": 0.3},
    "Anemia": {"female_bonus": 0.3},
    "Dysmenorrhea": {"female_bonus": 1.0},
}

COMBINATION_RULES = [
    {
        "required": {"chest pain", "shortness of breath"},
        "condition": "Potential Cardiac Concern",
        "bonus": 3.2,
        "urgency": "high",
        "note": "Chest pain plus breathing difficulty needs urgent in-person evaluation.",
    },
    {
        "required": {"fever", "cough", "congestion"},
        "condition": "Flu",
        "bonus": 2.1,
        "urgency": "medium",
        "note": "Fever with cough and congestion is a common flu pattern.",
    },
    {
        "required": {"vomiting", "diarrhea"},
        "condition": "Digestive Infection",
        "bonus": 2.0,
        "urgency": "medium",
        "note": "Vomiting and diarrhea together suggest infectious gastroenteritis.",
    },
    {
        "required": {"headache", "dizziness", "blurred vision"},
        "condition": "Migraine",
        "bonus": 1.8,
        "urgency": "medium",
        "note": "Headache with dizziness and visual symptoms can indicate migraine pattern.",
    },
    {
        "required": {"cold", "stress"},
        "condition": "Stress-Weakened Immunity",
        "bonus": 2.0,
        "urgency": "medium",
        "note": "Chronic stress can weaken immune response and worsen cold symptoms.",
    },
    {
        "required": {"cold", "fever", "cough"},
        "condition": "Flu",
        "bonus": 2.4,
        "urgency": "medium",
        "note": "Cold with fever and cough is a strong indicator of flu or viral infection.",
    },
    {
        "required": {"stress", "insomnia", "headache"},
        "condition": "Chronic Stress",
        "bonus": 2.2,
        "urgency": "medium",
        "note": "Stress with insomnia and headache indicate chronic stress syndrome.",
    },
]


def ordered_unique(items):
    seen = set()
    ordered = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def build_condition_profiles():
    profiles = {}
    for symptom, symptom_data in symptoms_conditions.items():
        for condition in symptom_data["conditions"]:
            name = condition["name"]
            score = float(condition.get("score", 1))
            severity = condition.get("severity", "low")

            if name not in profiles:
                profiles[name] = {
                    "symptom_weights": defaultdict(float),
                    "severity": severity,
                }

            profiles[name]["symptom_weights"][symptom] = max(
                profiles[name]["symptom_weights"][symptom],
                score,
            )
            if SEVERITY_ORDER.get(severity, 1) > SEVERITY_ORDER.get(
                profiles[name]["severity"], 1
            ):
                profiles[name]["severity"] = severity

    normalized = {}
    for name, payload in profiles.items():
        weights = dict(payload["symptom_weights"])
        top_symptoms = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
        normalized[name] = {
            "symptom_weights": weights,
            "severity": payload["severity"],
            "key_symptoms": [symptom for symptom, _ in top_symptoms[:4]],
            "total_weight": sum(weights.values()) or 1.0,
        }
    return normalized


CONDITION_PROFILES = build_condition_profiles()


def confidence_label(confidence):
    if confidence >= 78:
        return "Strong match"
    if confidence >= 60:
        return "Fair match"
    return "Possible match"


def urgency_from_severity(severity, confidence):
    if severity == "high" or confidence >= 82:
        return "high"
    if severity == "medium" or confidence >= 62:
        return "medium"
    return "low"


def demographic_adjustment(condition_name, age, gender):
    hints = CONDITION_DEMOGRAPHIC_HINTS.get(condition_name, {})
    adjustment = 0.0
    age_min = hints.get("age_min")
    if age_min and age >= age_min:
        adjustment += hints.get("age_bonus", 0.0)
    if hints.get("female_bonus") and gender == "female":
        adjustment += hints["female_bonus"]
    if hints.get("male_bonus") and gender == "male":
        adjustment += hints["male_bonus"]
    return adjustment


def detail_adjustment(condition_name, form_data):
    bonus = 0.0
    headache_type = (form_data.get("headache_type") or "").strip().lower()
    cough_type = (form_data.get("cough_type") or "").strip().lower()
    breath_severity = (form_data.get("breath_severity") or "").strip().lower()
    chest_type = (form_data.get("chest_type") or "").strip().lower()

    if condition_name == "Tension Headache" and headache_type == "pressure":
        bonus += 0.4
    if condition_name == "Migraine" and headache_type == "throbbing":
        bonus += 0.5
    if condition_name == "Dry Cough" and cough_type == "dry":
        bonus += 0.5
    if condition_name == "Chest Congestion" and cough_type == "wet":
        bonus += 0.5
    if condition_name == "Asthma (Breathlessness)" and breath_severity == "severe":
        bonus += 0.8
    if condition_name == "Potential Cardiac Concern" and chest_type == "pressure":
        bonus += 1.2
    return bonus


def compute_condition_matches(selected_symptoms, age, gender, form_data):
    selected_set = set(selected_symptoms)
    if not selected_set:
        return []

    ranked = {}
    for condition_name, profile in CONDITION_PROFILES.items():
        symptom_weights = profile["symptom_weights"]
        matched = [symptom for symptom in selected_set if symptom in symptom_weights]
        if not matched:
            continue

        matched_weight = sum(symptom_weights[symptom] for symptom in matched)
        coverage = matched_weight / max(profile["total_weight"], 1.0)
        key_hits = sum(1 for symptom in profile["key_symptoms"] if symptom in selected_set)
        key_coverage = key_hits / max(len(profile["key_symptoms"]), 1)

        raw_score = (matched_weight * 1.3) + (coverage * 3.6) + (key_coverage * 2.1)
        raw_score += demographic_adjustment(condition_name, age, gender)
        raw_score += detail_adjustment(condition_name, form_data)

        confidence = max(20, min(96, int(25 + raw_score * 8.5)))
        ranked[condition_name] = {
            "name": condition_name,
            "confidence": confidence,
            "match_label": confidence_label(confidence),
            "urgency": urgency_from_severity(profile["severity"], confidence),
            "severity": profile["severity"],
            "evidence": sorted(matched, key=lambda s: symptom_weights[s], reverse=True)[:4],
            "description": CONDITION_DESCRIPTIONS.get(
                condition_name,
                "Pattern inferred from your selected symptoms.",
            ),
            "raw_score": raw_score,
            "note": "",
        }

    for rule in COMBINATION_RULES:
        required = rule["required"]
        if not required.issubset(selected_set):
            continue
        target = rule["condition"]
        if target not in ranked:
            bonus_raw = rule["bonus"] + 2.0
            confidence = max(58, min(97, int(25 + bonus_raw * 10)))
            ranked[target] = {
                "name": target,
                "confidence": confidence,
                "match_label": confidence_label(confidence),
                "urgency": rule["urgency"],
                "severity": "medium" if rule["urgency"] != "high" else "high",
                "evidence": sorted(list(required)),
                "description": CONDITION_DESCRIPTIONS.get(
                    target, "Important symptom combination that needs closer evaluation."
                ),
                "raw_score": bonus_raw,
                "note": rule["note"],
            }
        else:
            ranked[target]["raw_score"] += rule["bonus"]
            ranked[target]["confidence"] = max(
                ranked[target]["confidence"],
                min(97, int(25 + ranked[target]["raw_score"] * 8.5)),
            )
            ranked[target]["match_label"] = confidence_label(ranked[target]["confidence"])
            ranked[target]["urgency"] = rule["urgency"]
            ranked[target]["note"] = rule["note"]

    results = sorted(ranked.values(), key=lambda item: item["raw_score"], reverse=True)[:8]
    for item in results:
        del item["raw_score"]
    return results


def detect_emergency_signals(selected_symptoms, form_data):
    selected_set = set(selected_symptoms)

    # Fast-path high risk combination.
    if {"chest pain", "shortness of breath"}.issubset(selected_set):
        chest_type = (form_data.get("chest_type") or "").strip().lower()
        breath_severity = (form_data.get("breath_severity") or "").strip().lower()
        if chest_type == "pressure" or breath_severity == "severe":
            return (
                True,
                "Chest pressure with severe breathing symptoms can be an emergency. Seek urgent care now.",
            )

    for symptom in selected_symptoms:
        if symptom not in EMERGENCY_SYMPTOMS:
            continue

        emergency_info = EMERGENCY_SYMPTOMS[symptom]
        triggers = emergency_info.get("triggers", [])
        for trigger in triggers:
            if isinstance(trigger, (int, float)) and symptom == "fever":
                try:
                    fever_temp = float(form_data.get("fever_temp", 0))
                    if fever_temp >= trigger:
                        return True, emergency_info["message"]
                except ValueError:
                    pass
            else:
                for value in form_data.values():
                    if value and str(trigger).lower() in str(value).lower():
                        return True, emergency_info["message"]

    if {"chest pain", "shortness of breath"}.issubset(selected_set):
        return True, "Please seek urgent medical evaluation if chest symptoms continue."

    return False, ""


def get_searchable_symptoms():
    return sorted(
        ordered_unique(list(symptoms_conditions.keys()) + list(SYMPTOM_ALIASES.keys()))
    )


def get_symptom_categories():
    searchable = set(get_searchable_symptoms())
    categorized = {}
    for category, symptom_names in SYMPTOM_CATEGORY_GROUPS.items():
        categorized[category] = [item for item in symptom_names if item in searchable]

    used = {symptom for items in categorized.values() for symptom in items}
    categorized["general"] = [item for item in searchable if item not in used]
    return categorized


def get_condition_precautions(condition):
    urgency = (condition.get("urgency") or "low").lower()
    base_precautions = [
        "Stay hydrated and rest while monitoring symptoms.",
        "Avoid self-medicating with antibiotics without clinician advice.",
        "Track symptom changes every 4-6 hours.",
    ]
    if urgency == "high":
        return [
            "Seek same-day medical care for this pattern.",
            "Do not delay evaluation if symptoms are worsening.",
            "Call emergency services for chest pain, severe breathlessness, or confusion.",
        ]
    if urgency == "medium":
        return [
            "Arrange a clinical visit within 24-48 hours.",
            "Escalate sooner if fever, pain, or breathing issues increase.",
            "Avoid heavy activity until symptoms improve.",
        ]
    return base_precautions

