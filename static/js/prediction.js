/**
 * Shared prediction functionality for both developer and user dashboards
 */

// Constants for required columns
const REQUIRED_COLUMNS = {
    categorical: [
        'InternetService', 'OnlineSecurity', 'TechSupport', 'Contract',
        'SeniorCitizen', 'Partner', 'Dependents', 'OnlineBackup',
        'DeviceProtection', 'StreamingTV', 'StreamingMovies',
        'PaymentMethod', 'PaperlessBilling'
    ],
    numerical: ['tenure', 'TotalCharges', 'MonthlyCharges'],
    meta: ['customerID']
};

/**
 * Fetch available models for the current user
 * @returns {Promise<Array>} Array of available models
 */
async function fetchAvailableModels() {
    try {
        const response = await fetch('/api/models/metrics');

        if (!response.ok) {
            throw new Error(`Failed to fetch models: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        if (data.status !== 'success' || !data.data) {
            throw new Error(data.message || 'Failed to fetch models');
        }

        return data.data;
    } catch (error) {
        console.error('Error fetching available models:', error);
        throw error;
    }
}

/**
 * Populate the model selection dropdown
 * @param {string} selectElementId - ID of the select element to populate
 * @param {Array} models - Array of model objects
 */
function populateModelSelect(selectElementId, models) {
    const selectElement = document.getElementById(selectElementId);
    if (!selectElement) return;

    // Clear existing options except the first one
    while (selectElement.options.length > 1) {
        selectElement.remove(1);
    }

    // Group models by type
    const modelsByType = {};
    models.forEach(model => {
        const type = model.is_default ? 'Default Models' : 'Custom Models';
        if (!modelsByType[type]) {
            modelsByType[type] = [];
        }
        modelsByType[type].push(model);
    });

    // Add options grouped by type
    Object.keys(modelsByType).forEach(type => {
        const optgroup = document.createElement('optgroup');
        optgroup.label = type;

        modelsByType[type].forEach(model => {
            const option = document.createElement('option');
            // Ensure model.id is a string to avoid type issues
            option.value = String(model.id);
            option.textContent = `${formatModelName(model.name)} (${model.version})`;
            // Store only necessary data to avoid circular references
            const modelData = {
                id: model.id,
                name: model.name,
                type: model.type,
                version: model.version,
                metrics: model.metrics
            };
            option.dataset.model = JSON.stringify(modelData);
            optgroup.appendChild(option);
        });

        selectElement.appendChild(optgroup);
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
 * Display model info when a model is selected
 * @param {string} selectElementId - ID of the select element
 * @param {string} infoElementId - ID of the element to display model info
 */
function setupModelSelectListener(selectElementId, infoElementId) {
    const selectElement = document.getElementById(selectElementId);
    const infoElement = document.getElementById(infoElementId);

    if (!selectElement || !infoElement) return;

    selectElement.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption.dataset.model) {
            const model = JSON.parse(selectedOption.dataset.model);
            const metrics = model.metrics || {};

            // Format metrics for display
            const accuracyText = metrics.Accuracy !== undefined ?
                `${(metrics.Accuracy * 100).toFixed(2)}%` : 'N/A';
            const f1Text = metrics['F1 Score'] !== undefined ?
                `${(metrics['F1 Score'] * 100).toFixed(2)}%` : 'N/A';

            // Create info HTML
            infoElement.innerHTML = `
                <p><strong>Model Type:</strong> ${model.type || 'Unknown'}</p>
                <p><strong>Version:</strong> ${model.version || 'v1'}</p>
                <p><strong>Accuracy:</strong> ${accuracyText}</p>
                <p><strong>F1 Score:</strong> ${f1Text}</p>
            `;
            infoElement.classList.add('active');
        } else {
            infoElement.innerHTML = '';
            infoElement.classList.remove('active');
        }
    });
}

/**
 * Submit prediction form
 * @param {string} formElementId - ID of the form element
 * @param {Function} onSuccess - Callback function on successful prediction
 * @param {Function} onError - Callback function on error
 */
function setupPredictionForm(formElementId, onSuccess, onError) {
    const formElement = document.getElementById(formElementId);
    const loadingOverlay = document.getElementById('loading-overlay');

    if (!formElement || !loadingOverlay) return;

    formElement.addEventListener('submit', async function(event) {
        event.preventDefault();

        try {
            // Show loading overlay
            loadingOverlay.classList.remove('hidden');

            // Get form data
            const formData = new FormData(formElement);

            // Ensure model_id is a string
            const modelSelect = formElement.querySelector('select[name="model_id"]');
            if (modelSelect) {
                // Remove any existing model_id field
                for (const pair of formData.entries()) {
                    if (pair[0] === 'model_id') {
                        formData.delete('model_id');
                    }
                }
                // Add model_id as a string
                formData.append('model_id', String(modelSelect.value));
            }

            // Log form data for debugging
            console.log('Form data:');
            for (const pair of formData.entries()) {
                console.log(pair[0] + ': ' + pair[1]);
            }

            // Send prediction request
            const response = await fetch('/api/predict', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok || data.status !== 'success') {
                // Check for specific error messages
                if (data.details && data.details.includes('scikit-learn')) {
                    throw new Error(`${data.message}\n\nDetails: ${data.details}`);
                } else {
                    throw new Error(data.message || `Prediction failed: ${response.status} ${response.statusText}`);
                }
            }

            // Call success callback
            if (typeof onSuccess === 'function') {
                onSuccess(data.data);
            }
        } catch (error) {
            console.error('Error submitting prediction:', error);

            // Convert error to string safely
            let errorMessage = '';
            if (typeof error === 'string') {
                errorMessage = error;
            } else if (error instanceof Error) {
                errorMessage = error.message;
            } else if (Array.isArray(error)) {
                errorMessage = 'Error: Received array instead of error message';
            } else if (error && typeof error === 'object') {
                errorMessage = 'Error: ' + JSON.stringify(error);
            } else {
                errorMessage = 'Unknown error occurred';
            }

            // Call error callback with safe string
            if (typeof onError === 'function') {
                onError(errorMessage);
            }
        } finally {
            // Hide loading overlay
            loadingOverlay.classList.add('hidden');
        }
    });
}

/**
 * Display prediction results
 * @param {Object} results - Prediction results data
 * @param {string} formSectionId - ID of the form section element
 * @param {string} resultsSectionId - ID of the results section element
 */
function displayPredictionResults(results, formSectionId, resultsSectionId) {
    const formSection = document.getElementById(formSectionId);
    const resultsSection = document.getElementById(resultsSectionId);

    if (!formSection || !resultsSection) return;

    // Hide form section and show results section
    formSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');

    // Update summary information
    document.getElementById('result-prediction-name').textContent = results.prediction_name;
    document.getElementById('result-model-name').textContent = results.model_name;
    document.getElementById('result-total-records').textContent = results.total_records;
    document.getElementById('result-date').textContent = new Date(results.created_at).toLocaleString();

    // Create charts
    createChurnDistributionChart(results.churn_distribution);
    createFeatureImportanceChart(results.feature_importance);

    // Create preview table
    createResultsPreview(results.download_url);

    // Set up download button
    const downloadButton = document.getElementById('download-results');
    if (downloadButton) {
        downloadButton.onclick = function() {
            window.location.href = results.download_url;
        };
    }

    // Set up back button
    const backButton = document.getElementById('back-to-form');
    if (backButton) {
        backButton.onclick = function() {
            // Hide results section and show form section
            resultsSection.classList.add('hidden');
            formSection.classList.remove('hidden');

            // Reset the form
            const form = document.getElementById('predict-form');
            if (form) {
                form.reset();

                // Clear the model info section
                const modelInfo = document.getElementById('selected-model-info');
                if (modelInfo) {
                    modelInfo.innerHTML = '';
                    modelInfo.classList.remove('active');
                }

                // Reset file upload display
                const fileUploadContainer = document.querySelector('.file-upload-container');
                if (fileUploadContainer) {
                    const fileUploadMessage = fileUploadContainer.querySelector('.file-upload-message');
                    if (fileUploadMessage) {
                        fileUploadMessage.textContent = 'Drag & drop your file here or click to browse';
                    }

                    // Remove any selected file indicators
                    fileUploadContainer.classList.remove('has-file');
                    const fileNameDisplay = fileUploadContainer.querySelector('.file-name');
                    if (fileNameDisplay) {
                        fileNameDisplay.remove();
                    }
                }
            }
        };
    }
}

/**
 * Create churn distribution chart
 * @param {Object} distribution - Churn distribution data
 */
function createChurnDistributionChart(distribution) {
    const ctx = document.getElementById('churn-distribution-chart').getContext('2d');

    // Destroy existing chart if it exists
    if (window.churnDistributionChart) {
        window.churnDistributionChart.destroy();
    }

    // Create new chart
    window.churnDistributionChart = new Chart(ctx, {
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
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    titleColor: '#1e293b',
                    bodyColor: '#64748b',
                    borderColor: '#e2e8f0',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    boxPadding: 6,
                    usePointStyle: true,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = distribution.churn + distribution.no_churn;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Customer Churn Distribution',
                    font: {
                        size: 16,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                }
            },
            animation: {
                animateScale: true,
                animateRotate: true,
                duration: 1000
            }
        }
    });
}

/**
 * Create feature importance chart
 * @param {Array} featureImportance - Feature importance data
 */
function createFeatureImportanceChart(featureImportance) {
    const ctx = document.getElementById('feature-importance-chart').getContext('2d');
    const chartContainer = document.getElementById('feature-importance-container');
    const noDataMessage = document.getElementById('feature-importance-no-data');

    // Destroy existing chart if it exists
    if (window.featureImportanceChart) {
        window.featureImportanceChart.destroy();
    }

    // Check if we have feature importance data
    if (!featureImportance || featureImportance.length === 0) {
        // Show no data message
        if (chartContainer) chartContainer.style.display = 'none';
        if (noDataMessage) {
            noDataMessage.style.display = 'block';
            noDataMessage.textContent = 'Feature importance data not available for this model.';
        }
        return;
    }

    // Show chart container and hide no data message
    if (chartContainer) chartContainer.style.display = 'block';
    if (noDataMessage) noDataMessage.style.display = 'none';

    // Sort features by importance
    const sortedFeatures = [...featureImportance].sort((a, b) => b.importance - a.importance);

    // Take top 5 features
    const topFeatures = sortedFeatures.slice(0, 5);

    // Create gradient for bars
    const gradient = ctx.createLinearGradient(0, 0, 400, 0);
    gradient.addColorStop(0, 'rgba(79, 70, 229, 0.9)');
    gradient.addColorStop(1, 'rgba(124, 58, 237, 0.7)');

    // Create new chart
    window.featureImportanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topFeatures.map(f => {
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
                data: topFeatures.map(f => f.importance),
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
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    titleColor: '#1e293b',
                    bodyColor: '#64748b',
                    borderColor: '#e2e8f0',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const value = context.raw || 0;
                            return `Importance: ${value.toFixed(4)}`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Top 5 Features by Importance',
                    font: {
                        size: 16,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 20
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
                    ticks: {
                        font: {
                            size: 12
                        },
                        color: '#64748b',
                        padding: 10
                    },
                    title: {
                        display: true,
                        text: 'Importance Score',
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        padding: {
                            top: 10,
                            bottom: 10
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
                        color: '#1e293b',
                        padding: 10
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
}

/**
 * Create results preview table
 * @param {string} downloadUrl - URL to download the full results
 */
function createResultsPreview(downloadUrl) {
    const tableContainer = document.getElementById('results-preview-table-container');
    const noDataMessage = document.getElementById('results-preview-no-data');
    const thead = document.getElementById('results-preview-thead');
    const tbody = document.getElementById('results-preview-tbody');

    if (!tableContainer || !thead || !tbody) return;

    // Show loading state
    tableContainer.style.display = 'none';
    noDataMessage.style.display = 'block';
    noDataMessage.textContent = 'Loading preview data...';

    // The download URL format is /api/predictions/{id}/download
    // Extract the prediction ID directly
    const predictionId = downloadUrl.replace('/api/predictions/', '').replace('/download', '');

    console.log('Download URL:', downloadUrl);
    console.log('Extracted prediction ID:', predictionId);

    // Fetch the preview data
    fetch(`/api/predictions/${predictionId}/preview`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load preview data');
            }
            return response.json();
        })
        .then(data => {
            if (!data.preview || !data.preview.length) {
                throw new Error('No preview data available');
            }

            // Clear existing content
            thead.innerHTML = '';
            tbody.innerHTML = '';

            // Create header row
            const headerRow = document.createElement('tr');
            const headers = Object.keys(data.preview[0]);

            headers.forEach(header => {
                const th = document.createElement('th');
                th.textContent = header;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);

            // Create data rows
            data.preview.forEach(row => {
                const tr = document.createElement('tr');

                headers.forEach(header => {
                    const td = document.createElement('td');
                    let value = row[header];

                    // Special formatting for Churn column
                    if (header === 'Churn') {
                        if (value === '1' || value === 1 || value === true || value === 'true') {
                            td.textContent = 'Yes';
                            td.className = 'churn-yes';
                        } else {
                            td.textContent = 'No';
                            td.className = 'churn-no';
                        }
                    } else {
                        td.textContent = value !== null && value !== undefined ? value : '';
                    }

                    tr.appendChild(td);
                });

                tbody.appendChild(tr);
            });

            // Show the table
            tableContainer.style.display = 'block';
            noDataMessage.style.display = 'none';
        })
        .catch(error => {
            console.error('Error loading preview data:', error);
            tableContainer.style.display = 'none';
            noDataMessage.style.display = 'block';
            noDataMessage.textContent = 'Preview data not available. ' + error.message;
        });
}

/**
 * Show notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, warning)
 */
function showNotification(message, type = 'info') {
    // For now, just use alert
    if (type === 'error') {
        alert(`Error: ${message}`);
    } else if (type === 'success') {
        alert(`Success: ${message}`);
    } else {
        alert(message);
    }
}

// Export functions for use in dashboard scripts
window.predictionModule = {
    fetchAvailableModels,
    populateModelSelect,
    setupModelSelectListener,
    setupPredictionForm,
    displayPredictionResults,
    showNotification
};
