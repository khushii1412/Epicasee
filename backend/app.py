from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json as _json
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from services.features import build_features
from services.model_leaderboard import build_model_leaderboard
from services.forecasting_v2 import forecast_ml_models
from services.anomaly_detection import get_latest_anomaly_summary
from services.risk_engine import get_top_risk_states, generate_risk_summary
from services.alert_feed import generate_alert_feed
from services.disease_comparison_v2 import compare_diseases, get_forecast_trend
from services.intelligence_summary import generate_executive_summary
from services.data_quality import inspect_data_quality
from services.briefing import generate_briefing

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "data_processed")

print(f"[INFO] Backend app.py location: {os.path.abspath(__file__)}")
print(f"[INFO] PROCESSED_DIR: {PROCESSED_DIR}")


def load_standardized(disease_key: str) -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, disease_key, "standardized.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"standardized.csv not found for disease_key={disease_key}")
    df = pd.read_csv(path)
    # Ensure numeric types for aggregation
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce").fillna(0)
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").fillna(0)
    return df


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/diseases")
def diseases():
    disease_keys = ["covid", "dengue", "malaria", "idsp"]
    available = []
    for key in disease_keys:
        path = os.path.join(PROCESSED_DIR, key, "standardized.csv")
        if os.path.exists(path):
            available.append(key)
    return jsonify({"diseases": available})


@app.route("/api/states")
def states():
    disease_key = request.args.get("disease_key")
    if not disease_key:
        return jsonify({"error": "Missing disease_key parameter"}), 400
    try:
        df = load_standardized(disease_key)
        states_list = sorted(df["state"].dropna().unique().tolist())
        return jsonify({"states": states_list})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/districts")
def districts():
    disease_key = request.args.get("disease_key")
    state = request.args.get("state")
    if not disease_key or not state:
        return jsonify({"error": "Missing disease_key or state parameter"}), 400
    try:
        df = load_standardized(disease_key)
        sub = df[df["state"] == state]
        if "district" not in sub.columns:
            return jsonify({"districts": []})
        districts_list = sorted([
            d for d in sub["district"].dropna().unique().tolist()
            if str(d).strip()
        ])
        return jsonify({"districts": districts_list})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/data")
def data():
    disease_key = request.args.get("disease_key")
    state = request.args.get("state")
    district = request.args.get("district")
    if not disease_key:
        return jsonify({"error": "Missing disease_key parameter"}), 400
    try:
        df = load_standardized(disease_key)
        if state:
            df = df[df["state"] == state]
        if district:
            if "district" in df.columns:
                df = df[df["district"] == district]
        records = _json.loads(df.to_json(orient="records"))
        return jsonify({"data": records, "count": len(records)})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/forecast")
