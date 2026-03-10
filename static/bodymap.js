document.addEventListener("DOMContentLoaded", () => {
    const map = document.getElementById("body-map");
    const searchInput = document.getElementById("symptom-search");
    const zoneInput = document.getElementById("symptom-zone");
    const tooltip = document.getElementById("bodymap-tooltip");
    if (!map || !searchInput || !zoneInput) return;

    const setActiveZone = (zone) => {
        map.querySelectorAll(".body-zone").forEach((node) => {
            node.classList.toggle("is-active", node.dataset.zone === zone);
        });
    };

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
            zoneInput.value = selectedZone;
            searchInput.value = "";
            setActiveZone(selectedZone);

            const targetId = zone.dataset.target;
            const target = targetId ? document.getElementById(targetId) : null;
            if (target) {
                document.querySelectorAll(".category-card").forEach((card) => {
                    card.classList.remove("zone-focused");
                });
                target.classList.add("zone-focused");
                target.scrollIntoView({ behavior: "smooth", block: "center" });
            }

            if (window.htmx) {
                window.htmx.trigger(searchInput, "keyup");
            }
        });
    });
});
