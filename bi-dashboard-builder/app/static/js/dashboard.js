/**
 * BI Dashboard Builder - Client-Side Interactivity
 *
 * Handles:
 *  - Sidebar toggle and mobile menu
 *  - File upload drag-and-drop
 *  - Dashboard filtering with live chart/KPI refresh
 *  - Data table rendering, pagination, search, and sorting
 *  - Chart fullscreen modal
 *  - Export functionality
 */

/* ===========================================================
   Sidebar & Navigation
   =========================================================== */

(function () {
    "use strict";

    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const sidebarOverlay = document.getElementById("sidebarOverlay");

    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", function () {
            sidebar.classList.toggle("collapsed");
            const mainContent = document.getElementById("mainContent");
            if (sidebar.classList.contains("collapsed")) {
                mainContent.style.marginLeft = "var(--sidebar-collapsed)";
            } else {
                mainContent.style.marginLeft = "";
            }
        });
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener("click", function () {
            sidebar.classList.add("open");
            sidebarOverlay.classList.add("active");
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", function () {
            sidebar.classList.remove("open");
            sidebarOverlay.classList.remove("active");
        });
    }
})();


/* ===========================================================
   Upload Page Initialization
   =========================================================== */

function initUploadPage() {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const filePreview = document.getElementById("filePreview");
    const fileName = document.getElementById("fileName");
    const fileSize = document.getElementById("fileSize");
    const fileRemove = document.getElementById("fileRemove");
    const uploadBtn = document.getElementById("uploadBtn");

    if (!dropzone || !fileInput) return;

    // Click to open file picker
    dropzone.addEventListener("click", function () {
        fileInput.click();
    });

    // Drag events
    ["dragenter", "dragover"].forEach(function (evt) {
        dropzone.addEventListener(evt, function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(function (evt) {
        dropzone.addEventListener(evt, function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove("dragover");
        });
    });

    dropzone.addEventListener("drop", function (e) {
        var files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            showFilePreview(files[0]);
        }
    });

    // File selection
    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            showFilePreview(fileInput.files[0]);
        }
    });

    // Remove file
    if (fileRemove) {
        fileRemove.addEventListener("click", function (e) {
            e.stopPropagation();
            fileInput.value = "";
            filePreview.style.display = "none";
            dropzone.style.display = "";
            if (uploadBtn) uploadBtn.disabled = true;
        });
    }

    function showFilePreview(file) {
        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = formatFileSize(file.size);
        if (filePreview) filePreview.style.display = "block";
        dropzone.style.display = "none";
        if (uploadBtn) uploadBtn.disabled = false;
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return "0 Bytes";
        var k = 1024;
        var sizes = ["Bytes", "KB", "MB", "GB"];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
    }
}


/* ===========================================================
   Dashboard Initialization
   =========================================================== */

var currentPage = 1;
var pageSize = 25;
var allData = [];
var filteredData = [];
var sortColumn = null;
var sortAscending = true;

function initDashboard() {
    // Refresh button
    var refreshBtn = document.getElementById("refreshBtn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", refreshDashboard);
    }

    // Export button
    var exportBtn = document.getElementById("exportBtn");
    if (exportBtn) {
        exportBtn.addEventListener("click", exportDashboard);
    }

    // Fullscreen button
    var fullscreenBtn = document.getElementById("fullscreenBtn");
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener("click", togglePageFullscreen);
    }

    // Filter listeners
    var filterSelects = document.querySelectorAll(".filter-select");
    filterSelects.forEach(function (sel) {
        sel.addEventListener("change", onFilterChange);
    });

    var filterDates = document.querySelectorAll(".filter-date");
    filterDates.forEach(function (inp) {
        inp.addEventListener("change", onFilterChange);
    });

    // Clear filters
    var clearBtn = document.getElementById("clearFiltersBtn");
    if (clearBtn) {
        clearBtn.addEventListener("click", clearFilters);
    }

    // Table search
    var tableSearch = document.getElementById("tableSearch");
    if (tableSearch) {
        tableSearch.addEventListener("input", debounce(onTableSearch, 300));
    }

    // Page size
    var pageSizeSelect = document.getElementById("tablePageSize");
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener("change", function () {
            pageSize = parseInt(this.value);
            currentPage = 1;
            renderTable();
        });
    }
}


/* ===========================================================
   Filtering
   =========================================================== */

function getActiveFilters() {
    var filters = {};

    document.querySelectorAll(".filter-select").forEach(function (sel) {
        if (sel.value) {
            filters[sel.dataset.column] = sel.value;
        }
    });

    return filters;
}

function onFilterChange() {
    refreshDashboard();
}

function clearFilters() {
    document.querySelectorAll(".filter-select").forEach(function (sel) {
        sel.value = "";
    });

    document.querySelectorAll(".filter-date").forEach(function (inp) {
        inp.value = inp.min || "";
    });

    refreshDashboard();
}

