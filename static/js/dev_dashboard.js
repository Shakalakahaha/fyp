/**
 * Developer Dashboard JavaScript
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

    // Initialize modals
    initModals();

    // Load dashboard data
    loadDashboardData();

    // Initialize prediction functionality
    initPrediction();

    // Initialize prediction history
    initPredictionHistory();

    // Initialize retrain functionality
    initRetrain();

    // Initialize FAQ functionality
    initFAQ();
});

// Global function to navigate to a section
function navigateToSection(sectionId) {
    // Get the content ID
    const contentId = sectionId + '-content';

    // Hide all content sections
    document.querySelectorAll('.content-container').forEach(container => {
        container.classList.add('hidden');
    });

    // Show the selected content section
    document.getElementById(contentId).classList.remove('hidden');

    // Update active navigation item
    document.querySelectorAll('.sidebar-nav li').forEach(item => {
        item.classList.remove('active');
    });

    // Find and activate the corresponding nav item
    const navItem = document.getElementById('nav-' + sectionId);
    if (navItem) {
        navItem.closest('li').classList.add('active');
    }
}

/**
 * Initialize navigation between dashboard sections
 */
function initNavigation() {
    const navLinks = {
        'nav-dashboard': 'dashboard-content',
        'nav-retrain': 'retrain-content',
        'nav-manage': 'manage-content',
        'nav-predict': 'predict-content',
        'nav-history': 'history-content',
        'nav-faq': 'faq-content'
    };

    // Add click event listeners to all navigation links
    Object.keys(navLinks).forEach(navId => {
        const navElement = document.getElementById(navId);
        if (navElement) {
            navElement.addEventListener('click', function(e) {
                e.preventDefault();
                const sectionId = navId.replace('nav-', '');
                navigateToSection(sectionId);
            });
        }
    });

    // Add click event listeners to quick action buttons
    document.querySelectorAll('[data-section]').forEach(button => {
        button.addEventListener('click', function() {
            const sectionId = this.getAttribute('data-section');
            navigateToSection(sectionId);
        });
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
 * Initialize modal functionality
 */
function initModals() {
    // Quick action buttons
    const retrainBtn = document.getElementById('retrainBtn');
    const closeBtn = document.querySelector('.modal .close');
    const errorOkBtn = document.getElementById('error-ok-btn');
    const errorModal = document.getElementById('error-modal');

    // Navigate to retrain section when retrain button is clicked
    if (retrainBtn) {
        retrainBtn.addEventListener('click', function() {
            // Navigate to retrain section
            navigateToSection('retrain');
        });
    }

    // Close error modal when close button is clicked
    if (closeBtn && errorModal) {
        closeBtn.addEventListener('click', function() {
            errorModal.style.display = 'none';
        });
    }

    // Close error modal when OK button is clicked
    if (errorOkBtn && errorModal) {
        errorOkBtn.addEventListener('click', function() {
            errorModal.style.display = 'none';
        });
    }

    // Close modals when clicking outside the modal content
    window.addEventListener('click', function(event) {
        if (event.target === errorModal) {
            errorModal.style.display = 'none';
        }
    });
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
    gradient.addColorStop(0, 'rgba(37, 99, 235, 0.8)'); // Blue 600
    gradient.addColorStop(1, 'rgba(37, 99, 235, 0.1)');

    performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: modelNames,
            datasets: [{
                label: 'Accuracy',
                data: metrics.map(metric => metric['Accuracy']),
                backgroundColor: gradient,
                borderColor: 'rgba(37, 99, 235, 1)',
                borderWidth: 2,
                borderRadius: 8,
                barThickness: 50,
                hoverBackgroundColor: 'rgba(37, 99, 235, 0.9)',
                hoverBorderColor: 'rgba(37, 99, 235, 1)',
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
                    titleColor: '#1e293b',
                    titleFont: {
                        size: 14,
                        weight: 'bold',
                        family: "'Segoe UI', Arial, sans-serif"
                    },
                    bodyColor: '#64748b',
                    bodyFont: {
                        size: 13,
                        family: "'Segoe UI', Arial, sans-serif"
                    },
                    borderColor: '#e2e8f0',
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
                                `F1 Score: ${(modelMetrics['F1 Score'] * 100).toFixed(2)}%`
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
                        color: 'rgba(226, 232, 240, 0.5)',
                        zeroLineColor: 'rgba(226, 232, 240, 0.9)'
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
                        color: '#64748b'
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
                        color: '#1e293b'
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
                        color: '#64748b'
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

        // Create table cells
        row.innerHTML = `
            <td>${formattedName}</td>
            <td>${model.type || 'Default'}</td>
            <td>${model.version || 'v1'}</td>
            <td>${accuracy}</td>
            <td>${precision}</td>
            <td>${recall}</td>
            <td>${f1Score}</td>
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
 * Initialize prediction functionality
 */
function initPrediction() {
    // Only initialize if we're on the prediction page
    const predictContent = document.getElementById('predict-content');
    if (!predictContent) return;

    // Get available models and populate the dropdown
    predictionModule.fetchAvailableModels()
        .then(models => {
            predictionModule.populateModelSelect('model-select', models);
            predictionModule.setupModelSelectListener('model-select', 'selected-model-info');
        })
        .catch(error => {
            console.error('Error initializing prediction:', error);
            showNotification('Error loading available models', 'error');
        });

    // Set up prediction form submission
    predictionModule.setupPredictionForm('predict-form',
        // Success callback
        function(results) {
            predictionModule.displayPredictionResults(
                results,
                'prediction-form-section',
                'prediction-results-section'
            );
        },
        // Error callback
        function(errorMessage) {
            showNotification(errorMessage, 'error');
        }
    );
}

/**
 * Initialize prediction history functionality
 */
function initPredictionHistory() {
    // Set up start prediction button in empty state
    const startPredictionBtn = document.getElementById('start-prediction-btn');
    if (startPredictionBtn) {
        startPredictionBtn.addEventListener('click', function() {
            document.getElementById('nav-predict').click();
        });
    }

    // Set up modal close button
    const modalCloseBtn = document.querySelector('#prediction-details-modal .close');
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', function() {
            document.getElementById('prediction-details-modal').style.display = 'none';
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('prediction-details-modal');
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Load prediction history when navigating to the history section
    document.getElementById('nav-history').addEventListener('click', function() {
        loadPredictionHistory();
    });
}

/**
 * Load prediction history from the server
 */
function loadPredictionHistory() {
    console.log('Loading prediction history...');
    const loadingElement = document.getElementById('history-loading');
    const emptyElement = document.getElementById('history-empty');
    const tableContainer = document.getElementById('history-table-container');

    if (!loadingElement || !emptyElement || !tableContainer) {
        console.error('Missing required elements for prediction history');
        return;
    }

    // Reset all states first
    loadingElement.style.display = 'flex';
    emptyElement.style.display = 'none';
    tableContainer.style.display = 'none';

    // Fetch prediction history
    fetch('/api/predictions/history')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load prediction history');
            }
            return response.json();
        })
        .then(data => {
            console.log('Prediction history data:', data);

            // Hide loading state
            loadingElement.style.display = 'none';

            if (!data.data || data.data.length === 0) {
                // Show empty state
                emptyElement.style.display = 'flex';
                tableContainer.style.display = 'none';
                console.log('No prediction history found');
            } else {
                // Show table and populate with data
                emptyElement.style.display = 'none';
                tableContainer.style.display = 'block';
                populatePredictionHistory(data.data);
                console.log('Populated prediction history table');
            }
        })
        .catch(error => {
            console.error('Error loading prediction history:', error);
            loadingElement.style.display = 'none';
            emptyElement.style.display = 'flex';
            tableContainer.style.display = 'none';
            showNotification('Error loading prediction history: ' + error.message, 'error');
        });
}

/**
 * Populate prediction history table
 * @param {Array} predictions - Array of prediction objects
 */
function populatePredictionHistory(predictions) {
    const tableBody = document.getElementById('history-table-body');
    tableBody.innerHTML = '';

    predictions.forEach(prediction => {
        const row = document.createElement('tr');

        // Format date
        const date = new Date(prediction.created_at);
        const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // Format churn rate
        const churnRate = prediction.churn_distribution.churn_rate * 100;
        let churnRateClass = 'low';
        if (churnRate > 30) {
            churnRateClass = 'high';
        } else if (churnRate > 15) {
            churnRateClass = 'medium';
        }

        // Create row content
        row.innerHTML = `
            <td>${prediction.prediction_name}</td>
            <td>${prediction.model_name}</td>
            <td>${formattedDate}</td>
            <td>${prediction.total_records.toLocaleString()}</td>
            <td><span class="churn-rate ${churnRateClass}">${churnRate.toFixed(1)}%</span></td>
            <td class="actions-cell">
                <button class="action-button view-btn" data-id="${prediction.id}">
                    <i class="fas fa-chart-pie"></i> View
                </button>
                <button class="action-button download-original-btn" data-url="${prediction.upload_download_url}">
                    <i class="fas fa-file-upload"></i> Original
                </button>
                <button class="action-button download-results-btn" data-url="${prediction.download_url}">
                    <i class="fas fa-file-download"></i> Results
                </button>
            </td>
        `;

        // Add event listeners to buttons
        const viewBtn = row.querySelector('.view-btn');
        const downloadOriginalBtn = row.querySelector('.download-original-btn');
        const downloadResultsBtn = row.querySelector('.download-results-btn');

        viewBtn.addEventListener('click', function() {
            showPredictionDetails(prediction);
        });

        downloadOriginalBtn.addEventListener('click', function() {
            window.location.href = this.getAttribute('data-url');
        });

        downloadResultsBtn.addEventListener('click', function() {
            window.location.href = this.getAttribute('data-url');
        });

        tableBody.appendChild(row);
    });
}

/**
 * Show prediction details in modal
 * @param {Object} prediction - Prediction object
 */
function showPredictionDetails(prediction) {
    // Set modal content
    document.getElementById('modal-prediction-name').textContent = prediction.prediction_name;
    document.getElementById('modal-model-name').textContent = prediction.model_name;
    document.getElementById('modal-date').textContent = new Date(prediction.created_at).toLocaleString();
    document.getElementById('modal-total-records').textContent = prediction.total_records.toLocaleString();
    document.getElementById('modal-churn-rate').textContent = (prediction.churn_distribution.churn_rate * 100).toFixed(1) + '%';

    // Set download buttons
    const downloadOriginalBtn = document.getElementById('modal-download-original');
    const downloadResultsBtn = document.getElementById('modal-download-results');

    downloadOriginalBtn.onclick = function() {
        window.location.href = prediction.upload_download_url;
    };

    downloadResultsBtn.onclick = function() {
        window.location.href = prediction.download_url;
    };

    // Create charts
    createModalChurnChart(prediction.churn_distribution);

    // Fetch feature importance data
    fetch(`/api/predictions/${prediction.id}/feature-importance`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load feature importance data');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success' && data.data && data.data.length > 0) {
                document.getElementById('modal-feature-container').style.display = 'block';
                document.getElementById('modal-feature-no-data').style.display = 'none';
                createModalFeatureChart(data.data);
            } else {
                document.getElementById('modal-feature-container').style.display = 'none';
                document.getElementById('modal-feature-no-data').style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error loading feature importance:', error);
            document.getElementById('modal-feature-container').style.display = 'none';
            document.getElementById('modal-feature-no-data').style.display = 'block';
        });

    // Show modal
    document.getElementById('prediction-details-modal').style.display = 'block';
}

/**
 * Create churn distribution chart in modal
 * @param {Object} distribution - Churn distribution data
 */
function createModalChurnChart(distribution) {
    const ctx = document.getElementById('modal-churn-chart').getContext('2d');

    // Destroy existing chart if it exists
    if (window.modalChurnChart) {
        window.modalChurnChart.destroy();
    }

    // Create new chart
    window.modalChurnChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Churn', 'No Churn'],
            datasets: [{
                data: [distribution.churn, distribution.no_churn],
                backgroundColor: ['#ef4444', '#10b981'],
                borderColor: ['#ffffff', '#ffffff'],
                borderWidth: 2,
                hoverBackgroundColor: ['#dc2626', '#059669'],
                hoverBorderColor: ['#ffffff', '#ffffff'],
                hoverBorderWidth: 4,
                borderRadius: 5,
                spacing: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = distribution.churn + distribution.no_churn;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create feature importance chart in modal
 * @param {Array} featureImportance - Feature importance data
 */
function createModalFeatureChart(featureImportance) {
    const ctx = document.getElementById('modal-feature-chart').getContext('2d');

    // Destroy existing chart if it exists
    if (window.modalFeatureChart) {
        window.modalFeatureChart.destroy();
    }

    // Create gradient for bars
    const gradient = ctx.createLinearGradient(0, 0, 400, 0);
    gradient.addColorStop(0, 'rgba(79, 70, 229, 0.9)');
    gradient.addColorStop(1, 'rgba(124, 58, 237, 0.7)');

    // Create new chart
    window.modalFeatureChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: featureImportance.map(f => {
                // Format feature names for better display
                let name = f.feature;
                // If it's a one-hot encoded feature (contains underscore)
                if (name.includes('_')) {
                    const parts = name.split('_');
                    name = `${parts[0]}: ${parts.slice(1).join(' ')}`;
                }
                return name;
            }),
            datasets: [{
                label: 'Importance',
                data: featureImportance.map(f => f.importance),
                backgroundColor: gradient,
                borderColor: 'rgba(79, 70, 229, 1)',
                borderWidth: 2,
                borderRadius: 6,
                hoverBackgroundColor: 'rgba(79, 70, 229, 1)',
                hoverBorderColor: 'rgba(79, 70, 229, 1)',
                hoverBorderWidth: 3,
                barPercentage: 0.8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw || 0;
                            return `Importance: ${value.toFixed(4)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(226, 232, 240, 0.5)',
                        drawBorder: false
                    },
                    title: {
                        display: true,
                        text: 'Importance Score',
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        color: '#1e293b'
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 13,
                            weight: 'bold'
                        },
                        color: '#1e293b'
                    }
                }
            }
        }
    });
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

