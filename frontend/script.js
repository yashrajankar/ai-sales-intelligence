// ============================================================
// AI SALES INTELLIGENCE SYSTEM
// Frontend JavaScript Logic
// ============================================================

const API_URL = "http://127.0.0.1:5000/api";

// Chart storage reference
const charts = {};

// Color Palette
const COLORS = {
    primary: "#0f766e",
    primaryLight: "rgba(15, 118, 110, 0.12)",
    blue: "#2563eb",
    blueLight: "rgba(37, 99, 235, 0.12)",
    purple: "#7c3aed",
    purpleLight: "rgba(124, 58, 237, 0.12)",
    orange: "#d97706",
    red: "#ef4444",
    teal: "#14b8a6",
    grid: "rgba(226, 232, 240, 0.8)",
    text: "#64748b"
};

// ============================================================
// API FETCH HELPER
// ============================================================

async function getData(endpoint) {
    const response = await fetch(API_URL + endpoint);
    if (!response.ok) {
        throw new Error(`API Error ${response.status}: ${response.statusText}`);
    }
    return await response.json();
}

// ============================================================
// FORMATTING HELPERS
// ============================================================

function toNumber(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
}

function formatCurrency(value) {
    const num = toNumber(value);
    if (Math.abs(num) >= 1000000) {
        return "$" + (num / 1000000).toFixed(2) + "M";
    }
    if (Math.abs(num) >= 10000) {
        return "$" + (num / 1000).toFixed(1) + "K";
    }
    return "$" + num.toLocaleString("en-US", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}

function formatDecimal(value) {
    return toNumber(value).toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatNumber(value) {
    return toNumber(value).toLocaleString("en-US");
}

function escapeHTML(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function destroyChart(id) {
    if (charts[id]) {
        charts[id].destroy();
        charts[id] = null;
    }
}

// ============================================================
// CHART DEFAULTS
// ============================================================

function getChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            intersect: false,
            mode: "index"
        },
        plugins: {
            legend: {
                display: true,
                position: "top",
                labels: {
                    color: COLORS.text,
                    font: { size: 12, weight: 500 },
                    usePointStyle: true,
                    boxWidth: 8
                }
            },
            tooltip: {
                backgroundColor: "#0f172a",
                titleColor: "#ffffff",
                bodyColor: "#f8fafc",
                borderColor: "rgba(255,255,255,0.1)",
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8,
                displayColors: true
            }
        },
        scales: {
            x: {
                grid: { display: false },
                border: { display: false },
                ticks: { color: COLORS.text, font: { size: 11 } }
            },
            y: {
                beginAtZero: true,
                grid: { color: COLORS.grid },
                border: { display: false },
                ticks: {
                    color: COLORS.text,
                    font: { size: 11 },
                    callback: function(value) {
                        return formatCurrency(value);
                    }
                }
            }
        }
    };
}

// ============================================================
// API STATUS CHECK
// ============================================================

async function checkAPIStatus() {
    const badge = document.getElementById("apiStatus");
    if (!badge) return;

    try {
        await getData("/health");
        badge.classList.remove("offline");
        badge.innerHTML = `<span class="status-dot"></span> API Connected`;
    } catch (error) {
        console.error("API Status Error:", error);
        badge.classList.add("offline");
        badge.innerHTML = `<span class="status-dot"></span> API Offline`;
    }
}