function refreshDashboard() {
    var sessionId = window.DASHBOARD_SESSION_ID;
    if (!sessionId) return;

    var filters = getActiveFilters();

    // Show loading state
    var refreshBtn = document.getElementById("refreshBtn");
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;"></span> Refreshing...';
    }

    fetch("/api/refresh/" + sessionId, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filters: filters }),
    })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.kpis) {
                updateKPIs(data.kpis);
            }
            if (data.charts) {
                updateCharts(data.charts);
            }
            // Reload table data
            loadDataPreview();
        })
        .catch(function (err) {
            console.error("Refresh error:", err);
        })
        .finally(function () {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg><span>Refresh</span>';
            }
        });
}

function updateKPIs(kpis) {
    kpis.forEach(function (kpi, i) {
        var card = document.querySelector('[data-kpi-index="' + i + '"]');
        if (!card) return;

        var valueEl = card.querySelector(".kpi-value");
        if (valueEl) {
            animateValue(valueEl, valueEl.textContent, kpi.formatted);
        }

        var changeEl = card.querySelector(".kpi-change");
        if (changeEl && kpi.change_pct !== null && kpi.change_pct !== undefined) {
            changeEl.textContent = (kpi.change_pct > 0 ? "+" : "") + kpi.change_pct + "%";
            changeEl.className = "kpi-change " + (kpi.change_pct > 0 ? "positive" : kpi.change_pct < 0 ? "negative" : "");
        }

        // Update card trend class
        card.className = card.className.replace(/\b(up|down|neutral)\b/g, "").trim();
        card.classList.add(kpi.trend);
    });
}

function updateCharts(charts) {
    charts.forEach(function (chart) {
        var container = document.getElementById("chart-container-" + chart.index);
        if (container && chart.html) {
            container.innerHTML = chart.html;
            // Re-initialize Plotly charts
            var plotDiv = container.querySelector(".js-plotly-plot");
            if (plotDiv) {
                Plotly.Plots.resize(plotDiv);
            }
        }
    });
}

function animateValue(element, from, to) {
    element.style.opacity = "0.5";
    setTimeout(function () {
        element.textContent = to;
        element.style.opacity = "1";
        element.style.transition = "opacity 0.3s ease";
    }, 150);
}


/* ===========================================================
   Data Table
   =========================================================== */

function loadDataPreview() {
    var sessionId = window.DASHBOARD_SESSION_ID;
    if (!sessionId) return;

    var filters = getActiveFilters();
    var params = new URLSearchParams({ limit: "500", offset: "0" });
    Object.keys(filters).forEach(function (key) {
        params.append("filter_" + key, filters[key]);
    });

    fetch("/api/data/" + sessionId + "?" + params.toString())
        .then(function (res) { return res.json(); })
        .then(function (data) {
            allData = data.data || [];
            filteredData = allData.slice();
            currentPage = 1;
            renderTable();
        })
        .catch(function (err) {
            console.error("Data load error:", err);
            var wrapper = document.getElementById("dataTableWrapper");
            if (wrapper) {
                wrapper.innerHTML = '<div class="table-loading"><span>Failed to load data preview.</span></div>';
            }
        });
}

function renderTable() {
    var wrapper = document.getElementById("dataTableWrapper");
    if (!wrapper || filteredData.length === 0) {
        if (wrapper) {
            wrapper.innerHTML = '<div class="table-loading"><span>No data available.</span></div>';
        }
        return;
    }

    var columns = Object.keys(filteredData[0]);
    var totalPages = Math.ceil(filteredData.length / pageSize);
    var start = (currentPage - 1) * pageSize;
    var end = Math.min(start + pageSize, filteredData.length);
    var pageData = filteredData.slice(start, end);

    var html = '<table class="data-table">';
    html += "<thead><tr>";
    columns.forEach(function (col) {
        var arrow = "";
        if (sortColumn === col) {
            arrow = sortAscending ? " &uarr;" : " &darr;";
        }
        html += '<th onclick="sortTable(\'' + col + '\')">' + escapeHtml(col.replace(/_/g, " ")) + arrow + "</th>";
    });
    html += "</tr></thead>";
    html += "<tbody>";
    pageData.forEach(function (row) {
        html += "<tr>";
        columns.forEach(function (col) {
            var val = row[col];
            if (val === null || val === undefined) val = "";
            html += "<td>" + escapeHtml(String(val)) + "</td>";
        });
        html += "</tr>";
    });
    html += "</tbody></table>";

    wrapper.innerHTML = html;

    // Render pagination
    renderPagination(totalPages);
}

