// Main JavaScript functionality for PK Analysis App

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Setup navigation click handlers
    setupNavigation();

    // Setup form validation
    setupFormValidation();

    // Setup file upload preview
    setupFileUploadPreview();

    // Setup analysis-specific functionality
    setupNCAFunctionality();
    setupCompartmentalFunctionality();
    setupBioequivalenceFunctionality();
    setupDataProcessingFunctionality();
    setupStatisticsFunctionality();
    setupReportsFunctionality();

    // Load plots if there's analysis data
    loadAnalysisPlots();
});

function setupNavigation() {
    // Handle sidebar navigation
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // If link has no href (used as tab toggle), prevent default
            if (!this.getAttribute('href') || this.getAttribute('href') === '#') {
                e.preventDefault();
            }
        });
    });

    // Setup tab navigation if tabs exist
    const tabEls = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEls.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', function(event) {
            // Store the active tab in localStorage
            localStorage.setItem('activeTab', event.target.getAttribute('data-bs-target'));
        });
    });

    // Restore active tab if it exists
    const activeTab = localStorage.getItem('activeTab');
    if (activeTab) {
        const tabEl = document.querySelector(`button[data-bs-target="${activeTab}"]`);
        if (tabEl) {
            const tab = new bootstrap.Tab(tabEl);
            tab.show();
        }
    }
}

function setupFormValidation() {
    // Find all forms with the 'needs-validation' class
    const forms = document.querySelectorAll('.needs-validation');

    // Loop over them and prevent submission if they're invalid
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

function setupFileUploadPreview() {
    // Setup file input change handler
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileLabel = this.nextElementSibling;
            if (fileLabel && fileLabel.classList.contains('form-file-label')) {
                if (this.files.length > 0) {
                    fileLabel.textContent = this.files[0].name;
                } else {
                    fileLabel.textContent = 'Choose file...';
                }
            }

            // If this is a dataset upload, show file preview
            if (this.id === 'datasetFile') {
                previewDatasetFile(this);
            }
        });
    });
}

function previewDatasetFile(fileInput) {
    if (fileInput.files.length === 0) return;

    const file = fileInput.files[0];
    const reader = new FileReader();

    reader.onload = function(e) {
        let data;
        let headers;
        let rows = [];

        // Parse CSV data
        if (file.name.endsWith('.csv')) {
            const csvData = e.target.result;
            const lines = csvData.split('\n');
            headers = lines[0].split(',');
            
            for (let i = 1; i < Math.min(lines.length, 6); i++) {
                if (lines[i].trim()) {
                    rows.push(lines[i].split(','));
                }
            }
        } 
        // Parse Excel data (simplified - in reality, would need a library like SheetJS)
        else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
            // For demo, show message that preview is not available for Excel
            const previewElement = document.getElementById('datasetPreview');
            if (previewElement) {
                previewElement.innerHTML = '<div class="alert alert-info">Preview not available for Excel files. Please upload to see data.</div>';
            }
            return;
        }

        // Create preview table
        const previewElement = document.getElementById('datasetPreview');
        if (previewElement && headers && rows.length > 0) {
            let tableHTML = '<table class="table table-sm table-striped">';
            
            // Add header row
            tableHTML += '<thead><tr>';
            headers.forEach(header => {
                tableHTML += `<th>${header.trim()}</th>`;
            });
            tableHTML += '</tr></thead>';
            
            // Add data rows
            tableHTML += '<tbody>';
            rows.forEach(row => {
                tableHTML += '<tr>';
                row.forEach(cell => {
                    tableHTML += `<td>${cell.trim()}</td>`;
                });
                tableHTML += '</tr>';
            });
            tableHTML += '</tbody></table>';
            
            previewElement.innerHTML = tableHTML;
        }
    };

    reader.readAsText(file);
}

function setupNCAFunctionality() {
    // Add NCA-specific functionality
    const ncaMethodSelect = document.getElementById('ncaMethod');
    if (ncaMethodSelect) {
        ncaMethodSelect.addEventListener('change', function() {
            // Additional setup based on selected method could go here
        });
    }
}

function setupCompartmentalFunctionality() {
    // Setup model type and absorption type interactions
    const modelTypeSelect = document.getElementById('modelType');
    const absorptionTypeSelect = document.getElementById('absorptionType');
    
    if (modelTypeSelect && absorptionTypeSelect) {
        modelTypeSelect.addEventListener('change', function() {
            updateAbsorptionOptions(this.value);
        });
        
        // Initialize absorption options
        if (modelTypeSelect.value) {
            updateAbsorptionOptions(modelTypeSelect.value);
        }
    }
}

function updateAbsorptionOptions(modelType) {
    const absorptionTypeSelect = document.getElementById('absorptionType');
    if (!absorptionTypeSelect) return;
    
    // Clear current options
    absorptionTypeSelect.innerHTML = '';
    
    // Add appropriate options based on model type
    if (modelType === 'one_compartment') {
        addOption(absorptionTypeSelect, 'iv_bolus', 'IV Bolus');
        addOption(absorptionTypeSelect, 'first-order', 'First-Order Absorption');
        addOption(absorptionTypeSelect, 'zero-order', 'Zero-Order Absorption');
    } else if (modelType === 'two_compartment') {
        addOption(absorptionTypeSelect, 'iv_bolus', 'IV Bolus');
        addOption(absorptionTypeSelect, 'first-order', 'First-Order Absorption');
    }
    
    // Select first option
    if (absorptionTypeSelect.options.length > 0) {
        absorptionTypeSelect.selectedIndex = 0;
    }
}

