const STORAGE_KEY = "hc_theme_mode";

function showLoadingOverlay() {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) overlay.classList.remove("d-none");
}

function hideLoadingOverlay() {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) overlay.classList.add("d-none");
}

function setThemeMode(mode) {
    const darkMode = mode === "dark";
    document.body.classList.toggle("dark-mode", darkMode);
    document.documentElement.classList.remove("preload-dark");
    document.body.setAttribute("data-bs-theme", darkMode ? "dark" : "light");
}

function setupThemeToggle() {
    const toggle = document.getElementById("theme-toggle");
    const savedMode = localStorage.getItem(STORAGE_KEY) || "light";
    setThemeMode(savedMode);
    if (!toggle) return;

    toggle.addEventListener("click", () => {
        const nextMode = document.body.classList.contains("dark-mode") ? "light" : "dark";
        localStorage.setItem(STORAGE_KEY, nextMode);
        setThemeMode(nextMode);
    });
}

function setupAOS() {
    if (window.AOS) {
        window.AOS.init({
            duration: 650,
            once: true,
            easing: "ease-out-cubic",
        });
    }
}

function setupWorkflowProgress() {
    const track = document.getElementById("workflow-track");
    if (!track) return;
    const steps = Array.from(track.querySelectorAll(".workflow-step"));
    const activeIndex = Math.max(
        0,
        steps.findIndex((step) => step.classList.contains("is-active"))
    );
    const width = steps.length > 1 ? (activeIndex / (steps.length - 1)) * 100 : 0;
    track.style.setProperty("--progress-width", `${width}%`);
}

function setupRevealSections() {
    const nodes = document.querySelectorAll(".reveal-on-scroll");
    if (!nodes.length) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.2 }
    );

    nodes.forEach((node) => observer.observe(node));
}

function setupCountUp() {
    const targets = document.querySelectorAll("[data-countup]");
    if (!targets.length) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                const node = entry.target;
                const endValue = Number(node.dataset.countup || "0");
                const suffix = node.dataset.suffix || "";
                const duration = 1000;
                const start = performance.now();

                const tick = (now) => {
                    const progress = Math.min((now - start) / duration, 1);
                    node.textContent = `${Math.floor(progress * endValue)}${suffix}`;
                    if (progress < 1) {
                        requestAnimationFrame(tick);
                    }
                };

                requestAnimationFrame(tick);
                observer.unobserve(node);
            });
        },
        { threshold: 0.4 }
    );

    targets.forEach((target) => observer.observe(target));
}

function setupTypewriter() {
    const target = document.getElementById("hero-typewriter");
    if (!target) return;

    const phrases = [
        "Check your symptoms.",
        "Understand your health.",
        "Get guidance fast.",
    ];
    let phraseIndex = 0;
    let charIndex = 0;
    let deleting = false;

    const type = () => {
        const phrase = phrases[phraseIndex];
        target.textContent = deleting
            ? phrase.slice(0, charIndex--)
            : phrase.slice(0, charIndex++);

        if (!deleting && charIndex > phrase.length + 1) {
            deleting = true;
            setTimeout(type, 1200);
            return;
        }

        if (deleting && charIndex < 0) {
            deleting = false;
            phraseIndex = (phraseIndex + 1) % phrases.length;
        }

        setTimeout(type, deleting ? 35 : 70);
    };

    type();
}

function setupRippleButtons() {
    document.querySelectorAll(".btn").forEach((button) => {
        button.addEventListener("click", (event) => {
            const ripple = document.createElement("span");
            ripple.className = "ripple";
            ripple.style.left = `${event.clientX - button.getBoundingClientRect().left}px`;
            ripple.style.top = `${event.clientY - button.getBoundingClientRect().top}px`;
            button.appendChild(ripple);
            window.setTimeout(() => ripple.remove(), 650);
        });
    });
}

function getSelectedSymptoms() {
    const hiddenContainer = document.getElementById("selected-symptom-inputs");
    if (!hiddenContainer) return [];
    return Array.from(
        hiddenContainer.querySelectorAll('input[name="symptoms"]')
    ).map((input) => input.value);
}

function refreshSymptomResults() {
    const searchInput = document.getElementById("symptom-search");
    if (searchInput && window.htmx) {
        window.htmx.trigger(searchInput, "keyup");
    }
}