function renderPagination(totalPages) {
    var container = document.getElementById("tablePagination");
    if (!container) return;

    if (totalPages <= 1) {
        container.innerHTML = '<span style="color:var(--gray-400);font-size:13px;">Showing ' + filteredData.length + ' records</span>';
        return;
    }

    var html = '';
    html += '<button class="page-btn" onclick="goToPage(' + (currentPage - 1) + ')" ' + (currentPage === 1 ? "disabled" : "") + '>&laquo; Prev</button>';

    var startPage = Math.max(1, currentPage - 2);
    var endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }

    for (var i = startPage; i <= endPage; i++) {
        html += '<button class="page-btn ' + (i === currentPage ? "active" : "") + '" onclick="goToPage(' + i + ')">' + i + "</button>";
    }

    html += '<button class="page-btn" onclick="goToPage(' + (currentPage + 1) + ')" ' + (currentPage === totalPages ? "disabled" : "") + '>Next &raquo;</button>';
    html += '<span style="margin-left:12px;color:var(--gray-400);font-size:13px;">Page ' + currentPage + ' of ' + totalPages + '</span>';

    container.innerHTML = html;
}

function goToPage(page) {
    var totalPages = Math.ceil(filteredData.length / pageSize);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderTable();
    // Scroll to table
    var section = document.querySelector(".data-preview-section");
    if (section) {
        section.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function sortTable(column) {
    if (sortColumn === column) {
        sortAscending = !sortAscending;
    } else {
        sortColumn = column;
        sortAscending = true;
    }

    filteredData.sort(function (a, b) {
        var valA = a[column];
        var valB = b[column];

        // Handle nulls
        if (valA === null || valA === undefined) valA = "";
        if (valB === null || valB === undefined) valB = "";

        // Try numeric comparison
        var numA = parseFloat(valA);
        var numB = parseFloat(valB);
        if (!isNaN(numA) && !isNaN(numB)) {
            return sortAscending ? numA - numB : numB - numA;
        }

        // String comparison
        var strA = String(valA).toLowerCase();
        var strB = String(valB).toLowerCase();
        if (strA < strB) return sortAscending ? -1 : 1;
        if (strA > strB) return sortAscending ? 1 : -1;
        return 0;
    });

    currentPage = 1;
    renderTable();
}

function onTableSearch() {
    var query = document.getElementById("tableSearch").value.toLowerCase().trim();

    if (!query) {
        filteredData = allData.slice();
    } else {
        filteredData = allData.filter(function (row) {
            return Object.values(row).some(function (val) {
                return String(val).toLowerCase().indexOf(query) >= 0;
            });
        });
    }

    currentPage = 1;
    renderTable();
}


/* ===========================================================
   Chart Fullscreen Modal
   =========================================================== */

function toggleChartFullscreen(chartIndex) {
    var modal = document.getElementById("chartModal");
    var modalTitle = document.getElementById("modalChartTitle");
    var modalBody = document.getElementById("modalChartBody");

    if (!modal || !modalBody) return;

    var charts = window.DASHBOARD_CHARTS || [];
    var chart = charts.find(function (c) { return c.index === chartIndex; });

    if (!chart) return;

    modalTitle.textContent = chart.title;
    modalBody.innerHTML = chart.html || "<p>No chart data available.</p>";

    modal.classList.add("active");

    // Resize the chart in modal
    setTimeout(function () {
        var plotDiv = modalBody.querySelector(".js-plotly-plot");
        if (plotDiv) {
            Plotly.Plots.resize(plotDiv);
        }
    }, 100);

    // Close on escape key
    document.addEventListener("keydown", handleModalEscape);
}

function closeChartModal() {
    var modal = document.getElementById("chartModal");
    if (modal) {
        modal.classList.remove("active");
    }
    document.removeEventListener("keydown", handleModalEscape);
}

function handleModalEscape(e) {
    if (e.key === "Escape") {
        closeChartModal();
    }
}


/* ===========================================================
   Export
   =========================================================== */

function exportDashboard() {
    var sessionId = window.DASHBOARD_SESSION_ID;
    if (!sessionId) return;

    fetch("/api/export/" + sessionId)
        .then(function (res) { return res.json(); })
        .then(function (data) {
            var json = JSON.stringify(data, null, 2);
            var blob = new Blob([json], { type: "application/json" });
            var url = URL.createObjectURL(blob);
            var a = document.createElement("a");
            a.href = url;
            a.download = "dashboard_config_" + new Date().toISOString().slice(0, 10) + ".json";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        })
        .catch(function (err) {
            console.error("Export error:", err);
            alert("Failed to export dashboard configuration.");
        });
}

function togglePageFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(function () {});
    } else {
        document.exitFullscreen();
    }
}


/* ===========================================================
   Utility Functions
   =========================================================== */

function escapeHtml(text) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

function debounce(func, wait) {
    var timeout;
    return function () {
        var context = this;
        var args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function () {
            func.apply(context, args);
        }, wait);
    };
}

function formatNumber(num) {
    if (typeof num !== "number") return num;
    if (Math.abs(num) >= 1e9) return (num / 1e9).toFixed(1) + "B";
    if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(1) + "M";
    if (Math.abs(num) >= 1e3) return (num / 1e3).toFixed(1) + "K";
    return num.toFixed(Number.isInteger(num) ? 0 : 2);
}

function formatCurrency(num) {
    return "$" + formatNumber(num);
}
