/**
 * Manage Models JavaScript
 * Handles the functionality for the Manage Models section
 */

// Global variables
let currentPage = 1;
let totalPages = 1;
let modelsPerPage = 10;
let allModels = [];
let filteredModels = [];

// DOM elements
const modelSearchInput = document.getElementById('model-search');
const modelTypeFilter = document.getElementById('model-type-filter');
const modelsTableBody = document.getElementById('models-table-body');
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const pageInfo = document.getElementById('page-info');

/**
 * Initialize the manage models functionality
 */
function initManageModels() {
    // Add event listeners
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', handleSearch);
    }

    if (modelTypeFilter) {
        modelTypeFilter.addEventListener('change', handleFilterChange);
    }

    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderModelsTable();
                updatePagination();
            }
        });
    }

    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                renderModelsTable();
                updatePagination();
            }
        });
    }

    // Load models when the manage section is shown
    document.getElementById('nav-manage').addEventListener('click', function() {
        loadModels();
    });
}

/**
 * Load models from the server
 */
function loadModels() {
    // Show loading state
    modelsTableBody.innerHTML = `
        <tr class="loading-row">
            <td colspan="6" class="text-center">
                <i class="fas fa-spinner fa-spin"></i> Loading models...
            </td>
        </tr>
    `;

    // Fetch models from the server
    fetch('/api/models/list')
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Failed to load models');
                });
            }
            return response.json();
        })
        .then(data => {
            allModels = data.models;
            filteredModels = [...allModels];

            // Reset pagination
            currentPage = 1;
            updatePagination();

            // Render the table
            renderModelsTable();
        })
        .catch(error => {
            console.error('Error loading models:', error);
            modelsTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">
                        <i class="fas fa-exclamation-circle"></i> Error loading models: ${error.message}
                    </td>
                </tr>
            `;
        });
}

/**
 * Handle search input
 */
function handleSearch() {
    const searchTerm = modelSearchInput.value.toLowerCase().trim();

    if (searchTerm === '') {
        // If search is empty, just apply the type filter
        handleFilterChange();
        return;
    }

    // Apply both search and type filter
    const typeFilter = modelTypeFilter.value;

    filteredModels = allModels.filter(model => {
        const matchesSearch = model.name.toLowerCase().includes(searchTerm) ||
                             model.version.toLowerCase().includes(searchTerm);

        if (typeFilter === 'all') {
            return matchesSearch;
        } else {
            return matchesSearch && model.model_type_id.toString() === typeFilter;
        }
    });

    // Reset to first page and update
    currentPage = 1;
    updatePagination();
    renderModelsTable();
}

/**
 * Handle filter change
 */
function handleFilterChange() {
    const typeFilter = modelTypeFilter.value;
    const searchTerm = modelSearchInput.value.toLowerCase().trim();

    if (typeFilter === 'all' && searchTerm === '') {
        // No filters applied
        filteredModels = [...allModels];
    } else {
        // Apply filters
        filteredModels = allModels.filter(model => {
            const matchesType = typeFilter === 'all' || model.model_type_id.toString() === typeFilter;
            const matchesSearch = searchTerm === '' ||
                                 model.name.toLowerCase().includes(searchTerm) ||
                                 model.version.toLowerCase().includes(searchTerm);

            return matchesType && matchesSearch;
        });
    }

    // Reset to first page and update
    currentPage = 1;
    updatePagination();
    renderModelsTable();
}

/**
 * Update pagination controls and info
 */
function updatePagination() {
    totalPages = Math.max(1, Math.ceil(filteredModels.length / modelsPerPage));

    // Update page info
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;

    // Update button states
    prevPageBtn.disabled = currentPage <= 1;
    nextPageBtn.disabled = currentPage >= totalPages;
}

/**
 * Render the models table with current filters and pagination
 */
function renderModelsTable() {
    // Clear the table
    modelsTableBody.innerHTML = '';

    // If no models, show message
    if (filteredModels.length === 0) {
        modelsTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">
                    No models found matching your criteria.
                </td>
            </tr>
        `;
        return;
    }

    // Calculate slice for current page
    const startIndex = (currentPage - 1) * modelsPerPage;
    const endIndex = Math.min(startIndex + modelsPerPage, filteredModels.length);
    const modelsToShow = filteredModels.slice(startIndex, endIndex);

    // Add rows for each model
    modelsToShow.forEach(model => {
        const row = document.createElement('tr');

        // Format date
        const createdDate = new Date(model.created_at).toLocaleDateString();

        // Determine if model is deployed
        const isDeployed = model.is_deployed;
        const isRetrained = !model.is_default;

        // Create row content
        row.innerHTML = `
            <td>${model.name}</td>
            <td>${model.model_type_name || getModelTypeName(model.model_type_id)}</td>
            <td>${model.version}</td>
            <td>${(model.accuracy * 100).toFixed(2)}%</td>
            <td>${createdDate}</td>
            <td>
                <div class="model-status">
                    ${isRetrained ? `
                        <label class="toggle-switch">
                            <input type="checkbox" class="deploy-toggle" data-model-id="${model.id}" ${isDeployed ? 'checked' : ''}>
                            <span class="toggle-slider"></span>
                        </label>
                        <span class="status-label ${isDeployed ? 'active' : 'inactive'}">
                            ${isDeployed ? 'Deployed' : 'Not Deployed'}
                        </span>
                    ` : `
                        <span class="status-label active">Default</span>
                    `}
                </div>
            </td>
        `;

        modelsTableBody.appendChild(row);
    });

    // Add event listeners to toggle switches
    const toggles = document.querySelectorAll('.deploy-toggle');
    toggles.forEach(toggle => {
        toggle.addEventListener('change', handleDeployToggle);
    });
}

