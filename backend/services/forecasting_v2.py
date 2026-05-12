import pandas as pd
import numpy as np
import warnings
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from services.features import build_features

# Suppress setitem warnings
warnings.filterwarnings("ignore", category=FutureWarning)

def prepare_model_data(df):
    """
    Prepares features (X) and target (y) for model training.
    A. Strictly uses only engineered predictor columns.
    """
    df_featured = build_features(df)
    
    # Target
    y = df_featured['cases']
    
    # Predictors - Only use numeric engineered features
    # Explicitly exclude identifiers and the target itself
    exclude = ['cases', 'deaths', 'state', 'district', 'time_index', 'quarter']
    X = df_featured.drop(columns=[c for c in exclude if c in df_featured.columns])
    X = X.select_dtypes(include=[np.number])
    
    # Drop rows with NaNs from initial lagging
    valid_idx = X.dropna().index
    X = X.loc[valid_idx]
    y = y.loc[valid_idx]
    
    return X, y, X.columns.tolist()

def train_linear_regression(X_train, y_train):
    return LinearRegression().fit(X_train, y_train)

def train_ridge_regression(X_train, y_train):
    return Ridge(alpha=1.0).fit(X_train, y_train)

def train_random_forest(X_train, y_train):
    return RandomForestRegressor(n_estimators=50, random_state=42).fit(X_train, y_train)

def train_gradient_boosting(X_train, y_train):
    return GradientBoostingRegressor(n_estimators=50, random_state=42).fit(X_train, y_train)

def forecast_ml_models(df, steps=4):
    """
    B. Converts cases to float and recursively forecasts next quarters.
    """
    if len(df) < 8:
        return {"error": "Insufficient data (need >= 8 points)"}

    # B. Cast to float immediately to avoid dtype warnings
    df = df.copy()
    df['cases'] = df['cases'].astype(float)
    if 'deaths' in df.columns:
        df['deaths'] = df['deaths'].astype(float)

    # Use first available state/district as reference for dummy rows
    state = df['state'].iloc[0]
    # Handle district carefully (standardize to 'Unknown' if missing/empty)
    district = 'Unknown'
    if 'district' in df.columns:
        d_val = df['district'].iloc[0]
        if pd.notna(d_val) and str(d_val).strip() != "":
            district = str(d_val)

    # A. Train models on purely engineered features
    X_train, y_train, feature_cols = prepare_model_data(df)
    
    models = {
        "linear": train_linear_regression(X_train, y_train),
        "ridge": train_ridge_regression(X_train, y_train),
        "random_forest": train_random_forest(X_train, y_train),
        "gradient_boosting": train_gradient_boosting(X_train, y_train)
    }
    
    last_date = pd.to_datetime(df['time_index']).max()
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=3), periods=steps, freq="QS")
    
    results = {
        "future_dates": [str(d.date()) for d in future_dates],
        "predictions": {}
    }

    # C. Recursive forecasting loop
    for name, model in models.items():
        # C. Maintain separate history for each model
        current_history = df.copy()
        model_preds = []
        
        for i in range(steps):
            # 1. Append future dummy row
            f_date = future_dates[i]
            dummy = pd.DataFrame([{
                'state': state,
                'district': district,
                'time_index': f_date,
                'cases': 0.0,
                'deaths': 0.0
            }])
            current_history = pd.concat([current_history, dummy], ignore_index=True)
            
            # 2. Rebuild features
            df_feat = build_features(current_history)
            
            # 3. Predict using the LATEST row for this specific series
            # We filter by time_index to be absolutely sure we get the dummy row
            # Use .iloc[-1] after filtering to get the single row for the prediction point
            mask = (df_feat['time_index'] == f_date) & (df_feat['state'] == state)
            X_next = df_feat[mask][feature_cols].tail(1)
            
            if X_next.empty:
                # Fallback: if mask fails, take the very last row (usually correct)
                X_next = df_feat[feature_cols].tail(1)

            pred = model.predict(X_next)[0]
            pred = max(0.0, float(pred)) # E. Non-negative
            
            # 4. Store and update history
            model_preds.append(pred)
            current_history.loc[current_history.index[-1], 'cases'] = pred
            
        results["predictions"][name] = model_preds

    return results
