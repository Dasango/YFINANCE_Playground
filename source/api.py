from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Robust path finding
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, '..', 'assets', 'data', 'BTC-USD_data.csv')

@app.get("/api/data")
def get_data():
    if not os.path.exists(CSV_PATH):
        return {"error": "File not found"}
    
    try:
        # Read CSV skipping the Ticker and Datetime non-header rows
        # Row 0: Headers (Price, Close, High...)
        # Row 1: Ticker info -> Skip
        # Row 2: Datetime,,, -> Skip
        df = pd.read_csv(CSV_PATH, header=0, skiprows=[1, 2])
        
        # Rename the first column 'Price' to 'datetime' as it contains the timestamps
        # The 'Price' header is actually the label for the column index in yfinance, 
        # but it sits over the index column in the CSV.
        if 'Price' in df.columns:
            df.rename(columns={'Price': 'datetime'}, inplace=True)
            
        # Ensure we have data
        if df.empty:
            return []
            
        # Convert to list of dicts
        result = df.to_dict(orient='records')
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