function updateLastUpdated() {
    const element = document.getElementById("lastUpdated");
    if (!element) return;
    const now = new Date();
    element.textContent = `Updated ${now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}

// ============================================================
// LOAD KPIs
// ============================================================

async function loadKPIs() {
    try {
        const data = await getData("/dashboard/kpis");

        const totalSales = toNumber(data.total_sales);
        const totalProfit = toNumber(data.total_profit);
        const totalOrders = toNumber(data.total_orders);
        const totalQuantity = toNumber(data.total_quantity);
        const averageOrderValue = totalOrders > 0 ? totalSales / totalOrders : 0;

        if (document.getElementById("totalSales")) document.getElementById("totalSales").textContent = formatCurrency(totalSales);
        if (document.getElementById("totalProfit")) document.getElementById("totalProfit").textContent = formatCurrency(totalProfit);
        if (document.getElementById("totalOrders")) document.getElementById("totalOrders").textContent = formatNumber(totalOrders);
        if (document.getElementById("totalQuantity")) document.getElementById("totalQuantity").textContent = formatNumber(totalQuantity);
        if (document.getElementById("averageOrderValue")) document.getElementById("averageOrderValue").textContent = formatCurrency(averageOrderValue);

        try {
            const segments = await getData("/customers/segments/summary");
            let totalCustomers = 0;
            segments.forEach(row => { totalCustomers += toNumber(row.customers); });
            if (document.getElementById("totalCustomers")) {
                document.getElementById("totalCustomers").textContent = formatNumber(totalCustomers);
            }
        } catch (e) {
            if (document.getElementById("totalCustomers")) document.getElementById("totalCustomers").textContent = "--";
        }

        const margin = totalSales > 0 ? (totalProfit / totalSales) * 100 : 0;
        if (document.getElementById("profitMargin")) {
            document.getElementById("profitMargin").textContent = `${margin.toFixed(1)}%`;
        }

    } catch (error) {
        console.error("KPI Loading Error:", error);
        showKPIError();
    }
}

function showKPIError() {
    ["totalSales", "totalProfit", "totalOrders", "totalCustomers"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = "--";
    });
}

// ============================================================
// MONTHLY SALES
// ============================================================

async function loadMonthlySales() {
    try {
        const data = await getData("/sales/monthly");
        const canvas = document.getElementById("monthlySalesChart");
        if (!canvas) return;

        const labels = data.map(row => row.month);
        const sales = data.map(row => toNumber(row.sales));
        const profit = data.map(row => toNumber(row.profit));

        destroyChart("monthlySalesChart");

        const options = getChartOptions();
        options.plugins.tooltip.callbacks = {
            label: function(context) {
                return ` ${context.dataset.label}: ${formatCurrency(context.raw)}`;
            }
        };

        charts["monthlySalesChart"] = new Chart(canvas, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Sales Revenue",
                        data: sales,
                        borderColor: COLORS.primary,
                        backgroundColor: COLORS.primaryLight,
                        borderWidth: 2.5,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        fill: true,
                        tension: 0.35
                    },
                    {
                        label: "Net Profit",
                        data: profit,
                        borderColor: COLORS.blue,
                        backgroundColor: COLORS.blueLight,
                        borderWidth: 2,
                        pointRadius: 2.5,
                        pointHoverRadius: 5,
                        fill: false,
                        tension: 0.35
                    }
                ]
            },
            options: options
        });

    } catch (error) {
        console.error("Monthly Sales Error:", error);
    }
}

// ============================================================
// CATEGORY SALES (Fixed Horizontal Axis Labeling)
// ============================================================

async function loadCategorySales() {
    try {
        const data = await getData("/sales/category");
        const canvas = document.getElementById("categorySalesChart");
        if (!canvas) return;

        data.sort((a, b) => toNumber(b.sales) - toNumber(a.sales));

        const labels = data.map(row => row.category);
        const sales = data.map(row => toNumber(row.sales));

        destroyChart("categorySalesChart");

        charts["categorySalesChart"] = new Chart(canvas, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Sales",
                    data: sales,
                    backgroundColor: [COLORS.primary, COLORS.blue, COLORS.purple, COLORS.orange, COLORS.teal],
                    borderRadius: 6,
                    barThickness: 22
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y",
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` Sales: ${formatCurrency(context.raw)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: COLORS.grid },
                        border: { display: false },
                        ticks: {
                            color: COLORS.text,
                            font: { size: 11 },
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    },
                    y: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: { color: COLORS.text, font: { size: 11 } }
                    }
                }
            }
        });

    } catch (error) {
        console.error("Category Sales Error:", error);
    }
}

// ============================================================
// REGION SALES (Fixed Horizontal Axis Labeling)
// ============================================================

