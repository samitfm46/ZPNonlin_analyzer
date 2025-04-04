// Models functionality for PK Analysis Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize models functionality
    initModels();
});

function initModels() {
    // Setup model type and absorption type interactions
    setupModelTypeInteractions();
    
    // Setup model parameters defaults
    setupParameterDefaults();
    
    // Initialize tooltips for model parameters
    initializeParameterTooltips();
}

function setupModelTypeInteractions() {
    const modelTypeSelect = document.getElementById('model_type');
    const absorptionTypeSelect = document.getElementById('absorption');
    
    if (modelTypeSelect && absorptionTypeSelect) {
        modelTypeSelect.addEventListener('change', function() {
            updateAbsorptionOptions(this.value);
            updateParameterFields(this.value, absorptionTypeSelect.value);
            
            // Update model description
            updateModelDescription(this.value, absorptionTypeSelect.value);
        });
        
        absorptionTypeSelect.addEventListener('change', function() {
            updateParameterFields(modelTypeSelect.value, this.value);
            
            // Update model description
            updateModelDescription(modelTypeSelect.value, this.value);
        });
        
        // Initialize if values already selected
        if (modelTypeSelect.value && absorptionTypeSelect.value) {
            updateParameterFields(modelTypeSelect.value, absorptionTypeSelect.value);
            updateModelDescription(modelTypeSelect.value, absorptionTypeSelect.value);
        }
    }
}

function updateAbsorptionOptions(modelType) {
    const absorptionSelect = document.getElementById('absorption');
    if (!absorptionSelect) return;
    
    // Store current selection if possible
    const currentSelection = absorptionSelect.value;
    
    // Clear current options
    absorptionSelect.innerHTML = '';
    
    // Add appropriate options based on model type
    if (modelType === 'one_compartment') {
        addOption(absorptionSelect, 'iv_bolus', 'IV Bolus');
        addOption(absorptionSelect, 'first-order', 'First-Order Absorption');
        addOption(absorptionSelect, 'zero-order', 'Zero-Order Absorption');
    } else if (modelType === 'two_compartment') {
        addOption(absorptionSelect, 'iv_bolus', 'IV Bolus');
        addOption(absorptionSelect, 'first-order', 'First-Order Absorption');
    }
    
    // Try to restore previous selection if it exists in new options
    if (currentSelection) {
        const option = absorptionSelect.querySelector(`option[value="${currentSelection}"]`);
        if (option) {
            absorptionSelect.value = currentSelection;
        } else {
            // Otherwise select first option
            absorptionSelect.selectedIndex = 0;
        }
    } else {
        // Select first option if no previous selection
        absorptionSelect.selectedIndex = 0;
    }
}

function addOption(selectElement, value, text) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = text;
    selectElement.appendChild(option);
}

