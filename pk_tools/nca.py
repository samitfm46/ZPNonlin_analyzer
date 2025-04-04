import numpy as np
from scipy import integrate
import pandas as pd

def linear_trapezoidal(times, concentrations):
    """Calculate AUC using linear trapezoidal method."""
    if len(times) != len(concentrations):
        raise ValueError("Time and concentration arrays must have the same length")
    
    if len(times) < 2:
        return 0.0
    
    auc = 0.0
    for i in range(1, len(times)):
        auc += 0.5 * (concentrations[i] + concentrations[i-1]) * (times[i] - times[i-1])
    
    return auc

def log_linear_trapezoidal(times, concentrations):
    """Calculate AUC using log-linear trapezoidal method."""
    if len(times) != len(concentrations):
        raise ValueError("Time and concentration arrays must have the same length")
    
    if len(times) < 2:
        return 0.0
    
    auc = 0.0
    for i in range(1, len(times)):
        if concentrations[i] <= 0 or concentrations[i-1] <= 0:
            # Fall back to linear if any concentration is zero or negative
            auc += 0.5 * (concentrations[i] + concentrations[i-1]) * (times[i] - times[i-1])
        else:
            # Log-linear formula
            dt = times[i] - times[i-1]
            if concentrations[i] == concentrations[i-1]:
                auc += concentrations[i] * dt
            else:
                auc += dt * (concentrations[i] - concentrations[i-1]) / np.log(concentrations[i] / concentrations[i-1])
    
    return auc

def calculate_lambda_z(times, concentrations, min_points=3):
    """Calculate terminal elimination rate constant using log-linear regression."""
    if len(times) < min_points:
        return None, None, None, None
    
    # Filter non-positive concentrations
    valid_idx = [i for i, c in enumerate(concentrations) if c > 0]
    if len(valid_idx) < min_points:
        return None, None, None, None
    
    valid_times = [times[i] for i in valid_idx]
    valid_concs = [concentrations[i] for i in valid_idx]
    
    # Take the last min_points points for regression
    t_term = valid_times[-min_points:]
    c_term = valid_concs[-min_points:]
    
    # Log-transform concentrations
    log_c = np.log(c_term)
    
    # Linear regression: log(C) = b + a*t, where a = -lambda_z
    n = len(t_term)
    sum_t = sum(t_term)
    sum_log_c = sum(log_c)
    sum_t2 = sum(t**2 for t in t_term)
    sum_t_log_c = sum(t*lc for t, lc in zip(t_term, log_c))
    
    # Calculate slope and intercept
    slope = (n*sum_t_log_c - sum_t*sum_log_c) / (n*sum_t2 - sum_t**2)
    intercept = (sum_log_c - slope*sum_t) / n
    
    # lambda_z is negative of the slope
    lambda_z = -slope
    
    # Calculate R² (coefficient of determination)
    y_mean = sum_log_c / n
    ss_tot = sum((y - y_mean)**2 for y in log_c)
    ss_res = sum((y - (intercept + slope*x))**2 for x, y in zip(t_term, log_c))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    # Calculate adjusted points for the regression line
    adjusted_points = [(t, np.exp(intercept + slope*t)) for t in valid_times]
    
    return lambda_z, r_squared, intercept, adjusted_points

def extrapolate_auc_inf(times, concentrations, lambda_z):
    """Calculate extrapolated AUC from last time point to infinity."""
    if lambda_z is None or lambda_z <= 0:
        return None
    
    last_time = times[-1]
    last_conc = concentrations[-1]
    
    if last_conc <= 0:
        return None
    
    # AUC from t_last to infinity = C_last / lambda_z
    auc_extrap = last_conc / lambda_z
    
    return auc_extrap

def calculate_half_life(lambda_z):
    """Calculate half-life from elimination rate constant."""
    if lambda_z is None or lambda_z <= 0:
        return None
    
    return np.log(2) / lambda_z

