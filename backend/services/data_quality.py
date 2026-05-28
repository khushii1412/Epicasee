import os
import pandas as pd
import numpy as np

def inspect_data_quality(processed_dir):
    """
    Inspects standardized datasets for covid, dengue, and malaria,
    and calculates data quality metrics and overall summary.
    """
    diseases = ["covid", "dengue", "malaria"]
    required_columns = ["state", "district", "time_index", "cases", "deaths"]
    
    sources = {
        "covid": "MoHFW / COVID historical public datasets",
        "dengue": "NCVBDC / NCDC public health records",
        "malaria": "NCVBDC public health records"
    }
    
    credibility_notes = {
        "covid": "Comprehensive national data updated from official MoHFW dashboards and historical time-series repositories.",
        "dengue": "Quarterly public health surveillance records monitored through national vector-borne disease control programs.",
        "malaria": "Standardized vector-borne surveillance data compiled across state healthcare centers and public reporting portals."
    }
    
    datasets = []
    total_rows_all_diseases = 0
    unique_states_all = set()
    overall_schema_status = "Valid"
    total_missing_values = 0
    total_cells_all = 0
    
    for disease in diseases:
        path = os.path.join(processed_dir, disease, "standardized.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"standardized.csv not found for disease={disease}")
            
        df = pd.read_csv(path)
        row_count = len(df)
        column_count = len(df.columns)
        
        # Calculate states covered
        states = df["state"].dropna().unique().tolist()
        states_covered = len(states)
        unique_states_all.update(states)
        
        # Calculate date range
        if "time_index" in df.columns:
            date_range_start = str(df["time_index"].min())
            date_range_end = str(df["time_index"].max())
        else:
            date_range_start = "N/A"
            date_range_end = "N/A"
            
        # Calculate totals
        total_cases = int(pd.to_numeric(df["cases"], errors="coerce").fillna(0).sum()) if "cases" in df.columns else 0
        total_deaths = int(pd.to_numeric(df["deaths"], errors="coerce").fillna(0).sum()) if "deaths" in df.columns else 0
        
        # Missing values (count of NaN/Null across the entire dataframe, excluding district blanks)
        cols_to_check = [c for c in df.columns if c != "district"]
        missing_values = int(df[cols_to_check].isna().sum().sum())
        total_missing_values += missing_values
        
        cells_to_check = row_count * len(cols_to_check)
        total_cells_all += cells_to_check
        
        missing_value_percentage = round((missing_values / cells_to_check * 100), 2) if cells_to_check > 0 else 0.0
        
        # Schema verification
        required_columns_present = [col for col in required_columns if col in df.columns]
        is_schema_valid = all(col in df.columns for col in required_columns)
        schema_status = "Valid" if is_schema_valid else "Invalid"
        
        if schema_status == "Invalid":
            overall_schema_status = "Invalid"
            
        datasets.append({
            "disease": disease,
            "row_count": row_count,
            "column_count": column_count,
            "states_covered": states_covered,
            "date_range_start": date_range_start,
            "date_range_end": date_range_end,
            "total_cases": total_cases,
            "total_deaths": total_deaths,
            "missing_values": missing_values,
            "missing_value_percentage": missing_value_percentage,
            "required_columns_present": required_columns_present,
            "schema_status": schema_status,
            "source_name": sources[disease],
            "credibility_note": credibility_notes[disease],
            "data_granularity": "State-level aggregate",
            "district_note": "District values are intentionally blank because the current dataset is aggregated at state level."
        })
        
        total_rows_all_diseases += row_count
        
    # Calculate Data Quality Score
    schema_deduction = 20 if overall_schema_status == "Invalid" else 0
    overall_missing_percentage = (total_missing_values / total_cells_all * 100) if total_cells_all > 0 else 0.0
    missing_deduction = min(20.0, overall_missing_percentage)
    
    data_quality_score = max(0.0, min(100.0, 100.0 - schema_deduction - missing_deduction))
    data_quality_score = round(data_quality_score, 2)
    
    overall_summary = {
        "total_rows_all_diseases": total_rows_all_diseases,
        "total_states_covered": len(unique_states_all),
        "overall_schema_status": overall_schema_status,
        "datasets_checked": len(diseases),
        "data_quality_score": data_quality_score
    }
    
    return {
        "overall_summary": overall_summary,
        "datasets": datasets
    }
