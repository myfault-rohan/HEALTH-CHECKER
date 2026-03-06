import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-dev-secret-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "health_checker.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def normalize_email(raw_email):
    return (raw_email or "").strip().lower()


def create_user(email, password):
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (email, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (
                normalize_email(email),
                generate_password_hash(password),
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()


def verify_user(email, password):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (normalize_email(email),),
        ).fetchone()
    if not row:
        return False
    return check_password_hash(row["password_hash"], password)


def save_history_entry(email, payload):
    now = datetime.utcnow().isoformat(timespec="seconds")
    serialized = json.dumps(payload, ensure_ascii=False)
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO history (email, created_at, payload_json)
            VALUES (?, ?, ?)
            """,
            (normalize_email(email), now, serialized),
        )
        conn.commit()


def get_history_entries(email):
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT created_at, payload_json
            FROM history
            WHERE email = ?
            ORDER BY id DESC
            LIMIT 25
            """,
            (normalize_email(email),),
        ).fetchall()

    parsed = []
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
            parsed.append(payload)
        except json.JSONDecodeError:
            continue
    return parsed

# Symptom to conditions mapping with Ayurveda remedies (Dabur-style)
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


init_db()

CHECKER_SESSION_KEYS = [
    "selected_symptoms",
    "condition_details",
    "remedies",
    "emergency_detected",
    "emergency_message",
    "analysis",
    "active_condition",
    "lifestyle_suggestions",
]


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


def clear_checker_session():
    for key in CHECKER_SESSION_KEYS:
        session.pop(key, None)


def get_profile_from_session():
    try:
        age = int(session.get("patient_age", 0))
    except (TypeError, ValueError):
        age = 0
    gender = (session.get("patient_gender") or "").strip().lower()
    return age, gender


def has_profile():
    age, gender = get_profile_from_session()
    return age > 0 and gender in {"male", "female", "other"}


def format_gender(gender):
    if not gender:
        return "Not set"
    return gender.capitalize()


def checker_sidebar_context():
    age, gender = get_profile_from_session()
    return {
        "age": age if age > 0 else "Not set",
        "gender": format_gender(gender),
        "selected_symptoms": session.get("selected_symptoms", []),
    }


def get_condition_from_session(condition_name):
    condition_details = session.get("condition_details", [])
    target = (condition_name or "").strip().lower()
    for condition in condition_details:
        if condition.get("name", "").strip().lower() == target:
            return condition
    return None