def find_tmax_cmax(times, concentrations):
    """Find time and concentration at maximum observed concentration."""
    if not times or not concentrations:
        return None, None
    
    max_idx = np.argmax(concentrations)
    return times[max_idx], concentrations[max_idx]

def calculate_nca_parameters(subjects_data, dose=None):
    """
    Calculate NCA parameters for each subject.
    
    Parameters:
    - subjects_data: Dictionary with subject IDs as keys and dicts with 'times' and 'concentrations' as values
    - dose: Optional dose value for calculating dose-normalized parameters
    
    Returns:
    - Dictionary with calculated parameters for each subject
    """
    results = {}
    
    for subject_id, data in subjects_data.items():
        times = data['times']
        concentrations = data['concentrations']
        
        # Sort data by time
        sorted_indices = np.argsort(times)
        times = [times[i] for i in sorted_indices]
        concentrations = [concentrations[i] for i in sorted_indices]
        
        # Find Tmax and Cmax
        tmax, cmax = find_tmax_cmax(times, concentrations)
        
        # Calculate AUC using linear trapezoidal method
        auc_last = linear_trapezoidal(times, concentrations)
        
        # Calculate terminal elimination rate constant
        lambda_z, r_squared, intercept, adjusted_points = calculate_lambda_z(times, concentrations)
        
        # Calculate half-life
        half_life = calculate_half_life(lambda_z)
        
        # Calculate AUC extrapolated to infinity
        auc_extrap = extrapolate_auc_inf(times, concentrations, lambda_z)
        
        # Calculate total AUC (to infinity)
        auc_inf = auc_last + (auc_extrap if auc_extrap is not None else 0)
        
        # Calculate percent extrapolation
        pct_extrap = 100 * auc_extrap / auc_inf if auc_inf > 0 and auc_extrap is not None else None
        
        # Calculate MRT
        aumc_last = 0
        for i in range(1, len(times)):
            dt = times[i] - times[i-1]
            aumc_last += 0.5 * (times[i]*concentrations[i] + times[i-1]*concentrations[i-1]) * dt
        
        # Extrapolate AUMC to infinity if possible
        aumc_extrap = None
        if lambda_z is not None and lambda_z > 0 and concentrations[-1] > 0:
            aumc_extrap = concentrations[-1] * times[-1] / lambda_z + concentrations[-1] / (lambda_z**2)
        
        aumc_inf = aumc_last + (aumc_extrap if aumc_extrap is not None else 0)
        
        # Mean residence time
        mrt = aumc_inf / auc_inf if auc_inf > 0 else None
        
        # Store results
        results[subject_id] = {
            'tmax': tmax,
            'cmax': cmax,
            'auc_last': auc_last,
            'auc_inf': auc_inf,
            'auc_extrap': auc_extrap,
            'pct_extrap': pct_extrap,
            'lambda_z': lambda_z,
            'r_squared': r_squared,
            'half_life': half_life,
            'mrt': mrt,
            'aumc_last': aumc_last,
            'aumc_inf': aumc_inf,
            'times': times,
            'concentrations': concentrations,
            'adjusted_points': adjusted_points
        }
        
        # Add dose-normalized parameters if dose is provided
        if dose is not None and dose > 0:
            results[subject_id]['cmax_dn'] = cmax / dose
            results[subject_id]['auc_last_dn'] = auc_last / dose
            results[subject_id]['auc_inf_dn'] = auc_inf / dose
    
    # Calculate mean and SD across subjects
    parameter_keys = ['tmax', 'cmax', 'auc_last', 'auc_inf', 'half_life', 'mrt']
    summary = {}
    
    for param in parameter_keys:
        values = [results[subject_id][param] for subject_id in results if results[subject_id][param] is not None]
        if values:
            summary[f'{param}_mean'] = np.mean(values)
            summary[f'{param}_sd'] = np.std(values)
            summary[f'{param}_cv'] = 100 * np.std(values) / np.mean(values) if np.mean(values) > 0 else None
            summary[f'{param}_min'] = np.min(values)
            summary[f'{param}_max'] = np.max(values)
    
    results['summary'] = summary
    
    return results