def forecast():
    """Run ARIMA, SARIMA, and Linear Regression on historical data and return forecasts."""
    disease_key = request.args.get("disease_key")
    state = request.args.get("state")
    steps = int(request.args.get("steps", 4))  # quarters ahead

    if not disease_key or not state:
        return jsonify({"error": "disease_key and state required"}), 400

    try:
        from statsmodels.tsa.arima.model import ARIMA
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        from sklearn.linear_model import LinearRegression

        df = load_standardized(disease_key)
        df = df[df["state"] == state].copy()
        df["time_index"] = pd.to_datetime(df["time_index"])
        df = df.sort_values("time_index")
        series = df.set_index("time_index")["cases"].astype(float)

        if len(series) < 8:
            return jsonify({"error": "Not enough data points for forecasting (need ≥8)"}), 422

        historical = [{"date": str(idx.date()), "actual": float(v)} for idx, v in series.items()]
        last_date = series.index[-1]
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=3), periods=steps, freq="QS")
        future_dates_str = [str(d.date()) for d in future_dates]

        results = {}

        # ── ARIMA(2,1,2) ──────────────────────────────────────
        try:
            arima_model = ARIMA(series, order=(2, 1, 2)).fit()
            arima_fc = arima_model.get_forecast(steps=steps)
            arima_mean = arima_fc.predicted_mean.values.tolist()
            arima_ci = arima_fc.conf_int(alpha=0.2).values.tolist()
            arima_aic = round(arima_model.aic, 2)
            in_sample = arima_model.fittedvalues.values
            arima_rmse = round(float(np.sqrt(np.mean((series.values[1:] - in_sample[1:]) ** 2))), 2)
            arima_mae = round(float(np.mean(np.abs(series.values[1:] - in_sample[1:]))), 2)
            results["arima"] = {
                "forecast": [max(0, v) for v in arima_mean],
                "lower": [max(0, ci[0]) for ci in arima_ci],
                "upper": [ci[1] for ci in arima_ci],
                "aic": arima_aic,
                "rmse": arima_rmse,
                "mae": arima_mae,
                "description": "ARIMA(2,1,2): Auto-Regressive Integrated Moving Average. Captures non-seasonal trends and autocorrelation patterns.",
            }
        except Exception as e:
            results["arima"] = {"error": str(e)}

        # ── SARIMA(1,1,1)(1,1,0,4) ────────────────────────────
        try:
            sarima_model = SARIMAX(series, order=(1, 1, 1), seasonal_order=(1, 1, 0, 4)).fit(disp=False)
            sarima_fc = sarima_model.get_forecast(steps=steps)
            sarima_mean = sarima_fc.predicted_mean.values.tolist()
            sarima_ci = sarima_fc.conf_int(alpha=0.2).values.tolist()
            sarima_aic = round(sarima_model.aic, 2)
            sarima_fitted = sarima_model.fittedvalues.values
            trim = min(len(series), len(sarima_fitted))
            sarima_rmse = round(float(np.sqrt(np.mean((series.values[-trim:] - sarima_fitted[-trim:]) ** 2))), 2)
            sarima_mae = round(float(np.mean(np.abs(series.values[-trim:] - sarima_fitted[-trim:]))), 2)
            results["sarima"] = {
                "forecast": [max(0, v) for v in sarima_mean],
                "lower": [max(0, ci[0]) for ci in sarima_ci],
                "upper": [ci[1] for ci in sarima_ci],
                "aic": sarima_aic,
                "rmse": sarima_rmse,
                "mae": sarima_mae,
                "description": "SARIMA(1,1,1)(1,1,0,4): Seasonal ARIMA with quarterly seasonality. Ideal for diseases with regular seasonal outbreaks.",
            }
        except Exception as e:
            results["sarima"] = {"error": str(e)}

        # ── Linear Regression ─────────────────────────────────
        try:
            X = np.arange(len(series)).reshape(-1, 1)
            y = series.values
            lr = LinearRegression().fit(X, y)
            X_future = np.arange(len(series), len(series) + steps).reshape(-1, 1)
            lr_pred = lr.predict(X_future).tolist()
            lr_fitted = lr.predict(X)
            lr_rmse = round(float(np.sqrt(np.mean((y - lr_fitted) ** 2))), 2)
            lr_mae = round(float(np.mean(np.abs(y - lr_fitted))), 2)
            lr_r2 = round(float(lr.score(X, y)), 4)
            results["linear"] = {
                "forecast": [max(0, v) for v in lr_pred],
                "lower": [max(0, v * 0.8) for v in lr_pred],
                "upper": [v * 1.2 for v in lr_pred],
                "rmse": lr_rmse,
                "mae": lr_mae,
                "r2": lr_r2,
                "slope": round(float(lr.coef_[0]), 4),
                "description": "Linear Regression: Baseline trend model. Captures the overall direction (increasing/decreasing) of disease burden.",
            }
        except Exception as e:
            results["linear"] = {"error": str(e)}

        return jsonify({
            "disease": disease_key,
            "state": state,
            "historical": historical,
            "future_dates": future_dates_str,
            "models": results,
        })

    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/comparison")
def comparison():
    """Return top states by total cases for a disease."""
    disease_key = request.args.get("disease_key")
    top_n = int(request.args.get("top", 10))
    if not disease_key:
        return jsonify({"error": "disease_key required"}), 400
    try:
        df = load_standardized(disease_key)
        summary = (
            df.groupby("state")
            .agg(total_cases=("cases", "sum"), total_deaths=("deaths", "sum"))
            .reset_index()
            .sort_values("total_cases", ascending=False)
            .head(top_n)
        )
        summary["total_cases"] = summary["total_cases"].astype(int)
        summary["total_deaths"] = summary["total_deaths"].astype(int)
        summary["cfr"] = (summary["total_deaths"] / summary["total_cases"] * 100).round(2)
        records = _json.loads(summary.to_json(orient="records"))
        return jsonify({"data": records})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/features/preview")
