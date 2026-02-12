/**
 * SecureAudit Pro - Chart.js Visualizations
 *
 * Provides chart initialization functions for the dashboard:
 *   - Severity distribution (doughnut chart)
 *   - Risk by category (horizontal bar chart)
 *   - Compliance comparison (grouped bar chart)
 *   - Effort distribution (stacked bar chart)
 */

/* Color palette aligned with the CSS severity colors */
const COLORS = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#22c55e',
    info: '#94a3b8',
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    accent: '#06b6d4',
    success: '#22c55e',
    warning: '#eab308',
    danger: '#ef4444',
    quickWin: '#14b8a6',
    shortTerm: '#eab308',
    longTerm: '#6366f1',
};

/* Global Chart.js defaults */
if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = "'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif";
    Chart.defaults.font.size = 13;
    Chart.defaults.color = '#64748b';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 16;
}

/**
 * Initialize the severity distribution doughnut chart.
 * @param {string} canvasId - Canvas element ID.
 * @param {Object} data - Severity distribution {critical, high, medium, low, info}.
 */
function initSeverityChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
            datasets: [{
                data: [
                    data.critical || 0,
                    data.high || 0,
                    data.medium || 0,
                    data.low || 0,
                    data.info || 0,
                ],
                backgroundColor: [
                    COLORS.critical,
                    COLORS.high,
                    COLORS.medium,
                    COLORS.low,
                    COLORS.info,
                ],
                borderWidth: 0,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyleWidth: 10,
                    },
                },
                tooltip: {
                    backgroundColor: '#0f172a',
                    titleColor: '#ffffff',
                    bodyColor: '#e2e8f0',
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const value = context.raw;
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${context.label}: ${value} (${percentage}%)`;
                        },
                    },
                },
            },
        },
    });
}

/**
 * Initialize the risk-by-category horizontal bar chart.
 * @param {string} canvasId - Canvas element ID.
 * @param {Array} categories - Array of category objects with display_name and raw_score.
 */
function initCategoryChart(canvasId, categories) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = categories.map(c => c.display_name);
    const scores = categories.map(c => c.raw_score);
    const bgColors = scores.map(score => {
        if (score >= 8) return COLORS.critical;
        if (score >= 6) return COLORS.high;
        if (score >= 4) return COLORS.medium;
        if (score >= 2) return COLORS.low;
        return COLORS.info;
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Risk Score',
                data: scores,
                backgroundColor: bgColors,
                borderRadius: 6,
                borderSkipped: false,
                barPercentage: 0.6,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    max: 10,
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        stepSize: 2,
                        callback: function(value) { return value + '/10'; },
                    },
                },
                y: {
                    grid: { display: false },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0f172a',
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return `Risk Score: ${context.raw}/10`;
                        },
                    },
                },
            },
        },
    });
}

/**
 * Initialize the compliance comparison chart.
 * @param {string} canvasId - Canvas element ID.
 * @param {Object} data - Object with labels, passed, failed, partial arrays.
 */
function initComplianceChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Passed',
                    data: data.passed,
                    backgroundColor: COLORS.success,
                    borderRadius: 4,
                    barPercentage: 0.7,
                },
                {
                    label: 'Partial',
                    data: data.partial,
                    backgroundColor: COLORS.warning,
                    borderRadius: 4,
                    barPercentage: 0.7,
                },
                {
                    label: 'Failed',
                    data: data.failed,
                    backgroundColor: COLORS.danger,
                    borderRadius: 4,
                    barPercentage: 0.7,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { display: false } },
                y: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: { stepSize: 2 },
                },
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { padding: 16 },
                },
                tooltip: {
                    backgroundColor: '#0f172a',
                    cornerRadius: 8,
                    padding: 12,
                },
            },
        },
    });
}

/**
 * Initialize the effort distribution chart for the remediation page.
 * @param {string} canvasId - Canvas element ID.
 * @param {Object} data - Object with labels, counts, and hours arrays.
 */
function initEffortChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Action Items',
                    data: data.counts,
                    backgroundColor: [COLORS.quickWin, COLORS.shortTerm, COLORS.longTerm],
                    borderRadius: 8,
                    barPercentage: 0.5,
                    yAxisID: 'y',
                },
                {
                    label: 'Estimated Hours',
                    data: data.hours,
                    backgroundColor: [
                        COLORS.quickWin + '60',
                        COLORS.shortTerm + '60',
                        COLORS.longTerm + '60',
                    ],
                    borderColor: [COLORS.quickWin, COLORS.shortTerm, COLORS.longTerm],
                    borderWidth: 2,
                    borderRadius: 8,
                    barPercentage: 0.5,
                    yAxisID: 'y1',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { display: false } },
                y: {
                    type: 'linear',
                    position: 'left',
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    title: { display: true, text: 'Action Items' },
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    beginAtZero: true,
                    grid: { display: false },
                    title: { display: true, text: 'Hours' },
                },
            },
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    backgroundColor: '#0f172a',
                    cornerRadius: 8,
                    padding: 12,
                },
            },
        },
    });
}
