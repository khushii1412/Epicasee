from services.backtesting import run_rolling_backtest

def rank_models(backtest_results):
    """
    Ranks models based on their backtesting performance metrics.
    Primary sort: lowest average_rmse.
    Secondary sort: lowest average_mae.
    
    Args:
        backtest_results (list): List of summarized model metrics.
        
    Returns:
        list: Sorted list of model metrics.
    """
    if not isinstance(backtest_results, list) or not backtest_results:
        return []
        
    # Check if the list contains an error message instead of results
    if len(backtest_results) > 0 and "error" in backtest_results[0]:
        return []

    # Sort logic: Primary = RMSE (lower is better), Secondary = MAE (lower is better)
    sorted_results = sorted(
        backtest_results,
        key=lambda x: (
            x.get('average_rmse', float('inf')),
            x.get('average_mae', float('inf'))
        )
    )
    
    return sorted_results

def get_best_model(backtest_results):
    """
    Identifies the top-performing model from backtesting results.
    
    Args:
        backtest_results (list): Summarized model metrics.
        
    Returns:
        dict: Metrics of the best model, or None.
    """
    ranked = rank_models(backtest_results)
    return ranked[0] if ranked else None

def explain_model_choice(model_result, is_best=False):
    """
    Provides a short textual explanation for a model's rank or selection.
    
    Args:
        model_result (dict): Metrics for a specific model.
        is_best (bool): Whether this model is the top-ranked one.
        
    Returns:
        str: Human-readable explanation.
    """
    name = model_result.get('model_name', 'Model')
    rmse = model_result.get('average_rmse', 0.0)
    mae = model_result.get('average_mae', 0.0)
    
    if is_best:
        return (f"Selected as best model because it achieved the lowest RMSE ({rmse}) "
                f"and competitive MAE ({mae}) during rolling-origin backtesting.")
    
    return f"Ranked performance with an average RMSE of {rmse}."

def build_model_leaderboard(df):
    """
    Orchestrates the backtesting, ranking, and explanation process to build a leaderboard.
    
    Args:
        df (pd.DataFrame): The dataset to evaluate models on.
        
    Returns:
        list: A JSON-friendly leaderboard with ranks, metrics, and explanations.
    """
    # 1. Run the backtesting engine to get summarized metrics for all models
    # This uses the default summarized output from services.backtesting
    backtest_results = run_rolling_backtest(df)
    
    # 2. Handle cases with insufficient data or errors
    if isinstance(backtest_results, list) and len(backtest_results) > 0 and "error" in backtest_results[0]:
        return backtest_results
        
    # 3. Rank models based on the defined logic (RMSE then MAE)
    ranked_models = rank_models(backtest_results)
    
    # 4. Construct the final leaderboard with rank numbers and qualitative explanations
    leaderboard = []
    for i, model in enumerate(ranked_models):
        is_best = (i == 0)
        
        # Build the leaderboard entry
        entry = {
            "rank": i + 1,
            "model_name": model.get("model_name"),
            "average_rmse": model.get("average_rmse"),
            "average_mae": model.get("average_mae"),
            "average_mape": model.get("average_mape"),
            "average_smape": model.get("average_smape"),
            "average_r2": model.get("average_r2"),
            "number_of_backtest_windows": model.get("number_of_backtest_windows"),
            "best_model": is_best,
            "reason": explain_model_choice(model, is_best=is_best)
        }
        leaderboard.append(entry)
        
    return leaderboard
