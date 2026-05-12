import pandas as pd
import numpy as np

def prepare_anomaly_data(df):
    """
    Prepares and sorts the dataframe for time-series anomaly detection.
    Ensures date types are consistent and districts are handled safely.
    """
    df = df.copy()
    df['time_index'] = pd.to_datetime(df['time_index'])
    
    # Handle missing or 'Unknown' districts safely for grouping
    if 'district' in df.columns:
        df['district'] = df['district'].fillna('').replace('Unknown', '')
    else:
        df['district'] = ''
        
    group_cols = ['state', 'district']
    
    # Sort chronologically within each location group
    df = df.sort_values(group_cols + ['time_index'])
    
    return df, group_cols

def calculate_rolling_z_scores(df):
    """
    Calculates rolling Z-scores for cases.
    Uses a shifted window of 4 quarters to ensure the current observation
    is compared against a purely historical baseline.
    """
    df, group_cols = prepare_anomaly_data(df)
    
    # rolling(4) on shifted data means looking at [t-4, t-3, t-2, t-1]
    df['rolling_mean_4'] = df.groupby(group_cols)['cases'].transform(
        lambda x: x.shift(1).rolling(window=4, min_periods=1).mean()
    )
    
    df['rolling_std_4'] = df.groupby(group_cols)['cases'].transform(
        lambda x: x.shift(1).rolling(window=4, min_periods=1).std()
    )
    
    # Logic for Z-score calculation with safety checks
    def compute_z_score(row):
        cases = row['cases']
        mean = row['rolling_mean_4']
        std = row['rolling_std_4']
        
        # If std is 0, missing, or baseline is too small, we cannot compute a meaningful Z-score
        if pd.isna(mean) or pd.isna(std) or std == 0:
            return 0.0
            
        return (cases - mean) / std
        
    df['z_score'] = df.apply(compute_z_score, axis=1)
    
    return df

def classify_anomaly(z_score):
    """
    Classifies severity based on standard deviation thresholds.
    """
    if z_score < 1.5:
        return "Normal"
    elif z_score < 2.5:
        return "Watch"
    else:
        return "Possible Outbreak Spike"

def detect_anomalies(df):
    """
    Main detection engine that returns the full dataframe with anomaly metadata.
    """
    df = calculate_rolling_z_scores(df)
    
    # Generate human-readable alert messages
    def generate_alert(row):
        z = round(float(row['z_score']), 2)
        status = classify_anomaly(row['z_score'])
        location = row['state']
        if row['district'] and str(row['district']).strip():
            location = f"{row['district']}, {row['state']}"
            
        if status == "Normal":
            return f"Case levels in {location} are within the normal range."
            
        return f"Cases in {location} are {z} standard deviations above the recent 4-quarter average."

    df['anomaly_status'] = df['z_score'].apply(classify_anomaly)
    df['alert_message'] = df.apply(generate_alert, axis=1)
    
    # Clean up for JSON output (round floats and format dates)
    df['rolling_mean_4'] = df['rolling_mean_4'].round(2)
    df['rolling_std_4'] = df['rolling_std_4'].round(2)
    df['z_score'] = df['z_score'].round(4)
    df['time_index'] = df['time_index'].dt.strftime('%Y-%m-%d')
    
    # Fill remaining NaNs from early window rows
    df = df.fillna(0)
    
    return df

def get_latest_anomaly_summary(df):
    """
    Filters the detection results to provide only the status of the most recent quarter 
    available for each location.
    
    Returns:
        list: JSON-friendly list of dictionaries containing the latest alerts.
    """
    all_results = detect_anomalies(df)
    
    # Group by location and take the latest chronological entry
    latest_entries = all_results.groupby(['state', 'district']).tail(1)
    
    return latest_entries.to_dict(orient='records')
