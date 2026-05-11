from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json as _json
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from services.features import build_features

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


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  India Epidemiology Backend Server Starting")
    print("="*60)
    print(f"  Backend running at: http://127.0.0.1:5001")
    print(f"  Health check:       http://127.0.0.1:5001/api/health")
    print(f"  Forecast:           http://127.0.0.1:5001/api/forecast")
    print("="*60 + "\n")
    app.run(port=5001, debug=True)
