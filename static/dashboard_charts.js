document.addEventListener("DOMContentLoaded", async () => {
    const symptomCanvas = document.getElementById("symptom-frequency-chart");
    const conditionCanvas = document.getElementById("condition-trend-chart");
    if (!symptomCanvas || !conditionCanvas || !window.Chart) return;

    try {
        const response = await fetch("/api/history-stats", { headers: { Accept: "application/json" } });
        const stats = await response.json();

        const symptomLabels = stats.symptom_counts.map((item) => item.label);
        const symptomValues = stats.symptom_counts.map((item) => item.count);
        const categoryLabels = Object.keys(stats.category_breakdown);
        const categoryValues = Object.values(stats.category_breakdown);

        new Chart(symptomCanvas, {
            type: "bar",
            data: {
                labels: symptomLabels,
                datasets: [
                    {
                        label: "Logged frequency",
                        data: symptomValues,
                        borderRadius: 12,
                        backgroundColor: ["#00a3d5", "#0073ff", "#00d4aa", "#6a3de8", "#49c96d"],
                    },
                ],
            },
            options: {
                responsive: true,
                animation: { duration: 1200 },
                plugins: { legend: { display: false } },
            },
        });

        new Chart(conditionCanvas, {
            type: "doughnut",
            data: {
                labels: categoryLabels,
                datasets: [
                    {
                        data: categoryValues,
                        backgroundColor: ["#00a3d5", "#00d4aa", "#6a3de8", "#f6b332", "#7c91b8"],
                        borderWidth: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                cutout: "62%",
                animation: { duration: 1200 },
            },
        });

        const score = Number(stats.health_score || 0);
        const ring = document.getElementById("health-score-ring");
        if (ring) {
            ring.style.setProperty("--score", score);
            let ringColor = "#14b86d";
            if (score < 50) ringColor = "#ef5350";
            else if (score < 80) ringColor = "#f6b332";
            ring.style.setProperty("--ring-color", ringColor);
            const label = document.getElementById("health-score-value");
            if (label) label.textContent = score;
        }

        const streak = document.getElementById("streak-value");
        if (streak) streak.textContent = `${stats.streak || 0}-day check streak`;

        const totalChecks = document.getElementById("dashboard-total-checks");
        if (totalChecks) totalChecks.textContent = stats.total_checks;

        document.querySelectorAll(".dashboard-skeleton").forEach((node) => {
            node.classList.remove("skeleton", "dashboard-skeleton");
        });
    } catch (error) {
        console.error("Failed to load dashboard stats", error);
        document.querySelectorAll(".dashboard-skeleton").forEach((node) => {
            node.classList.remove("skeleton", "dashboard-skeleton");
        });
    }
});