function syncSelectedSymptomInputs() {
    const hiddenContainer = document.getElementById("selected-symptom-inputs");
    const selectedContainer = document.getElementById("selected-symptoms");
    const countDisplay = document.getElementById("symptom-count");
    if (!hiddenContainer) return;

    const values = getSelectedSymptoms();

    if (selectedContainer) {
        selectedContainer.innerHTML = "";
        values.forEach((value) => {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "symptom-pill removable-pill";
            chip.innerHTML = `<span>${value}</span><span class="pill-remove" aria-hidden="true">&times;</span>`;
            chip.setAttribute("aria-label", `Remove ${value}`);
            chip.addEventListener("click", () => {
                updateSelectedSymptom(value, false);
                refreshSymptomResults();
            });
            selectedContainer.appendChild(chip);
        });
        if (!values.length) {
            const emptyState = document.createElement("p");
            emptyState.className = "text-muted mb-0";
            emptyState.textContent = "No symptoms selected yet.";
            selectedContainer.appendChild(emptyState);
        }
    }

    if (countDisplay) {
        countDisplay.textContent = values.length;
    }

    document.querySelectorAll(".detail-field").forEach((field) => {
        const requires = (field.dataset.requires || "")
            .split(",")
            .map((item) => item.trim().toLowerCase());
        const shouldShow = requires.some((item) => values.includes(item));
        field.classList.toggle("d-none", !shouldShow);
    });
}

function updateSelectedSymptom(name, checked) {
    const hiddenContainer = document.getElementById("selected-symptom-inputs");
    if (!hiddenContainer) return;

    const existing = Array.from(
        hiddenContainer.querySelectorAll('input[name="symptoms"]')
    ).find((input) => input.value === name);
    if (checked && !existing) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "symptoms";
        input.value = name;
        hiddenContainer.appendChild(input);
    } else if (!checked && existing) {
        existing.remove();
    }
    syncSelectedSymptomInputs();
}

function updateSymptomResultButton(button) {
    const selected = getSelectedSymptoms().includes(button.dataset.symptom);
    button.dataset.selected = selected ? "true" : "false";
    button.setAttribute("aria-pressed", selected ? "true" : "false");
    button.classList.toggle("is-selected", selected);
    const state = button.querySelector(".symptom-result-state");
    if (state) {
        state.textContent = selected ? "Added" : "Add";
    }
}

function bindSymptomCards(scope = document) {
    scope.querySelectorAll(".symptom-result-button").forEach((button) => {
        updateSymptomResultButton(button);
        button.addEventListener("click", () => {
            const isSelected = button.dataset.selected === "true";
            updateSelectedSymptom(button.dataset.symptom, !isSelected);
            updateSymptomResultButton(button);
        });
    });
}

function setupVoiceInput() {
    const searchInput = document.getElementById("symptom-search");
    const button = document.getElementById("voice-search-button");
    const heardText = document.getElementById("voice-heard-text");
    const audioWave = document.getElementById("audio-wave");
    const zoneInput = document.getElementById("symptom-zone");
    if (!searchInput || !button) return;

    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        button.classList.add("d-none");
        if (audioWave) audioWave.classList.remove("is-visible");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;

    recognition.onstart = () => {
        button.classList.add("is-listening");
        if (audioWave) audioWave.classList.add("is-visible");
    };

    recognition.onend = () => {
        button.classList.remove("is-listening");
        if (audioWave) audioWave.classList.remove("is-visible");
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.trim().toLowerCase();
        searchInput.value = transcript;
        if (zoneInput) zoneInput.value = "";
        if (heardText) heardText.textContent = `Heard: ${transcript}`;
        if (window.htmx) {
            window.htmx.trigger(searchInput, "keyup");
        }
    };

    button.addEventListener("click", () => recognition.start());
}

function setupSymptomsPage() {
    const form = document.getElementById("symptom-form");
    if (!form) return;

    bindSymptomCards(document);
    syncSelectedSymptomInputs();
    setupVoiceInput();

    document.body.addEventListener("htmx:afterSwap", (event) => {
        if (event.target.id === "symptom-results") {
            bindSymptomCards(event.target);
            syncSelectedSymptomInputs();
        }
    });

    form.addEventListener("submit", (event) => {
        if (!getSelectedSymptoms().length) {
            event.preventDefault();
            document.getElementById("symptom-search")?.focus();
            return;
        }
        showLoadingOverlay();
    });
}

