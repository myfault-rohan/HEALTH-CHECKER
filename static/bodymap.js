document.addEventListener("DOMContentLoaded", () => {
    const map = document.getElementById("body-map");
    const searchInput = document.getElementById("symptom-search");
    const zoneInput = document.getElementById("symptom-zone");
    const categoryInput = document.getElementById("symptom-category");
    const tooltip = document.getElementById("bodymap-tooltip");
    const activeLabel = document.getElementById("active-zone-label");
    const resetBtn = document.getElementById("reset-bodymap-btn");
    const searchClearBtn = document.getElementById("search-clear-btn");

    if (!map || !searchInput || !zoneInput) return;

    const setActiveZone = (zone) => {
        map.querySelectorAll(".body-zone").forEach((node) => {
            node.classList.toggle("is-active", node.dataset.zone === zone);
        });
    };

    const resetBodyMap = () => {
        zoneInput.value = "";
        setActiveZone(null);
        if (activeLabel) activeLabel.textContent = "Active: All Zones";
        if (resetBtn) resetBtn.classList.add("d-none");

        // Sync with category tab "all"
        if (categoryInput) categoryInput.value = "all";
        document.querySelectorAll(".category-tab-chip").forEach((btn) => {
            btn.classList.toggle("active", btn.dataset.category === "all");
        });

        if (window.htmx) {
            window.htmx.trigger(searchInput, "keyup");
        }
    };

    if (resetBtn) {
        resetBtn.addEventListener("click", resetBodyMap);
    }

    map.querySelectorAll(".body-zone").forEach((zone) => {
        zone.addEventListener("mouseenter", () => {
            if (!tooltip) return;
            tooltip.textContent = zone.dataset.label;
            tooltip.classList.add("is-visible");
        });

        zone.addEventListener("mouseleave", () => {
            if (tooltip) tooltip.classList.remove("is-visible");
        });

        zone.addEventListener("click", () => {
            const selectedZone = zone.dataset.zone;
            const label = zone.dataset.label;
            const targetCategory = zone.dataset.category || "all";

            zoneInput.value = selectedZone;
            if (categoryInput) categoryInput.value = targetCategory;

            // Clear search query
            searchInput.value = "";
            if (searchClearBtn) searchClearBtn.classList.add("d-none");

            setActiveZone(selectedZone);

            if (activeLabel) {
                activeLabel.textContent = `Active: ${label}`;
            }
            if (resetBtn) {
                resetBtn.classList.remove("d-none");
            }

            // Sync with category tab
            document.querySelectorAll(".category-tab-chip").forEach((btn) => {
                btn.classList.toggle("active", btn.dataset.category === targetCategory);
            });

            if (window.htmx) {
                window.htmx.trigger(searchInput, "keyup");
            }
        });
    });

    window.resetBodyMap = resetBodyMap;
});
