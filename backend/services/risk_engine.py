import pandas as pd
import numpy as np
from services.features import build_features
from services.anomaly_detection import detect_anomalies

def normalize_score(value, min_val, max_val):
    """
    Normalizes a value to a 0-100 scale based on provided min and max.
    Handles division by zero and NaNs.
    """
    if pd.isna(value) or pd.isna(min_val) or pd.isna(max_val):
        return 0.0
    if max_val <= min_val:
        return 0.0
    
    score = ((value - min_val) / (max_val - min_val)) * 100
    return max(0.0, min(100.0, float(score)))

def classify_risk(score):
    """
    Categorizes the risk score into Low, Medium, or High levels.
    """
    if score <= 35:
        return "Low"
    elif score <= 70:
        return "Medium"
    else:
        return "High"

def generate_risk_summary(df):
    """
    Calculates a comprehensive risk score for each location (state/district).
    Combines case burden, growth, fatality, seasonality, and anomalies.
    """
    # 1. Engineering features and detecting anomalies
    raw_featured = build_features(df)
    raw_anomalies = detect_anomalies(df)
    
    # 2. Standardize districts to ensure correct merging
    def standardize_geo(temp_df):
        temp_df = temp_df.copy()
        if 'district' not in temp_df.columns:
            temp_df['district'] = 'Unknown'
        else:
            temp_df['district'] = temp_df['district'].fillna('Unknown').replace(['', 'nan', 'NaN', 'None'], 'Unknown')
        return temp_df

    df_featured = standardize_geo(raw_featured)
    df_anomalies = standardize_geo(raw_anomalies)

    # Ensure time_index is datetime in both to avoid merge errors
    df_featured['time_index'] = pd.to_datetime(df_featured['time_index'])
    df_anomalies['time_index'] = pd.to_datetime(df_anomalies['time_index'])
    
    # 3. Merge z-scores and anomaly status into the featured dataframe
    df_combined = pd.merge(
        df_featured,
        df_anomalies[['state', 'district', 'time_index', 'z_score', 'anomaly_status']],
        on=['state', 'district', 'time_index'],
        how='left'
    )
    
    # 4. Filter for the latest observation in each location
    df_latest = df_combined.sort_values(['state', 'district', 'time_index']).groupby(['state', 'district']).tail(1).copy()
    
    if df_latest.empty:
        return []

    # 5. Normalize components across the current geographic snapshot
    # This allows comparing states against each other
    metrics = {
        'cases': 'norm_cases',
        'growth_rate': 'norm_growth',
        'case_fatality_rate': 'norm_cfr',
        'z_score': 'norm_z',
        'outbreak_intensity_score': 'norm_intensity'
    }
    
    for col, norm_col in metrics.items():
        min_v = df_latest[col].min()
        max_v = df_latest[col].max()
        df_latest[norm_col] = df_latest[col].apply(lambda x: normalize_score(x, min_v, max_v))
        
    # Seasonality risk (is_monsoon_quarter is 0 or 1)
    df_latest['norm_seasonal'] = df_latest['is_monsoon_quarter'].astype(float) * 100
    
    # 5. Weighted Risk Scoring Formula
    # Weights: Cases(30%), Growth(20%), CFR(15%), Season(15%), Anomaly(10%), Intensity(10%)
    df_latest['risk_score'] = (
        0.30 * df_latest['norm_cases'] +
        0.20 * df_latest['norm_growth'] +
        0.15 * df_latest['norm_cfr'] +
        0.15 * df_latest['norm_seasonal'] +
        0.10 * df_latest['norm_z'] +
        0.10 * df_latest['norm_intensity']
    ).round(2)
    
    # 6. Classification and Reason Generation
    df_latest['risk_level'] = df_latest['risk_score'].apply(classify_risk)
    
    # Fill missing anomaly statuses from the merge
    df_latest['anomaly_status'] = df_latest['anomaly_status'].fillna("Normal")
    
    def generate_reason(row):
        reasons = []
        if row['norm_cases'] > 75: reasons.append("Critical case volume")
        # Only flag rapid expansion if growth is also positive
        if row['norm_growth'] > 75 and row['growth_rate'] > 0: 
            reasons.append("Rapid outbreak expansion")
        if row['norm_cfr'] > 75: reasons.append("High mortality rate relative to other regions")
        if row['anomaly_status'] != "Normal": 
            reasons.append(f"Statistical anomaly detected ({row['anomaly_status']})")
        if row['is_monsoon_quarter']: 
            reasons.append("High seasonal risk (monsoon period)")
        
        if not reasons:
            return "Metric indicators are currently stable and within expected ranges."
        return ". ".join(reasons) + "."

    df_latest['reason'] = df_latest.apply(generate_reason, axis=1)
    
    # Final JSON-friendly cleanup
    output_cols = [
        'state', 'district', 'time_index', 'cases', 'deaths', 
        'growth_rate', 'case_fatality_rate', 'z_score', 'anomaly_status',
        'outbreak_intensity_score', 'risk_score', 'risk_level', 'reason'
    ]
    df_final = df_latest[output_cols].copy()
    df_final['time_index'] = df_final['time_index'].dt.strftime('%Y-%m-%d')
    df_final = df_final.fillna(0)
    
    # Round metrics for presentation
    df_final['growth_rate'] = df_final['growth_rate'].round(4)
    df_final['case_fatality_rate'] = df_final['case_fatality_rate'].round(4)
    df_final['z_score'] = df_final['z_score'].round(2)
    df_final['outbreak_intensity_score'] = df_final['outbreak_intensity_score'].round(2)
    
    return df_final.to_dict(orient='records')

def get_top_risk_states(df, top_n=10):
    """
    Returns the top N states with the highest risk scores.
    """
    results = generate_risk_summary(df)
    # Sort descending by risk_score
    sorted_results = sorted(results, key=lambda x: x['risk_score'], reverse=True)
    return sorted_results[:top_n]