@app.route("/")
@login_required
def index():
    return redirect(url_for("info"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "logged_in" in session:
        return redirect(url_for("info"))

    error = ""
    if request.method == "POST":
        email = normalize_email(request.form.get("email"))
        password = request.form.get("password", "")
        if not email or not password:
            error = "Please enter both email and password."
        elif verify_user(email, password):
            session["logged_in"] = True
            session["email"] = email
            return redirect(url_for("info"))
        else:
            error = "Invalid email or password."
    return render_template("login.html", error=error)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "logged_in" in session:
        return redirect(url_for("info"))

    error = ""
    if request.method == "POST":
        email = normalize_email(request.form.get("email"))
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not password:
            error = "Email and password are required."
        elif len(password) < 6:
            error = "Use at least 6 characters for password."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            try:
                create_user(email, password)
                session["logged_in"] = True
                session["email"] = email
                return redirect(url_for("info"))
            except sqlite3.IntegrityError:
                error = "That email is already registered."

    return render_template("signup.html", error=error)


@app.route("/info", methods=["GET", "POST"])
@login_required
def info():
    error = ""
    age, gender = get_profile_from_session()
    form_age = age if age > 0 else ""
    form_gender = gender

    if request.method == "POST":
        try:
            age = int(request.form.get("age", 0))
        except ValueError:
            age = 0
        gender = (request.form.get("gender") or "").strip().lower()

        form_age = request.form.get("age", "")
        form_gender = gender

        if age <= 0 or age > 120:
            error = "Please enter a valid age between 1 and 120."
        elif gender not in {"male", "female", "other"}:
            error = "Please select a gender."
        else:
            session["patient_age"] = age
            session["patient_gender"] = gender
            clear_checker_session()
            return redirect(url_for("symptoms"))

    return render_template(
        "info.html",
        current_step="info",
        show_steps=True,
        show_sidebar=True,
        sidebar=checker_sidebar_context(),
        age=form_age,
        gender=form_gender,
        error=error,
    )


@app.route("/symptoms")
@login_required
def symptoms():
    if not has_profile():
        return redirect(url_for("info"))

    searchable_symptoms = sorted(
        ordered_unique(list(symptoms_conditions.keys()) + list(SYMPTOM_ALIASES.keys()))
    )

    return render_template(
        "symptoms.html",
        current_step="symptoms",
        show_steps=True,
        show_sidebar=True,
        sidebar=checker_sidebar_context(),
        symptom_names=searchable_symptoms,
        selected_symptoms=session.get("selected_symptoms", []),
    )


@app.route("/conditions")
@login_required
def conditions():
    if not has_profile():
        return redirect(url_for("info"))

    condition_details = session.get("condition_details", [])
    if not condition_details:
        return redirect(url_for("symptoms"))

    return render_template(
        "conditions.html",
        current_step="conditions",
        show_steps=True,
        show_sidebar=True,
        sidebar=checker_sidebar_context(),
        condition_details=condition_details,
        analysis=session.get("analysis", {}),
    )


@app.route("/details/<path:condition_name>")
@login_required
def details(condition_name):
    if not has_profile():
        return redirect(url_for("info"))
    if not session.get("condition_details"):
        return redirect(url_for("symptoms"))

    condition = get_condition_from_session(condition_name)
    if not condition:
        return redirect(url_for("conditions"))

    session["active_condition"] = condition.get("name", "")

    return render_template(
        "details.html",
        current_step="details",
        show_steps=True,
        show_sidebar=True,
        sidebar=checker_sidebar_context(),
        condition=condition,
    )


@app.route("/treatment/<path:condition_name>")
@login_required
def treatment(condition_name):
    if not has_profile():
        return redirect(url_for("info"))
    if not session.get("condition_details"):
        return redirect(url_for("symptoms"))

    condition = get_condition_from_session(condition_name)
    if not condition:
        return redirect(url_for("conditions"))

    session["active_condition"] = condition.get("name", "")
    emergency_detected = bool(session.get("emergency_detected"))
    emergency_message = session.get("emergency_message", "")

    when_to_see_doctor = []
    if emergency_detected and emergency_message:
        when_to_see_doctor.append(emergency_message)

    urgency = (condition.get("urgency") or "low").lower()
    if urgency == "high":
        when_to_see_doctor.append("This pattern is high urgency. Seek same-day in-person medical care.")
    elif urgency == "medium":
        when_to_see_doctor.append("If symptoms worsen or continue beyond 24-48 hours, schedule a clinician visit.")
    else:
        when_to_see_doctor.append("See a doctor if symptoms persist, interfere with daily life, or new symptoms appear.")
    when_to_see_doctor.append("Call emergency services immediately for severe chest pain, breathing trouble, fainting, or confusion.")
    when_to_see_doctor = ordered_unique(when_to_see_doctor)

    lifestyle_suggestions = session.get("lifestyle_suggestions", [])
    if not lifestyle_suggestions:
        lifestyle_suggestions = [
            "Maintain hydration throughout the day.",
            "Get adequate sleep and avoid overexertion.",
            "Prefer light and balanced meals while recovering.",
        ]

    return render_template(
        "treatment.html",
        current_step="treatment",
        show_steps=True,
        show_sidebar=True,
        sidebar=checker_sidebar_context(),
        condition=condition,
        remedies=session.get("remedies", []),
        emergency_detected=emergency_detected,
        emergency_message=emergency_message,
        when_to_see_doctor=when_to_see_doctor,
        lifestyle_suggestions=lifestyle_suggestions,
    )


@app.route("/start-over")
@login_required
def start_over():
    clear_checker_session()
    session.pop("patient_age", None)
    session.pop("patient_gender", None)
    return redirect(url_for("info"))


@app.route("/about")
@login_required
def about():
    return render_template("about.html", show_steps=False, show_sidebar=False)


@app.route("/contact")
@login_required
def contact():
    return render_template("contact.html", show_steps=False, show_sidebar=False)


@app.route("/profile")
@login_required
def profile():
    email = normalize_email(session.get("email"))
    history = get_history_entries(email)
    return render_template("profile.html", history=history, show_steps=False, show_sidebar=False)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/check", methods=["POST"])
@login_required
def check_symptoms():
    if not has_profile():
        return redirect(url_for("info"))

    selected_symptoms = ordered_unique(
        [
            normalize_symptom_name(symptom)
            for symptom in request.form.getlist("symptoms")
            if (symptom or "").strip()
        ]
    )
    if not selected_symptoms:
        clear_checker_session()
        return redirect(url_for("symptoms"))

    age, gender = get_profile_from_session()
    form_data = {key: (request.form.get(key) or "").strip() for key in request.form.keys()}
    cough_type = (form_data.get("cough_type") or "").strip().lower()

    remedies_pool = []
    for symptom in selected_symptoms:
        symptom_data = symptoms_conditions.get(symptom)
        if symptom_data:
            remedies_pool.extend(symptom_data.get("remedies", []))
    remedies = ordered_unique(remedies_pool)[:24]

    lifestyle_suggestions = []

    # Generate authentic Ayurvedic paragraph
    if remedies:
        # Group remedies by type
        herbals = [r for r in remedies if "🌿" in r]
        dietary = [r for r in remedies if "🥕" in r or "🍎" in r or "🍌" in r or "🍚" in r or "🥬" in r]
        lifestyle = [r for r in remedies if "🧘" in r or "😴" in r or "🛌" in r or "👁️" in r]
        liquids = [r for r in remedies if "💧" in r or "🫐" in r or "🥛" in r]
        other = [r for r in remedies if r not in herbals + dietary + lifestyle + liquids]

        remedy_paragraphs = []

        if herbals:
            herbs_text = ", ".join([r.replace("🌿 ", "") for r in herbals[:-1]])
            if herbs_text:
                remedy_paragraphs.append(
                    f"🌿 **Ayurvedic Herbal Remedies**: {herbs_text}{' and ' if len(herbs_text) > 0 else ''}{herbals[-1].replace('🌿 ', '') if herbals else ''}."
                )
            else:
                remedy_paragraphs.append(f"🌿 **Ayurvedic Herbal Remedies**: {herbals[-1].replace('🌿 ', '')}.")

        if dietary:
            foods_text = ", ".join([r.split(" ", 1)[1] if " " in r else r for r in dietary])
            remedy_paragraphs.append(f"🍎 **Dietary Recommendations**: Incorporate {foods_text} into your daily diet to support recovery and boost immunity.")

        if lifestyle:
            lifestyle_text = ", ".join(
                [r.replace("🧘 ", "").replace("😴 ", "").replace("🛌 ", "").replace("👁️ ", "") for r in lifestyle]
            )
            remedy_paragraphs.append(f"🧘 **Lifestyle & Rest**: {lifestyle_text}.")

        if liquids:
            liquids_text = ", ".join([r.replace("💧 ", "").replace("🫐 ", "").replace("🥛 ", "") for r in liquids])
            remedy_paragraphs.append(f"💧 **Hydration**: {liquids_text}.")

        if other:
            other_text = " ".join(other)
            remedy_paragraphs.append(other_text)

        final_remedy_text = " ".join(remedy_paragraphs)
        remedies = [final_remedy_text]

        lifestyle_suggestions = ordered_unique(
            [
                item.replace("🧘 ", "")
                .replace("😴 ", "")
                .replace("🛌 ", "")
                .replace("👁️ ", "")
                .replace("💧 ", "")
                .replace("🫐 ", "")
                .replace("🥛 ", "")
                .replace("🌿 ", "")
                for item in lifestyle + liquids + dietary
            ]
        )[:8]

    condition_details = compute_condition_matches(selected_symptoms, age, gender, form_data)
    final_conditions = [f"{condition['name']} ({condition['match_label']})" for condition in condition_details]

    emergency_detected, emergency_message = detect_emergency_signals(selected_symptoms, form_data)

    quality = "good"
    suggestion = "Results confidence improves when you add specific symptom details."
    if len(selected_symptoms) <= 1:
        quality = "limited"
        suggestion = "Add at least 2-3 symptoms for better accuracy."
    elif len(selected_symptoms) >= 5:
        quality = "high"
        suggestion = "Good symptom coverage. Review the top matches and urgent flags carefully."
    if "cough" in selected_symptoms and cough_type in {"dry", "wet"}:
        suggestion = f"{suggestion} Cough type noted as {cough_type}."

    history_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "symptoms": selected_symptoms,
        "conditions": final_conditions,
        "remedies": remedies,
        "analysis_quality": quality,
    }

    email = normalize_email(session.get("email"))
    if email:
        save_history_entry(email, history_entry)

    session["selected_symptoms"] = selected_symptoms
    session["condition_details"] = condition_details
    session["remedies"] = remedies
    session["emergency_detected"] = emergency_detected
    session["emergency_message"] = emergency_message
    session["analysis"] = {
        "symptom_count": len(selected_symptoms),
        "quality": quality,
        "suggestion": suggestion,
    }
    session["lifestyle_suggestions"] = lifestyle_suggestions
    if condition_details:
        session["active_condition"] = condition_details[0]["name"]

    return redirect(url_for("conditions"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
