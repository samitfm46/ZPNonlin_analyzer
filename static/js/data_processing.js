// Data processing functionality for PK Analysis Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize data processing functionality
    initDataProcessing();
});

function initDataProcessing() {
    // Setup dataset preview when a dataset is selected
    const datasetSelect = document.getElementById('dataset_id');
    if (datasetSelect) {
        datasetSelect.addEventListener('change', function() {
            fetchDatasetPreview(this.value);
        });
    }

    // Setup transformation type change event
    const transformationSelect = document.getElementById('transformation');
    if (transformationSelect) {
        transformationSelect.addEventListener('change', function() {
            updateTransformationDescription(this.value);
        });
        
        // Initialize with default value
        if (transformationSelect.value) {
            updateTransformationDescription(transformationSelect.value);
        }
    }

    // Setup filtering functionality
    setupFilterControls();
    
    // Setup data merge functionality
    setupDataMergeControls();
}

function fetchDatasetPreview(datasetId) {
    if (!datasetId) return;
    
    const previewContainer = document.getElementById('dataPreview');
    if (!previewContainer) return;
    
    // Show loading indicator
    previewContainer.innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    
    fetch(`/api/dataset/${datasetId}/preview`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                previewContainer.innerHTML = '<div class="alert alert-danger">Error loading dataset preview</div>';
                return;
            }
            
            renderDatasetPreview(previewContainer, data.data);
            
            // Show plot preview if available
            fetchAndRenderDatasetPlot(datasetId);
        })
        .catch(error => {
            console.error('Error fetching dataset preview:', error);
            previewContainer.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        });
}

