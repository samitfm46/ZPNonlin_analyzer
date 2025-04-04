import numpy as np
import pandas as pd

def validate_dataset(df):
    """
    Validate that a DataFrame has the correct format for PK analysis.
    
    Parameters:
    - df: Pandas DataFrame to validate
    
    Returns:
    - tuple: (is_valid, message)
    """
    # Check required columns
    required_columns = ['subject_id', 'time', 'concentration']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    # Check data types
    try:
        df['time'] = pd.to_numeric(df['time'])
        df['concentration'] = pd.to_numeric(df['concentration'])
    except ValueError:
        return False, "Time and concentration must be numeric"
    
    # Check for negative values
    if (df['time'] < 0).any():
        return False, "Time values cannot be negative"
    
    if (df['concentration'] < 0).any():
        return False, "Concentration values cannot be negative"
    
    # Check that each subject has at least 3 time points
    counts = df['subject_id'].value_counts()
    invalid_subjects = counts[counts < 3].index.tolist()
    
    if invalid_subjects:
        return False, f"These subjects have fewer than 3 time points: {', '.join(map(str, invalid_subjects))}"
    
    return True, "Dataset is valid"

def transform_data(subjects_data, transformation='log'):
    """
    Apply transformation to concentration data.
    
    Parameters:
    - subjects_data: Dictionary with subject IDs as keys and dicts with 'times' and 'concentrations' as values
    - transformation: Type of transformation to apply ('log', 'sqrt', 'normalize')
    
    Returns:
    - Dictionary with transformed data
    """
    transformed = {}
    
    for subject_id, data in subjects_data.items():
        times = data['times']
        concentrations = data['concentrations']
        
        # Make a copy of the data
        transformed_concentrations = np.array(concentrations).copy()
        
        if transformation == 'log':
            # Replace zeros or negative values with a small positive value
            transformed_concentrations[transformed_concentrations <= 0] = 1e-10
            transformed_concentrations = np.log(transformed_concentrations)
        
        elif transformation == 'sqrt':
            # Replace negative values with zero
            transformed_concentrations[transformed_concentrations < 0] = 0
            transformed_concentrations = np.sqrt(transformed_concentrations)
        
        elif transformation == 'normalize':
            # Normalize to 0-1 range
            min_val = np.min(transformed_concentrations)
            max_val = np.max(transformed_concentrations)
            
            if max_val > min_val:
                transformed_concentrations = (transformed_concentrations - min_val) / (max_val - min_val)
        
        elif transformation == 'inverse':
            # Replace zeros with a small value to avoid division by zero
            transformed_concentrations[transformed_concentrations == 0] = 1e-10
            transformed_concentrations = 1.0 / transformed_concentrations
        
        else:
            raise ValueError(f"Unknown transformation: {transformation}")
        
        transformed[subject_id] = {
            'times': times,
            'concentrations': transformed_concentrations.tolist()
        }
    
    return transformed

def merge_datasets(dataset1, dataset2):
    """
    Merge two datasets by subject ID.
    
    Parameters:
    - dataset1: Dictionary with subject IDs as keys and dicts with 'times' and 'concentrations' as values
    - dataset2: Dictionary with subject IDs as keys and dicts with 'times' and 'concentrations' as values
    
    Returns:
    - Dictionary with merged data
    """
    merged = {}
    
    # Find common subject IDs
    common_subjects = set(dataset1.keys()) & set(dataset2.keys())
    
    for subject_id in common_subjects:
        times1 = dataset1[subject_id]['times']
        conc1 = dataset1[subject_id]['concentrations']
        
        times2 = dataset2[subject_id]['times']
        conc2 = dataset2[subject_id]['concentrations']
        
        # Combine times and concentrations
        all_times = []
        all_conc = []
        
        # Add data from dataset1, avoiding duplicates
        for t1, c1 in zip(times1, conc1):
            all_times.append(t1)
            all_conc.append(c1)
        
        # Add data from dataset2, avoiding duplicates
        for t2, c2 in zip(times2, conc2):
            if t2 not in times1:
                all_times.append(t2)
                all_conc.append(c2)
        
        # Sort by time
        sorted_idx = np.argsort(all_times)
        sorted_times = [all_times[i] for i in sorted_idx]
        sorted_conc = [all_conc[i] for i in sorted_idx]
        
        merged[subject_id] = {
            'times': sorted_times,
            'concentrations': sorted_conc
        }
    
    return merged
