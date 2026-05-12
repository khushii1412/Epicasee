from services.risk_engine import get_top_risk_states

def classify_alert_priority(risk_level, risk_score):
    """
    Determines alert priority based on the combination of 
    risk level category and the underlying numeric risk score.
    """
    if risk_level == "High" or risk_score >= 70:
        return "High"
    elif risk_level == "Medium" or risk_score >= 36:
        return "Medium"
    else:
        return "Low"

def build_alert_message(risk_row, disease):
    """
    Constructs a descriptive, human-readable alert message 
    outlining the risk factors for a specific location.
    """
    state = risk_row['state']
    district = risk_row.get('district', 'Unknown')
    score = risk_row['risk_score']
    level = risk_row['risk_level']
    reason = risk_row['reason']
    status = risk_row['anomaly_status']
    z = risk_row['z_score']
    
    location = state
    if district and district != 'Unknown' and str(district).strip():
        location = f"{district}, {state}"
        
    # Build the base message
    msg = (
        f"Public health alert for {disease.capitalize()} in {location}. "
        f"The current risk score is {score}/100, categorized as {level}. "
        f"Primary risk drivers: {reason} "
    )
    
    # Append statistical context
    if status != "Normal":
        msg += f"Additionally, a statistical anomaly has been detected (Z-score: {z})."
    else:
        msg += "Case counts are currently within expected statistical bounds (Z-score: {z}).".format(z=z)
        
    return msg

def generate_alert_feed(df, disease="dengue", top_n=10):
    """
    Generates a list of outbreak alerts by processing 
    the highest risk regions identified by the risk engine.
    """
    # 1. Get raw risk data for the top N states
    risk_states = get_top_risk_states(df, top_n=top_n)
    
    alert_feed = []
    
    # 2. Transform each risk record into a structured alert
    for row in risk_states:
        priority = classify_alert_priority(row['risk_level'], row['risk_score'])
        
        # Title format: "<Priority> <Disease> Risk in <State>"
        title = f"{priority} {disease.capitalize()} Risk in {row['state']}"
        
        # Comprehensive message
        message = build_alert_message(row, disease)
        
        alert_feed.append({
            "priority": priority,
            "title": title,
            "message": message,
            "disease": disease,
            "state": row['state'],
            "district": row['district'],
            "risk_score": row['risk_score'],
            "risk_level": row['risk_level'],
            "anomaly_status": row['anomaly_status'],
            "time_index": row['time_index']
        })
        
    return alert_feed
