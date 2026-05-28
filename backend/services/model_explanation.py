import os
import pandas as pd
from services.model_leaderboard import build_model_leaderboard

def load_standardized(processed_dir, disease_key: str) -> pd.DataFrame:
    path = os.path.join(processed_dir, disease_key, "standardized.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"standardized.csv not found for disease_key={disease_key}")
    df = pd.read_csv(path)
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce").fillna(0)
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").fillna(0)
    return df

def generate_model_explanation(processed_dir, disease):
    """
    Generates a professional explainability report for the best predictive model of the disease.
    """
    df = load_standardized(processed_dir, disease)
    leaderboard = build_model_leaderboard(df)
    
    if not leaderboard or not isinstance(leaderboard, list) or (len(leaderboard) > 0 and "error" in leaderboard[0]):
        error_msg = leaderboard[0]["error"] if leaderboard else "Insufficient data for model evaluation."
        raise ValueError(f"Leaderboard generation failed: {error_msg}")
        
    # Get the best model
    best_item = next((x for x in leaderboard if x.get("best_model") is True), leaderboard[0])
    
    selected_model = best_item.get("model_name", "Unknown")
    selection_reason = best_item.get("reason", "")
    backtesting_windows = best_item.get("number_of_backtest_windows", 0)
    best_model_rmse = best_item.get("average_rmse", 0.0)
    best_model_mae = best_item.get("average_mae", 0.0)
    best_model_mape = best_item.get("average_mape", 0.0)
    
    # Confidence logic
    if best_model_mape <= 20:
        confidence_level = "High"
    elif best_model_mape <= 50:
        confidence_level = "Medium"
    else:
        confidence_level = "Low"
        
    # Build model rankings list
    model_rankings = []
    for item in leaderboard:
        model_rankings.append({
            "rank": item.get("rank"),
            "model_name": item.get("model_name"),
            "average_rmse": item.get("average_rmse"),
            "average_mae": item.get("average_mae"),
            "average_mape": item.get("average_mape"),
            "best_model": item.get("best_model")
        })
        
    if confidence_level == "High":
        reliability_note = "The forecast reliability is strong based on low MAPE and backtesting performance."
    elif confidence_level == "Medium":
        reliability_note = "The forecast is moderately reliable and should be interpreted with surveillance context."
    else:
        reliability_note = "The selected model performed best among evaluated models, but high MAPE indicates uncertainty and forecasts should be interpreted cautiously."
    
    reviewer_explanation = (
        "The model was selected using rolling-origin backtesting. "
        "The model with the lowest RMSE was chosen because RMSE penalizes larger forecast errors, "
        "which is important in outbreak prediction."
    )
    
    return {
        "disease": disease,
        "selected_model": selected_model,
        "selection_reason": selection_reason,
        "backtesting_windows": backtesting_windows,
        "primary_metric": "RMSE",
        "best_model_rmse": best_model_rmse,
        "best_model_mae": best_model_mae,
        "best_model_mape": best_model_mape,
        "confidence_level": confidence_level,
        "model_rankings": model_rankings,
        "reliability_note": reliability_note,
        "reviewer_explanation": reviewer_explanation
    }
