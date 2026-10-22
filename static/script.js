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
    const stickyContainer = document.getElementById("sticky-pills-list");
    const stickyBar = document.getElementById("sticky-selection-bar");
    const countDisplay = document.getElementById("symptom-count");
    const stickyCountNum = document.getElementById("sticky-count-num");
    const bottomCount = document.getElementById("bottom-symptom-count");

    if (!hiddenContainer) return;

    const values = getSelectedSymptoms();

    // 1. Update bottom selected pills
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
            });
            selectedContainer.appendChild(chip);
        });
        if (!values.length) {
            const emptyState = document.createElement("p");
            emptyState.className = "text-muted small mb-0";
            emptyState.textContent = "No symptoms selected yet. Tap any card or common symptom above.";
            selectedContainer.appendChild(emptyState);
        }
    }

    // 2. Update sticky bar pills
    if (stickyContainer) {
        stickyContainer.innerHTML = "";
        values.forEach((value) => {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "symptom-pill removable-pill py-1 px-2 small";
            chip.innerHTML = `<span>${value}</span><span class="pill-remove" aria-hidden="true">&times;</span>`;
            chip.setAttribute("aria-label", `Remove ${value}`);
            chip.addEventListener("click", () => {
                updateSelectedSymptom(value, false);
            });
            stickyContainer.appendChild(chip);
        });
    }

    // 3. Toggle sticky bar visibility
    if (stickyBar) {
        stickyBar.classList.toggle("d-none", values.length === 0);
    }

    // 4. Update count indicators
    if (countDisplay) {
        countDisplay.textContent = values.length;
    }
    if (stickyCountNum) {
        stickyCountNum.textContent = values.length;
    }
    if (bottomCount) {
        bottomCount.textContent = `${values.length} item${values.length === 1 ? '' : 's'}`;
    }

    // 5. Sync popular symptom chips
    document.querySelectorAll(".quick-symptom-chip").forEach((chip) => {
        const sym = chip.dataset.symptom;
        const isSel = values.includes(sym);
        chip.classList.toggle("is-selected", isSel);
        chip.setAttribute("aria-pressed", isSel ? "true" : "false");
        const icon = chip.querySelector(".quick-chip-status i");
        if (icon) {
            icon.className = isSel ? "fa-solid fa-check" : "fa-solid fa-plus";
        }
    });

    // 6. Sync symptom result buttons on page
    document.querySelectorAll(".symptom-result-button").forEach((button) => {
        updateSymptomResultButton(button);
    });

    // 7. Sync conditional clinical details fields
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

function clearAllSymptoms() {
    const hiddenContainer = document.getElementById("selected-symptom-inputs");
    if (hiddenContainer) {
        hiddenContainer.innerHTML = "";
    }
    syncSelectedSymptomInputs();
    refreshSymptomResults();
}

function updateSymptomResultButton(button) {
    const selected = getSelectedSymptoms().includes(button.dataset.symptom);
    button.dataset.selected = selected ? "true" : "false";
    button.setAttribute("aria-pressed", selected ? "true" : "false");
    button.classList.toggle("is-selected", selected);
    const pill = button.querySelector(".symptom-action-pill");
    if (pill) {
        pill.classList.toggle("is-added", selected);
        const icon = pill.querySelector("i");
        if (icon) {
            icon.className = selected ? "fa-solid fa-check me-1 check-icon" : "fa-solid fa-plus me-1 plus-icon";
        }
    }
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

window.syncSelectedSymptomInputs = syncSelectedSymptomInputs;
window.updateSelectedSymptom = updateSelectedSymptom;
window.clearAllSymptoms = clearAllSymptoms;

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

function setupAIChatVoiceInput() {
    const chatInput = document.getElementById("ai-chat-input");
    const voiceBtn = document.getElementById("ai-voice-button");
    const submitBtn = document.getElementById("ai-chat-submit");
    if (!chatInput || !voiceBtn) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        voiceBtn.classList.add("d-none");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    
    let isRecording = false;

    recognition.onstart = () => {
        isRecording = true;
        voiceBtn.classList.add("btn-danger", "text-white");
        voiceBtn.classList.remove("btn-outline-secondary");
        voiceBtn.innerHTML = '<i class="fa-solid fa-stop"></i>';
        chatInput.placeholder = "Listening...";
    };

    recognition.onend = () => {
        isRecording = false;
        voiceBtn.classList.remove("btn-danger", "text-white");
        voiceBtn.classList.add("btn-outline-secondary");
        voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
        chatInput.placeholder = "E.g., I have a terrible headache...";
        if (chatInput.value.trim() !== "") {
            submitBtn.click();
        }
    };

    recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            transcript += event.results[i][0].transcript;
        }
        chatInput.value = transcript;
    };

    voiceBtn.addEventListener("click", () => {
        if (isRecording) {
            recognition.stop();
        } else {
            chatInput.value = "";
            recognition.start();
        }
    });
}