function setupConditionPage() {
    document.querySelectorAll(".confidence-bar").forEach((bar) => {
        window.setTimeout(() => {
            bar.style.width = `${bar.dataset.confidence}%`;
        }, 100);
    });

    const reportButtons = document.querySelectorAll(".btn-download");
    reportButtons.forEach((button) => {
        button.addEventListener("click", () => {
            button.classList.add("is-loading");
        });
    });

    const container = document.getElementById("conditions-page");
    if (!container) return;

    const highUrgency = container.dataset.highUrgency === "true";
    const checkId = container.dataset.checkId;

    if (highUrgency) {
        const warning = document.getElementById("conditions-warning-banner");
        if (warning) warning.classList.add("is-pulsing");
        return;
    }

    if (window.confetti && checkId) {
        const seenKey = `hc_confetti_${checkId}`;
        if (!sessionStorage.getItem(seenKey)) {
            sessionStorage.setItem(seenKey, "1");
            window.setTimeout(() => {
                window.confetti({
                    particleCount: 140,
                    spread: 80,
                    origin: { y: 0.55 },
                });
            }, 250);
        }
    }
}

function setupProfileAccordion() {
    document.querySelectorAll(".history-toggle").forEach((toggle) => {
        toggle.addEventListener("click", () => {
            const accordion = toggle.closest(".history-card")?.querySelector(".history-accordion");
            toggle.classList.toggle("is-open");
            toggle.textContent = toggle.classList.contains("is-open") ? "Collapse" : "Expand";
            toggle.setAttribute(
                "aria-expanded",
                toggle.classList.contains("is-open") ? "true" : "false"
            );
            if (accordion) {
                accordion.style.maxHeight = toggle.classList.contains("is-open")
                    ? `${accordion.scrollHeight + 20}px`
                    : "0px";
            }
        });
    });
}

function setupInfoChat() {
    const shell = document.getElementById("info-chat");
    if (!shell) return;

    const windowEl = document.getElementById("chat-window");
    const form = document.getElementById("info-form");
    const ageInput = document.getElementById("chat-age-input");
    const ageHidden = document.getElementById("info-age");
    const genderHidden = document.getElementById("info-gender");
    const prompt = document.getElementById("chat-prompt");
    const chipButtons = document.querySelectorAll(".chat-chip");

    const appendBubble = (text, type = "bot") => {
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble ${type}`;
        bubble.textContent = text;
        windowEl.appendChild(bubble);
        windowEl.scrollTop = windowEl.scrollHeight;
        return bubble;
    };

    window.setTimeout(() => {
        prompt.classList.add("d-none");
        appendBubble("Hi! Before we start, how old are you? 👋", "bot");
    }, 900);

    shell.addEventListener("submit", (event) => {
        event.preventDefault();
        const age = ageInput.value.trim();
        if (!age) return;
        ageHidden.value = age;
        appendBubble(age, "user");
        ageInput.value = "";
        appendBubble("Great! And your gender?", "bot");
        document.getElementById("gender-chip-group").classList.remove("d-none");
    });

    chipButtons.forEach((button) => {
        button.addEventListener("click", () => {
            chipButtons.forEach((chip) => chip.classList.remove("is-selected"));
            button.classList.add("is-selected");
            genderHidden.value = button.dataset.gender;
            appendBubble(button.textContent.trim(), "user");
            appendBubble("Perfect! Let's check your symptoms 🩺", "bot");
            window.setTimeout(() => form.submit(), 1200);
        });
    });
}

function setupLandingPage() {
    setupTypewriter();
    setupCountUp();
}

function setupLoadingForms() {
    document.querySelectorAll("form").forEach((form) => {
        if (form.id === "info-chat") return;
        form.addEventListener("submit", () => showLoadingOverlay());
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupThemeToggle();
    setupAOS();
    setupWorkflowProgress();
    setupRevealSections();
    setupRippleButtons();
    setupLandingPage();
    setupSymptomsPage();
    setupConditionPage();
    setupProfileAccordion();
    setupInfoChat();
    setupLoadingForms();
    hideLoadingOverlay();
});

window.addEventListener("pageshow", () => {
    hideLoadingOverlay();
});
