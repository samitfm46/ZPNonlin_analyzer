import numpy as np
import scipy.stats as stats
import pandas as pd

def perform_statistical_analysis(subjects_data, stat_type='ttest', alpha=0.05):
    """
    Perform statistical analysis on PK data.
    
    Parameters:
    - subjects_data: Dictionary with subject IDs as keys and dicts with 'times' and 'concentrations' as values
    - stat_type: Type of statistical test to perform ('ttest', 'anova', 'regression')
    - alpha: Significance level
    
    Returns:
    - Dictionary with statistical results
    """
    results = {}
    
    # Extract data
    subject_ids = list(subjects_data.keys())
    
    if stat_type == 'ttest':
        # Perform t-test at each time point where data exists for all subjects
        
        # Find common time points
        all_times = set()
        for subject_id in subject_ids:
            all_times.update(subjects_data[subject_id]['times'])
        
        common_times = []
        for time in sorted(all_times):
            # Check if all subjects have this time point
            if all(time in subjects_data[subject_id]['times'] for subject_id in subject_ids):
                common_times.append(time)
        
        if len(common_times) < 2:
            return {'error': 'Insufficient common time points for t-test analysis'}
        
        # Perform t-test for each time point
        time_results = {}
        for time in common_times:
            concentrations = []
            for subject_id in subject_ids:
                time_idx = subjects_data[subject_id]['times'].index(time)
                concentrations.append(subjects_data[subject_id]['concentrations'][time_idx])
            
            # Calculate statistics
            mean_conc = np.mean(concentrations)
            std_conc = np.std(concentrations, ddof=1)
            sem_conc = std_conc / np.sqrt(len(concentrations))
            cv_percent = 100 * std_conc / mean_conc if mean_conc > 0 else None
            
            # One-sample t-test against 0
            t_stat, p_value = stats.ttest_1samp(concentrations, 0)
            
            # 95% confidence interval
            df = len(concentrations) - 1
            t_crit = stats.t.ppf(1 - alpha/2, df)
            ci_lower = mean_conc - t_crit * sem_conc
            ci_upper = mean_conc + t_crit * sem_conc
            
            time_results[time] = {
                'mean': mean_conc,
                'std': std_conc,
                'sem': sem_conc,
                'cv_percent': cv_percent,
                't_stat': t_stat,
                'p_value': p_value,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'significant': p_value < alpha
            }
        
        results['time_results'] = time_results
        
    elif stat_type == 'anova':
        # Perform one-way ANOVA across subjects at each time point
        
        # Find common time points
        all_times = set()
        for subject_id in subject_ids:
            all_times.update(subjects_data[subject_id]['times'])
        
        common_times = []
        for time in sorted(all_times):
            # Check if at least 3 subjects have this time point (minimum for ANOVA)
            subjects_with_time = sum(1 for subject_id in subject_ids if time in subjects_data[subject_id]['times'])
            if subjects_with_time >= 3:
                common_times.append(time)
        
        if len(common_times) < 1:
            return {'error': 'Insufficient common time points for ANOVA analysis'}
        
        # Perform ANOVA for each time point
        time_results = {}
        for time in common_times:
            # Group concentrations by subject
            groups = []
            for subject_id in subject_ids:
                if time in subjects_data[subject_id]['times']:
                    time_idx = subjects_data[subject_id]['times'].index(time)
                    groups.append([subjects_data[subject_id]['concentrations'][time_idx]])
            
            # Perform one-way ANOVA
            f_stat, p_value = stats.f_oneway(*groups)
            
            # Calculate summary statistics
            all_values = [val for group in groups for val in group]
            mean_conc = np.mean(all_values)
            std_conc = np.std(all_values, ddof=1)
            cv_percent = 100 * std_conc / mean_conc if mean_conc > 0 else None
            
            time_results[time] = {
                'mean': mean_conc,
                'std': std_conc,
                'cv_percent': cv_percent,
                'f_stat': f_stat,
                'p_value': p_value,
                'significant': p_value < alpha,
                'n_subjects': len(groups)
            }
        
        results['time_results'] = time_results
        
    elif stat_type == 'regression':
        # Perform linear regression for each subject
        
        regression_results = {}
        for subject_id in subject_ids:
            times = np.array(subjects_data[subject_id]['times'])
            concentrations = np.array(subjects_data[subject_id]['concentrations'])
            
            # Filter out non-positive concentrations for log transformation
            valid_idx = concentrations > 0
            if not np.all(valid_idx):
                valid_times = times[valid_idx]
                valid_conc = concentrations[valid_idx]
            else:
                valid_times = times
                valid_conc = concentrations
            
            if len(valid_times) < 3:
                regression_results[subject_id] = {
                    'error': 'Insufficient data points for regression'
                }
                continue
            
            # Linear regression on log-transformed concentrations
            log_conc = np.log(valid_conc)
            
            # Calculate linear regression parameters
            slope, intercept, r_value, p_value, std_err = stats.linregress(valid_times, log_conc)
            
            # Calculate predicted values
            predicted = intercept + slope * valid_times
            predicted_conc = np.exp(predicted)
            
            # Calculate residuals
            residuals = log_conc - predicted
            
            # Calculate R-squared and adjusted R-squared
            r_squared = r_value ** 2
            n = len(valid_times)
            p = 2  # Number of parameters (slope and intercept)
            adj_r_squared = 1 - ((1 - r_squared) * (n - 1) / (n - p))
            
            regression_results[subject_id] = {
                'slope': slope,
                'intercept': intercept,
                'r_value': r_value,
                'r_squared': r_squared,
                'adj_r_squared': adj_r_squared,
                'p_value': p_value,
                'std_err': std_err,
                'elimination_rate': -slope,
                'half_life': np.log(2) / (-slope) if slope < 0 else None,
                'times': valid_times.tolist(),
                'observed': valid_conc.tolist(),
                'predicted': predicted_conc.tolist(),
                'residuals': residuals.tolist()
            }
        
        results['regression_results'] = regression_results
        
        # Calculate summary statistics
        valid_results = [res for res in regression_results.values() if 'error' not in res]
        if valid_results:
            results['summary'] = {
                'mean_r_squared': np.mean([res['r_squared'] for res in valid_results]),
                'mean_half_life': np.mean([res['half_life'] for res in valid_results if res['half_life'] is not None]),
                'std_half_life': np.std([res['half_life'] for res in valid_results if res['half_life'] is not None])
            }
    
    else:
        return {'error': f'Unknown statistical test type: {stat_type}'}
    
    # Add general information
    results['stat_type'] = stat_type
    results['alpha'] = alpha
    results['n_subjects'] = len(subject_ids)
    
    return results