function updateParameterFields(modelType, absorptionType) {
    const parameterContainer = document.getElementById('modelParameters');
    if (!parameterContainer) return;
    
    // Default parameter fields
    let parameterFields = [];
    
    // Define parameters based on model type and absorption
    if (modelType === 'one_compartment') {
        if (absorptionType === 'iv_bolus') {
            parameterFields = [
                { name: 'V', label: 'Volume of Distribution (V)', defaultValue: '1', min: '0.001', step: '0.1', unit: 'L' },
                { name: 'k', label: 'Elimination Rate Constant (k)', defaultValue: '0.1', min: '0.001', step: '0.01', unit: 'h⁻¹' }
            ];
        } else if (absorptionType === 'first-order') {
            parameterFields = [
                { name: 'ka', label: 'Absorption Rate Constant (ka)', defaultValue: '1', min: '0.001', step: '0.1', unit: 'h⁻¹' },
                { name: 'V', label: 'Volume of Distribution (V)', defaultValue: '1', min: '0.001', step: '0.1', unit: 'L' },
                { name: 'k', label: 'Elimination Rate Constant (k)', defaultValue: '0.1', min: '0.001', step: '0.01', unit: 'h⁻¹' },
                { name: 'F', label: 'Bioavailability (F)', defaultValue: '1', min: '0', max: '1', step: '0.01', unit: 'fraction' }
            ];
        } else if (absorptionType === 'zero-order') {
            parameterFields = [
                { name: 'k0', label: 'Zero-Order Rate (k0)', defaultValue: '1', min: '0.001', step: '0.1', unit: 'mg/h' },
                { name: 'V', label: 'Volume of Distribution (V)', defaultValue: '1', min: '0.001', step: '0.1', unit: 'L' },
                { name: 'k', label: 'Elimination Rate Constant (k)', defaultValue: '0.1', min: '0.001', step: '0.01', unit: 'h⁻¹' },
                { name: 'tdur', label: 'Duration of Infusion (tdur)', defaultValue: '1', min: '0.1', step: '0.1', unit: 'h' }
            ];
        }
    } else if (modelType === 'two_compartment') {
        if (absorptionType === 'iv_bolus') {
            parameterFields = [
                { name: 'A', label: 'Intercept for First Compartment (A)', defaultValue: '1', min: '0.001', step: '0.1', unit: 'ng/mL' },
                { name: 'alpha', label: 'Hybrid Rate Constant (α)', defaultValue: '0.5', min: '0.001', step: '0.01', unit: 'h⁻¹' },
                { name: 'B', label: 'Intercept for Second Compartment (B)', defaultValue: '0.5', min: '0.001', step: '0.1', unit: 'ng/mL' },
                { name: 'beta', label: 'Hybrid Rate Constant (β)', defaultValue: '0.1', min: '0.001', step: '0.01', unit: 'h⁻¹' }
            ];
        } else if (absorptionType === 'first-order') {
            parameterFields = [
                { name: 'ka', label: 'Absorption Rate Constant (ka)', defaultValue: '1', min: '0.001', step: '0.1', unit: 'h⁻¹' },
                { name: 'A', label: 'Intercept for First Compartment (A)', defaultValue: '1', min: '0.001', step: '0.1', unit: 'ng/mL' },
                { name: 'alpha', label: 'Hybrid Rate Constant (α)', defaultValue: '0.5', min: '0.001', step: '0.01', unit: 'h⁻¹' },
                { name: 'B', label: 'Intercept for Second Compartment (B)', defaultValue: '0.5', min: '0.001', step: '0.1', unit: 'ng/mL' },
                { name: 'beta', label: 'Hybrid Rate Constant (β)', defaultValue: '0.1', min: '0.001', step: '0.01', unit: 'h⁻¹' }
            ];
        }
    }
    
    // Generate HTML for parameter fields
    let html = '<div class="row">';
    
    parameterFields.forEach((param, index) => {
        html += `
            <div class="col-md-6 mb-3">
                <label for="${param.name}" class="form-label">
                    ${param.label}
                    <i class="fas fa-info-circle ms-1 text-info" 
                       data-bs-toggle="tooltip" 
                       title="Initial estimate for ${param.label}"></i>
                </label>
                <div class="input-group">
                    <input type="number" 
                           class="form-control" 
                           id="${param.name}" 
                           name="${param.name}"
                           value="${param.defaultValue}"
                           min="${param.min || '0'}"
                           ${param.max ? `max="${param.max}"` : ''}
                           step="${param.step || '0.01'}">
                    <span class="input-group-text">${param.unit}</span>
                </div>
            </div>
        `;
        
        // Create a new row after every 2 parameters
        if ((index + 1) % 2 === 0 && index < parameterFields.length - 1) {
            html += '</div><div class="row">';
        }
    });
    
    // Close the row
    html += '</div>';
    
    // Update the container
    parameterContainer.innerHTML = html;
    
    // Initialize tooltips
    const tooltips = parameterContainer.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltipEl => {
        new bootstrap.Tooltip(tooltipEl);
    });
}

function setupParameterDefaults() {
    // These are default parameter estimates that can be applied
    // when the user clicks a "Use default estimates" button
    const defaultParamsBtn = document.getElementById('useDefaultParamsBtn');
    if (defaultParamsBtn) {
        defaultParamsBtn.addEventListener('click', function() {
            const modelType = document.getElementById('model_type').value;
            const absorptionType = document.getElementById('absorption').value;
            
            updateParameterFields(modelType, absorptionType);
        });
    }
}

function initializeParameterTooltips() {
    // Tooltips for model fitting parameters with more detailed explanations
    const tooltipData = {
        'weighting_scheme': 'Choose how to weight residuals during fitting. Uniform weighting treats all points equally, while 1/Y and 1/Y² give less weight to higher concentration values.',
        'max_iterations': 'Maximum number of iterations for the optimization algorithm. Higher values may improve fit but increase computation time.',
        'convergence_criteria': 'Threshold for convergence. Lower values result in more precise fits but may require more iterations.',
        'lambda_z_points': 'Number of terminal points to use for calculating elimination rate constant.',
        'initial_estimates': 'Starting values for the optimization algorithm. Better initial estimates can improve convergence.'
    };
    
    // Apply tooltips to elements with matching IDs
    Object.entries(tooltipData).forEach(([id, text]) => {
        const element = document.getElementById(id);
        if (element) {
            const tooltipIcon = document.createElement('i');
            tooltipIcon.className = 'fas fa-info-circle ms-1 text-info';
            tooltipIcon.setAttribute('data-bs-toggle', 'tooltip');
            tooltipIcon.setAttribute('title', text);
            
            // Append to label if exists
            const label = element.previousElementSibling;
            if (label && label.tagName === 'LABEL') {
                label.appendChild(tooltipIcon);
            }
        }
    });
    
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltipEl => {
        new bootstrap.Tooltip(tooltipEl);
    });
}

