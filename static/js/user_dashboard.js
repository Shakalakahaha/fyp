/**
 * User Dashboard JavaScript
 * Handles dashboard functionality, navigation, and data visualization
 */

// Global variables
let performanceChart = null;
let currentModels = [];

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize navigation
    initNavigation();

    // Initialize sidebar toggle for mobile
    initSidebarToggle();

    // Load dashboard data
    loadDashboardData();
});

/**
 * Initialize navigation between dashboard sections
 */
function initNavigation() {
    const navLinks = {
        'nav-dashboard': 'dashboard-content',
        'nav-predict': 'predict-content',
        'nav-history': 'history-content'
    };

    // Add click event listeners to all navigation links
    Object.keys(navLinks).forEach(navId => {
        const navElement = document.getElementById(navId);
        if (navElement) {
            navElement.addEventListener('click', function(e) {
                e.preventDefault();

                // Hide all content sections
                document.querySelectorAll('.content-container').forEach(container => {
                    container.classList.add('hidden');
                });

                // Show the selected content section
                const contentId = navLinks[navId];
                document.getElementById(contentId).classList.remove('hidden');

                // Update active navigation item
                document.querySelectorAll('.sidebar-nav li').forEach(item => {
                    item.classList.remove('active');
                });
                this.closest('li').classList.add('active');
            });
        }
    });
}

/**
 * Initialize sidebar toggle for mobile view
 */
function initSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
}

/**
 * Load dashboard data from the server
 */