function renderDatasetPreview(container, data) {
    if (!data || data.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No data available for preview</div>';
        return;
    }
    
    let html = '<div class="table-responsive mt-3">';
    html += '<table class="table table-sm table-striped">';
    html += '<thead><tr><th>Subject ID</th><th>Time</th><th>Concentration</th></tr></thead>';
    html += '<tbody>';
    
    data.forEach(item => {
        html += `<tr>
            <td>${item.subject_id}</td>
            <td>${item.time}</td>
            <td>${item.concentration}</td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function fetchAndRenderDatasetPlot(datasetId) {
    const plotContainer = document.getElementById('dataPlotPreview');
    if (!plotContainer) return;
    
    fetch(`/api/dataset/${datasetId}/plot-data`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                plotContainer.innerHTML = '<div class="alert alert-danger">Error loading plot data</div>';
                return;
            }
            
            renderDatasetPlot(plotContainer, data.data);
        })
        .catch(error => {
            console.error('Error fetching dataset plot data:', error);
            plotContainer.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        });
}

function renderDatasetPlot(container, data) {
    if (!data || data.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No plot data available</div>';
        return;
    }
    
    // Create plot container if it doesn't exist
    let plotDiv = container.querySelector('.plot-container');
    if (!plotDiv) {
        plotDiv = document.createElement('div');
        plotDiv.className = 'plot-container';
        plotDiv.style.height = '400px';
        container.innerHTML = '';
        container.appendChild(plotDiv);
    }
    
    const traces = [];
    
    // Add trace for each subject
    data.forEach(subject => {
        traces.push({
            x: subject.times,
            y: subject.concentrations,
            type: 'scatter',
            mode: 'lines+markers',
            name: `Subject ${subject.subject_id}`,
            marker: { size: 8 }
        });
    });
    
    const layout = {
        title: 'Concentration vs. Time',
        xaxis: {
            title: 'Time (h)',
            zeroline: false
        },
        yaxis: {
            title: 'Concentration',
            zeroline: false
        },
        hovermode: 'closest',
        legend: {
            x: 1,
            xanchor: 'right',
            y: 1
        },
        template: 'plotly_dark',
        autosize: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function updateTransformationDescription(transformation) {
    const descriptionContainer = document.getElementById('transformationDescription');
    if (!descriptionContainer) return;
    
    let description = '';
    
    switch (transformation) {
        case 'log':
            description = `
                <div class="alert alert-info">
                    <h6>Logarithmic Transformation</h6>
                    <p>Applies natural logarithm (ln) to all concentration values. Useful for:</p>
                    <ul>
                        <li>Normalizing skewed concentration distributions</li>
                        <li>Linearizing exponential decay in elimination phase</li>
                        <li>Preparing data for bioequivalence analysis</li>
                    </ul>
                    <p class="mb-0"><strong>Note:</strong> Zero or negative concentrations will be replaced with a small positive value.</p>
                </div>
            `;
            break;
        case 'sqrt':
            description = `
                <div class="alert alert-info">
                    <h6>Square Root Transformation</h6>
                    <p>Applies square root to all concentration values. Useful for:</p>
                    <ul>
                        <li>Stabilizing variance in data with Poisson distribution</li>
                        <li>Less aggressive than log transformation for moderately skewed data</li>
                    </ul>
                    <p class="mb-0"><strong>Note:</strong> Negative concentrations will be replaced with zero.</p>
                </div>
            `;
            break;
        case 'normalize':
            description = `
                <div class="alert alert-info">
                    <h6>Normalization (0-1 Scale)</h6>
                    <p>Scales all concentrations to a 0-1 range. Useful for:</p>
                    <ul>
                        <li>Comparing profiles with different concentration scales</li>
                        <li>Standardizing data for machine learning algorithms</li>
                        <li>Visualization purposes</li>
                    </ul>
                    <p class="mb-0"><strong>Formula:</strong> (value - min) / (max - min)</p>
                </div>
            `;
            break;
        case 'inverse':
            description = `
                <div class="alert alert-info">
                    <h6>Inverse Transformation (1/x)</h6>
                    <p>Calculates 1/concentration for each value. Useful for:</p>
                    <ul>
                        <li>Linearizing certain pharmacokinetic relationships</li>
                        <li>Specialized PK models</li>
                    </ul>
                    <p class="mb-0"><strong>Note:</strong> Zero concentrations will be replaced with a small positive value.</p>
                </div>
            `;
            break;
        default:
            description = '<div class="alert alert-info">Select a transformation to see description</div>';
    }
    
    descriptionContainer.innerHTML = description;
}

function setupFilterControls() {
    const filterForm = document.getElementById('filterForm');
    if (!filterForm) return;
    
    // Add new filter criteria row
    const addFilterBtn = document.getElementById('addFilterBtn');
    if (addFilterBtn) {
        addFilterBtn.addEventListener('click', function() {
            addFilterRow();
        });
    }
    
    // Initial filter row
    addFilterRow();
}

function addFilterRow() {
    const filterContainer = document.getElementById('filterCriteria');
    if (!filterContainer) return;
    
    const rowId = Date.now(); // Unique ID for this row
    
    const rowHtml = `
        <div class="row mb-2 filter-row" id="filter-${rowId}">
            <div class="col-md-3">
                <select class="form-select" name="filter_field[]">
                    <option value="subject_id">Subject ID</option>
                    <option value="time">Time</option>
                    <option value="concentration">Concentration</option>
                </select>
            </div>
            <div class="col-md-3">
                <select class="form-select" name="filter_operator[]">
                    <option value="eq">Equals</option>
                    <option value="neq">Not Equals</option>
                    <option value="gt">Greater Than</option>
                    <option value="lt">Less Than</option>
                    <option value="gte">Greater Than or Equal</option>
                    <option value="lte">Less Than or Equal</option>
                    <option value="contains">Contains</option>
                </select>
            </div>
            <div class="col-md-4">
                <input type="text" class="form-control" name="filter_value[]" placeholder="Value">
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-danger" onclick="removeFilterRow('filter-${rowId}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
    
    // Append new row
    filterContainer.insertAdjacentHTML('beforeend', rowHtml);
}

function removeFilterRow(rowId) {
    const row = document.getElementById(rowId);
    if (row) {
        row.remove();
    }
}

function setupDataMergeControls() {
    const mergeForm = document.getElementById('mergeForm');
    if (!mergeForm) return;
    
    // Setup dataset selections
    const primaryDatasetSelect = document.getElementById('primary_dataset_id');
    const secondaryDatasetSelect = document.getElementById('secondary_dataset_id');
    
    if (primaryDatasetSelect && secondaryDatasetSelect) {
        // Prevent selecting the same dataset for both primary and secondary
        primaryDatasetSelect.addEventListener('change', function() {
            updateSecondaryOptions(this.value);
        });
        
        secondaryDatasetSelect.addEventListener('change', function() {
            updatePrimaryOptions(this.value);
        });
    }
    
    // Toggle merge options based on merge type
    const mergeTypeSelect = document.getElementById('merge_type');
    if (mergeTypeSelect) {
        mergeTypeSelect.addEventListener('change', function() {
            updateMergeOptions(this.value);
        });
        
        // Initialize with default
        if (mergeTypeSelect.value) {
            updateMergeOptions(mergeTypeSelect.value);
        }
    }
}

function updateSecondaryOptions(selectedPrimaryId) {
    const secondarySelect = document.getElementById('secondary_dataset_id');
    if (!secondarySelect) return;
    
    // Enable all options
    Array.from(secondarySelect.options).forEach(option => {
        option.disabled = false;
    });
    
    // Disable the option that matches the primary dataset
    const matchingOption = secondarySelect.querySelector(`option[value="${selectedPrimaryId}"]`);
    if (matchingOption) {
        matchingOption.disabled = true;
    }
    
    // If the currently selected secondary is now disabled, select the first enabled option
    if (secondarySelect.selectedOptions[0] && secondarySelect.selectedOptions[0].disabled) {
        const firstEnabled = Array.from(secondarySelect.options).find(opt => !opt.disabled);
        if (firstEnabled) {
            secondarySelect.value = firstEnabled.value;
        }
    }
}

function updatePrimaryOptions(selectedSecondaryId) {
    const primarySelect = document.getElementById('primary_dataset_id');
    if (!primarySelect) return;
    
    // Enable all options
    Array.from(primarySelect.options).forEach(option => {
        option.disabled = false;
    });
    
    // Disable the option that matches the secondary dataset
    const matchingOption = primarySelect.querySelector(`option[value="${selectedSecondaryId}"]`);
    if (matchingOption) {
        matchingOption.disabled = true;
    }
    
    // If the currently selected primary is now disabled, select the first enabled option
    if (primarySelect.selectedOptions[0] && primarySelect.selectedOptions[0].disabled) {
        const firstEnabled = Array.from(primarySelect.options).find(opt => !opt.disabled);
        if (firstEnabled) {
            primarySelect.value = firstEnabled.value;
        }
    }
}

function updateMergeOptions(mergeType) {
    const subjectMappingSection = document.getElementById('subjectMappingSection');
    const timeAlignmentSection = document.getElementById('timeAlignmentSection');
    
    if (!subjectMappingSection || !timeAlignmentSection) return;
    
    if (mergeType === 'append') {
        subjectMappingSection.style.display = 'none';
        timeAlignmentSection.style.display = 'none';
    } else if (mergeType === 'merge') {
        subjectMappingSection.style.display = 'block';
        timeAlignmentSection.style.display = 'block';
    } else if (mergeType === 'join') {
        subjectMappingSection.style.display = 'block';
        timeAlignmentSection.style.display = 'none';
    }
}
