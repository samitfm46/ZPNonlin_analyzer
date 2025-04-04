import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# Define compartmental models
def one_compartment_iv_bolus(t, V, k):
    """One-compartment model with IV bolus administration."""
    return (1/V) * np.exp(-k * t)

def one_compartment_first_order(t, ka, V, k, F=1, D=1):
    """One-compartment model with first-order absorption."""
    # F is bioavailability, D is dose
    return (F * D * ka) / (V * (ka - k)) * (np.exp(-k * t) - np.exp(-ka * t))

def one_compartment_zero_order(t, k0, V, k, tdur):
    """One-compartment model with zero-order absorption."""
    result = np.zeros_like(t, dtype=float)
    
    # During infusion (t <= tdur)
    mask_during = t <= tdur
    result[mask_during] = (k0 / (V * k)) * (1 - np.exp(-k * t[mask_during]))
    
    # After infusion (t > tdur)
    mask_after = t > tdur
    result[mask_after] = (k0 / (V * k)) * (1 - np.exp(-k * tdur)) * np.exp(-k * (t[mask_after] - tdur))
    
    return result

def two_compartment_iv_bolus(t, A, alpha, B, beta):
    """Two-compartment model with IV bolus administration."""
    return A * np.exp(-alpha * t) + B * np.exp(-beta * t)

def two_compartment_first_order(t, ka, A, alpha, B, beta):
    """Two-compartment model with first-order absorption."""
    term1 = A * ka / (ka - alpha) * (np.exp(-alpha * t) - np.exp(-ka * t))
    term2 = B * ka / (ka - beta) * (np.exp(-beta * t) - np.exp(-ka * t))
    return term1 + term2

def calculate_parameters(model_type, params):
    """Calculate derived PK parameters from model parameters."""
    derived_params = {}
    
    if model_type == 'one_compartment_iv_bolus':
        V, k = params
        derived_params['V'] = V
        derived_params['k'] = k
        derived_params['CL'] = V * k
        derived_params['half_life'] = np.log(2) / k
        
    elif model_type == 'one_compartment_first_order':
        ka, V, k = params[:3]
        derived_params['ka'] = ka
        derived_params['V'] = V
        derived_params['k'] = k
        derived_params['CL'] = V * k
        derived_params['absorption_half_life'] = np.log(2) / ka
        derived_params['elimination_half_life'] = np.log(2) / k
        derived_params['tmax'] = np.log(ka / k) / (ka - k) if ka != k else 1 / k
        
    elif model_type == 'one_compartment_zero_order':
        k0, V, k, tdur = params
        derived_params['k0'] = k0
        derived_params['V'] = V
        derived_params['k'] = k
        derived_params['tdur'] = tdur
        derived_params['CL'] = V * k
        derived_params['elimination_half_life'] = np.log(2) / k
        derived_params['tmax'] = tdur if k * tdur < np.log(2) else -np.log(k * tdur) / k
        
    elif model_type == 'two_compartment_iv_bolus':
        A, alpha, B, beta = params
        derived_params['A'] = A
        derived_params['alpha'] = alpha
        derived_params['B'] = B
        derived_params['beta'] = beta
        derived_params['k10'] = (A * beta + B * alpha) / (A + B)
        derived_params['k12'] = alpha + beta - derived_params['k10']
        derived_params['k21'] = (alpha * beta) / derived_params['k10']
        derived_params['V1'] = 1 / (A + B)
        derived_params['V2'] = derived_params['V1'] * derived_params['k12'] / derived_params['k21']
        derived_params['CL'] = derived_params['V1'] * derived_params['k10']
        derived_params['alpha_half_life'] = np.log(2) / alpha
        derived_params['beta_half_life'] = np.log(2) / beta
        
    elif model_type == 'two_compartment_first_order':
        ka, A, alpha, B, beta = params
        derived_params['ka'] = ka
        derived_params['A'] = A
        derived_params['alpha'] = alpha
        derived_params['B'] = B
        derived_params['beta'] = beta
        derived_params['k10'] = (A * beta + B * alpha) / (A + B)
        derived_params['k12'] = alpha + beta - derived_params['k10']
        derived_params['k21'] = (alpha * beta) / derived_params['k10']
        derived_params['V1'] = 1 / (A + B)
        derived_params['V2'] = derived_params['V1'] * derived_params['k12'] / derived_params['k21']
        derived_params['CL'] = derived_params['V1'] * derived_params['k10']
        derived_params['absorption_half_life'] = np.log(2) / ka
        derived_params['alpha_half_life'] = np.log(2) / alpha
        derived_params['beta_half_life'] = np.log(2) / beta
    
    return derived_params