/**
 * Handle deploy toggle change
 * @param {Event} event - The change event
 */
function handleDeployToggle(event) {
    const toggle = event.target;
    const modelId = toggle.getAttribute('data-model-id');
    const isDeployed = toggle.checked;

    // Disable toggle while processing
    toggle.disabled = true;

    // Update status label
    const statusLabel = toggle.closest('.model-status').querySelector('.status-label');
    statusLabel.textContent = isDeployed ? 'Deploying...' : 'Undeploying...';
    statusLabel.className = 'status-label';

    // Send request to server
    fetch(`/api/models/${isDeployed ? 'deploy' : 'undeploy'}/${modelId}`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || `Failed to ${isDeployed ? 'deploy' : 'undeploy'} model`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log(`Model ${isDeployed ? 'deployed' : 'undeployed'} successfully:`, data);

        // Update status label
        statusLabel.textContent = isDeployed ? 'Deployed' : 'Not Deployed';
        statusLabel.className = `status-label ${isDeployed ? 'active' : 'inactive'}`;

        // Show success message
        showNotification(`Model ${isDeployed ? 'deployed' : 'undeployed'} successfully`, 'success');
    })
    .catch(error => {
        console.error(`Error ${isDeployed ? 'deploying' : 'undeploying'} model:`, error);

        // Revert toggle state
        toggle.checked = !isDeployed;

        // Update status label
        statusLabel.textContent = !isDeployed ? 'Deployed' : 'Not Deployed';
        statusLabel.className = `status-label ${!isDeployed ? 'active' : 'inactive'}`;

        // Show error message
        showNotification(error.message, 'error');
    })
    .finally(() => {
        // Re-enable toggle
        toggle.disabled = false;
    });
}



/**
 * Get model type name from ID
 * @param {number} typeId - The model type ID
 * @returns {string} The model type name
 */
function getModelTypeName(typeId) {
    const modelTypes = {
        1: 'Gradient Boosting',
        2: 'Random Forest',
        3: 'Decision Tree',
        4: 'Logistic Regression'
    };

    return modelTypes[typeId] || 'Unknown';
}

/**
 * Show notification
 * @param {string} message - The notification message
 * @param {string} type - The notification type (success, error)
 */
function showNotification(message, type) {
    // Check if notification container exists, create if not
    let notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        document.body.appendChild(notificationContainer);
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;

    // Add to container
    notificationContainer.appendChild(notification);

    // Remove after delay
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initManageModels);
