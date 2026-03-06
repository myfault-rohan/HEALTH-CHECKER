function showLoadingOverlay() {
    const overlay = document.getElementById("loading-overlay");
    if (!overlay) {
        return;
    }
    overlay.classList.remove("d-none");
}

function hideLoadingOverlay() {
    const overlay = document.getElementById("loading-overlay");
    if (!overlay) {
        return;
    }
    overlay.classList.add("d-none");
}

function setThemeMode(mode) {
    const body = document.body;
    if (!body) {
        return;
    }

    const darkMode = mode === "dark";
    body.classList.toggle("theme-dark", darkMode);
    body.setAttribute("data-bs-theme", darkMode ? "dark" : "light");
}

function setupThemeToggle() {
    const toggle = document.getElementById("theme-toggle");
    if (!toggle) {
        return;
    }

    const storageKey = "hc_theme_mode";
    const savedMode = localStorage.getItem(storageKey) || "light";
    setThemeMode(savedMode);

    const updateButton = () => {
        const darkMode = document.body.classList.contains("theme-dark");
        toggle.innerHTML = darkMode
            ? '<i class="fa-solid fa-sun me-1"></i>Day'
            : '<i class="fa-solid fa-moon me-1"></i>Night';
    };

    updateButton();
    toggle.addEventListener("click", () => {
        const nextMode = document.body.classList.contains("theme-dark")
            ? "light"
            : "dark";
        setThemeMode(nextMode);
        localStorage.setItem(storageKey, nextMode);
        updateButton();
    });
}

function setupCustomCursor() {
    const cursor = document.getElementById("custom-cursor");
    if (!cursor) {
        return;
    }
    const cursorDot = cursor.querySelector(".cursor-dot");
    const cursorRing = cursor.querySelector(".cursor-ring");
    if (!(cursorDot instanceof HTMLElement) || !(cursorRing instanceof HTMLElement)) {
        return;
    }

    const supportsFinePointer = window.matchMedia("(pointer: fine)").matches;
    const supportsHover = window.matchMedia("(hover: hover)").matches;
    if (!supportsFinePointer || !supportsHover) {
        return;
    }

    document.body.classList.add("cursor-enabled");

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let dotX = mouseX;
    let dotY = mouseY;
    let ringX = mouseX;
    let ringY = mouseY;
    let dotScale = 1;
    let ringScale = 1;
    let targetDotScale = 1;
    let targetRingScale = 1;
    let isHoveringInteractive = false;
    const dotMaxTravel = 10;

    const interactiveSelector =
        "a, button, .btn, [role='button'], input[type='submit'], input[type='button']";

    const animate = () => {
        // Dot tracks faster, ring trails slightly for a flexible premium effect.
        dotX += (mouseX - dotX) * 0.44;
        dotY += (mouseY - dotY) * 0.44;
        ringX += (mouseX - ringX) * 0.16;
        ringY += (mouseY - ringY) * 0.16;

        dotScale += (targetDotScale - dotScale) * 0.25;
        ringScale += (targetRingScale - ringScale) * 0.2;

        // Keep the inner dot moving inside the outer ring.
        let dotOffsetX = dotX - ringX;
        let dotOffsetY = dotY - ringY;
        const offsetDistance = Math.hypot(dotOffsetX, dotOffsetY);
        const maxDistance = dotMaxTravel * ringScale;
        if (offsetDistance > maxDistance && offsetDistance > 0) {
            const clampFactor = maxDistance / offsetDistance;
            dotOffsetX *= clampFactor;
            dotOffsetY *= clampFactor;
        }

        const renderDotX = ringX + dotOffsetX;
        const renderDotY = ringY + dotOffsetY;

        cursorDot.style.transform =
            `translate3d(${renderDotX}px, ${renderDotY}px, 0) translate(-50%, -50%) scale(${dotScale})`;
        cursorRing.style.transform =
            `translate3d(${ringX}px, ${ringY}px, 0) translate(-50%, -50%) scale(${ringScale})`;

        window.requestAnimationFrame(animate);
    };

    document.addEventListener("mousemove", (event) => {
        mouseX = event.clientX;
        mouseY = event.clientY;
        cursor.classList.add("is-visible");
        cursor.classList.remove("is-hidden");
    });

    document.addEventListener("mouseover", (event) => {
        if (event.target instanceof Element && event.target.closest(interactiveSelector)) {
            isHoveringInteractive = true;
            targetDotScale = 1.18;
            targetRingScale = 1.34;
        }
    });

    document.addEventListener("mouseout", (event) => {
        if (!(event.target instanceof Element)) {
            return;
        }
        if (!event.target.closest(interactiveSelector)) {
            return;
        }
        const next = event.relatedTarget;
        if (next instanceof Element && next.closest(interactiveSelector)) {
            return;
        }
        isHoveringInteractive = false;
        targetDotScale = 1;
        targetRingScale = 1;
    });

    document.addEventListener("mousedown", () => {
        targetDotScale = Math.max(0.9, targetDotScale - 0.12);
        targetRingScale = Math.max(1.05, targetRingScale - 0.18);
    });

    document.addEventListener("mouseup", () => {
        targetDotScale = isHoveringInteractive ? 1.18 : 1;
        targetRingScale = isHoveringInteractive ? 1.34 : 1;
    });

    document.addEventListener("mouseleave", () => {
        cursor.classList.add("is-hidden");
        cursor.classList.remove("is-visible");
    });

    document.addEventListener("mouseenter", () => {
        cursor.classList.add("is-visible");
        cursor.classList.remove("is-hidden");
    });

    animate();
}

