const symptomBodyParts = {
    head: ["headache", "dizziness", "blurred vision", "confusion", "insomnia", "watery eyes"],
    chest: ["cough", "shortness of breath", "chest pain", "wheezing", "palpitations"],
    abdomen: ["abdominal pain", "stomach pain", "nausea", "vomiting", "diarrhea", "constipation", "bloating", "heartburn", "acidity", "menstrual pain", "urinary problems"],
    arms: ["sore throat", "runny nose", "sneezing", "congestion", "rash", "swelling"],
    legs: ["joint pain", "back pain", "muscle pain", "stiffness", "leg pain", "waist pain"]
};

const generalSymptoms = ["fever", "fatigue", "body weakness", "dehydration", "nightfall", "chills", "insomnia", "loss of appetite", "weight loss"];

function setupThemeToggle() {
    const toggle = document.getElementById("theme-toggle");
    if (!toggle) {
        return;
    }

    const key = "hc_theme_mode";
    const setLabel = () => {
        const isNight = document.body.classList.contains("night-mode");
        toggle.textContent = isNight ? "Day" : "Night";
    };

    const saved = localStorage.getItem(key);
    if (saved === "night") {
        document.body.classList.add("night-mode");
    }
    setLabel();

    toggle.addEventListener("click", () => {
        document.body.classList.toggle("night-mode");
        localStorage.setItem(
            key,
            document.body.classList.contains("night-mode") ? "night" : "day"
        );
        setLabel();
    });
}

function parseJsonFromScript(id) {
    const node = document.getElementById(id);
    if (!node) {
        return null;
    }
    try {
        return JSON.parse(node.textContent);
    } catch (_error) {
        return null;
    }
}

function uniqueLower(values) {
    const seen = new Set();
    const items = [];
    values.forEach((value) => {
        const normalized = String(value || "").trim().toLowerCase();
        if (!normalized || seen.has(normalized)) {
            return;
        }
        seen.add(normalized);
        items.push(normalized);
    });
    return items;
}

