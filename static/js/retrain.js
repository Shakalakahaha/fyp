/**
 * Retrain Model Functionality
 */

/**
 * Initialize retrain model functionality
 */
function initRetrain() {
    console.log('Initializing retrain functionality');

    // Set up file upload UI
    setupFileUpload();

    // Set up form submission
    setupFormSubmission();

    // Set up retrain results actions
    setupResultsActions();

    // Set up error modal
    setupErrorModal();
}

/**
 * Set up file upload UI
 */
function setupFileUpload() {
    const fileInput = document.getElementById('dataset-file');
    const fileUploadContainer = document.querySelector('.file-upload-container');
    const fileUploadMessage = document.querySelector('.file-upload-message');

    if (!fileInput || !fileUploadContainer || !fileUploadMessage) return;

    // Handle file selection
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // Check file type
            const fileType = file.name.split('.').pop().toLowerCase();
            if (fileType !== 'csv' && fileType !== 'xlsx') {
                showError('Invalid file type. Please upload a CSV or Excel file.');
                fileInput.value = '';
                return;
            }

            // Check file size (max 10MB)
            if (file.size > 10 * 1024 * 1024) {
                showError('File size exceeds the 10MB limit.');
                fileInput.value = '';
                return;
            }

            // Update UI
            fileUploadMessage.textContent = file.name;
            fileUploadContainer.classList.add('has-file');

            // Add file name display
            if (!fileUploadContainer.querySelector('.file-name')) {
                const fileNameElement = document.createElement('div');
                fileNameElement.className = 'file-name';
                fileNameElement.innerHTML = `
                    <i class="fas fa-file-${fileType === 'csv' ? 'csv' : 'excel'}"></i>
                    <span>${file.name}</span>
                    <button type="button" class="remove-file">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                fileUploadContainer.appendChild(fileNameElement);

                // Set up remove button
                const removeButton = fileNameElement.querySelector('.remove-file');
                removeButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    fileInput.value = '';
                    fileUploadMessage.textContent = 'Drag & drop your file here or click to browse';
                    fileUploadContainer.classList.remove('has-file');
                    fileNameElement.remove();
                });
            }
        }
    });

    // Handle drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileUploadContainer.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        fileUploadContainer.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileUploadContainer.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        fileUploadContainer.classList.add('highlight');
    }

    function unhighlight() {
        fileUploadContainer.classList.remove('highlight');
    }

    fileUploadContainer.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length) {
            fileInput.files = files;
            // Trigger change event
            const event = new Event('change');
            fileInput.dispatchEvent(event);
        }
    }
}

/**
 * Set up form submission
 */
function setupFormSubmission() {
    const form = document.getElementById('retrain-form');

    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        // Validate form
        const datasetName = document.getElementById('dataset-name').value.trim();
        const datasetFile = document.getElementById('dataset-file').files[0];

        if (!datasetName) {
            showError('Please enter a dataset name.');
            return;
        }

        if (!datasetFile) {
            showError('Please select a dataset file.');
            return;
        }

        // Show progress modal
        const progressModal = document.getElementById('retraining-progress-modal');
        if (progressModal) {
            progressModal.style.display = 'block';
        }

        // Create form data
        const formData = new FormData();
        formData.append('dataset_name', datasetName);
        formData.append('dataset_file', datasetFile);

        // Send request to server
        fetch('/api/retrain/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Failed to upload dataset');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Upload successful:', data);

            // Update progress
            updateProgress('step-upload', 'completed');
            updateProgress('step-combine', 'active');
            updateProgressMessage('Dataset uploaded successfully. Combining datasets...');

            // Start dataset combination
            return fetch(`/api/retrain/combine/${data.dataset_id}`);
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Failed to combine datasets');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Combination successful:', data);

            // Log detailed information about the combination
            const existingDatasetType = data.existing_dataset.type;
            const combinationDetails = `Combined ${data.uploaded_dataset.name} with ${existingDatasetType === 'combined' ? 'previous combined dataset' : 'original dataset'} (${data.existing_dataset.name}). Total records: ${data.total_records}`;
            console.log(combinationDetails);

            // Update progress
            updateProgress('step-combine', 'completed');
            updateProgress('step-train', 'active');
            updateProgressMessage(`Datasets combined successfully (${data.total_records} records). Training model...`);

            // Start model training
            return fetch(`/api/retrain/train/${data.combined_dataset_id}`);
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Failed to train model');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Training successful:', data);

            // Update progress
            updateProgress('step-train', 'completed');
            updateProgress('step-evaluate', 'active');
            updateProgressMessage('Model trained successfully. Evaluating performance...');

            // Wait a moment for dramatic effect
            setTimeout(() => {
                // Update progress
                updateProgress('step-evaluate', 'completed');
                updateProgressMessage('Retraining completed successfully!');

                // Hide progress modal after a delay
                setTimeout(() => {
                    if (progressModal) {
                        progressModal.style.display = 'none';
                    }

                    // Display results
                    displayResults(data);
                }, 1000);
            }, 1000);
        })
        .catch(error => {
            console.error('Error during retraining:', error);

            // Hide progress modal
            if (progressModal) {
                progressModal.style.display = 'none';
            }

            // Show error
            showError(error.message || 'An error occurred during retraining.');
        });
    });
}

/**
 * Update progress step
 * @param {string} stepId - ID of the step element
 * @param {string} status - Status to set (active, completed)
 */
function updateProgress(stepId, status) {
    const step = document.getElementById(stepId);
    if (!step) return;

    // Remove existing status classes
    step.classList.remove('active', 'completed');

    // Add new status class
    step.classList.add(status);
}

/**
 * Update progress message
 * @param {string} message - Message to display
 */
function updateProgressMessage(message) {
    const messageElement = document.getElementById('progress-message');
    if (!messageElement) return;

    messageElement.textContent = message;
}

/**
 * Display retraining results
 * @param {Object} data - Results data from the server
 */
function displayResults(data) {
    // Hide form and show results
    const form = document.getElementById('retrain-form');
    const results = document.getElementById('retrain-results');

    if (form) form.classList.add('hidden');
    if (results) results.classList.remove('hidden');

    // Update summary information
    document.getElementById('model-version').textContent = data.model_version;
    document.getElementById('dataset-info').textContent = `${data.total_records} records`;
    document.getElementById('training-date').textContent = new Date().toLocaleString();

    // Update metrics table
    // Previous model metrics
    document.getElementById('accuracy-previous').textContent = (data.previous_metrics.accuracy * 100).toFixed(2) + '%';
    document.getElementById('precision-previous').textContent = (data.previous_metrics.precision * 100).toFixed(2) + '%';
    document.getElementById('recall-previous').textContent = (data.previous_metrics.recall * 100).toFixed(2) + '%';
    document.getElementById('f1-previous').textContent = (data.previous_metrics.f1_score * 100).toFixed(2) + '%';

    // New model metrics
    document.getElementById('accuracy-new').textContent = (data.metrics.accuracy * 100).toFixed(2) + '%';
    document.getElementById('precision-new').textContent = (data.metrics.precision * 100).toFixed(2) + '%';
    document.getElementById('recall-new').textContent = (data.metrics.recall * 100).toFixed(2) + '%';
    document.getElementById('f1-new').textContent = (data.metrics.f1_score * 100).toFixed(2) + '%';

    // Differences
    updateMetricDifference('accuracy-diff', data.metrics.accuracy, data.previous_metrics.accuracy);
    updateMetricDifference('precision-diff', data.metrics.precision, data.previous_metrics.precision);
    updateMetricDifference('recall-diff', data.metrics.recall, data.previous_metrics.recall);
    updateMetricDifference('f1-diff', data.metrics.f1_score, data.previous_metrics.f1_score);

    // Set model ID on deploy button
    const deployButton = document.getElementById('deploy-model-btn');
    if (deployButton) {
        deployButton.setAttribute('data-model-id', data.model_id);
        deployButton.disabled = false;
        deployButton.innerHTML = '<i class="fas fa-rocket"></i> Deploy Model';
        deployButton.classList.remove('deployed');
    }
}

/**
 * Update metric difference display
 * @param {string} elementId - ID of the element to update
 * @param {number} newValue - New metric value
 * @param {number} oldValue - Old metric value
 */
function updateMetricDifference(elementId, newValue, oldValue) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const change = newValue - oldValue;
    const changePercent = (change / oldValue * 100).toFixed(2);

    if (change > 0) {
        element.textContent = `+${changePercent}%`;
        element.className = 'positive';
    } else if (change < 0) {
        element.textContent = `${changePercent}%`;
        element.className = 'negative';
    } else {
        element.textContent = 'No change';
    }
}

/**
 * Set up results actions
 */
function setupResultsActions() {
    // Deploy model button
    const deployButton = document.getElementById('deploy-model-btn');
    if (deployButton) {
        deployButton.addEventListener('click', function() {
            // Get the model ID from the button's data attribute
            const modelId = this.getAttribute('data-model-id');
            if (!modelId) {
                showError('No model ID found. Please try again.');
                return;
            }

            // Show confirmation dialog
            if (confirm('Are you sure you want to deploy this model? It will be available for predictions.')) {
                // Show loading state
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deploying...';

                // Send request to deploy the model
                fetch(`/api/retrain/deploy/${modelId}`, {
                    method: 'POST'
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(data => {
                            throw new Error(data.message || 'Failed to deploy model');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Deployment successful:', data);

                    // Show success message
                    alert(`Model ${data.model_name} (${data.model_version}) deployed successfully!`);

                    // Update button state
                    this.disabled = true;
                    this.innerHTML = '<i class="fas fa-check"></i> Deployed';
                    this.classList.add('deployed');
                })
                .catch(error => {
                    console.error('Error deploying model:', error);
                    showError(error.message);

                    // Reset button state
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-rocket"></i> Deploy Model';
                });
            }
        });
    }

    // New retraining button
    const newRetrainButton = document.getElementById('new-retrain-btn');
    if (newRetrainButton) {
        newRetrainButton.addEventListener('click', function() {
            // Reset form
            const form = document.getElementById('retrain-form');
            const results = document.getElementById('retrain-results');

            if (form) {
                form.reset();
                form.classList.remove('hidden');
            }

            if (results) {
                results.classList.add('hidden');
            }

            // Reset file upload UI
            const fileUploadContainer = document.querySelector('.file-upload-container');
            const fileUploadMessage = document.querySelector('.file-upload-message');
            const fileName = document.querySelector('.file-name');

            if (fileUploadContainer) fileUploadContainer.classList.remove('has-file');
            if (fileUploadMessage) fileUploadMessage.textContent = 'Drag & drop your file here or click to browse';
            if (fileName && fileName.parentNode) fileName.parentNode.removeChild(fileName);

            // Clear file input
            const fileInput = document.getElementById('dataset-file');
            if (fileInput) fileInput.value = '';

            // Reset dataset name field
            const datasetNameInput = document.getElementById('dataset-name');
            if (datasetNameInput) datasetNameInput.value = '';

            // Reset any validation messages
            const validationMessages = document.querySelectorAll('.validation-message');
            validationMessages.forEach(msg => {
                msg.textContent = '';
                msg.classList.remove('error');
            });

            // Reset submit button
            const submitButton = document.getElementById('retrain-submit');
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = 'Start Retraining';
            }
        });
    }
}

/**
 * Set up error modal
 */
function setupErrorModal() {
    const modal = document.getElementById('error-modal');
    const closeButton = modal ? modal.querySelector('.close') : null;
    const okButton = document.getElementById('error-ok-btn');

    if (closeButton) {
        closeButton.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }

    if (okButton) {
        okButton.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

/**
 * Show error message in modal
 * @param {string} message - Error message to display
 */
function showError(message) {
    const modal = document.getElementById('error-modal');
    const messageElement = document.getElementById('error-message');

    if (messageElement) {
        messageElement.textContent = message;
    }

    if (modal) {
        modal.style.display = 'block';
    }
}
