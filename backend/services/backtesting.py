import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from services.features import build_features

def calculate_metrics(y_true, y_pred):
    """
    Calculates key performance indicators for regression models.
    Handles potential divide-by-zero errors and ensures metrics are JSON-friendly.
    Rounds all metrics to 4 decimal places.
    
    Args:
        y_true (list/array): Ground truth case counts.
        y_pred (list/array): Model-predicted case counts.
        
    Returns:
        dict: Calculated metrics (MAE, RMSE, MAPE, sMAPE, R2).
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Ensure non-negative predictions for metrics calculation
    y_pred = np.maximum(y_pred, 0)
    
    def safe_val(val):
        """Helper to ensure values are finite and rounded."""
        if val is None or not np.isfinite(val):
            return 0.0
        return round(float(val), 4)
    
    # Mean Absolute Error
    try:
        mae = mean_absolute_error(y_true, y_pred)
    except Exception:
        mae = 0.0
    
    # Root Mean Squared Error
    try:
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    except Exception:
        rmse = 0.0
    
    # MAPE (Mean Absolute Percentage Error) - safely handle zeros in y_true
    mask = y_true > 0
    if np.any(mask):
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    else:
        mape = 0.0
    
    # sMAPE (Symmetric MAPE) - robust to zero values in ground truth
    denominator = (np.abs(y_true) + np.abs(y_pred))
    smape_mask = denominator > 0
    if np.any(smape_mask):
        smape = np.mean(200 * np.abs(y_pred[smape_mask] - y_true[smape_mask]) / denominator[smape_mask])
    else:
        smape = 0.0
        
    # R2 Score - calculated across all available predictions
    try:
        if len(y_true) > 1 and np.var(y_true) > 0:
            r2 = r2_score(y_true, y_pred)
        else:
            r2 = 0.0
    except Exception:
        r2 = 0.0
        
    return {
        "mae": safe_val(mae),
        "rmse": safe_val(rmse),
        "mape": safe_val(mape),
        "smape": safe_val(smape),
        "r2": safe_val(r2)
    }

def get_model_registry():
    """
    Returns a dictionary of initialized ML models to be evaluated in backtesting.
    """
    return {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=100, random_state=42)
    }

def prepare_backtest_data(df):
    """
    Prepares features and targets using build_features, ensuring no raw leakage.
    
    Args:
        df (pd.DataFrame): Raw epidemiological data.
        
    Returns:
        tuple: (X, y, time_index)
    """
    # Orchestrate feature engineering from central service
    df_feat = build_features(df)
    
    # Exclude non-numeric identifiers and raw case/death counts to prevent data leakage
    # We only want to use engineered features (lags, rolling stats, etc.)
    exclude = ['state', 'district', 'time_index', 'quarter', 'cases', 'deaths', 'year', 'quarter_number']
    
    # Identify numeric engineered features
    feature_cols = [c for c in df_feat.columns if c not in exclude]
    
    # Extract predictor matrix X and target vector y
    X = df_feat[feature_cols].select_dtypes(include=[np.number])
    y = df_feat['cases']
    
    return X, y, df_feat['time_index']

def run_rolling_backtest(df, min_train_size=8, return_raw=False):
    """
    Performs a rolling-origin backtest for all registered ML models.
    Simulates the actual forecasting environment for each test window.
    
    Args:
        df (pd.DataFrame): Dataset to backtest on.
        min_train_size (int): Minimum samples required before starting evaluation.
        return_raw (bool): If True, returns the list of every prediction. 
                          If False (default), returns summary metrics.
        
    Returns:
        list or dict: Summary metrics (list) or raw predictions (dict).
    """
    if len(df) < min_train_size + 1:
        return {"error": f"Insufficient data for backtesting. Found {len(df)}, need > {min_train_size}."}
        
    models = get_model_registry()
    results = {name: [] for name in models.keys()}
    
    # Rolling origin loop: origin moves from min_train_size to N-1
    for i in range(min_train_size, len(df)):
        # 1. Capture the 'actual' ground truth before any modification
        actual_val = float(df.iloc[i]['cases'])
        
        # 2. Segment history for training
        train_df = df.iloc[:i].copy()
        
        # 3. Prepare training data (X, y)
        # Note: Features for training are built using the history available up to i-1
        X_train, y_train, _ = prepare_backtest_data(train_df)
        
        # 4. Prepare test features simulating the forecasting environment
        # We MUST zero out the target variables in the test row to prevent the model 
        # from seeing the 'future' during the feature engineering step.
        test_row_dummy = df.iloc[i:i+1].copy()
        test_row_dummy['cases'] = 0.0
        test_row_dummy['deaths'] = 0.0
        
        dummy_test_df = pd.concat([train_df, test_row_dummy], ignore_index=True)
        
        # Rebuild features for the combined set (history + dummy test row)
        X_full, _, _ = prepare_backtest_data(dummy_test_df)
        X_test = X_full.tail(1)
        
        # 5. Evaluate each model using the original actual_val preserved in step 1
        for name, model in models.items():
            try:
                # Fit on history
                model.fit(X_train, y_train)
                
                # Predict the 'future' point
                pred = model.predict(X_test)[0]
                pred = max(0.0, float(pred)) # Non-negative constraint
                
                # IMPORTANT: We compare against original actual_val, NOT the 0.0 used for features
                results[name].append({
                    "actual": actual_val,
                    "predicted": pred
                })
            except Exception:
                # Skip windows where models fail to converge/fit
                continue
                
    if return_raw:
        return results
        
    return summarize_backtest_results(results)

def summarize_backtest_results(results):
    """
    Aggregates rolling predictions into a standardized JSON-friendly summary.
    
    Args:
        results (dict): Raw results from run_rolling_backtest.
        
    Returns:
        list: Aggregated performance metrics for each model.
    """
    if "error" in results:
        return [results]
        
    summary = []
    
    for model_name, preds in results.items():
        if not preds:
            continue
            
        y_true = [p['actual'] for p in preds]
        y_pred = [p['predicted'] for p in preds]
        
        metrics = calculate_metrics(y_true, y_pred)
        
        summary.append({
            "model_name": model_name,
            "average_mae": metrics['mae'],
            "average_rmse": metrics['rmse'],
            "average_mape": metrics['mape'],
            "average_smape": metrics['smape'],
            "average_r2": metrics['r2'],
            "number_of_backtest_windows": len(preds)
        })
        
    return summary