function setupSymptomsPage() {
    const form = document.getElementById("symptom-form");
    if (!form) return;

    bindSymptomCards(document);
    syncSelectedSymptomInputs();
    setupVoiceInput();
    setupAIChatVoiceInput();

    const searchInput = document.getElementById("symptom-search");
    const searchClearBtn = document.getElementById("search-clear-btn");
    const categoryInput = document.getElementById("symptom-category");
    const zoneInput = document.getElementById("symptom-zone");
    const clearAllBtn = document.getElementById("clear-all-btn");

    // Clear all selected symptoms
    if (clearAllBtn) {
        clearAllBtn.addEventListener("click", clearAllSymptoms);
    }

    // Quick Add Popular Symptoms
    document.querySelectorAll(".quick-symptom-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            const sym = chip.dataset.symptom;
            const isSel = getSelectedSymptoms().includes(sym);
            updateSelectedSymptom(sym, !isSel);
        });
    });

    // Search Input handling: clear button & instant client-side filtering
    if (searchInput) {
        const toggleClearBtn = () => {
            if (searchClearBtn) {
                searchClearBtn.classList.toggle("d-none", !searchInput.value.trim());
            }
        };

        searchInput.addEventListener("input", () => {
            toggleClearBtn();

            // Client-side instant filter for zero-latency response
            const q = searchInput.value.trim().toLowerCase();
            const cols = document.querySelectorAll("#symptom-grid .symptom-col");
            if (cols.length > 0) {
                let matchCount = 0;
                cols.forEach((col) => {
                    const val = (col.dataset.symptomValue || "").toLowerCase();
                    const text = col.textContent.toLowerCase();
                    const isMatch = !q || val.includes(q) || text.includes(q);
                    col.classList.toggle("d-none", !isMatch);
                    if (isMatch) matchCount++;
                });
                const countBadge = document.getElementById("results-count");
                if (countBadge) countBadge.textContent = matchCount;
            }
        });

        // Quick add on Enter key
        searchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                const visibleButtons = Array.from(
                    document.querySelectorAll("#symptom-grid .symptom-col:not(.d-none) .symptom-result-button")
                );
                if (visibleButtons.length > 0) {
                    // Pick the first unselected, or fallback to first
                    const targetBtn = visibleButtons.find((btn) => btn.dataset.selected !== "true") || visibleButtons[0];
                    targetBtn.click();
                    searchInput.value = "";
                    toggleClearBtn();
                    refreshSymptomResults();
                }
            }
        });

        if (searchClearBtn) {
            searchClearBtn.addEventListener("click", () => {
                searchInput.value = "";
                toggleClearBtn();
                searchInput.focus();
                refreshSymptomResults();
            });
        }
    }

    // Category Tabs Bar
    document.querySelectorAll(".category-tab-chip").forEach((tab) => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".category-tab-chip").forEach((t) => {
                t.classList.remove("active");
                t.setAttribute("aria-selected", "false");
            });
            tab.classList.add("active");
            tab.setAttribute("aria-selected", "true");

            const selectedCat = tab.dataset.category || "all";
            if (categoryInput) categoryInput.value = selectedCat;
            if (zoneInput) zoneInput.value = "";

            // Reset active body map indicator if category is chosen
            const map = document.getElementById("body-map");
            if (map) {
                map.querySelectorAll(".body-zone").forEach((z) => z.classList.remove("is-active"));
            }
            const activeLabel = document.getElementById("active-zone-label");
            if (activeLabel) {
                activeLabel.textContent = `Active: ${tab.querySelector(".tab-label")?.textContent || selectedCat}`;
            }
            const resetBodymapBtn = document.getElementById("reset-bodymap-btn");
            if (resetBodymapBtn) {
                resetBodymapBtn.classList.toggle("d-none", selectedCat === "all");
            }

            refreshSymptomResults();
        });
    });

    // Reset filters delegation (e.g. from empty state)
    document.addEventListener("click", (e) => {
        const resetBtn = e.target.closest(".reset-filter-btn");
        if (resetBtn) {
            if (searchInput) {
                searchInput.value = "";
                if (searchClearBtn) searchClearBtn.classList.add("d-none");
            }
            if (categoryInput) categoryInput.value = "all";
            if (zoneInput) zoneInput.value = "";
            document.querySelectorAll(".category-tab-chip").forEach((t) => {
                t.classList.toggle("active", t.dataset.category === "all");
            });
            if (window.resetBodyMap) {
                window.resetBodyMap();
            }
            refreshSymptomResults();
        }
    });

    // HTMX afterSwap re-binding
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

    // SHAP waterfall bar animation — animate width when the panel enters view
    const shapBars = document.querySelectorAll(".shap-bar");
    if (shapBars.length > 0) {
        const revealBars = () => {
            shapBars.forEach((bar, idx) => {
                const targetPct = bar.parentElement?.closest(".shap-row")
                    ?.querySelector("[data-shap]")
                    ?.dataset.shap
                    ? null : null; // width is already encoded in the style attr from server

                // Delay each bar slightly for a cascading effect
                window.setTimeout(() => {
                    const inlineTarget = bar.getAttribute("data-target-width") || bar.style.width;
                    bar.style.width = "0";  // reset first
                    window.setTimeout(() => {
                        bar.style.width = inlineTarget || bar.style.width;
                    }, 40);
                }, idx * 60);
            });
        };

        // Use IntersectionObserver for scroll-triggered reveal
        const shapPanel = document.querySelector(".shap-panel");
        if (shapPanel && "IntersectionObserver" in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        revealBars();
                        observer.disconnect();
                    }
                });
            }, { threshold: 0.15 });
            observer.observe(shapPanel);
        } else {
            window.setTimeout(revealBars, 300);
        }
    }


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
        if (form.id === "info-chat" || form.id === "chat-form") return;
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
