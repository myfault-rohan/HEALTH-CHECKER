function showLoadingOverlay() {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) overlay.classList.remove("d-none");
}

function hideLoadingOverlay() {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) overlay.classList.add("d-none");
}

function setThemeMode(mode) {
    const body = document.body;
    if (!body) return;
    const darkMode = mode === "dark";
    body.classList.toggle("theme-dark", darkMode);
    body.setAttribute("data-bs-theme", darkMode ? "dark" : "light");
}

function setupThemeToggle() {
    const toggle = document.getElementById("theme-toggle");
    if (!toggle) return;
    const storageKey = "hc_theme_mode";
    const savedMode = localStorage.getItem(storageKey) || "light";
    setThemeMode(savedMode);
    const updateButton = () => {
        const darkMode = document.body.classList.contains("theme-dark");
        toggle.innerHTML = darkMode ? '<i class="fa-solid fa-sun me-1"></i>Day' : '<i class="fa-solid fa-moon me-1"></i>Night';
    };
    updateButton();
    toggle.addEventListener("click", () => {
        const nextMode = document.body.classList.contains("theme-dark") ? "light" : "dark";
        setThemeMode(nextMode);
        localStorage.setItem(storageKey, nextMode);
        updateButton();
    });
}

// Functions for other pages
function setupSymptomsPage() {
    const form = document.getElementById("symptom-form");
    if (form) {
        form.addEventListener("submit", () => showLoadingOverlay());
    }

    const searchInput = document.getElementById("symptom-search");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase().trim();
            const items = document.querySelectorAll(".symptom-item");
            if (query === "") {
                items.forEach(item => item.classList.add("d-none"));
                return;
            }
            items.forEach(item => {
                const symptomName = item.getAttribute("data-symptom");
                if (symptomName.includes(query)) {
                    item.classList.remove("d-none");
                } else {
                    item.classList.add("d-none");
                }
            });
        });
    }

    const checkboxes = document.querySelectorAll(".symptom-checkbox");
    const selectedContainer = document.getElementById("selected-symptoms");
    const countDisplay = document.getElementById("symptom-count");
    const detailFields = document.querySelectorAll(".detail-field");

    function updateSelections() {
        if (!selectedContainer) return;
        
        selectedContainer.innerHTML = "";
        let count = 0;
        const selectedNames = [];

        checkboxes.forEach(cb => {
            const card = cb.closest(".symptom-card");
            if (cb.checked) {
                count++;
                selectedNames.push(cb.value.toLowerCase());
                
                if (card) {
                    card.classList.remove("border-0");
                    card.classList.add("border-primary", "bg-primary-subtle");
                }

                // create pill
                const pill = document.createElement("span");
                pill.className = "badge rounded-pill symptom-pill bg-primary px-3 py-2 text-white";
                pill.textContent = cb.nextElementSibling.textContent;
                selectedContainer.appendChild(pill);
            } else {
                if (card) {
                    card.classList.add("border-0");
                    card.classList.remove("border-primary", "bg-primary-subtle");
                }
            }
        });

        if(countDisplay) {
            countDisplay.textContent = count;
        }

        // update optional details visibility
        detailFields.forEach(field => {
            const requires = field.getAttribute("data-requires").split(",");
            const shouldShow = requires.some(req => selectedNames.includes(req.trim().toLowerCase()));
            if (shouldShow) {
                field.classList.remove("d-none");
            } else {
                field.classList.add("d-none");
            }
        });
    }

    if (checkboxes.length > 0) {
        checkboxes.forEach(cb => cb.addEventListener("change", updateSelections));
        updateSelections(); // initial call
    }
}
function setupContactPage() {
    const form = document.getElementById("message-form");
    if (form) form.addEventListener("submit", () => showLoadingOverlay());
}
function setupLoginPage() {
    const form = document.getElementById("login-form");
    if (form) form.addEventListener("submit", () => showLoadingOverlay());
}


/**
 * Toggles the light scene between on and off states.
 * @param {boolean} [forceState] - Optional state to force (true for on, false for off).
 */
