from collections import defaultdict


symptoms_conditions = {
    # Head & Brain
    "headache": {
        "conditions": [
            {"name": "Tension Headache", "severity": "low", "score": 1},
            {"name": "Stress-related Headache", "severity": "low", "score": 1},
            {"name": "Migraine", "severity": "medium", "score": 2},
            {"name": "Dehydration", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Massaging temples with peppermint oil",
            "🌿 Drinking chamomile or ginger tea",
            "🌿 Practicing Anulom Vilom (deep breathing) for 10 minutes",
            "🌿 Applying cooling sandalwood paste on forehead",
            "💧 Drinking plenty of water",
            "😴 Taking adequate rest in a dark room"
        ]
    },
    "dizziness": {
        "conditions": [
            {"name": "Low Blood Sugar", "severity": "low", "score": 1},
            {"name": "Dehydration", "severity": "low", "score": 1},
            {"name": "Vertigo (Inner ear imbalance)", "severity": "medium", "score": 2},
            {"name": "Weakness", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Chewing a small piece of fresh ginger",
            "🌿 Drinking ginger tea with honey",
            "💧 Having electrolyte water or coconut water",
            "🌿 Consuming soaked almonds and raisins",
            "🍌 Eating a banana for quick energy",
            "😴 Resting in a comfortable position"
        ]
    },
    "blurred vision": {
        "conditions": [
            {"name": "Eye Strain", "severity": "low", "score": 1},
            {"name": "Digital Eye Fatigue", "severity": "low", "score": 1},
            {"name": "Vitamin A Deficiency", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🥕 Eating carrots rich in Vitamin A",
            "🌿 Applying rose water to eyes",
            "🌿 Using cucumber slices on eyes for 15 minutes",
            "👁️ Taking breaks from screen every 20 minutes",
            "🌿 Consuming triphala churna (Ayurvedic supplement)"
        ]
    },
    "confusion": {
        "conditions": [
            {"name": "Fatigue", "severity": "low", "score": 1},
            {"name": "Low Energy", "severity": "low", "score": 1},
            {"name": "Need for Rest", "severity": "low", "score": 1}
        ],
        "remedies": [
            "😴 Getting adequate sleep (7-8 hours)",
            "💧 Staying hydrated",
            "🌿 Consuming Brahmi (Bacopa monnieri) for mental clarity",
            "🍎 Eating regular balanced meals",
            "🧘 Practicing meditation for mental focus"
        ]
    },

    # Respiratory
    "cough": {
        "conditions": [
            {"name": "Common Cold", "severity": "low", "score": 1},
            {"name": "Dry Cough", "severity": "low", "score": 1},
            {"name": "Chest Congestion", "severity": "medium", "score": 2},
            {"name": "Bronchial Irritation", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Mixing honey with fresh lemon juice",
            "🌿 Drinking warm milk with turmeric (Golden Milk)",
            "🌿 Gargling with warm salt water",
            "🌿 Taking steam inhalation with eucalyptus oil",
            "🌿 Consuming ginger-honey mixture",
            "🍵 Drinking Tulsi (Holy Basil) tea"
        ]
    },
    "shortness of breath": {
        "conditions": [
            {"name": "Asthma (Breathlessness)", "severity": "medium", "score": 2},
            {"name": "Respiratory Congestion", "severity": "medium", "score": 2},
            {"name": "Anxiety-related Breathing", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Practicing Pranayama (deep breathing exercises)",
            "🌿 Inhaling steam with eucalyptus oil",
            "🌿 Drinking mulethi (licorice) tea",
            "🧘 Sitting upright and practicing calm breathing",
            "🌿 Using ajwain (carom seed) steam",
            "🍵 Drinking warm ginger tea"
        ]
    },
    "chest pain": {
        "conditions": [
            {"name": "Muscle Strain", "severity": "low", "score": 1},
            {"name": "Digestive Issue", "severity": "low", "score": 1},
            {"name": "Gas/Acidity", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Drinking fennel seed tea for digestion",
            "🌿 Applying warm compress on chest",
            "🌿 Taking ajwain water after meals",
            "🚫 Avoiding spicy and fried foods",
            "🌿 Consuming ginger before meals"
        ]
    },
    "wheezing": {
        "conditions": [
            {"name": "Allergic Bronchitis", "severity": "medium", "score": 2},
            {"name": "Respiratory Allergy", "severity": "low", "score": 1},
            {"name": "Dust Sensitivity", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Drinking honey with ginger juice",
            "🌿 Taking steam with tulsi leaves",
            "🌿 Using honey and turmeric mixture",
            "🌿 Consuming licorice root tea",
            "🚫 Avoiding dust and allergens"
        ]
    },
    "palpitations": {
        "conditions": [
            {"name": "Stress/Anxiety", "severity": "low", "score": 1},
            {"name": "Excess Caffeine", "severity": "low", "score": 1},
            {"name": "Overwork", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🧘 Practicing meditation and yoga",
            "🌿 Drinking chamomile tea",
            "🌿 Consuming arjuna bark tea for heart health",
            "🚫 Reducing caffeine intake",
            "🌿 Taking ashwagandha for stress relief"
        ]
    },

    # Digestive
    "abdominal pain": {
        "conditions": [
            {"name": "Indigestion", "severity": "low", "score": 1},
            {"name": "Gas/Bloating", "severity": "low", "score": 1},
            {"name": "Acidity", "severity": "low", "score": 1},
            {"name": "Digestive Weakness", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Drinking jeera (cumin) water",
            "🌿 Chewing fennel seeds after meals",
            "🌿 Applying castor oil pack on abdomen",
            "🌿 Taking ajwain (carom seed) water",
            "🚫 Avoiding overeating",
            "🌿 Consuming triphala for digestion"
        ]
    },
    "nausea": {
        "conditions": [
            {"name": "Digestive Upset", "severity": "low", "score": 1},
            {"name": "Acidity", "severity": "low", "score": 1},
            {"name": "Morning Sickness", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Chewing fresh ginger",
            "🌿 Drinking peppermint tea",
            "🌿 Sipping lemon water",
            "🍚 Eating light foods like toast",
            "🌿 Taking ginger-honey mixture"
        ]
    },
    "vomiting": {
        "conditions": [
            {"name": "Food Poisoning", "severity": "medium", "score": 2},
            {"name": "Stomach Flu", "severity": "medium", "score": 2},
            {"name": "Digestive Infection", "severity": "medium", "score": 2}
        ],
        "remedies": [
            "💧 Sipping ginger tea slowly",
            "💧 Drinking electrolyte water",
            "🌿 Inhaling lemon scent",
            "🍚 Following BRAT diet (Banana, Rice, Apple, Toast)",
            "🌿 Consuming pomegranate juice"
        ]
    },
    "diarrhea": {
        "conditions": [
            {"name": "Food Intolerance", "severity": "low", "score": 1},
            {"name": "Digestive Infection", "severity": "medium", "score": 2},
            {"name": "Stress-related", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🍚 Drinking rice water",
            "🍌 Eating ripe bananas",
            "🌿 Consuming curd/yogurt",
            "🌿 Taking isabgol (psyllium husk)",
            "🚫 Avoiding dairy and fried foods",
            "💧 Staying hydrated"
        ]
    },
    "constipation": {
        "conditions": [
            {"name": "Digestive sluggishness", "severity": "low", "score": 1},
            {"name": "Low Fiber Diet", "severity": "low", "score": 1},
            {"name": "Dehydration", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Taking triphala churna at night",
            "🌿 Soaking figs overnight and eating in morning",
            "🌿 Drinking warm water with lemon and honey",
            "🌿 Consuming isabgol with milk",
            "🥬 Eating high-fiber foods",
            "💧 Drinking 8-10 glasses of water daily"
        ]
    },
    "bloating": {
        "conditions": [
            {"name": "Gas Formation", "severity": "low", "score": 1},
            {"name": "Indigestion", "severity": "low", "score": 1},
            {"name": "Food Intolerance", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Drinking jeera (cumin) water",
            "🌿 Chewing fennel seeds",
            "🌿 Taking ajwain water",
            "🚫 Avoiding carbonated drinks",
            "🌿 Consuming ginger tea"
        ]
    },
    "heartburn": {
        "conditions": [
            {"name": "Acid Reflux", "severity": "low", "score": 1},
            {"name": "Acidity", "severity": "low", "score": 1},
            {"name": "Spicy Food Sensitivity", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🥛 Drinking cold milk",
            "🌿 Consuming fennel seeds",
            "🌿 Taking amla (Indian gooseberry)",
            "🚫 Avoiding spicy and oily foods",
            "🌿 Drinking aloe vera juice"
        ]
    },
    "urinary problems": {
        "conditions": [
            {"name": "Urinary Tract Infection (UTI)", "severity": "medium", "score": 2},
            {"name": "Kidney Health Support", "severity": "low", "score": 1},
            {"name": "Frequent Urination", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🫐 Drinking cranberry juice",
            "🌿 Consuming chandana (sandalwood) water",
            "🌿 Taking秦皮 (Indian barberry) extract",
            "💧 Drinking plenty of water",
            "🌿 Using punarnava (Boerhavia diffusa) for kidney health",
            "🚫 Avoiding caffeine and alcohol"
        ]
    },

    # General
    "fever": {
        "conditions": [
            {"name": "Viral Fever", "severity": "medium", "score": 2},
            {"name": "Flu", "severity": "medium", "score": 2},
            {"name": "Body Infection", "severity": "medium", "score": 2}
        ],
        "remedies": [
            "🌿 Drinking Tulsi (Holy Basil) decoction with black pepper",
            "🌿 Taking ginger tea with honey",
            "🌿 Consuming giloy (Tinospora cordifolia) juice",
            "💧 Drinking plenty of warm fluids",
            "🌿 Applying sandalwood paste on forehead",
            "🥵 Rest and sponge bath with lukewarm water"
        ]
    },
    "fatigue": {
        "conditions": [
            {"name": "Weakness/Low Energy", "severity": "low", "score": 1},
            {"name": "Anemia", "severity": "medium", "score": 2},
            {"name": "Overwork", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Taking ashwagandha churna with milk",
            "🌿 Consuming shatavari for energy",
            "🍎 Eating iron-rich foods (spinach, dates, lentils)",
            "🧘 Practicing Surya Namaskar (Sun Salutation)",
            "🌿 Drinking chyawanprash"
        ]
    },
    "chills": {
        "conditions": [
            {"name": "Fever Onset", "severity": "low", "score": 1},
            {"name": "Cold/Flu", "severity": "low", "score": 1},
            {"name": "Body Ache", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🛌 Taking rest under warm blankets",
            "🌿 Drinking hot ginger tea",
            "🌿 Consuming tulsi tea",
            "💧 Staying warm and hydrated"
        ]
    },
    "night sweats": {
        "conditions": [
            {"name": "Stress-related", "severity": "low", "score": 1},
            {"name": "Body Detoxification", "severity": "low", "score": 1},
            {"name": "Hormonal Changes", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Taking ashoka bark for hormonal balance",
            "🧘 Practicing relaxation techniques",
            "👕 Wearing light cotton clothes",
            "🌿 Consuming shatavari milk"
        ]
    },
    "weight loss": {
        "conditions": [
            {"name": "Metabolism Issues", "severity": "low", "score": 1},
            {"name": "Digestive Weakness", "severity": "low", "score": 1},
            {"name": "Thyroid Support Needed", "severity": "medium", "score": 2}
        ],
        "remedies": [
            "🌿 Taking triphala for digestion",
            "🌿 Consuming guggulu for metabolism",
            "🧘 Practicing yoga for weight management",
            "🍎 Eating balanced meals regularly"
        ]
    },
    "insomnia": {
        "conditions": [
            {"name": "Sleep Disorder", "severity": "low", "score": 1},
            {"name": "Stress/Anxiety", "severity": "low", "score": 1},
            {"name": "Restlessness", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Drinking warm milk with nutmeg",
            "🌿 Taking shankhapushpi for mental calm",
            "🌿 Massaging feet with sesame oil (Padabhyanga)",
            "🧘 Practicing Yoga Nidra before sleep",
            "🌿 Consuming brahmi tea"
        ]
    },
    "loss of appetite": {
        "conditions": [
            {"name": "Digestive Weakness", "severity": "low", "score": 1},
            {"name": "Stress", "severity": "low", "score": 1},
            {"name": "Liver Support Needed", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Taking ginger before meals",
            "🌿 Consuming ajwain water",
            "🌿 Using punarnava for appetite",
            "🚫 Eating small frequent meals",
            "🌿 Taking triphala before bed"
        ]
    },

    # Throat & Nose
    "sore throat": {
        "conditions": [
            {"name": "Throat Infection", "severity": "low", "score": 1},
            {"name": "Cold/Flu", "severity": "low", "score": 1},
            {"name": "Tonsillitis", "severity": "medium", "score": 2}
        ],
        "remedies": [
            "🌿 Gargling with turmeric and salt water",
            "🌿 Chewing fresh ginger",
            "🌿 Drinking Tulsi tea with honey",
            "🌿 Taking licorice root tea",
            "🍋 Sipping warm water with lemon"
        ]
    },
    "runny nose": {
        "conditions": [
            {"name": "Common Cold", "severity": "low", "score": 1},
            {"name": "Allergies", "severity": "low", "score": 1},
            {"name": "Sinus Congestion", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Inhaling steam with tulsi leaves",
            "🌿 Drinking ginger tea",
            "🌿 Using saline nasal spray",
            "🌿 Consuming turmeric milk"
        ]
    },
    "sneezing": {
        "conditions": [
            {"name": "Allergic Rhinitis", "severity": "low", "score": 1},
            {"name": "Cold", "severity": "low", "score": 1},
            {"name": "Dust Allergy", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Drinking golden milk with turmeric",
            "🌿 Taking steam with mint leaves",
            "🌿 Consuming vitamin C rich foods",
            "🚫 Avoiding dust and allergens"
        ]
    },
    "congestion": {
        "conditions": [
            {"name": "Nasal Congestion", "severity": "low", "score": 1},
            {"name": "Sinusitis", "severity": "medium", "score": 2},
            {"name": "Cold", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Steam inhalation with eucalyptus oil",
            "🌿 Using saline nasal drops",
            "🌿 Drinking ginger-tulsi tea",
            "🌿 Applying warm compress on nose"
        ]
    },

    # Skin
    "rash": {
        "conditions": [
            {"name": "Skin Allergy", "severity": "low", "score": 1},
            {"name": "Heat Rash", "severity": "low", "score": 1},
            {"name": "Eczema Support", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Applying fresh aloe vera gel",
            "🌿 Washing with neem water",
            "🌿 Applying coconut oil",
            "🌿 Using turmeric paste",
            "🚫 Avoiding scratching"
        ]
    },
    "swelling": {
        "conditions": [
            {"name": "Inflammation", "severity": "low", "score": 1},
            {"name": "Water Retention", "severity": "low", "score": 1},
            {"name": "Injury", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🧊 Applying ice pack",
            "🌿 Taking ginger tea",
            "🌿 Using arnica gel",
            "🌿 Consuming punarnava for water balance",
            "🦶 Keeping elevated"
        ]
    },

    # Musculoskeletal
    "joint pain": {
        "conditions": [
            {"name": "Arthritis Support", "severity": "low", "score": 1},
            {"name": "Joint Stiffness", "severity": "low", "score": 1},
            {"name": "Vata Imbalance", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🌿 Applying turmeric paste with warm water",
            "🌿 Massaging with sesame oil",
            "🌿 Taking ginger tea",
            "🌿 Consuming guggulu supplements",
            "🧘 Practicing gentle yoga"
        ]
    },
    "back pain": {
        "conditions": [
            {"name": "Muscle Strain", "severity": "low", "score": 1},
            {"name": "Poor Posture", "severity": "low", "score": 1},
            {"name": "Back Stiffness", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🧊 Applying hot water bottle",
            "🌿 Massaging with mahanarayan oil",
            "🧘 Practicing Cat-Cow yoga stretch",
            "🌿 Taking ginger tea",
            "🛌 Taking adequate rest"
        ]
    },
    "muscle pain": {
        "conditions": [
            {"name": "Muscle Strain", "severity": "low", "score": 1},
            {"name": "Body Ache", "severity": "low", "score": 1},
            {"name": "Overexertion", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🛁 Taking Epsom salt bath",
            "🌿 Applying warm compress",
            "🌿 Massaging with ginger oil",
            "🧘 Gentle stretching exercises",
            "🌿 Taking ashwagandha"
        ]
    },
    "stiffness": {
        "conditions": [
            {"name": "Joint Stiffness", "severity": "low", "score": 1},
            {"name": "Morning Stiffness", "severity": "low", "score": 1},
            {"name": "Vata Imbalance", "severity": "low", "score": 1}
        ],
        "remedies": [
            "🧘 Regular morning yoga",
            "🌿 Massaging with warm sesame oil",
            "🛁 Warm water bath",
            "🌿 Taking guggulu"
        ]
    }
}

symptoms_conditions.update(
    {
        "acidity": {
            "conditions": [
                {"name": "Acid Reflux", "severity": "medium", "score": 2},
                {"name": "Gastritis", "severity": "medium", "score": 2},
                {"name": "Indigestion", "severity": "low", "score": 1},
            ],
            "remedies": [
                "Drink lukewarm water in small sips.",
                "Avoid very spicy, oily, and late-night meals.",
                "Try fennel or cumin infused water after meals.",
                "Take light meals and avoid lying down immediately after eating.",
            ],
        },
        "leg pain": {
            "conditions": [
                {"name": "Muscle Strain", "severity": "low", "score": 1},
                {"name": "Joint Pain", "severity": "low", "score": 1},
                {"name": "Circulatory Fatigue", "severity": "low", "score": 1},
            ],
            "remedies": [
                "Rest the affected leg and avoid overexertion.",
                "Use warm compress for stiffness and gentle stretching.",
                "Stay hydrated and include potassium-rich foods.",
                "Use light massage with warm sesame oil.",
            ],
        },
        "body weakness": {
            "conditions": [
                {"name": "Fatigue", "severity": "low", "score": 1},
                {"name": "Dehydration", "severity": "medium", "score": 2},
                {"name": "Anemia", "severity": "low", "score": 1},
            ],
            "remedies": [
                "Drink ORS or electrolyte fluids through the day.",
                "Take balanced meals with fruits, lentils, and leafy vegetables.",
                "Get 7-8 hours sleep and avoid screen stress at night.",
                "Include dates, raisins, and soaked almonds in diet.",
            ],
        },
        "stomach pain": {
            "conditions": [
                {"name": "Digestive Issue", "severity": "low", "score": 1},
                {"name": "Gastritis", "severity": "medium", "score": 2},
                {"name": "Acid Reflux", "severity": "medium", "score": 2},
            ],
            "remedies": [
                "Use warm water and avoid very cold drinks.",
                "Prefer simple meals like rice, khichdi, and bananas.",
                "Avoid fried and processed foods until symptoms improve.",
                "Try ginger-fennel tea in small quantities.",
            ],
        },
        "waist pain": {
            "conditions": [
                {"name": "Lower Back Strain", "severity": "low", "score": 1},
                {"name": "Muscle Spasm", "severity": "low", "score": 1},
                {"name": "Posture-related Pain", "severity": "low", "score": 1},
            ],
            "remedies": [
                "Use a warm compress on lower back 2-3 times daily.",
                "Avoid prolonged sitting and improve posture support.",
                "Do gentle mobility stretches and short walks.",
                "Massage with warm oil before sleep.",
            ],
        },
        "watery eyes": {
            "conditions": [
                {"name": "Allergic Eye Irritation", "severity": "low", "score": 1},
                {"name": "Common Cold", "severity": "low", "score": 1},
                {"name": "Viral Eye Irritation", "severity": "low", "score": 1},
            ],
            "remedies": [
                "Wash eyes gently with clean cool water.",
                "Avoid rubbing eyes and screen overuse.",
                "Use clean tissues and maintain hand hygiene.",
                "Rest eyes and maintain good hydration.",
            ],
        },
        "nightfall": {
            "conditions": [
                {"name": "Nocturnal Emission", "severity": "low", "score": 1},
                {"name": "Stress/Anxiety", "severity": "low", "score": 1},
                {"name": "Sleep Disturbance", "severity": "low", "score": 1},
            ],
            "remedies": [
                "Follow regular sleep schedule and reduce late-night stimulation.",
                "Practice breathing exercises before bed.",
                "Avoid spicy or heavy meals late at night.",
                "Hydrate well and maintain balanced nutrition.",
            ],
        },
        "menstrual pain": {
            "conditions": [
                {"name": "Dysmenorrhea", "severity": "medium", "score": 2},
                {"name": "Hormonal Cramps", "severity": "medium", "score": 2},
                {"name": "Pelvic Muscle Spasm", "severity": "low", "score": 1},
            ],
            "remedies": [
                "Use warm compress over lower abdomen.",
                "Take warm fluids and avoid skipping meals.",
                "Do gentle stretching and light walking.",
                "Seek medical care for severe pain, heavy bleeding, or faintness.",
            ],
        },
        "dehydration": {
            "conditions": [
                {"name": "Dehydration", "severity": "medium", "score": 2},
                {"name": "Heat Exhaustion", "severity": "medium", "score": 2},
                {"name": "Weakness", "severity": "low", "score": 1},
            ],
            "remedies": [
                "Take ORS solution in small frequent sips.",
                "Drink coconut water, lemon water with salt, or electrolyte fluids.",
                "Avoid heavy sun exposure until hydration improves.",
                "Seek urgent care for confusion, persistent vomiting, or reduced urination.",
            ],
        },
    }
)

SYMPTOM_CATEGORY_GROUPS = {
    "respiratory": [
        "cough",
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

