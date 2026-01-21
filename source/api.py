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
        df = pd.read_csv(CSV_PATH, header=0, skiprows=[1, 2])
        
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
