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
    console.log("Creating chart with models:", models);
    
    const modelNames = models.map(m => formatModelName(m.name));
    const metrics = models.map(m => m.metrics);

    if (performanceChart) {
        performanceChart.destroy();
    }

    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(65, 105, 225, 0.8)'); // Royal Blue
    gradient.addColorStop(1, 'rgba(65, 105, 225, 0.1)');

    performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: modelNames,
            datasets: [{
                label: 'Model Performance',
                data: metrics.map(metric => metric['Accuracy']),
                backgroundColor: gradient,
                borderColor: 'rgba(65, 105, 225, 1)',
                borderWidth: 2,
                borderRadius: 8,
                barThickness: 50,
                hoverBackgroundColor: 'rgba(65, 105, 225, 0.9)',
                hoverBorderColor: 'rgba(65, 105, 225, 1)',
                hoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Model Performance Overview',
                    font: {
                        size: 18,
                        weight: 'bold',
                        family: "'Segoe UI', Arial, sans-serif"
                    },
                    padding: {
                        top: 20,
                        bottom: 20
                    },
                    color: '#2c3e50'
                },
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    titleColor: '#2c3e50',
                    titleFont: {
                        size: 16,
                        weight: 'bold',
                        family: "'Segoe UI', Arial, sans-serif"
                    },
                    bodyColor: '#34495e',
                    bodyFont: {
                        size: 14,
                        family: "'Segoe UI', Arial, sans-serif"
                    },
                    borderColor: '#e0e0e0',
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
                        color: 'rgba(200, 200, 200, 0.2)',
                        zeroLineColor: 'rgba(200, 200, 200, 0.6)'
                    },
                    ticks: {
                        callback: function(value) {
                            return (value * 100).toFixed(0) + '%';
                        },
                        stepSize: 0.1, // This will create 10% steps
                        font: {
                            size: 12,
                            family: "'Segoe UI', Arial, sans-serif"
                        },
                        padding: 10,
                        color: '#2c3e50'
                    },
                    title: {
                        display: true,
                        text: 'Accuracy Score',
                        font: {
                            size: 14,
                            weight: 'bold',
                            family: "'Segoe UI', Arial, sans-serif"
                        },
                        padding: {
                            top: 20,
                            bottom: 10
                        },
                        color: '#2c3e50'
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
                        color: '#2c3e50'
                    }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeInOutQuart'
            }
        }
    });

    return performanceChart;
}

function updateDashboard(models) {
    console.log("Received models data:", models); // Debug log

    // Update chart only
    const ctx = document.getElementById('performanceChart').getContext('2d');
    createPerformanceChart(ctx, models);

    // Initialize modal event listener
    initializeModalListeners();
}

function formatModelName(name) {
    return name.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function initializeModalListeners() {
    // Quick action buttons
    document.getElementById('retrainBtn').addEventListener('click', function() {
        openRetrainingModal();
    });
}

function openRetrainingModal() {
    const modal = document.getElementById('retrainingModal');
    modal.style.display = 'block';
}

// Close modal when clicking the close button or outside the modal
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('retrainingModal');
    const closeBtn = document.getElementsByClassName('close')[0];

    closeBtn.onclick = function() {
        modal.style.display = 'none';
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
}); 