function toggleLight(forceState) {
    const sceneUi = document.getElementById("light-scene-ui");
    if (!sceneUi) return;

    const loginCard = document.getElementById("login-card");
    const currentState = sceneUi.dataset.lightOn === "true";
    const nextState = typeof forceState === "boolean" ? forceState : !currentState;

    sceneUi.dataset.lightOn = String(nextState);
    sceneUi.classList.toggle("is-on", nextState);
    sceneUi.style.setProperty("--light-intensity", nextState ? "1" : "0");

    if (loginCard) {
        loginCard.classList.toggle("active", nextState);
    }
    
    document.body.classList.toggle('light-on', nextState);
}

/**
 * Sets up the login scene interactions.
 */
function setupLoginScene() {
    const wallSwitch = document.getElementById("wall-switch");
    const sceneUi = document.getElementById("light-scene-ui");

    if (!wallSwitch || !sceneUi) return;

    document.body.classList.add("is-login-page");

    wallSwitch.addEventListener("click", () => {
        toggleLight();
    });

    toggleLight(false); // Initial state should be off
}

// Main initialization
document.addEventListener("DOMContentLoaded", () => {
    setupThemeToggle();
    setupSymptomsPage();
    setupContactPage();
    setupLoginPage();
    
    // Initialize the login scene if the container exists
    if (document.getElementById("light-scene-ui")) {
        setupLoginScene();
    }
    
    // Custom cursor functionality
    const cursor = document.getElementById('custom-cursor');
    if (cursor) {
        const cursorDot = cursor.querySelector('.cursor-dot');
        const cursorRing = cursor.querySelector('.cursor-ring');
        
        let mouseX = 0, mouseY = 0;
        let cursorX = 0, cursorY = 0;
        let ringX = 0, ringY = 0;
        
        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });
        
        // Add trailing particles
        const trailContainer = document.createElement('div');
        trailContainer.className = 'cursor-trail';
        cursor.appendChild(trailContainer);
        
        const trailCount = 8;
        const trails = [];
        
        for (let i = 0; i < trailCount; i++) {
            const trail = document.createElement('div');
            trail.className = 'cursor-trail-dot';
            trail.style.opacity = (1 - i / trailCount) * 0.5;
            trail.style.transform = `scale(${1 - i / trailCount})`;
            trailContainer.appendChild(trail);
            trails.push({ x: 0, y: 0, element: trail });
        }
        
        function updateCursor() {
            // Smooth follow for dot
            cursorX += (mouseX - cursorX) * 0.15;
            cursorY += (mouseY - cursorY) * 0.15;
            
            if (cursorDot) {
                cursorDot.style.left = mouseX + 'px';
                cursorDot.style.top = mouseY + 'px';
            }
            
            if (cursorRing) {
                // Ring follows with slight delay for smoothness
                ringX += (mouseX - ringX) * 0.12;
                ringY += (mouseY - ringY) * 0.12;
                cursorRing.style.left = ringX + 'px';
                cursorRing.style.top = ringY + 'px';
            }
            
            // Update trail positions
            let prevX = mouseX;
            let prevY = mouseY;
            trails.forEach((trail, i) => {
                trail.x += (prevX - trail.x) * (0.3 - i * 0.03);
                trail.y += (prevY - trail.y) * (0.3 - i * 0.03);
                trail.element.style.left = trail.x + 'px';
                trail.element.style.top = trail.y + 'px';
                prevX = trail.x;
                prevY = trail.y;
            });
            
            requestAnimationFrame(updateCursor);
        }
        
        // Add hover effect on interactive elements
        const interactiveElements = document.querySelectorAll('a, button, .btn, input, .nav-link, [role="button"]');
        interactiveElements.forEach(el => {
            el.addEventListener('mouseenter', () => cursor.classList.add('hovering'));
            el.addEventListener('mouseleave', () => cursor.classList.remove('hovering'));
        });
        
        updateCursor();
    }
    
    hideLoadingOverlay();
});

window.addEventListener("pageshow", () => {
    hideLoadingOverlay();
});