function setupSymptomsPage() {
    const form = document.getElementById("symptom-form");
    if (!form) {
        return;
    }

    const checkboxes = Array.from(
        document.querySelectorAll(".symptom-checkbox")
    );
    const detailFields = Array.from(
        document.querySelectorAll(".detail-field[data-requires]")
    );
    const selectedContainer = document.getElementById("selected-symptoms");
    const countNode = document.getElementById("symptom-count");
    const searchInput = document.getElementById("symptom-search");
    const categoryButtons = Array.from(
        document.querySelectorAll(".category-btn")
    );
    const categories = Array.from(document.querySelectorAll(".symptom-category"));

    function getSelectedSymptoms() {
        return checkboxes
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.value.toLowerCase().trim());
    }

    function updateCount() {
        const selectedCount = getSelectedSymptoms().length;
        if (countNode) {
            countNode.textContent = String(selectedCount);
        }
    }

    function renderSelectedSymptoms() {
        if (!selectedContainer) {
            return;
        }

        selectedContainer.innerHTML = "";
        const selected = getSelectedSymptoms();
        if (selected.length === 0) {
            selectedContainer.innerHTML =
                '<span class="text-secondary small">No symptoms selected.</span>';
            return;
        }

        selected.forEach((symptom) => {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "btn btn-sm btn-outline-primary rounded-pill";
            chip.textContent = symptom;
            chip.addEventListener("click", () => {
                const target = checkboxes.find(
                    (checkbox) => checkbox.value.toLowerCase() === symptom
                );
                if (!target) {
                    return;
                }
                target.checked = false;
                handleStateChange();
            });
            selectedContainer.appendChild(chip);
        });
    }

    function updateDetailFields() {
        const selected = new Set(getSelectedSymptoms());
        detailFields.forEach((field) => {
            const requiredSymptoms = (field.dataset.requires || "")
                .split(",")
                .map((value) => value.trim().toLowerCase())
                .filter(Boolean);
            const shouldShow = requiredSymptoms.some((item) => selected.has(item));
            field.classList.toggle("d-none", !shouldShow);
        });
    }

    function filterBySearch() {
        const query = (searchInput?.value || "").trim().toLowerCase();
        const symptomItems = Array.from(document.querySelectorAll(".symptom-item"));
        symptomItems.forEach((item) => {
            const symptomName = (item.dataset.symptom || "").toLowerCase();
            const visible = !query || symptomName.includes(query);
            item.classList.toggle("d-none", !visible);
        });
    }

    function filterByCategory(categoryName) {
        categories.forEach((categoryBlock) => {
            if (categoryName === "all") {
                categoryBlock.classList.remove("d-none");
                return;
            }
            const active = categoryBlock.dataset.category === categoryName;
            categoryBlock.classList.toggle("d-none", !active);
        });
    }

    function showInlineError(message) {
        let node = document.getElementById("symptom-inline-error");
        if (!node) {
            node = document.createElement("div");
            node.id = "symptom-inline-error";
            node.className = "alert alert-danger mt-3";
            form.prepend(node);
        }
        node.textContent = message;
    }

    function clearInlineError() {
        const node = document.getElementById("symptom-inline-error");
        if (node) {
            node.remove();
        }
    }

    function handleStateChange() {
        updateCount();
        renderSelectedSymptoms();
        updateDetailFields();
        clearInlineError();
    }

    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", handleStateChange);
    });

    if (searchInput) {
        searchInput.addEventListener("input", filterBySearch);
    }

    categoryButtons.forEach((button) => {
        button.addEventListener("click", () => {
            categoryButtons.forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
            filterByCategory(button.dataset.category || "all");
            filterBySearch();
        });
    });

    form.addEventListener("submit", (event) => {
        if (getSelectedSymptoms().length === 0) {
            event.preventDefault();
            showInlineError("Select at least one symptom before running prediction.");
            return;
        }
        showLoadingOverlay();
    });

    handleStateChange();
}

function setupContactPage() {
    const form = document.getElementById("message-form");
    if (!form) {
        return;
    }

    form.addEventListener("submit", () => {
        showLoadingOverlay();
    });
}

window.addEventListener("pageshow", () => {
    hideLoadingOverlay();
});

document.addEventListener("DOMContentLoaded", () => {
    setupCustomCursor();
    setupThemeToggle();
    setupSymptomsPage();
    setupContactPage();
    hideLoadingOverlay();
});
