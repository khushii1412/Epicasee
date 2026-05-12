import pandas as pd
import numpy as np
from services.model_leaderboard import build_model_leaderboard
from services.risk_engine import get_top_risk_states
from services.forecasting_v2 import forecast_ml_models

def get_forecast_trend(forecast_values):
    """
    Determines the trend direction of a forecast sequence.
    Returns 'increasing', 'decreasing', or 'stable' based on a 5% threshold.
    """
    if not forecast_values or len(forecast_values) < 2:
        return "stable"
    
    first = float(forecast_values[0])
    last = float(forecast_values[-1])
    
    if first == 0:
        return "increasing" if last > 0 else "stable"
    
    change_pct = (last - first) / first
    
    if change_pct > 0.05:
        return "increasing"
    elif change_pct < -0.05:
        return "decreasing"
    else:
        return "stable"

def summarize_disease(df, disease_name):
    """
    Computes high-level summary metrics, risk status, and forecast trends 
    for a single disease dataset.
    """
    # Ensure time_index is datetime
    df = df.copy()
    df['time_index'] = pd.to_datetime(df['time_index'])
    
    # 1. Aggregate Statistics
    total_cases = int(df['cases'].sum())
    total_deaths = int(df['deaths'].sum())
    cfr = round((total_deaths / total_cases * 100), 2) if total_cases > 0 else 0.0
    
    # 2. Burden Analysis
    state_totals = df.groupby('state')['cases'].sum().reset_index()
    if state_totals.empty:
        highest_state = "None"
        highest_cases = 0
    else:
        highest_row = state_totals.sort_values('cases', ascending=False).iloc[0]
        highest_state = highest_row['state']
        highest_cases = int(highest_row['cases'])
    
    # 3. Temporal Context
    latest_time = df['time_index'].max()
    latest_time_str = latest_time.strftime('%Y-%m-%d') if not pd.isna(latest_time) else "Unknown"
        
    # 4. Risk Assessment (Top 1)
    risk_results = get_top_risk_states(df, top_n=1)
    top_risk_state = risk_results[0]['state'] if risk_results else "Unknown"
    top_risk_score = risk_results[0]['risk_score'] if risk_results else 0.0
    top_risk_level = risk_results[0]['risk_level'] if risk_results else "Unknown"
    
    # 5. Model Performance (Leaderboard)
    leaderboard = build_model_leaderboard(df)
    best_model = "Unknown"
    best_rmse = 0.0
    if leaderboard and isinstance(leaderboard, list) and "model_name" in leaderboard[0]:
        best_model = leaderboard[0]['model_name']
        best_rmse = round(float(leaderboard[0].get('average_rmse', 0.0)), 2)
        
    # 6. Forecasting and Trend Prediction
    # Map human model names to internal forecast keys
    name_to_key = {
        "Linear Regression": "linear",
        "Ridge Regression": "ridge",
        "Random Forest Regressor": "random_forest",
        "Gradient Boosting Regressor": "gradient_boosting"
    }
    model_key = name_to_key.get(best_model, "linear")
    
    ml_forecasts = forecast_ml_models(df, steps=4)
    trend = "stable"
    if "predictions" in ml_forecasts and model_key in ml_forecasts["predictions"]:
        trend = get_forecast_trend(ml_forecasts["predictions"][model_key])
        
    return {
        "disease": disease_name,
        "total_cases": total_cases,
        "total_deaths": total_deaths,
        "case_fatality_rate": cfr,
        "highest_burden_state": highest_state,
        "highest_burden_state_cases": highest_cases,
        "latest_time_index": latest_time_str,
        "top_risk_state": top_risk_state,
        "top_risk_score": top_risk_score,
        "top_risk_level": top_risk_level,
        "best_model": best_model,
        "best_model_rmse": best_rmse,
        "forecast_trend": trend
    }

def compare_diseases(data_map):
    """
    Main orchestration function to compare multiple diseases.
    data_map should be { "disease_name": dataframe }
    """
    comparison_results = []
    for disease_name, df in data_map.items():
        try:
            summary = summarize_disease(df, disease_name)
            comparison_results.append(summary)
        except Exception as e:
            # Capture errors per disease to prevent total failure
            comparison_results.append({
                "disease": disease_name,
                "error": str(e)
            })
            
    return comparison_results
