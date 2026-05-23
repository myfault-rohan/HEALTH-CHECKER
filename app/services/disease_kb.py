"""
Disease Knowledge Base
======================
Loaded from Kaggle CSVs at import time.
Provides: description, ayurvedic_remedies, precautions per disease name.
All remedies are Ayurvedic / natural — no drugs or chemicals.
"""
import csv
from pathlib import Path

_RAW = Path(__file__).parent.parent.parent / "model" / "_raw_downloads"

# ── Ayurvedic remedy overrides (replaces chemical Kaggle precautions) ────────
AYURVEDIC_REMEDIES = {
    "Fungal Infection": [
        "🌿 Apply neem leaf paste on affected area daily",
        "🌿 Use turmeric-coconut oil mix as antifungal",
        "🌿 Bathe with neem water (boil 20 neem leaves)",
        "🌿 Apply fresh aloe vera gel to soothe itching",
        "🧘 Keep affected area clean and dry at all times",
    ],
    "Allergy": [
        "🌿 Drink warm tulsi (holy basil) tea 2x daily",
        "🌿 Apply aloe vera gel to itchy areas",
        "🌿 Inhale steam with eucalyptus leaves",
        "🌿 Consume raw local honey to build tolerance",
        "🧘 Practice Pranayama to strengthen immunity",
    ],
    "Gerd": [
        "🌿 Drink aloe vera juice (1 tbsp) before meals",
        "🌿 Chew fennel seeds after eating",
        "🌿 Sip warm ginger tea with honey",
        "🌿 Mix 1 tsp of amla powder in warm water",
        "🧘 Eat smaller meals; avoid lying down after eating",
    ],
    "Chronic Cholestasis": [
        "🌿 Drink milk thistle tea daily (liver support)",
        "🌿 Take 1 tsp triphala powder in warm water at night",
        "🌿 Consume dandelion root tea for bile flow",
        "🌿 Add turmeric to meals for anti-inflammatory benefit",
        "🧘 Follow a low-fat, high-fibre plant-based diet",
    ],
    "Drug Reaction": [
        "🌿 Drink neem tea to purify blood",
        "🌿 Apply sandalwood paste to calm skin reactions",
        "🌿 Use aloe vera gel topically for rashes",
        "💧 Drink plenty of water to flush toxins",
        "⚕️ Stop the triggering substance and seek medical review",
    ],
    "Peptic Ulcer Disease": [
        "🌿 Drink raw cabbage juice daily (natural ulcer healer)",
        "🌿 Consume licorice root (mulethi) tea",
        "🌿 Eat banana and plantain — coats stomach lining",
        "🌿 Take 1 tsp of pure ghee in warm milk before bed",
        "🧘 Avoid spicy and fried foods; eat at regular intervals",
    ],
    "AIDS": [
        "🌿 Ashwagandha (500mg) daily to support immunity",
        "🌿 Tulsi leaves chewed daily — natural immunomodulator",
        "🌿 Giloy (Guduchi) kadha to strengthen immunity",
        "🌿 Amla (Indian gooseberry) juice — high Vitamin C",
        "⚕️ Always follow prescribed medical care in parallel",
    ],
    "Diabetes": [
        "🌿 Drink bitter gourd (karela) juice every morning",
        "🌿 Consume methi (fenugreek) seed water on empty stomach",
        "🌿 Eat 1 tsp of turmeric + black pepper in warm milk",
        "🌿 Chew 5–10 curry leaves daily",
        "🧘 Walk 30 minutes daily; practice yoga asanas",
    ],
    "Gastroenteritis": [
        "🌿 Drink jeera (cumin) water to settle stomach",
        "🌿 Sip warm ginger-honey tea",
        "🌿 Eat plain khichdi (rice + moong dal) for easy digestion",
        "💧 Drink ORS or coconut water to prevent dehydration",
        "🧘 Rest and avoid solid food for a few hours",
    ],
    "Asthma": [
        "🌿 Drink warm ginger + honey + black pepper tea",
        "🌿 Practice Bhramari Pranayama daily",
        "🌿 Inhale steam with ajwain (carom seeds)",
        "🌿 Consume licorice root (mulethi) with honey",
        "🧘 Keep living spaces dust-free; avoid cold air",
    ],
    "Hypertension": [
        "🌿 Drink hibiscus (gudhal) flower tea daily",
        "🌿 Eat 2 cloves of raw garlic in the morning",
        "🌿 Consume arjuna bark tea (Terminalia arjuna)",
        "🧘 Practice meditation and Shavasana daily",
        "🌿 Reduce salt; increase banana and spinach intake",
    ],
    "Migraine": [
        "🌿 Apply peppermint oil to temples and neck",
        "🌿 Drink Brahmi (Bacopa) herbal tea",
        "🌿 Apply lavender oil and rest in a dark room",
        "🌿 Sip warm ginger tea at onset of symptoms",
        "🧘 Practice Sheetali Pranayama for cooling effect",
    ],
    "Cervical Spondylosis": [
        "🌿 Apply warm sesame oil massage on neck daily",
        "🌿 Drink Shallaki (Boswellia) herbal tea for inflammation",
        "🌿 Use Mahanarayan oil for warm compress",
        "🧘 Practice Bhujangasana and gentle neck stretches",
        "🌿 Consume turmeric-milk (haldi doodh) before sleep",
    ],
    "Brain Hemorrhage": [
        "🌿 Ashwagandha for neuroprotective support post-recovery",
        "🌿 Brahmi supplements for cognitive rehabilitation",
        "🌿 Gentle massage with sesame oil to improve circulation",
        "🧘 Follow physiotherapy exercises for motor recovery",
        "⚕️ Requires immediate emergency medical care",
    ],
    "Jaundice": [
        "🌿 Drink radish (mooli) leaf juice — detoxifies liver",
        "🌿 Consume milk thistle extract daily",
        "🌿 Eat sugarcane juice with lime daily",
        "🌿 Drink barley water to flush toxins",
        "💧 Stay hydrated; eat papaya and ripe mangoes",
    ],
    "Malaria": [
        "🌿 Drink Papaya leaf juice to raise platelet count",
        "🌿 Take Giloy (Guduchi) kadha twice daily",
        "🌿 Eat tulsi leaves with black pepper and honey",
        "🌿 Apply neem oil to prevent mosquito bites",
        "⚕️ Medical treatment is essential — use herbs alongside",
    ],
    "Chickenpox": [
        "🌿 Bathe daily with neem-infused water",
        "🌿 Apply neem leaf paste to blisters",
        "🌿 Drink neem leaf decoction (kadha) twice daily",
        "🌿 Use sandalwood paste to reduce itching",
        "🧘 Rest well; avoid scratching to prevent scarring",
    ],
    "Dengue Fever": [
        "🌿 Drink papaya leaf juice 2x daily (raises platelets)",
        "🌿 Giloy stem juice with black pepper",
        "🌿 Eat pomegranate and kiwi to boost platelets",
        "💧 Drink coconut water every 2–3 hours",
        "🌿 Turmeric-milk to reduce body ache and fever",
    ],
    "Typhoid Fever": [
        "🌿 Eat high-calorie foods: boiled potatoes, bananas",
        "🌿 Drink pomegranate juice for strength",
        "🌿 Consume ginger-garlic tea to fight infection",
        "🌿 Triphala decoction to cleanse the gut",
        "💧 Drink boiled and cooled water only",
    ],
    "Hepatitis A": [
        "🌿 Drink gourd (lauki) juice for liver support",
        "🌿 Consume milk thistle (silymarin) tea daily",
        "🌿 Eat papaya and amla for antioxidant support",
        "🌿 Drink buttermilk with roasted jeera",
        "🧘 Rest completely; avoid oily and fried food",
    ],
    "Hepatitis B": [
        "🌿 Bhumyamalaki (Phyllanthus niruri) herb — proven hepatoprotective",
        "🌿 Drink kutki (Picrorhiza kurroa) root decoction",
        "🌿 Consume amla and turmeric in warm water daily",
        "🌿 Punarnava (Boerhavia diffusa) herb for liver regeneration",
        "⚕️ Follow prescribed antiviral treatment alongside herbs",
    ],
    "Hepatitis C": [
        "🌿 Milk thistle (silymarin) — strongest herbal liver protector",
        "🌿 Drink bhumyamalaki decoction daily",
        "🌿 Consume amla juice on empty stomach",
        "🌿 Turmeric + black pepper in warm water mornings",
        "⚕️ Hepatitis C requires medical antiviral therapy",
    ],
    "Hepatitis D": [
        "🌿 Bhumyamalaki for liver cell protection",
        "🌿 Milk thistle tea twice daily",
        "🌿 Amla + giloy juice combination daily",
        "🌿 Avoid alcohol completely; eat light plant-based diet",
        "⚕️ Requires specialist hepatology care",
    ],
    "Hepatitis E": [
        "🌿 Rest and drink plenty of clean boiled water",
        "🌿 Amla juice for immune and liver support",
        "🌿 Eat easily digestible foods: khichdi, moong soup",
        "🌿 Kutki and bhumyamalaki herbal combination",
        "🧘 Avoid alcohol and fatty foods completely",
    ],
    "Alcoholic Hepatitis": [
        "🌿 Milk thistle is essential — take twice daily",
        "🌿 Dandelion root tea to support liver bile flow",
        "🌿 Kutki (Picrorhiza) herb for liver cell repair",
        "🌿 Drink fresh beetroot + carrot juice daily",
        "⚕️ Complete alcohol cessation is mandatory",
    ],
    "Tuberculosis": [
        "🌿 Vasaka (Malabar nut) leaf juice for lungs",
        "🌿 Drink tulsi + ginger + black pepper kadha daily",
        "🌿 Consume ashwagandha for immune strengthening",
        "🌿 Eat high-protein foods: lentils, eggs, nuts",
        "⚕️ Complete the full TB antibiotic course — never skip",
    ],
    "Common Cold": [
        "🌿 Drink tulsi-ginger-honey tea 3x daily",
        "🌿 Inhale steam with ajwain (carom seeds) and eucalyptus",
        "🌿 Mix turmeric + black pepper in warm milk",
        "🌿 Gargle with warm salt water twice daily",
        "💧 Drink plenty of warm fluids; rest adequately",
    ],
    "Pneumonia": [
        "🌿 Drink vasaka (Malabar nut) leaf decoction",
        "🌿 Take tulsi + ginger + black pepper kadha",
        "🌿 Steam inhalation with eucalyptus oil",
        "🌿 Consume turmeric milk with a pinch of black pepper",
        "⚕️ Pneumonia needs medical antibiotics — herbs are supportive",
    ],
    "Piles": [
        "🌿 Apply Arshoghni vati (Ayurvedic piles treatment)",
        "🌿 Drink warm water with triphala churna at night",
        "🌿 Apply haritaki and sesame oil paste locally",
        "🌿 Eat high-fibre diet: fruits, isabgol (psyllium husk)",
        "💧 Drink 3+ litres of water daily to soften stools",
    ],
    "Heart Attack": [
        "🌿 Arjuna bark (Terminalia arjuna) tea — cardio tonic",
        "🌿 Garlic (2 raw cloves) daily for arterial health",
        "🌿 Ashwagandha to reduce cardiac stress",
        "🌿 Consume omega-rich flaxseeds and walnuts daily",
        "⚕️ Heart attack is a medical emergency — call 108/112 immediately",
    ],
    "Varicose Veins": [
        "🌿 Apply horse chestnut extract gel on legs",
        "🌿 Elevate legs while resting (above heart level)",
        "🌿 Drink grape seed extract tea — strengthens veins",
        "🌿 Apply mahanarayan oil and gently massage upward",
        "🧘 Walk 30 minutes daily; avoid standing for long periods",
    ],
    "Hypothyroidism": [
        "🌿 Consume ashwagandha (500mg) — thyroid support",
        "🌿 Eat selenium-rich foods: Brazil nuts, sunflower seeds",
        "🌿 Drink kanchanar guggulu decoction (classic Ayurveda)",
        "🌿 Use iodine-rich seaweed/kelp in cooking",
        "🧘 Practice Sarvangasana (shoulder stand) yoga pose",
    ],
    "Hyperthyroidism": [
        "🌿 Lemon balm tea — calms overactive thyroid",
        "🌿 Bugleweed herb tea (do not use if pregnant)",
        "🌿 Brahmi and ashwagandha for hormonal balance",
        "🌿 Eat cooling foods: coconut, cucumber, coriander",
        "🧘 Shavasana and meditation to calm nervous system",
    ],
    "Hypoglycemia": [
        "🌿 Eat small frequent meals with complex carbs",
        "🌿 Drink sugarcane juice or eat dates immediately",
        "🌿 Consume ashwagandha to stabilise blood sugar",
        "🌿 Eat almond + walnut mix as snacks",
        "💧 Carry natural jaggery candy as emergency sugar",
    ],
    "Osteoarthritis": [
        "🌿 Take Shallaki (Boswellia) — reduces joint inflammation",
        "🌿 Massage with warm sesame or mahanarayan oil",
        "🌿 Drink turmeric + ginger tea twice daily",
        "🌿 Consume guggul (Commiphora) for joint lubrication",
        "🧘 Practice Pawanmuktasana series for joints",
    ],
    "Arthritis": [
        "🌿 Apply castor oil pack on inflamed joints",
        "🌿 Drink Shallaki (Boswellia) + Guggul tea",
        "🌿 Take turmeric + black pepper capsules",
        "🌿 Use warm sesame oil for daily joint massage",
        "🧘 Gentle yoga and swimming — low-impact exercises",
    ],
    "Vertigo": [
        "🌿 Eat a few almonds soaked overnight — nerve tonic",
        "🌿 Drink ginger tea to reduce nausea and dizziness",
        "🌿 Brahmi and shankhapushpi for vestibular support",
        "🌿 Use sesame oil warm ear drops (Karna Purana)",
        "🧘 Epley manoeuvre exercises under guidance",
    ],
    "Acne": [
        "🌿 Apply neem + turmeric face pack (15 min, 3x/week)",
        "🌿 Use rose water as a natural toner",
        "🌿 Apply aloe vera gel overnight on breakouts",
        "🌿 Drink 2 glasses of methi (fenugreek) seed water daily",
        "🧘 Avoid oily and spicy food; manage stress",
    ],
    "Urinary Tract Infection": [
        "🌿 Drink cranberry juice (unsweetened) daily",
        "🌿 Consume gokshura (Tribulus) herbal tea",
        "🌿 Drink barley water every 2 hours",
        "🌿 Eat 1 tsp of coriander seed powder in water",
        "💧 Drink minimum 3 litres of water daily",
    ],
    "Psoriasis": [
        "🌿 Apply neem oil directly to plaques",
        "🌿 Take soak in warm water with Himalayan salt",
        "🌿 Use aloe vera gel 2x daily on patches",
        "🌿 Drink bitter gourd (karela) juice daily — blood purifier",
        "🧘 Avoid stress triggers; follow Panchakarma Ayurvedic therapy",
    ],
    "Impetigo": [
        "🌿 Apply neem leaf paste — natural antibacterial",
        "🌿 Use turmeric + coconut oil paste on sores",
        "🌿 Bathe with neem-infused warm water",
        "🌿 Apply manuka honey to wounds for healing",
        "🧘 Keep area clean; change clothes and towels daily",
    ],
    "Dehydration": [
        "💧 Drink ORS (oral rehydration salts) or coconut water",
        "🌿 Sip jeera (cumin) water throughout the day",
        "🌿 Eat water-rich fruits: watermelon, cucumber, oranges",
        "🌿 Drink buttermilk with a pinch of salt and roasted jeera",
        "🧘 Avoid tea/coffee; rest in shade",
    ],
    "Muscle Strain": [
        "🌿 Apply warm mahanarayan oil and massage gently",
        "🌿 Use castor oil warm compress on strained area",
        "🌿 Drink turmeric milk with ashwagandha powder",
        "🌿 Consume Shallaki (Boswellia) for inflammation",
        "🧘 Rest the muscle; do gentle stretching after 24hrs",
    ],
}

