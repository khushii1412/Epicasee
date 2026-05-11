import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from services.features import build_features

def prepare_model_data(df):
    """
    Prepares features (X) and target (y) for model training.
    Filters only numeric columns and drops rows with NaNs from lagging.
    """
    df_featured = build_features(df)
    
    # Define target
    y = df_featured['cases']
    
    # Filter for numeric features only
    # We exclude 'cases' (target), 'deaths' (leaky), and non-numeric cols
    exclude = ['cases', 'deaths', 'state', 'district', 'time_index', 'quarter']
    X = df_featured.drop(columns=[c for c in exclude if c in df_featured.columns])
    X = X.select_dtypes(include=[np.number])
    
    # Drop rows where lags are NaN (from start of time series)
    valid_idx = X.dropna().index
    X = X.loc[valid_idx]
    y = y.loc[valid_idx]
    
    return X, y, df_featured

def train_linear_regression(X_train, y_train):
    """Trains a Linear Regression model."""
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model

def train_ridge_regression(X_train, y_train):
    """Trains a Ridge Regression model."""
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    return model

def train_random_forest(X_train, y_train):
    """Trains a Random Forest Regressor."""
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model

def train_gradient_boosting(X_train, y_train):
    """Trains a Gradient Boosting Regressor."""
    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model

def forecast_ml_models(df, steps=4):
    """
    Trains 4 ML models and generates forecasts for the next N steps.
    Returns a dictionary with predictions from all models.
    """
    if len(df) < 8:
        return {"error": "Insufficient data for ML forecasting (need >= 8 points)"}

    # Prepare data
    X, y, df_featured = prepare_model_data(df)
    
    # Train models
    models = {
        "linear": train_linear_regression(X, y),
        "ridge": train_ridge_regression(X, y),
        "random_forest": train_random_forest(X, y),
        "gradient_boosting": train_gradient_boosting(X, y)
    }
    
    # For future predictions, we'll use the last known feature row as a base.
    # Note: A full recursive forecast would re-calculate lags. 
    # For this version, we'll project using the most recent feature state.
    last_row_X = X.tail(1)
    
    results = {}
    last_date = pd.to_datetime(df['time_index']).max()
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=3), periods=steps, freq="QS")
    results["future_dates"] = [str(d.date()) for d in future_dates]
    results["predictions"] = {}

    for name, model in models.items():
        # Predict next 'steps' using the last feature state 
        # (simplification: assuming features like 'is_monsoon' or 'year' are stable enough for short-term)
        pred = model.predict(last_row_X)[0]
        # Since these are quarterly, we'll return the prediction repeated or 
        # implement a simple trend projection if it's linear.
        # For RF/GBM, we'll return the static prediction for the immediate horizon.
        preds = [max(0, float(pred)) for _ in range(steps)]
        results["predictions"][name] = preds

    return results