async function loadDashboardData() {
    try {
        // Get model metrics from the API
        const response = await fetch('/api/models/metrics');

        if (!response.ok) {
            throw new Error(`Failed to fetch model metrics: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        if (data.status === 'success') {
            if (!data.data || !Array.isArray(data.data) || data.data.length === 0) {
                console.warn('No model data received from server');
                showNotification('No model data available', 'warning');
                return;
            }
            updateDashboard(data.data);
        } else {
            console.error('Error fetching model metrics:', data.message);
            showNotification(`Error fetching model metrics: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showNotification(`Error loading dashboard data: ${error.message}`, 'error');
    }
}

/**
 * Update dashboard with model data
 * @param {Array} models - Array of model objects with metrics
 */
function updateDashboard(models) {
    console.log("Received models data:", models);

    if (!models || !Array.isArray(models)) {
        console.error('Invalid models data received:', models);
        showNotification('Error: Invalid model data received', 'error');
        return;
    }

    currentModels = models;

    // Update models table only
    updateModelsTable(models);

    // Set up prediction button
    const predictBtn = document.getElementById('predictBtn');
    if (predictBtn) {
        predictBtn.addEventListener('click', function() {
            // Navigate to prediction page
            document.getElementById('nav-predict').click();
        });
    }
}

/**
 * Create performance chart using Chart.js
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {Array} models - Array of model objects with metrics
 */
function createPerformanceChart(ctx, models) {
    const modelNames = models.map(m => formatModelName(m.name));
    const metrics = models.map(m => m.metrics);

    if (performanceChart) {
        performanceChart.destroy();
    }

    // Create gradient for bars
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(13, 148, 136, 0.8)'); // Teal 600
    gradient.addColorStop(1, 'rgba(13, 148, 136, 0.1)');

    performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: modelNames,
            datasets: [{
                label: 'Accuracy',
                data: metrics.map(metric => metric['Accuracy']),
                backgroundColor: gradient,
                borderColor: 'rgba(13, 148, 136, 1)',
                borderWidth: 2,
                borderRadius: 8,
                barThickness: 50,
                hoverBackgroundColor: 'rgba(13, 148, 136, 0.9)',
                hoverBorderColor: 'rgba(13, 148, 136, 1)',
                hoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    titleColor: '#134e4a',
                    titleFont: {
                        size: 14,
                        weight: 'bold',
                        family: "'Segoe UI', Arial, sans-serif"
                    },
                    bodyColor: '#134e4a',
                    bodyFont: {
                        size: 13,
                        family: "'Segoe UI', Arial, sans-serif"
                    },
                    borderColor: '#ccfbf1',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const modelMetrics = metrics[context.dataIndex];
                            return [
                                `Accuracy: ${(modelMetrics['Accuracy'] * 100).toFixed(2)}%`,
                                `Precision: ${(modelMetrics['Precision'] * 100).toFixed(2)}%`,
                                `Recall: ${(modelMetrics['Recall'] * 100).toFixed(2)}%`,
                                `F1 Score: ${(modelMetrics['F1 Score'] * 100).toFixed(2)}%`,
                                modelMetrics['AUC'] ? `AUC: ${(modelMetrics['AUC'] * 100).toFixed(2)}%` : null
                            ].filter(Boolean);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    grid: {
                        drawBorder: false,
                        color: 'rgba(204, 251, 241, 0.5)',
                        zeroLineColor: 'rgba(204, 251, 241, 0.9)'
                    },
                    ticks: {
                        callback: function(value) {
                            return (value * 100).toFixed(0) + '%';
                        },
                        stepSize: 0.1,
                        font: {
                            size: 12,
                            family: "'Segoe UI', Arial, sans-serif"
                        },
                        padding: 10,
                        color: '#134e4a'
                    },
                    title: {
                        display: true,
                        text: 'Accuracy Score',
                        font: {
                            size: 13,
                            weight: 'bold',
                            family: "'Segoe UI', Arial, sans-serif"
                        },
                        padding: {
                            top: 10,
                            bottom: 10
                        },
                        color: '#134e4a'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 12,
                            family: "'Segoe UI', Arial, sans-serif"
                        },
                        padding: 10,
                        color: '#134e4a'
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });

    return performanceChart;
}

/**
 * Update the models table with model data
 * @param {Array} models - Array of model objects
 */
function updateModelsTable(models) {
    const tableBody = document.getElementById('modelsTableBody');
    if (!tableBody) return;

    // Clear existing rows
    tableBody.innerHTML = '';

    // Add a row for each model
    models.forEach(model => {
        const row = document.createElement('tr');

        // Format model name
        const formattedName = formatModelName(model.name);

        // Safely get metrics with fallbacks
        const metrics = model.metrics || {};
        const accuracy = metrics.Accuracy !== undefined ? (metrics.Accuracy * 100).toFixed(2) + '%' : 'N/A';
        const precision = metrics.Precision !== undefined ? (metrics.Precision * 100).toFixed(2) + '%' : 'N/A';
        const recall = metrics.Recall !== undefined ? (metrics.Recall * 100).toFixed(2) + '%' : 'N/A';
        const f1Score = metrics['F1 Score'] !== undefined ? (metrics['F1 Score'] * 100).toFixed(2) + '%' : 'N/A';
        const auc = metrics.AUC !== undefined ? (metrics.AUC * 100).toFixed(2) + '%' : 'N/A';

        // Create table cells
        row.innerHTML = `
            <td>${formattedName}</td>
            <td>${model.type || 'Default'}</td>
            <td>${model.version || 'v1'}</td>
            <td>${accuracy}</td>
            <td>${precision}</td>
            <td>${recall}</td>
            <td>${f1Score}</td>
            <td>${auc}</td>
            <td><span class="status-badge active">Active</span></td>
        `;

        tableBody.appendChild(row);
    });
}

/**
 * Format model name for display
 * @param {string} name - Raw model name
 * @returns {string} Formatted model name
 */
function formatModelName(name) {
    return name.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Show notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, warning)
 */
function showNotification(message, type = 'info') {
    // This function will be implemented later when we add a notification system
    console.log(`${type.toUpperCase()}: ${message}`);
    // For now, just use alert for errors
    if (type === 'error') {
        alert(message);
    }
}