async function loadRegionSales() {
    try {
        const data = await getData("/sales/region");
        const canvas = document.getElementById("regionSalesChart");
        if (!canvas) return;

        data.sort((a, b) => toNumber(b.sales) - toNumber(a.sales));

        const labels = data.map(row => row.region);
        const sales = data.map(row => toNumber(row.sales));

        destroyChart("regionSalesChart");

        charts["regionSalesChart"] = new Chart(canvas, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Sales",
                    data: sales,
                    backgroundColor: COLORS.primary,
                    borderRadius: 6,
                    barThickness: 20
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y",
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` Sales: ${formatCurrency(context.raw)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: COLORS.grid },
                        border: { display: false },
                        ticks: {
                            color: COLORS.text,
                            font: { size: 11 },
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    },
                    y: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: { color: COLORS.text, font: { size: 11 } }
                    }
                }
            }
        });

    } catch (error) {
        console.error("Region Sales Error:", error);
    }
}

// ============================================================
// FORECAST (XGBoost)
// ============================================================

async function loadForecast() {
    try {
        const data = await getData("/forecast");
        const canvas = document.getElementById("forecastChart");
        if (!canvas) return;

        const labels = data.map(row => row.month);
        const forecast = data.map(row => toNumber(row.predicted_sales));

        destroyChart("forecastChart");

        const options = getChartOptions();
        options.plugins.legend.display = false;
        options.plugins.tooltip.callbacks = {
            label: function(context) {
                return ` Predicted Sales: ${formatCurrency(context.raw)}`;
            }
        };

        charts["forecastChart"] = new Chart(canvas, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Predicted Sales",
                    data: forecast,
                    borderColor: COLORS.purple,
                    backgroundColor: COLORS.purpleLight,
                    borderWidth: 2.5,
                    borderDash: [5, 5],
                    pointRadius: 4,
                    pointBackgroundColor: COLORS.purple,
                    fill: true,
                    tension: 0.35
                }]
            },
            options: options
        });

        const modelElement = document.getElementById("forecastModel");
        if (modelElement && data.length > 0 && data[0].model) {
            modelElement.textContent = `${data[0].model} Forecast`;
        }

    } catch (error) {
        console.error("Forecast Error:", error);
    }
}

// ============================================================
// BUSINESS INSIGHTS
// ============================================================

async function loadBusinessInsights() {
    try {
        const [kpi, categories] = await Promise.all([
            getData("/dashboard/kpis"),
            getData("/sales/category")
        ]);

        const salesInsight = document.getElementById("salesInsight");
        if (salesInsight && categories.length > 0) {
            categories.sort((a, b) => toNumber(b.sales) - toNumber(a.sales));
            const topCategory = categories[0].category;
            salesInsight.textContent = `Total revenue reached ${formatCurrency(kpi.total_sales)}, with ${topCategory} driving the highest sales volume.`;
        }

        const segments = await getData("/customers/segments/summary");
        const customerInsight = document.getElementById("customerInsight");
        if (customerInsight && segments.length > 0) {
            segments.sort((a, b) => toNumber(b.customers) - toNumber(a.customers));
            const topSegment = segments[0].segment;
            const topCount = formatNumber(segments[0].customers);
            customerInsight.textContent = `The ${topSegment} cluster represents the largest segment with ${topCount} customers analyzed via RFM analysis.`;
        }

        const forecast = await getData("/forecast");
        const forecastInsight = document.getElementById("forecastInsight");
        if (forecastInsight && forecast.length > 1) {
            const first = toNumber(forecast[0].predicted_sales);
            const last = toNumber(forecast[forecast.length - 1].predicted_sales);
            const modelName = forecast[0].model || "XGBoost";
            const trend = last >= first ? "an increasing" : "a decreasing";
            forecastInsight.textContent = `The ${modelName} model projects ${trend} sales trajectory across the upcoming forecast horizon.`;
        }

    } catch (error) {
        console.error("Business Insights Error:", error);
    }
}

// ============================================================
// CUSTOMER SEGMENTATION (RFM + K-Means)
// ============================================================

async function loadCustomerSegments() {
    try {
        const data = await getData("/customers/segments/summary");
        
        const canvas = document.getElementById("segmentChart");
        if (canvas) {
            const labels = data.map(row => row.segment);
            const customers = data.map(row => toNumber(row.customers));

            destroyChart("segmentChart");

            charts["segmentChart"] = new Chart(canvas, {
                type: "doughnut",
                data: {
                    labels: labels,
                    datasets: [{
                        data: customers,
                        backgroundColor: [COLORS.primary, COLORS.blue, COLORS.purple, COLORS.orange, COLORS.teal, COLORS.red],
                        borderWidth: 2,
                        borderColor: "#ffffff"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "70%",
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: { color: COLORS.text, font: { size: 11 }, usePointStyle: true, padding: 15 }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return ` ${context.label}: ${formatNumber(context.raw)} Customers`;
                                }
                            }
                        }
                    }
                }
            });
        }

        const table = document.getElementById("segmentTable");
        if (table) {
            table.innerHTML = "";
            if (!data.length) {
                table.innerHTML = `<tr><td colspan="5" class="empty-state">No segment data available</td></tr>`;
                return;
            }

            data.forEach(row => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${escapeHTML(row.segment)}</strong></td>
                    <td>${formatNumber(row.customers)}</td>
                    <td>${row.avg_recency != null ? Math.round(toNumber(row.avg_recency)) + " days" : "--"}</td>
                    <td>${row.avg_frequency != null ? formatDecimal(row.avg_frequency) : "--"}</td>
                    <td class="text-end font-monospace">${row.avg_monetary != null ? formatCurrency(row.avg_monetary) : "--"}</td>
                `;
                table.appendChild(tr);
            });
        }

    } catch (error) {
        console.error("Customer Segments Error:", error);
        showTableError("segmentTable", 5, "Unable to load segment details");
    }
}

// ============================================================
// TOP PRODUCTS
// ============================================================

