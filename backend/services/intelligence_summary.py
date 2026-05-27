import os
import pandas as pd
from services.disease_comparison_v2 import compare_diseases
from services.risk_engine import get_top_risk_states
from services.alert_feed import generate_alert_feed

# Define data processed directory relative to this service file
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SERVICES_DIR)
PROCESSED_DIR = os.path.join(BACKEND_DIR, "data_processed")

def load_standardized(disease_key: str) -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, disease_key, "standardized.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"standardized.csv not found for disease_key={disease_key}")
    df = pd.read_csv(path)
    # Ensure numeric types for aggregation
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce").fillna(0)
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").fillna(0)
    return df

def generate_executive_summary():
    """
    Orchestrates the calculations to produce a government-style Executive Intelligence Summary.
    """
    # 1. Load data for COVID, Dengue, and Malaria
    data_map = {
        "covid": load_standardized("covid"),
        "dengue": load_standardized("dengue"),
        "malaria": load_standardized("malaria")
    }

    # 2. Run the disease comparison engine
    comparison = compare_diseases(data_map)

    # 3. Check for error logs within the comparison results to escalate as system exceptions
    for item in comparison:
        if "error" in item:
            raise ValueError(f"Comparison error in {item['disease']}: {item['error']}")

    # 4. Determine national_risk_level
    # High if any disease has a top risk level High
    # Medium if any disease has a top risk level Medium
    # Low otherwise
    risk_levels = [item.get("top_risk_level", "Low") for item in comparison]
    if "High" in risk_levels:
        national_risk_level = "High"
    elif "Medium" in risk_levels:
        national_risk_level = "Medium"
    else:
        national_risk_level = "Low"

    # 5. Determine highest_risk_disease
    # Disease with the highest top_risk_score from disease comparison
    highest_risk_item = max(comparison, key=lambda x: x.get("top_risk_score", 0.0))
    highest_risk_disease = highest_risk_item["disease"]

    # 6. Determine top_hotspot_state & top_hotspot_disease
    # State with the highest risk_score across all diseases
    # Disease associated with the top hotspot state
    top_hotspot_state = "Unknown"
    top_hotspot_score = -1.0
    top_hotspot_disease = "Unknown"

    for disease, df in data_map.items():
        top_states = get_top_risk_states(df, top_n=1)
        if top_states:
            top_s = top_states[0]
            if top_s.get("risk_score", 0.0) > top_hotspot_score:
                top_hotspot_score = top_s.get("risk_score", 0.0)
                top_hotspot_state = top_s.get("state", "Unknown")
                top_hotspot_disease = disease

    # 7. Count alerts across the major diseases
    active_high_alerts = 0
    active_medium_alerts = 0

    for disease, df in data_map.items():
        # Using a top_n value large enough to scan all possible states and districts
        alerts = generate_alert_feed(df, disease=disease, top_n=100)
        for alert in alerts:
            if alert.get("priority") == "High":
                active_high_alerts += 1
            elif alert.get("priority") == "Medium":
                active_medium_alerts += 1

    # 8. Determine best_forecasting_model
    # Most frequently selected best model across all diseases
    # If tied, choose the one attached to the highest-risk disease
    model_counts = {}
    for item in comparison:
        model = item.get("best_model", "Unknown")
        model_counts[model] = model_counts.get(model, 0) + 1

    max_count = max(model_counts.values()) if model_counts else 0
    candidates = [m for m, count in model_counts.items() if count == max_count]

    if len(candidates) == 1:
        best_forecasting_model = candidates[0]
    else:
        # Tie-breaker: choose the model of the highest-risk disease
        best_forecasting_model = highest_risk_item.get("best_model", "Unknown")

    # 9. Determine forecast_trend_summary
    forecast_trend_summary = {
        "increasing": 0,
        "decreasing": 0,
        "stable": 0
    }
    for item in comparison:
        trend = item.get("forecast_trend", "stable")
        if trend in forecast_trend_summary:
            forecast_trend_summary[trend] += 1

    # 10. Compute aggregated case and death totals
    total_cases_all_diseases = sum(item.get("total_cases", 0) for item in comparison)
    total_deaths_all_diseases = sum(item.get("total_deaths", 0) for item in comparison)

    # 11. Create disease_snapshot
    disease_snapshot = []
    for item in comparison:
        disease_snapshot.append({
            "disease": item["disease"],
            "total_cases": item["total_cases"],
            "total_deaths": item["total_deaths"],
            "case_fatality_rate": item["case_fatality_rate"],
            "top_risk_state": item["top_risk_state"],
            "top_risk_score": item["top_risk_score"],
            "top_risk_level": item["top_risk_level"],
            "best_model": item["best_model"],
            "forecast_trend": item["forecast_trend"]
        })

    # 12. Create readable deterministic one-line summary
    hr_disease_formatted = "COVID" if highest_risk_disease == "covid" else highest_risk_disease.capitalize()
    
    other_diseases = [d for d in ["covid", "dengue", "malaria"] if d != highest_risk_disease]
    other_formatted = [("COVID" if d == "covid" else d.capitalize()) for d in other_diseases]

    # Combine other disease risk strings
    other_risks_desc = " and ".join(other_formatted)

    executive_message = (
        f"{hr_disease_formatted} currently shows the highest overall risk, with {top_hotspot_state} flagged as the top hotspot. "
        f"{other_risks_desc} remain under surveillance based on current risk levels and alerts."
    )

    return {
        "national_risk_level": national_risk_level,
        "highest_risk_disease": highest_risk_disease,
        "top_hotspot_state": top_hotspot_state,
        "top_hotspot_disease": top_hotspot_disease,
        "active_high_alerts": active_high_alerts,
        "active_medium_alerts": active_medium_alerts,
        "best_forecasting_model": best_forecasting_model,
        "forecast_trend_summary": forecast_trend_summary,
        "total_cases_all_diseases": total_cases_all_diseases,
        "total_deaths_all_diseases": total_deaths_all_diseases,
        "disease_snapshot": disease_snapshot,
        "executive_message": executive_message
    }