/**
 * Initialize FAQ functionality
 */
function initFAQ() {
    // Get FAQ elements
    const faqItems = document.querySelectorAll('.faq-item');
    const faqSearch = document.getElementById('faq-search');
    const faqCategoryBtns = document.querySelectorAll('.faq-category-btn');

    // Toggle FAQ answers when clicking on questions
    if (faqItems && faqItems.length > 0) {
        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question');
            if (question) {
                question.addEventListener('click', () => {
                    // Toggle active class on the item
                    item.classList.toggle('active');
                });
            }
        });
    }

    // Filter FAQs when typing in search box
    if (faqSearch) {
        faqSearch.addEventListener('input', () => {
            const searchTerm = faqSearch.value.toLowerCase().trim();

            // If search term is empty, show all FAQs based on active category
            if (searchTerm === '') {
                const activeCategory = document.querySelector('.faq-category-btn.active');
                if (activeCategory) {
                    const categoryId = activeCategory.getAttribute('data-category');
                    filterFAQsByCategory(categoryId);
                }
                return;
            }

            // Hide all categories first
            document.querySelectorAll('.faq-category').forEach(category => {
                category.style.display = 'none';
            });

            // Show all categories that have matching FAQs
            let hasResults = false;

            // Search through all FAQ items
            faqItems.forEach(item => {
                const questionText = item.querySelector('.faq-question h4').textContent.toLowerCase();
                const answerText = item.querySelector('.faq-answer').textContent.toLowerCase();

                if (questionText.includes(searchTerm) || answerText.includes(searchTerm)) {
                    // Show this item
                    item.style.display = 'block';
                    // Show its parent category
                    const parentCategory = item.closest('.faq-category');
                    if (parentCategory) {
                        parentCategory.style.display = 'block';
                    }
                    hasResults = true;
                } else {
                    // Hide this item
                    item.style.display = 'none';
                }
            });

            // If no results found, show a message
            const noResultsElement = document.getElementById('faq-no-results');
            if (noResultsElement) {
                noResultsElement.style.display = hasResults ? 'none' : 'block';
            }
        });
    }

    // Switch between FAQ categories
    if (faqCategoryBtns && faqCategoryBtns.length > 0) {
        faqCategoryBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove active class from all buttons
                faqCategoryBtns.forEach(b => b.classList.remove('active'));
                // Add active class to clicked button
                btn.classList.add('active');

                // Filter FAQs by category
                const categoryId = btn.getAttribute('data-category');
                filterFAQsByCategory(categoryId);

                // Clear search box
                if (faqSearch) {
                    faqSearch.value = '';
                }
            });
        });
    }

    // Initial setup - show the first category
    filterFAQsByCategory('general');
}

/**
 * Filter FAQs by category
 * @param {string} categoryId - Category ID to filter by
 */
function filterFAQsByCategory(categoryId) {
    // Hide all categories
    document.querySelectorAll('.faq-category').forEach(category => {
        category.style.display = 'none';
    });

    // Show the selected category
    const selectedCategory = document.getElementById(categoryId);
    if (selectedCategory) {
        selectedCategory.style.display = 'block';

        // Show all items in this category
        const items = selectedCategory.querySelectorAll('.faq-item');
        items.forEach(item => {
            item.style.display = 'block';
        });
    }
}