async function loadTopProducts() {
    try {
        const data = await getData("/products/top?limit=10");
        const table = document.getElementById("productTable");
        if (!table) return;

        table.innerHTML = "";
        if (!data || data.length === 0) {
            table.innerHTML = `<tr><td colspan="3" class="empty-state">No product records found</td></tr>`;
            return;
        }

        data.forEach((row, index) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><span class="table-rank">${index + 1}</span></td>
                <td class="text-truncate-cell" title="${escapeHTML(row.product)}">${escapeHTML(row.product)}</td>
                <td class="text-end fw-semibold font-monospace">${formatCurrency(row.sales)}</td>
            `;
            table.appendChild(tr);
        });

    } catch (error) {
        console.error("Top Products Error:", error);
        showTableError("productTable", 3, "Unable to load top products");
    }
}

// ============================================================
// TOP CUSTOMERS
// ============================================================

async function loadTopCustomers() {
    try {
        const data = await getData("/customers/top?limit=10");
        const table = document.getElementById("customerTable");
        if (!table) return;

        table.innerHTML = "";
        if (!data || data.length === 0) {
            table.innerHTML = `<tr><td colspan="3" class="empty-state">No customer records found</td></tr>`;
            return;
        }

        data.forEach((row, index) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><span class="table-rank">${index + 1}</span></td>
                <td class="text-truncate-cell" title="${escapeHTML(row.customer)}">${escapeHTML(row.customer)}</td>
                <td class="text-end fw-semibold font-monospace">${formatCurrency(row.sales)}</td>
            `;
            table.appendChild(tr);
        });

    } catch (error) {
        console.error("Top Customers Error:", error);
        showTableError("customerTable", 3, "Unable to load top customers");
    }
}

// ============================================================
// CATEGORY PERFORMANCE
// ============================================================

async function loadCategoryPerformance() {
    const table = document.getElementById("categoryPerformanceTable");
    if (!table) return;

    try {
        const data = await getData("/category/performance");
        table.innerHTML = "";

        if (!data.length) {
            table.innerHTML = `<tr><td colspan="4" class="empty-state">No category data available</td></tr>`;
            return;
        }

        data.forEach(row => {
            const tr = document.createElement("tr");
            const profitVal = toNumber(row.profit);
            const profitClass = profitVal < 0 ? "text-danger fw-bold" : "fw-semibold";

            tr.innerHTML = `
                <td><strong>${escapeHTML(row.category)}</strong></td>
                <td>${formatCurrency(row.sales)}</td>
                <td class="${profitClass}">${formatCurrency(row.profit)}</td>
                <td class="text-end"><span class="badge bg-light text-dark border">${formatDecimal(row.profit_margin)}%</span></td>
            `;
            table.appendChild(tr);
        });

    } catch (error) {
        console.error("Category Performance Error:", error);
        showTableError("categoryPerformanceTable", 4, "Unable to load category metrics");
    }
}

// ============================================================
// LOSS-MAKING PRODUCTS
// ============================================================

async function loadLossMakingProducts() {
    const table = document.getElementById("lossProductTable");
    if (!table) return;

    try {
        const data = await getData("/products/loss-making");
        table.innerHTML = "";

        if (!data || data.length === 0) {
            table.innerHTML = `<tr><td colspan="3" class="empty-state">No loss-making products identified</td></tr>`;
            return;
        }

        data.forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td class="text-truncate-cell" title="${escapeHTML(row.product)}">${escapeHTML(row.product)}</td>
                <td>${formatCurrency(row.sales)}</td>
                <td class="text-end text-danger fw-bold font-monospace">${formatCurrency(row.profit)}</td>
            `;
            table.appendChild(tr);
        });

    } catch (error) {
        console.error("Loss-Making Products Error:", error);
        showTableError("lossProductTable", 3, "Unable to load loss-making inventory");
    }
}

// ============================================================
// TABLE ERROR HELPER
// ============================================================

function showTableError(tableId, colspan, message) {
    const table = document.getElementById(tableId);
    if (!table) return;
    table.innerHTML = `
        <tr>
            <td colspan="${colspan}" class="empty-state error-state">
                ${escapeHTML(message)}
            </td>
        </tr>
    `;
}

// ============================================================
// DASHBOARD INITIALIZATION
// ============================================================

async function loadDashboard() {
    updateLastUpdated();
    await checkAPIStatus();

    await Promise.allSettled([
        loadKPIs(),
        loadMonthlySales(),
        loadCategorySales(),
        loadRegionSales(),
        loadForecast(),
        loadTopProducts(),
        loadTopCustomers(),
        loadCustomerSegments(),
        loadBusinessInsights(),
        loadCategoryPerformance(),
        loadLossMakingProducts()
    ]);
}

function startAutoRefresh() {
    setInterval(loadDashboard, 5 * 60 * 1000);
}

document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();
    startAutoRefresh();
});