def calculate_goodness_of_fit(observed, predicted):
    """Calculate goodness-of-fit metrics."""
    residuals = observed - predicted
    
    # Sum of squared residuals
    ssr = np.sum(residuals ** 2)
    
    # Sum of squares total
    sst = np.sum((observed - np.mean(observed)) ** 2)
    
    # R-squared
    r_squared = 1 - (ssr / sst) if sst != 0 else 0
    
    # Adjusted R-squared (will need the number of parameters p)
    # adj_r_squared = 1 - ((1 - r_squared) * (n - 1) / (n - p - 1))
    
    # Root mean squared error
    rmse = np.sqrt(np.mean(residuals ** 2))
    
    # Akaike Information Criterion (AIC)
    n = len(observed)
    p = 2  # Number of parameters - would need to be adjusted based on model
    aic = n * np.log(ssr / n) + 2 * p
    
    # Coefficient of variation
    cv = 100 * np.std(residuals) / np.mean(observed) if np.mean(observed) != 0 else float('inf')
    
    return {
        'r_squared': r_squared,
        'rmse': rmse,
        'aic': aic,
        'cv_percent': cv,
        'residuals': residuals.tolist()
    }

def fit_compartmental_model(subjects_data, model_type='one_compartment_first_order', dose=1, absorption='first-order'):
    """
    Fit compartmental models to concentration-time data.
    
    Parameters:
    - subjects_data: Dictionary with subject IDs as keys and dicts with 'times' and 'concentrations' as values
    - model_type: Type of compartmental model to fit
    - dose: Dose administered
    - absorption: Absorption type for oral models ('first-order', 'zero-order')
    
    Returns:
    - Dictionary with fitted parameters and derived parameters for each subject
    """
    results = {}
    
    # Select model function based on model_type
    if model_type == 'one_compartment':
        if absorption == 'iv_bolus':
            model_func = one_compartment_iv_bolus
            p0 = [1, 0.1]  # Initial guess for V, k
        elif absorption == 'first-order':
            model_func = one_compartment_first_order
            p0 = [1.0, 1.0, 0.1, 1.0, dose]  # Initial guess for ka, V, k, F, D
        elif absorption == 'zero-order':
            model_func = one_compartment_zero_order
            p0 = [0.5, 1.0, 0.1, 1.0]  # Initial guess for k0, V, k, tdur
        else:
            raise ValueError(f"Unknown absorption type: {absorption}")
    
    elif model_type == 'two_compartment':
        if absorption == 'iv_bolus':
            model_func = two_compartment_iv_bolus
            p0 = [1.0, 0.5, 0.5, 0.1]  # Initial guess for A, alpha, B, beta
        elif absorption == 'first-order':
            model_func = two_compartment_first_order
            p0 = [1.0, 1.0, 0.5, 0.5, 0.1]  # Initial guess for ka, A, alpha, B, beta
        else:
            raise ValueError(f"Unknown absorption type: {absorption}")
    
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    for subject_id, data in subjects_data.items():
        times = np.array(data['times'])
        concentrations = np.array(data['concentrations'])
        
        # Sort data by time
        sorted_indices = np.argsort(times)
        times = times[sorted_indices]
        concentrations = concentrations[sorted_indices]
        
        # Filter out invalid data (negative or zero concentrations for log transformation)
        valid_idx = concentrations > 0
        if not np.all(valid_idx):
            print(f"Warning: Removed {np.sum(~valid_idx)} non-positive concentration values for subject {subject_id}")
            times = times[valid_idx]
            concentrations = concentrations[valid_idx]
        
        if len(times) < len(p0):
            print(f"Warning: Not enough data points for subject {subject_id} to fit model.")
            continue
        
        try:
            # Fit model
            if model_type == 'one_compartment' and absorption == 'first-order':
                # Fix dose and bioavailability
                def model_fixed_dose(t, ka, V, k):
                    return one_compartment_first_order(t, ka, V, k, F=1, D=dose)
                
                popt, pcov = curve_fit(model_fixed_dose, times, concentrations, p0=p0[:3], 
                                       bounds=([0.01, 0.01, 0.001], [10, 100, 1]))
                
                # Add fixed parameters
                popt = np.append(popt, [1, dose])
                
                # Generate prediction times (more points for smooth curve)
                pred_times = np.linspace(0, max(times)*1.2, 100)
                predictions = model_fixed_dose(pred_times, *popt[:3])
                
                # Calculate observed vs predicted for goodness-of-fit
                obs_predictions = model_fixed_dose(times, *popt[:3])
                
            elif model_type == 'one_compartment' and absorption == 'zero-order':
                # Need to estimate infusion duration
                p0[3] = max(times) * 0.3  # Initial guess for tdur
                
                popt, pcov = curve_fit(one_compartment_zero_order, times, concentrations, p0=p0, 
                                       bounds=([0.01, 0.01, 0.001, 0.1], [10, 100, 1, max(times)]))
                
                # Generate prediction times
                pred_times = np.linspace(0, max(times)*1.2, 100)
                predictions = one_compartment_zero_order(pred_times, *popt)
                
                # Calculate observed vs predicted
                obs_predictions = one_compartment_zero_order(times, *popt)
                
            else:
                popt, pcov = curve_fit(model_func, times, concentrations, p0=p0, 
                                       bounds=([0.01] * len(p0), [10] * len(p0)))
                
                # Generate prediction times
                pred_times = np.linspace(0, max(times)*1.2, 100)
                predictions = model_func(pred_times, *popt)
                
                # Calculate observed vs predicted
                obs_predictions = model_func(times, *popt)
            
            # Calculate parameter error (standard deviation)
            perr = np.sqrt(np.diag(pcov))
            
            # Calculate derived parameters
            derived_params = calculate_parameters(f"{model_type}_{absorption}", popt)
            
            # Calculate goodness-of-fit metrics
            gof = calculate_goodness_of_fit(concentrations, obs_predictions)
            
            # Store results
            results[subject_id] = {
                'fitted_parameters': popt.tolist(),
                'parameter_errors': perr.tolist(),
                'derived_parameters': derived_params,
                'goodness_of_fit': gof,
                'observed_times': times.tolist(),
                'observed_concentrations': concentrations.tolist(),
                'predicted_times': pred_times.tolist(),
                'predicted_concentrations': predictions.tolist()
            }
            
        except Exception as e:
            print(f"Error fitting model for subject {subject_id}: {e}")
            results[subject_id] = {
                'error': str(e)
            }
    
    # Calculate mean and SD of parameters across subjects
    if len(results) > 0:
        # Get parameter names from the first successful fit
        successful_subject = next((s for s in results if 'error' not in results[s]), None)
        
        if successful_subject:
            derived_param_keys = results[successful_subject]['derived_parameters'].keys()
            
            # Initialize summary
            summary = {'derived_parameters': {}}
            
            # Calculate statistics for each parameter
            for param in derived_param_keys:
                values = [results[subject_id]['derived_parameters'][param] 
                          for subject_id in results 
                          if 'derived_parameters' in results[subject_id] and param in results[subject_id]['derived_parameters']]
                
                if values:
                    summary['derived_parameters'][f'{param}_mean'] = np.mean(values)
                    summary['derived_parameters'][f'{param}_sd'] = np.std(values)
                    summary['derived_parameters'][f'{param}_cv'] = 100 * np.std(values) / np.mean(values) if np.mean(values) != 0 else None
                    summary['derived_parameters'][f'{param}_min'] = np.min(values)
                    summary['derived_parameters'][f'{param}_max'] = np.max(values)
            
            results['summary'] = summary
    
    return results
