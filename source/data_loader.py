import pandas as pd
import os
from .config import ASSETS_CSV_PATH

def load_stock_data():
    """Loads stock data and returns a filtered dataframe for visualization."""
    try:
        if not os.path.exists(ASSETS_CSV_PATH):
            print(f"Warning: File not found at {ASSETS_CSV_PATH}")
            return pd.DataFrame({"Datetime": [], "Close": []})
            
        df = pd.read_csv(ASSETS_CSV_PATH, skiprows=3, names=["Datetime", "Close", "High", "Low", "Open", "Volume"])
        df["Datetime"] = pd.to_datetime(df["Datetime"])
        return df.tail(150) # Use a portion for clearer visualization
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame({"Datetime": [], "Close": []})

# Preload data
df_chart = load_stock_data()