function setupSymptomsPage() {
    const form = document.getElementById("symptom-form");
    if (!form) {
        return;
    }

    const database = uniqueLower(parseJsonFromScript("symptom-database") || []);
    let selectedSymptoms = uniqueLower(parseJsonFromScript("initial-symptoms") || []);
    let activePart = null;

    const searchInput = document.getElementById("symptom-search");
    const dropdown = document.getElementById("autocomplete-dropdown");
    const selectedContainer = document.getElementById("selected-symptoms");
    const hiddenInputs = document.getElementById("symptom-hidden-inputs");
    const progressFill = document.getElementById("symptom-progress-fill");
    const symptomCount = document.getElementById("symptom-count");
    const bodyButtons = Array.from(document.querySelectorAll("#body-filter button"));
    const detailFields = Array.from(document.querySelectorAll(".detail-field[data-requires]"));

    function updateProgress() {
        const count = selectedSymptoms.length;
        const percentage = Math.min(100, Math.round((count / 12) * 100));
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        if (symptomCount) {
            symptomCount.textContent = String(count);
        }
    }

    function renderSelectedSymptoms() {
        if (!selectedContainer) {
            return;
        }

        selectedContainer.innerHTML = "";
        if (selectedSymptoms.length === 0) {
            selectedContainer.innerHTML = '<p class="empty-note">No symptoms selected yet.</p>';
            return;
        }

        selectedSymptoms.forEach((symptom) => {
            const chip = document.createElement("span");
            chip.className = "symptom-chip";
            chip.innerHTML = `${symptom}<button type="button" data-symptom="${symptom}" aria-label="Remove ${symptom}">x</button>`;
            selectedContainer.appendChild(chip);
        });
    }

    function updateDetailFieldVisibility() {
        const selected = new Set(selectedSymptoms);
        detailFields.forEach((field) => {
            const requires = (field.dataset.requires || "")
                .split(",")
                .map((item) => item.trim().toLowerCase())
                .filter(Boolean);
            const show = requires.some((symptom) => selected.has(symptom));
            field.classList.toggle("is-hidden", !show);
        });
    }

    function closeDropdown() {
        if (!dropdown) {
            return;
        }
        dropdown.classList.remove("show");
        dropdown.innerHTML = "";
    }

    function getPool() {
        if (!activePart || !symptomBodyParts[activePart]) {
            return database;
        }
        return uniqueLower([...symptomBodyParts[activePart], ...generalSymptoms]);
    }

    function filterSymptoms(query) {
        const normalized = String(query || "").trim().toLowerCase();
        if (!normalized) {
            return [];
        }
        return getPool()
            .filter((symptom) => symptom.includes(normalized) && !selectedSymptoms.includes(symptom))
            .slice(0, 8);
    }

    function addSymptom(symptom) {
        const normalized = String(symptom || "").trim().toLowerCase();
        if (!normalized || selectedSymptoms.includes(normalized)) {
            return;
        }
        selectedSymptoms.push(normalized);
        renderSelectedSymptoms();
        updateProgress();
        updateDetailFieldVisibility();
        if (searchInput) {
            searchInput.value = "";
            searchInput.focus();
        }
        closeDropdown();
    }

    function renderDropdown(items) {
        if (!dropdown) {
            return;
        }
        dropdown.innerHTML = "";

        if (items.length === 0) {
            closeDropdown();
            return;
        }

        items.forEach((item) => {
            const row = document.createElement("button");
            row.type = "button";
            row.className = "autocomplete-item";
            row.textContent = item;
            row.addEventListener("click", () => addSymptom(item));
            dropdown.appendChild(row);
        });

        dropdown.classList.add("show");
    }

    bodyButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const part = button.dataset.part;
            if (activePart === part) {
                activePart = null;
                button.classList.remove("active");
            } else {
                activePart = part;
                bodyButtons.forEach((item) => item.classList.remove("active"));
                button.classList.add("active");
            }

            if (searchInput && searchInput.value.trim()) {
                renderDropdown(filterSymptoms(searchInput.value));
            }
        });
    });

    if (searchInput) {
        searchInput.addEventListener("input", () => {
            renderDropdown(filterSymptoms(searchInput.value));
        });

        searchInput.addEventListener("keydown", (event) => {
            if (event.key !== "Enter") {
                return;
            }
            event.preventDefault();
            const matches = filterSymptoms(searchInput.value);
            if (matches.length > 0) {
                addSymptom(matches[0]);
            }
        });
    }

    document.addEventListener("click", (event) => {
        if (!dropdown || !searchInput) {
            return;
        }
        if (dropdown.contains(event.target) || searchInput.contains(event.target)) {
            return;
        }
        closeDropdown();
    });

    if (selectedContainer) {
        selectedContainer.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof HTMLElement)) {
                return;
            }
            const symptom = target.dataset.symptom;
            if (!symptom) {
                return;
            }
            selectedSymptoms = selectedSymptoms.filter((item) => item !== symptom);
            renderSelectedSymptoms();
            updateProgress();
            updateDetailFieldVisibility();
        });
    }

    form.addEventListener("submit", (event) => {
        if (selectedSymptoms.length === 0) {
            event.preventDefault();
            alert("Please add at least one symptom.");
            return;
        }

        if (!hiddenInputs) {
            return;
        }

        hiddenInputs.innerHTML = "";
        selectedSymptoms.forEach((symptom) => {
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = "symptoms";
            input.value = symptom;
            hiddenInputs.appendChild(input);
        });
    });

    renderSelectedSymptoms();
    updateProgress();
    updateDetailFieldVisibility();
}

function setupContactPage() {
    const messageForm = document.getElementById("message-form");
    if (!messageForm) {
        return;
    }

    messageForm.addEventListener("submit", (event) => {
        event.preventDefault();
        messageForm.innerHTML = "<p class=\"success-note\">Message sent. Our support team will contact you shortly.</p>";
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupThemeToggle();
    setupSymptomsPage();
    setupContactPage();
});

window.showContactDetails = function showContactDetails(type) {
    if (type === "phone") {
        alert("Phone: +1 (987) 654-3210");
    }
    if (type === "emergency") {
        alert("Emergency: +1 (555) 911-0000");
    }
};
