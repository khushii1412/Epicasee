import os
import pandas as pd
import numpy as np

from services.disease_comparison_v2 import compare_diseases
from services.alert_feed import generate_alert_feed
from services.risk_engine import get_top_risk_states

def load_standardized(processed_dir, disease_key: str) -> pd.DataFrame:
    path = os.path.join(processed_dir, disease_key, "standardized.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"standardized.csv not found for disease_key={disease_key}")
    df = pd.read_csv(path)
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce").fillna(0)
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").fillna(0)
    return df

def generate_briefing(processed_dir):
    """
    Generates a readable executive early warning briefing across covid, dengue, and malaria datasets.
    """
    # 1. Load all three disease datasets
    data_map = {
        "covid": load_standardized(processed_dir, "covid"),
        "dengue": load_standardized(processed_dir, "dengue"),
        "malaria": load_standardized(processed_dir, "malaria")
    }
    
    # 2. Run disease comparison service
    comparison_results = compare_diseases(data_map)
    
    # Identify comparative stats
    highest_risk_item = max(comparison_results, key=lambda x: x.get("top_risk_score", 0.0))
    highest_risk_disease = highest_risk_item["disease"]
    highest_risk_score = highest_risk_item["top_risk_score"]
    top_hotspot_state = highest_risk_item["top_risk_state"]
    
    highest_burden_item = max(comparison_results, key=lambda x: x.get("total_cases", 0.0))
    highest_case_disease = highest_burden_item["disease"]
    highest_case_count = highest_burden_item["total_cases"]
    
    # 3. Use alert feed to aggregate and count warning levels (evaluate all checked states/regions)
    alerts_covid = generate_alert_feed(data_map["covid"], disease="covid", top_n=1000)
    alerts_dengue = generate_alert_feed(data_map["dengue"], disease="dengue", top_n=1000)
    alerts_malaria = generate_alert_feed(data_map["malaria"], disease="malaria", top_n=1000)
    
    all_alerts = alerts_covid + alerts_dengue + alerts_malaria
    high_count = sum(1 for a in all_alerts if a.get("priority") == "High")
    med_count = sum(1 for a in all_alerts if a.get("priority") == "Medium")
    
    # Determine overall risk level
    if high_count > 0:
        overall_risk_level = "High"
    elif med_count > 0:
        overall_risk_level = "Medium"
    else:
        overall_risk_level = "Low"
        
    # 4. Use risk engine to extract top risk states per disease
    disease_briefs = []
    recommended_attention = []
    
    for item in comparison_results:
        dis = item["disease"]
        state = item["top_risk_state"]
        score = item["top_risk_score"]
        lvl = item["top_risk_level"]
        trend = item["forecast_trend"]
        cases = item["total_cases"]
        
        disease_briefs.append({
            "disease": dis,
            "risk_score": score,
            "risk_level": lvl,
            "hotspot_state": state,
            "forecast_trend": trend,
            "total_cases": cases,
            "summary": f"{dis.capitalize()}: peak risk is {lvl} (score: {score}) in hotspot {state}. Forecast trend is {trend}."
        })
        
        if lvl == "High":
            recommended_attention.append(
                f"Immediate resource allocation, clinical containment protocols, and localized testing in {state} ({dis.upper()})."
            )
        elif lvl == "Medium":
            recommended_attention.append(
                f"Monsoon preparedness, active public-health surveillance, and diagnostics monitoring in {state} ({dis.capitalize()})."
            )
        else:
            recommended_attention.append(
                f"Routine seasonal monitoring and prophylactic distribution in {state} ({dis.capitalize()})."
            )
            
    # 5. Extract specific indicators for deterministic brief
    covid_state = next(x["top_risk_state"] for x in comparison_results if x["disease"] == "covid")
    dengue_state = next(x["top_risk_state"] for x in comparison_results if x["disease"] == "dengue")
    malaria_state = next(x["top_risk_state"] for x in comparison_results if x["disease"] == "malaria")
    
    covid_trend = next(x["forecast_trend"] for x in comparison_results if x["disease"] == "covid")
    dengue_trend = next(x["forecast_trend"] for x in comparison_results if x["disease"] == "dengue")
    malaria_trend = next(x["forecast_trend"] for x in comparison_results if x["disease"] == "malaria")
    
    # 6. Generate dynamic deterministic executive brief narrative
    highest_risk_cap = highest_risk_disease.upper() if highest_risk_disease == "covid" else highest_risk_disease.capitalize()
    
    executive_brief = (
        f"{highest_risk_cap} currently shows the highest national risk, with {top_hotspot_state} flagged as the leading hotspot due to high case burden and mortality impact. "
        f"Dengue risk remains concentrated in {dengue_state}, while Malaria risk is highest in {malaria_state}. "
        f"Forecast signals show {covid_trend} trends for COVID and {malaria_trend} for Malaria, while Dengue remains {dengue_trend}. "
        f"Continued surveillance is recommended for all medium and high-risk states."
    )
    
    # Construct Key Findings
    key_findings = [
        f"Highest outbreak risk identified for {highest_risk_cap} with peak risk score of {highest_risk_score}/100 centered in {top_hotspot_state}.",
        f"Cumulative case burden is highest for {highest_case_disease.capitalize()} at {highest_case_count:,} cases nationally.",
        f"Active surveillance system triggered {high_count} High-priority and {med_count} Medium-priority warning alerts across surveyed territories."
    ]
    
    return {
        "briefing_title": "National Multi-Disease Early Warning Brief",
        "overall_risk_level": overall_risk_level,
        "key_findings": key_findings,
        "disease_briefs": disease_briefs,
        "recommended_attention": recommended_attention,
        "executive_brief": executive_brief
    }