function addOption(selectElement, value, text) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = text;
    selectElement.appendChild(option);
}

function setupBioequivalenceFunctionality() {
    // Setup dataset selection interaction
    const testDatasetSelect = document.getElementById('testDatasetId');
    const referenceDatasetSelect = document.getElementById('referenceDatasetId');
    
    if (testDatasetSelect && referenceDatasetSelect) {
        // Prevent selecting the same dataset for both test and reference
        testDatasetSelect.addEventListener('change', function() {
            updateReferenceOptions(this.value);
        });
        
        referenceDatasetSelect.addEventListener('change', function() {
            updateTestOptions(this.value);
        });
    }
}

function updateReferenceOptions(selectedTestId) {
    const referenceSelect = document.getElementById('referenceDatasetId');
    if (!referenceSelect) return;
    
    // Enable all options
    Array.from(referenceSelect.options).forEach(option => {
        option.disabled = false;
    });
    
    // Disable the option that matches the test dataset
    const matchingOption = referenceSelect.querySelector(`option[value="${selectedTestId}"]`);
    if (matchingOption) {
        matchingOption.disabled = true;
    }
    
    // If the currently selected reference is now disabled, select the first enabled option
    if (referenceSelect.selectedOptions[0].disabled) {
        const firstEnabled = Array.from(referenceSelect.options).find(opt => !opt.disabled);
        if (firstEnabled) {
            referenceSelect.value = firstEnabled.value;
        }
    }
}

function updateTestOptions(selectedReferenceId) {
    const testSelect = document.getElementById('testDatasetId');
    if (!testSelect) return;
    
    // Enable all options
    Array.from(testSelect.options).forEach(option => {
        option.disabled = false;
    });
    
    // Disable the option that matches the reference dataset
    const matchingOption = testSelect.querySelector(`option[value="${selectedReferenceId}"]`);
    if (matchingOption) {
        matchingOption.disabled = true;
    }
    
    // If the currently selected test is now disabled, select the first enabled option
    if (testSelect.selectedOptions[0].disabled) {
        const firstEnabled = Array.from(testSelect.options).find(opt => !opt.disabled);
        if (firstEnabled) {
            testSelect.value = firstEnabled.value;
        }
    }
}

function setupDataProcessingFunctionality() {
    // Setup transformation selection
    const transformationSelect = document.getElementById('transformation');
    if (transformationSelect) {
        transformationSelect.addEventListener('change', function() {
            // Could add preview or explanation of the selected transformation
            const transformInfo = document.getElementById('transformationInfo');
            if (transformInfo) {
                let infoText = '';
                
                switch(this.value) {
                    case 'log':
                        infoText = 'Log transformation: Will apply natural logarithm to concentration values.';
                        break;
                    case 'sqrt':
                        infoText = 'Square root transformation: Will apply square root to concentration values.';
                        break;
                    case 'normalize':
                        infoText = 'Normalization: Will scale concentration values to a 0-1 range.';
                        break;
                    case 'inverse':
                        infoText = 'Inverse transformation: Will calculate 1/concentration for each value.';
                        break;
                }
                
                transformInfo.textContent = infoText;
            }
        });
    }
}

function setupStatisticsFunctionality() {
    // Setup statistics type selection
    const statTypeSelect = document.getElementById('statType');
    if (statTypeSelect) {
        statTypeSelect.addEventListener('change', function() {
            // Could add explanation of the selected statistical test
            const statInfo = document.getElementById('statTypeInfo');
            if (statInfo) {
                let infoText = '';
                
                switch(this.value) {
                    case 'ttest':
                        infoText = 'T-test: Compare means of concentrations at each timepoint.';
                        break;
                    case 'anova':
                        infoText = 'ANOVA: Analyze variance in concentrations across subjects at each timepoint.';
                        break;
                    case 'regression':
                        infoText = 'Regression: Perform linear regression on log-transformed concentration data for each subject.';
                        break;
                }
                
                statInfo.textContent = infoText;
            }
        });
    }
}

function setupReportsFunctionality() {
    // Setup report type selection
    const reportTypeSelect = document.getElementById('reportType');
    if (reportTypeSelect) {
        reportTypeSelect.addEventListener('change', function() {
            // Could preview report format or add functionality based on report type
        });
    }
}

function loadAnalysisPlots() {
    // Check if we have an analysis to display
    const analysisIdElement = document.getElementById('analysisId');
    if (!analysisIdElement) return;
    
    const analysisId = analysisIdElement.value;
    if (!analysisId) return;
    
    // Fetch analysis data for plotting
    fetch(`/api/analysis/${analysisId}/plot-data`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Render appropriate plots based on analysis type
                switch(data.type) {
                    case 'NCA':
                        renderNCAPlots(data.data);
                        break;
                    case 'Compartmental':
                        renderCompartmentalPlots(data.data);
                        break;
                    case 'Bioequivalence':
                        renderBioequivalencePlots(data.data);
                        break;
                    case 'Statistics':
                        renderStatisticsPlots(data.data);
                        break;
                }
            }
        })
        .catch(error => {
            console.error('Error fetching analysis data:', error);
        });
}