def features_preview():
    """Generate and return a preview of engineered features for Dengue."""
    try:
        # 1. Load sample data (Dengue)
        df = load_standardized("dengue")
        
        # 2. Build features
        df_featured = build_features(df)
        
        # 3. Select requested columns
        cols = [
            "state", "district", "time_index", "cases", "deaths", 
            "year", "quarter", "lag_1_cases", "rolling_mean_4", 
            "growth_rate", "case_fatality_rate", "is_monsoon_quarter", 
            "z_score_cases", "outbreak_intensity_score"
        ]
        
        # Filter columns that actually exist (defensive)
        available_cols = [c for c in cols if c in df_featured.columns]
        preview = df_featured[available_cols].head(10).copy()
        
        # Convert time_index to string for readable JSON
        if "time_index" in preview.columns:
            preview["time_index"] = preview["time_index"].dt.strftime("%Y-%m-%d")
        
        # 4. Return as JSON
        records = _json.loads(preview.to_json(orient="records"))
        return jsonify({
            "count": len(records),
            "columns": available_cols,
            "data": records
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/model-leaderboard")
def model_leaderboard():
    """
    Returns a ranked leaderboard of ML models for a specific disease.
    Uses rolling-origin backtesting metrics (RMSE, MAE, R2, etc.).
    """
    disease = request.args.get("disease", "dengue")
    try:
        # Load the relevant dataset
        df = load_standardized(disease)
        
        # Build the leaderboard using the service
        leaderboard = build_model_leaderboard(df)
        
        return jsonify({
            "disease": disease,
            "count": len(leaderboard) if isinstance(leaderboard, list) else 0,
            "leaderboard": leaderboard
        })
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/best-model-forecast")
def best_model_forecast():
    """
    Identifies the best model via backtesting and returns its forecast.
    """
    disease = request.args.get("disease", "dengue")
    try:
        # 1. Load data
        df = load_standardized(disease)
        
        # 2. Get leaderboard to find the best model (Rank 1)
        leaderboard = build_model_leaderboard(df)
        if not leaderboard or (isinstance(leaderboard, list) and "error" in leaderboard[0]):
            error_msg = leaderboard[0]["error"] if leaderboard else "Unknown error"
            return jsonify({"error": f"Leaderboard generation failed: {error_msg}"}), 500
            
        best_model_data = leaderboard[0]
        model_name = best_model_data["model_name"]
        
        # 3. Generate forecasts for all ML models
        ml_results = forecast_ml_models(df, steps=4)
        if "error" in ml_results:
            return jsonify({"error": f"Forecast generation failed: {ml_results['error']}"}), 500
            
        # 4. Map model name to internal key
        name_to_key = {
            "Linear Regression": "linear",
            "Ridge Regression": "ridge",
            "Random Forest Regressor": "random_forest",
            "Gradient Boosting Regressor": "gradient_boosting"
        }
        model_key = name_to_key.get(model_name)
        
        if not model_key or model_key not in ml_results["predictions"]:
            return jsonify({"error": f"Prediction key '{model_key}' not found for model '{model_name}'"}), 500
            
        predictions = ml_results["predictions"][model_key]
        future_dates = ml_results["future_dates"]
        
        # 5. Format the specific forecast for the best model with uncertainty bands
        forecast_payload = []
        rmse = best_model_data.get("average_rmse", 0.0)
        mape = best_model_data.get("average_mape", 100.0)
        
        # Determine confidence level based on MAPE
        if mape <= 20:
            confidence = "High"
        elif mape <= 50:
            confidence = "Medium"
        else:
            confidence = "Low"

        for i in range(len(predictions)):
            pred_val = float(predictions[i])
            
            # Confidence Band Formula: pred +/- 1.96 * RMSE
            lower = max(0.0, pred_val - (1.96 * rmse))
            upper = pred_val + (1.96 * rmse)
            
            forecast_payload.append({
                "date": future_dates[i],
                "predicted_cases": round(max(0.0, pred_val), 2),
                "lower_bound": round(lower, 2),
                "upper_bound": round(upper, 2),
                "confidence_level": confidence
            })
            
        return jsonify({
            "disease": disease,
            "best_model": model_name,
            "model_key": model_key,
            "selection_reason": best_model_data["reason"],
            "future_dates": future_dates,
            "forecast": forecast_payload,
            "leaderboard_summary": {
                "average_rmse": best_model_data["average_rmse"],
                "average_mae": best_model_data["average_mae"],
                "average_mape": best_model_data["average_mape"],
                "number_of_backtest_windows": best_model_data["number_of_backtest_windows"]
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/anomalies/latest")
def anomalies_latest():
    """
    Returns the latest anomaly detection results for a specific disease.
    Uses rolling Z-scores to identify outbreak spikes.
    """
    disease = request.args.get("disease", "dengue")
    try:
        # Load the relevant dataset
        df = load_standardized(disease)
        
        # Get the most recent anomalies using the service
        anomalies = get_latest_anomaly_summary(df)
        
        return jsonify({
            "disease": disease,
            "count": len(anomalies),
            "anomalies": anomalies
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/risk/top")
def risk_top():
    """
    Returns the top regions with the highest outbreak risk scores.
    Combines cases, growth, fatality, and statistical anomalies.
    """
    disease = request.args.get("disease", "dengue")
    top_n = request.args.get("top_n", default=10, type=int)
    
    try:
        # Load the relevant dataset
        df = load_standardized(disease)
        
        # Calculate risk scores and get top N
        risk_states = get_top_risk_states(df, top_n=top_n)
        
        return jsonify({
            "disease": disease,
            "count": len(risk_states),
            "risk_states": risk_states
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/alerts")
def alerts():
    """
    Returns a feed of outbreak alerts based on current risk levels.
    """
    disease = request.args.get("disease", "dengue")
    top_n = request.args.get("top_n", default=10, type=int)
    
    try:
        # Load the relevant dataset
        df = load_standardized(disease)
        
        # Generate the alert feed using the service
        alerts_list = generate_alert_feed(df, disease=disease, top_n=top_n)
        
        return jsonify({
            "disease": disease,
            "count": len(alerts_list),
            "alerts": alerts_list
        })
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/disease-comparison-v2")
def disease_comparison_v2():
    """
    Returns a high-level comparison across COVID, Dengue, and Malaria.
    """
    try:
        # Load data for all three major diseases
        data_map = {
            "covid": load_standardized("covid"),
            "dengue": load_standardized("dengue"),
            "malaria": load_standardized("malaria")
        }
        
        # Run the comparison engine
        comparison = compare_diseases(data_map)
        
        return jsonify({
            "count": len(comparison),
            "comparison": comparison
        })
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/intelligence-summary")
def intelligence_summary():
    """
    Returns a government-style Executive Intelligence Summary across major diseases.
    """
    try:
        summary = generate_executive_summary()
        return jsonify(summary)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/state-profile")
def state_profile():
    """
    Returns a comprehensive public health profile for a specific state and disease.
    """
    disease = request.args.get("disease", "dengue")
    state = request.args.get("state")
    
    if not state:
        return jsonify({"error": "state query parameter is required"}), 400
        
    try:
        # Load standardized data for the disease
        df = load_standardized(disease)
        
        # Verify state exists in df
        available_states = df["state"].dropna().unique()
        if state not in available_states:
            return jsonify({"error": f"State '{state}' not found for disease '{disease}'"}), 404
            
        # Get historical state data for aggregation and latest record
        df_state = df[df["state"] == state].copy()
        
        # Aggregate statistics
        total_cases = int(df_state["cases"].sum())
        total_deaths = int(df_state["deaths"].sum())
        case_fatality_rate = float(round((total_deaths / total_cases * 100), 4)) if total_cases > 0 else 0.0
        
        # Chronologically sort state data to find the latest time index and records
        df_state["time_index"] = pd.to_datetime(df_state["time_index"])
        df_state_sorted = df_state.sort_values("time_index")
        
        latest_row = df_state_sorted.iloc[-1]
        latest_time_index = latest_row["time_index"].strftime("%Y-%m-%d")
        latest_cases = float(latest_row["cases"])
        latest_deaths = float(latest_row["deaths"])
        
        # Risk assessment & anomalies on the full dataset (for proper relative normalization)
        risk_summary = generate_risk_summary(df)
        state_risk = next((x for x in risk_summary if x["state"] == state), None)
        
        if state_risk:
            risk_score = float(state_risk.get("risk_score", 0.0))
            risk_level = state_risk.get("risk_level", "Low")
            anomaly_status = state_risk.get("anomaly_status", "Normal")
            z_score = float(state_risk.get("z_score", 0.0))
        else:
            risk_score = 0.0
            risk_level = "Low"
            anomaly_status = "Normal"
            z_score = 0.0
            
        # Model Performance (Leaderboard) for the selected disease (using full df)
        leaderboard = build_model_leaderboard(df)
        best_model = "Unknown"
        best_model_rmse = 0.0
        if leaderboard and isinstance(leaderboard, list) and len(leaderboard) > 0 and "error" not in leaderboard[0]:
            best_item = next((x for x in leaderboard if x.get("best_model") is True), None)
            if not best_item:
                best_item = leaderboard[0]
            best_model = best_item.get("model_name", "Unknown")
            best_model_rmse = round(float(best_item.get("average_rmse", 0.0)), 2)
            
        # Forecasting for the selected disease (using full df)
        name_to_key = {
            "Linear Regression": "linear",
            "Ridge Regression": "ridge",
            "Random Forest Regressor": "random_forest",
            "Gradient Boosting Regressor": "gradient_boosting"
        }
        model_key = name_to_key.get(best_model, "linear")
        
        ml_forecasts = forecast_ml_models(df, steps=4)
        forecast_trend = "stable"
        if "predictions" in ml_forecasts and model_key in ml_forecasts["predictions"]:
            forecast_vals = ml_forecasts["predictions"][model_key]
            if forecast_vals and len(forecast_vals) >= 2:
                first_val = float(forecast_vals[0])
                last_val = float(forecast_vals[-1])
                if first_val == 0:
                    forecast_trend = "increasing" if last_val > 0 else "stable"
                else:
                    change_pct = (last_val - first_val) / first_val
                    if change_pct > 0.05:
                        forecast_trend = "increasing"
                    elif change_pct < -0.05:
                        forecast_trend = "decreasing"
                    else:
                        forecast_trend = "stable"
            
        # Alert priority and message
        alerts_list = generate_alert_feed(df, disease=disease, top_n=1000)
        state_alert = next((x for x in alerts_list if x["state"] == state), None)
        
        if state_alert:
            alert_priority = state_alert.get("priority", "Low")
            alert_message = state_alert.get("message", "")
        else:
            alert_priority = "Low"
            alert_message = ""
            
        return jsonify({
            "disease": disease,
            "state": state,
            "total_cases": total_cases,
            "total_deaths": total_deaths,
            "case_fatality_rate": case_fatality_rate,
            "latest_time_index": latest_time_index,
            "latest_cases": latest_cases,
            "latest_deaths": latest_deaths,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "anomaly_status": anomaly_status,
            "z_score": z_score,
            "forecast_trend": forecast_trend,
            "best_model": best_model,
            "best_model_rmse": best_model_rmse,
            "alert_priority": alert_priority,
            "alert_message": alert_message
        })
        
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/data-quality")
def data_quality():
    """
    Returns data quality and credibility metrics across standardized datasets.
    """
    try:
        results = inspect_data_quality(PROCESSED_DIR)
        return jsonify(results)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/briefing")
def briefing():
    """
    Returns an executive early warning public-health brief.
    """
    try:
        results = generate_briefing(PROCESSED_DIR)
        return jsonify(results)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  India Epidemiology Backend Server Starting")
    print("="*60)
    print(f"  Backend running at: http://127.0.0.1:5001")
    print(f"  Health check:       http://127.0.0.1:5001/api/health")
    print(f"  Forecast:           http://127.0.0.1:5001/api/forecast")
    print("="*60 + "\n")
    app.run(port=5001, debug=True)
