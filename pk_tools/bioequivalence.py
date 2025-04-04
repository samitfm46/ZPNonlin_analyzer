import numpy as np
import scipy.stats as stats
import pandas as pd

def calculate_bioequivalence(test_results, ref_results, design='crossover', alpha=0.05):
    """
    Calculate bioequivalence statistics for test and reference formulations.
    
    Parameters:
    - test_results: Dictionary with NCA parameters for test formulation
    - ref_results: Dictionary with NCA parameters for reference formulation
    - design: Study design ('crossover' or 'parallel')
    - alpha: Significance level (default 0.05 for 90% CI)
    
    Returns:
    - Dictionary with bioequivalence statistics
    """
    # Parameters to analyze for bioequivalence
    be_parameters = ['cmax', 'auc_last', 'auc_inf']
    
    results = {}
    
    # Get subject IDs excluding summary
    test_subjects = [s for s in test_results if s != 'summary']
    ref_subjects = [s for s in ref_results if s != 'summary']
    
    for param in be_parameters:
        # Collect parameter values for test and reference
        test_values = [np.log(test_results[s][param]) for s in test_subjects if param in test_results[s] and test_results[s][param] is not None and test_results[s][param] > 0]
        ref_values = [np.log(ref_results[s][param]) for s in ref_subjects if param in ref_results[s] and ref_results[s][param] is not None and ref_results[s][param] > 0]
        
        if not test_values or not ref_values:
            results[param] = {
                'error': f"Insufficient data for parameter {param}"
            }
            continue
        
        # Calculate geometric means
        test_geomean = np.exp(np.mean(test_values))
        ref_geomean = np.exp(np.mean(ref_values))
        
        # Calculate ratio
        ratio = test_geomean / ref_geomean * 100  # as percentage
        
        # For crossover design
        if design == 'crossover':
            # ANOVA-based approach for crossover design
            # This is simplified - in practice, would need to account for period and sequence effects
            
            # Create data for analysis
            if len(test_subjects) != len(ref_subjects):
                results[param] = {
                    'error': f"Unequal number of subjects for test and reference for {param}"
                }
                continue
            
            # Match subjects in test and reference (assuming they're the same)
            data = []
            for i, (test_subj, ref_subj) in enumerate(zip(test_subjects, ref_subjects)):
                if (param in test_results[test_subj] and test_results[test_subj][param] is not None and 
                    param in ref_results[ref_subj] and ref_results[ref_subj][param] is not None):
                    
                    data.append({
                        'subject': i,
                        'test': np.log(test_results[test_subj][param]),
                        'reference': np.log(ref_results[ref_subj][param])
                    })
            
            if not data:
                results[param] = {
                    'error': f"No matched data for parameter {param}"
                }
                continue
            
            # Calculate mean squared error (MSE)
            df = pd.DataFrame(data)
            df['diff'] = df['test'] - df['reference']
            mean_diff = df['diff'].mean()
            mse = df['diff'].var()
            
            # Degrees of freedom
            df_error = len(df) - 1
            
            # Standard error of the difference
            se_diff = np.sqrt(mse / len(df))
            
            # t-value for confidence interval
            t_value = stats.t.ppf(1 - alpha/2, df_error)
            
            # Calculate confidence interval for the difference
            ci_lower = mean_diff - t_value * se_diff
            ci_upper = mean_diff + t_value * se_diff
            
            # Convert to ratio scale
            ratio_ci_lower = np.exp(ci_lower) * 100
            ratio_ci_upper = np.exp(ci_upper) * 100
            
            # Determine if bioequivalent (typically 80-125% for 90% CI)
            is_bioequivalent = 80 <= ratio_ci_lower and ratio_ci_upper <= 125
            
            results[param] = {
                'test_geomean': test_geomean,
                'ref_geomean': ref_geomean,
                'ratio': ratio,
                'ci_lower': ratio_ci_lower,
                'ci_upper': ratio_ci_upper,
                'is_bioequivalent': is_bioequivalent,
                'intra_subject_cv': np.sqrt(np.exp(mse) - 1) * 100  # Intra-subject CV%
            }
            
        # For parallel design
        elif design == 'parallel':
            # Two-sample t-test approach for parallel design
            
            # Degrees of freedom
            df_error = len(test_values) + len(ref_values) - 2
            
            # Pooled variance
            pooled_var = ((len(test_values) - 1) * np.var(test_values) + 
                         (len(ref_values) - 1) * np.var(ref_values)) / df_error
            
            # Standard error of the difference
            se_diff = np.sqrt(pooled_var * (1/len(test_values) + 1/len(ref_values)))
            
            # Mean difference
            mean_diff = np.mean(test_values) - np.mean(ref_values)
            
            # t-value for confidence interval
            t_value = stats.t.ppf(1 - alpha/2, df_error)
            
            # Calculate confidence interval for the difference
            ci_lower = mean_diff - t_value * se_diff
            ci_upper = mean_diff + t_value * se_diff
            
            # Convert to ratio scale
            ratio_ci_lower = np.exp(ci_lower) * 100
            ratio_ci_upper = np.exp(ci_upper) * 100
            
            # Determine if bioequivalent (typically 80-125% for 90% CI)
            is_bioequivalent = 80 <= ratio_ci_lower and ratio_ci_upper <= 125
            
            results[param] = {
                'test_geomean': test_geomean,
                'ref_geomean': ref_geomean,
                'ratio': ratio,
                'ci_lower': ratio_ci_lower,
                'ci_upper': ratio_ci_upper,
                'is_bioequivalent': is_bioequivalent,
                'inter_subject_cv': np.sqrt(np.exp(pooled_var) - 1) * 100  # Inter-subject CV%
            }
        
        else:
            results[param] = {
                'error': f"Unknown study design: {design}"
            }
    
    # Add summary
    results['summary'] = {
        'design': design,
        'alpha': alpha,
        'ci_level': (1 - alpha) * 100,
        'be_criteria': "80-125%"
    }
    
    return results
