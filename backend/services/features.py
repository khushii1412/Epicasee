import pandas as pd
import numpy as np

def prepare_time_columns(df):
    """
    Ensures time_index is datetime and adds year, quarter, and quarter_number.
    """
    df = df.copy()
    df['time_index'] = pd.to_datetime(df['time_index'])
    df['year'] = df['time_index'].dt.year
    df['quarter_number'] = df['time_index'].dt.quarter
    df['quarter'] = 'Q' + df['quarter_number'].astype(str)
    return df

def add_lag_features(df, group_cols):
    """
    Adds lagged case counts (1, 2, and 4 quarters).
    """
    df = df.copy()
    df = df.sort_values(group_cols + ['time_index'])
    
    for lag in [1, 2, 4]:
        df[f'lag_{lag}_cases'] = df.groupby(group_cols)['cases'].shift(lag)
    
    return df

def add_rolling_features(df, group_cols):
    """
    Adds rolling mean (2, 4 quarters) and rolling std (4 quarters).
    """
    df = df.copy()
    df = df.sort_values(group_cols + ['time_index'])
    
    # Rolling mean 2
    df['rolling_mean_2'] = df.groupby(group_cols)['cases'].transform(
        lambda x: x.rolling(window=2, min_periods=1).mean()
    )
    
    # Rolling mean 4
    df['rolling_mean_4'] = df.groupby(group_cols)['cases'].transform(
        lambda x: x.rolling(window=4, min_periods=1).mean()
    )
    
    # Rolling std 4
    df['rolling_std_4'] = df.groupby(group_cols)['cases'].transform(
        lambda x: x.rolling(window=4, min_periods=1).std()
    )
    
    return df

def add_growth_features(df, group_cols):
    """
    Adds growth rate and absolute change from previous quarter.
    """
    df = df.copy()
    df = df.sort_values(group_cols + ['time_index'])
    
    # Absolute change
    df['absolute_case_change'] = df.groupby(group_cols)['cases'].diff()
    
    # Growth rate: (current - previous) / previous
    df['growth_rate'] = df.groupby(group_cols)['cases'].pct_change()
    
    # Handle infinities and large values from division by zero
    df['growth_rate'] = df['growth_rate'].replace([np.inf, -np.inf], np.nan).fillna(0)
    
    return df

def add_mortality_features(df):
    """
    Adds death rate and case fatality rate (CFR).
    """
    df = df.copy()
    
    # Handle division by zero safely
    df['death_rate'] = np.where(df['cases'] > 0, df['deaths'] / df['cases'], 0)
    df['case_fatality_rate'] = df['death_rate'] * 100
    
    return df

def add_seasonality_features(df):
    """
    Flags quarters associated with the Indian monsoon (Q3: Jul-Sep).
    """
    df = df.copy()
    # Monsoon in India typically peaks in Q3 (July, August, September)
    df['is_monsoon_quarter'] = np.where(df['quarter_number'] == 3, 1, 0)
    return df

def add_outbreak_features(df, group_cols):
    """
    Adds Z-Score and Outbreak Intensity Score.
    """
    df = df.copy()
    
    # Z-Score: (current - mean) / std
    def calculate_zscore(x):
        if len(x) < 2 or x.std() == 0:
            return 0
        return (x - x.mean()) / x.std()

    df['z_score_cases'] = df.groupby(group_cols)['cases'].transform(calculate_zscore)
    
    # Outbreak Intensity Score: Weighted combination of growth, Z-score and mortality
    # Formula: (Z-Score * 0.5) + (Growth Rate * 0.3) + (CFR * 0.2)
    # This is a normalized proxy for how 'severe' the current state is compared to its history.
    df['outbreak_intensity_score'] = (
        (df['z_score_cases'].fillna(0) * 0.5) + 
        (df['growth_rate'].fillna(0) * 0.3) + 
        (df['case_fatality_rate'].fillna(0) * 0.2)
    )
    
    return df

def build_features(df):
    """
    Orchestrates the entire feature engineering pipeline.
    """
    if df.empty:
        return df
        
    # Standardized columns: state, district, time_index, cases, deaths
    # Handle missing district safely by filling with 'Unknown' if column exists
    df_proc = df.copy()
    if 'district' in df_proc.columns:
        df_proc['district'] = df_proc['district'].fillna('Unknown').replace('', 'Unknown')
        group_cols = ['state', 'district']
    else:
        group_cols = ['state']
        
    # Sort for time-series operations
    df_proc = df_proc.sort_values(group_cols + ['time_index'])
    
    # Execute pipeline
    df_proc = prepare_time_columns(df_proc)
    df_proc = add_lag_features(df_proc, group_cols)
    df_proc = add_rolling_features(df_proc, group_cols)
    df_proc = add_growth_features(df_proc, group_cols)
    df_proc = add_mortality_features(df_proc)
    df_proc = add_seasonality_features(df_proc)
    df_proc = add_outbreak_features(df_proc, group_cols)
    
    # Final cleanup of NaNs for the entire dataframe
    df_proc = df_proc.fillna(0)
    
    return df_proc