# ── Load Kaggle description CSV ───────────────────────────────────────────────
_DESCRIPTIONS: dict[str, str] = {}
_PRECAUTIONS: dict[str, list[str]] = {}

def _normalise(name: str) -> str:
    return " ".join(name.strip().split()).title()


def _load_descriptions():
    path = _RAW / "symptom_Description.csv"
    if not path.exists():
        return
    with open(path, encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            key = _normalise(row.get("Disease", ""))
            desc = (row.get("Description") or "").strip()
            if key and desc:
                _DESCRIPTIONS[key] = desc


def _load_precautions():
    path = _RAW / "symptom_precaution.csv"
    if not path.exists():
        return
    with open(path, encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            key = _normalise(row.get("Disease", ""))
            tips = [
                row.get(f"Precaution_{i}", "").strip()
                for i in range(1, 5)
                if row.get(f"Precaution_{i}", "").strip()
            ]
            if key and tips:
                _PRECAUTIONS[key] = tips


_load_descriptions()
_load_precautions()

# ── Aliases: map our canonical disease names → Kaggle names ──────────────────
_ALIASES: dict[str, str] = {
    "Bronchial Asthma": "Bronchial Asthma",
    "Asthma": "Bronchial Asthma",
    "Chicken Pox": "Chicken Pox",
    "Chickenpox": "Chicken Pox",
    "Dengue Fever": "Dengue",
    "Dengue": "Dengue",
    "Typhoid Fever": "Typhoid",
    "Typhoid": "Typhoid",
    "Paralysis (Brain Hemorrhage)": "Paralysis (Brain Hemorrhage)",
    "Brain Hemorrhage": "Paralysis (Brain Hemorrhage)",
    "Paralysis": "Paralysis (Brain Hemorrhage)",
    "Dimorphic Hemmorhoids(Piles)": "Dimorphic Hemorrhoids(Piles)",
    "Dimorphic Haemorrhoids(Piles)": "Dimorphic Hemorrhoids(Piles)",
    "Piles": "Dimorphic Hemorrhoids(Piles)",
    "Osteoarthristis": "Osteoarthristis",
    "Osteoarthritis": "Osteoarthristis",
    "(Vertigo) Paroymsal Positional Vertigo": "(Vertigo) Paroymsal  Positional Vertigo",
    "Vertigo": "(Vertigo) Paroymsal  Positional Vertigo",
    "Peptic Ulcer Disease": "Peptic Ulcer Diseae",
    "Peptic Ulcer Diseae": "Peptic Ulcer Diseae",
    "Hepatitis A": "Hepatitis A",
    "Gerd": "Gerd",
    "Heart Attack": "Heart Attack",
    "Common Cold": "Common Cold",
    "Urinary Tract Infection": "Urinary Tract Infection",
    "Drug Reaction": "Drug Reaction",
    "Fungal Infection": "Fungal Infection",
    "Alcoholic Hepatitis": "Alcoholic Hepatitis",
    "Aids": "AIDS",
    "Cervical Spondylosis": "Cervical Spondylosis",
}


def _resolve(name: str) -> str:
    """Resolve a disease name to the canonical key used internally."""
    t = _normalise(name)
    return _ALIASES.get(t, t)


# ── Public API ────────────────────────────────────────────────────────────────

def get_description(disease_name: str) -> str:
    """Return a clinical description for the disease."""
    key = _resolve(disease_name)
    return _DESCRIPTIONS.get(key, _DESCRIPTIONS.get(disease_name, ""))


def get_ayurvedic_remedies(disease_name: str) -> list[str]:
    """Return Ayurvedic remedies. Falls back to empty list."""
    key = _resolve(disease_name)
    return AYURVEDIC_REMEDIES.get(key, AYURVEDIC_REMEDIES.get(disease_name, []))


def get_precautions(disease_name: str) -> list[str]:
    """
    Return lifestyle precautions from Kaggle — filtered to remove
    chemical/drug references, keeping only natural advice.
    """
    drug_keywords = {
        "antibiotic", "medication", "medicine", "drug", "asprin", "aspirin",
        "acetaminophen", "otc", "anti itch medicine", "radioactive",
        "vaccination", "vaccine", "therapy", "oinment",
    }
    key = _resolve(disease_name)
    raw = _PRECAUTIONS.get(key, _PRECAUTIONS.get(disease_name, []))
    filtered = []
    for tip in raw:
        low = tip.lower()
        if not any(kw in low for kw in drug_keywords):
            filtered.append(tip.capitalize())
    return filtered


def get_full_info(disease_name: str) -> dict:
    """Return combined description + remedies + precautions."""
    return {
        "description": get_description(disease_name),
        "ayurvedic_remedies": get_ayurvedic_remedies(disease_name),
        "precautions": get_precautions(disease_name),
    }