function updateModelDescription(modelType, absorptionType) {
    const descriptionContainer = document.getElementById('modelDescription');
    if (!descriptionContainer) return;
    
    let description = '';
    let equation = '';
    
    // Determine description and equation based on model and absorption type
    if (modelType === 'one_compartment') {
        if (absorptionType === 'iv_bolus') {
            description = `
                <p>The one-compartment IV bolus model describes drug concentration over time following instantaneous injection into the bloodstream.</p>
                <p>The body is treated as a single homogeneous compartment where the drug distributes instantaneously.</p>
                <p>Elimination occurs via first-order kinetics from the central compartment.</p>
            `;
            equation = `C(t) = \\frac{Dose}{V} \\cdot e^{-k \\cdot t}`;
        }
        else if (absorptionType === 'first-order') {
            description = `
                <p>The one-compartment model with first-order absorption describes drug concentration following oral or non-instantaneous administration.</p>
                <p>Drug is absorbed from the administration site at a rate proportional to the amount remaining to be absorbed (first-order process).</p>
                <p>Elimination occurs via first-order kinetics from the central compartment.</p>
            `;
            equation = `C(t) = \\frac{F \\cdot Dose \\cdot k_a}{V \\cdot (k_a - k)} \\cdot (e^{-k \\cdot t} - e^{-k_a \\cdot t})`;
        }
        else if (absorptionType === 'zero-order') {
            description = `
                <p>The one-compartment model with zero-order absorption describes drug concentration following constant-rate infusion or controlled-release formulations.</p>
                <p>Drug enters the circulation at a constant rate, independent of the amount remaining to be absorbed.</p>
                <p>Elimination occurs via first-order kinetics from the central compartment.</p>
            `;
            equation = `
                C(t) = \\begin{cases}
                \\frac{k_0}{V \\cdot k} \\cdot (1 - e^{-k \\cdot t}) & \\text{for } t \\leq t_{dur} \\\\
                \\frac{k_0}{V \\cdot k} \\cdot (1 - e^{-k \\cdot t_{dur}}) \\cdot e^{-k \\cdot (t - t_{dur})} & \\text{for } t > t_{dur}
                \\end{cases}
            `;
        }
    }
    else if (modelType === 'two_compartment') {
        if (absorptionType === 'iv_bolus') {
            description = `
                <p>The two-compartment IV bolus model describes drug concentration when distribution occurs into two compartments with different characteristics.</p>
                <p>The central compartment represents blood and highly perfused tissues, while the peripheral compartment represents less perfused tissues.</p>
                <p>Drug transfers between compartments, with elimination occurring only from the central compartment.</p>
            `;
            equation = `C(t) = A \\cdot e^{-\\alpha \\cdot t} + B \\cdot e^{-\\beta \\cdot t}`;
        }
        else if (absorptionType === 'first-order') {
            description = `
                <p>The two-compartment model with first-order absorption combines multi-compartmental distribution with non-instantaneous drug input.</p>
                <p>Drug is absorbed from the administration site via first-order kinetics into the central compartment.</p>
                <p>Distribution occurs between central and peripheral compartments, with elimination from the central compartment.</p>
            `;
            equation = `C(t) = \\frac{F \\cdot Dose \\cdot k_a}{V} \\cdot [\\frac{A}{k_a - \\alpha} \\cdot (e^{-\\alpha \\cdot t} - e^{-k_a \\cdot t}) + \\frac{B}{k_a - \\beta} \\cdot (e^{-\\beta \\cdot t} - e^{-k_a \\cdot t})]`;
        }
    }
    
    // Render the description and equation
    let html = `
        <div class="alert alert-info">
            <h6 class="alert-heading">Model Description</h6>
            ${description}
            <hr>
            <div class="text-center">
                <p><strong>Equation:</strong></p>
                <div id="modelEquation">\\[ ${equation} \\]</div>
            </div>
        </div>
    `;
    
    descriptionContainer.innerHTML = html;
    
    // Render the equation with MathJax if available
    if (typeof MathJax !== 'undefined') {
        MathJax.typeset(['#modelEquation']);
    }
}

// Parameter explanations for tooltips and help text
const parameterExplanations = {
    'V': 'Volume of distribution represents the theoretical volume into which the drug is distributed to produce the observed concentration.',
    'k': 'Elimination rate constant represents the fraction of drug eliminated per unit time. Related to half-life by t½ = ln(2)/k.',
    'ka': 'Absorption rate constant represents the fraction of drug absorbed per unit time from the administration site.',
    'F': 'Bioavailability represents the fraction of administered dose that reaches systemic circulation.',
    'k0': 'Zero-order absorption rate represents the constant amount of drug entering the system per unit time.',
    'tdur': 'Duration of zero-order input, such as an IV infusion or controlled release period.',
    'A': 'Coefficient associated with the fast distribution/elimination phase in a two-compartment model.',
    'B': 'Coefficient associated with the slow distribution/elimination phase in a two-compartment model.',
    'alpha': 'Hybrid rate constant for the fast phase in a two-compartment model.',
    'beta': 'Hybrid rate constant for the slow phase in a two-compartment model.',
    'k10': 'Elimination rate constant from central compartment in a multi-compartmental model.',
    'k12': 'Transfer rate constant from central to peripheral compartment.',
    'k21': 'Transfer rate constant from peripheral to central compartment.',
    'Vss': 'Volume of distribution at steady state in a multi-compartmental model.'
};

function getParameterDescription(paramName) {
    return parameterExplanations[paramName] || 'Parameter description not available';
}
