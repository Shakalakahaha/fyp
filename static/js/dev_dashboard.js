// Initialize performance chart
document.addEventListener('DOMContentLoaded', async function() {
    // Initialize models and get metrics
    try {
        // First, initialize the models
        const initResponse = await fetch('/api/models/initialize', {
            method: 'POST'
        });
        
        if (!initResponse.ok) {
            throw new Error('Failed to initialize models');
        }

        const initData = await initResponse.json();
        if (initData.status === 'success') {
            updateDashboard(initData.data);
        } else {
            console.error('Error initializing models:', initData.message);
            alert('Error initializing models. Please check console for details.');
        }
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        alert('Error initializing dashboard. Please check console for details.');
    }
});

let performanceChart = null;

function createPerformanceChart(ctx, models) {
    const modelNames = models.map(m => formatModelName(m.name));
    const metrics = models.map(m => m.metrics);

    // Destroy existing chart if it exists
    if (performanceChart) {
        performanceChart.destroy();
    }

    performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: modelNames,
            datasets: [{
                label: 'Accuracy',
                data: metrics.map(m => m.Accuracy),
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 20,
                    right: 20,
                    top: 20,
                    bottom: 20
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    titleColor: '#333',
                    titleFont: {
                        size: 16,
                        weight: 'bold'
                    },
                    bodyColor: '#666',
                    bodyFont: {
                        size: 14
                    },
                    borderColor: '#ddd',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        title: function(tooltipItems) {
                            return tooltipItems[0].label;
                        },
                        label: function(context) {
                            const modelMetrics = metrics[context.dataIndex];
                            return [
                                `Accuracy: ${(modelMetrics.Accuracy * 100).toFixed(2)}%`,
                                `Precision: ${(modelMetrics.Precision * 100).toFixed(2)}%`,
                                `Recall: ${(modelMetrics.Recall * 100).toFixed(2)}%`,
                                `F1 Score: ${(modelMetrics['F1 Score'] * 100).toFixed(2)}%`,
                                modelMetrics.AUC ? `AUC: ${(modelMetrics.AUC * 100).toFixed(2)}%` : null
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
                        color: 'rgba(200, 200, 200, 0.2)',
                        zeroLineColor: 'rgba(200, 200, 200, 0.6)'
                    },
                    ticks: {
                        callback: function(value) {
                            return (value * 100).toFixed(0) + '%';
                        },
                        font: {
                            size: 12
                        },
                        padding: 10
                    },
                    title: {
                        display: true,
                        text: 'Accuracy Score',
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        padding: 20
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 12
                        },
                        padding: 10
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            hover: {
                mode: 'index',
                intersect: false
            }
        }
    });

    return performanceChart;
}

function updateDashboard(models) {
    // Update table
    const tbody = document.querySelector('.model-table tbody');
    tbody.innerHTML = ''; // Clear existing rows

    models.forEach(model => {
        const metrics = model.metrics;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatModelName(model.name)}</td>
            <td>${(metrics.Accuracy * 100).toFixed(2)}%</td>
            <td>${(metrics.Precision * 100).toFixed(2)}%</td>
            <td>${(metrics.Recall * 100).toFixed(2)}%</td>
            <td>${(metrics['F1 Score'] * 100).toFixed(2)}%</td>
            <td>
                <button class="action-btn retrain">Retrain</button>
                <button class="action-btn deploy" ${model.is_deployed ? 'disabled' : ''}>
                    ${model.is_deployed ? 'Deployed' : 'Deploy'}
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    // Update chart
    const ctx = document.getElementById('performanceChart').getContext('2d');
    createPerformanceChart(ctx, models);

    // Reinitialize button event listeners
    initializeButtonListeners();
}

function formatModelName(name) {
    return name.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function initializeButtonListeners() {
    // Add event listeners for buttons
    document.querySelectorAll('.action-btn.retrain').forEach(button => {
        button.addEventListener('click', function() {
            const modelName = this.closest('tr').querySelector('td:first-child').textContent;
            handleRetraining(modelName);
        });
    });

    document.querySelectorAll('.action-btn.deploy').forEach(button => {
        button.addEventListener('click', function() {
            const modelName = this.closest('tr').querySelector('td:first-child').textContent;
            handleDeployment(modelName);
        });
    });

    // Quick action buttons
    document.getElementById('predictBtn').addEventListener('click', function() {
        handlePrediction();
    });

    document.getElementById('retrainBtn').addEventListener('click', function() {
        handleQuickRetrain();
    });
}

async function handleRetraining(modelName) {
    alert(`Retrain functionality will be implemented for ${modelName}`);
}

async function handleDeployment(modelName) {
    alert(`Deploy functionality will be implemented for ${modelName}`);
}

async function handlePrediction() {
    alert('Prediction functionality will be implemented');
}

async function handleQuickRetrain() {
    alert('Quick retrain functionality will be implemented');
}

// Function to update the performance metrics
function updateMetrics(modelName, newMetrics) {
    // This function will be implemented to update the table and chart
    // when new metrics are available after retraining
    console.log(`Updating metrics for ${modelName}`, newMetrics);
}

// Function to handle model deployment
function deployModel(modelName) {
    // This function will be implemented to handle model deployment
    console.log(`Deploying model: ${modelName}`);
}

// Function to handle prediction
function handlePrediction(data) {
    // This function will be implemented to handle predictions
    console.log('Handling prediction with data:', data);
}

// Function to handle model retraining
function handleRetraining(modelName, newData) {
    // This function will be implemented to handle model retraining
    console.log(`Retraining ${modelName} with new data:`, newData);
}

// Add CSS for version badge
const style = document.createElement('style');
style.textContent = `
    .version-badge {
        background-color: #e0e0e0;
        padding: 2px 6px;
        border-radius: 12px;
        font-size: 0.8em;
        margin-left: 8px;
    }
`;
document.head.appendChild(style); 