from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import glob
from typing import Optional

app = FastAPI()

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Subimos un nivel para llegar a la raíz del proyecto y luego a assets
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')
DATA_DIR = os.path.join(ASSETS_DIR, 'real_data')
PREDICTS_DIR = os.path.join(ASSETS_DIR, 'predicts')

# CORS (Permitir todo para desarrollo local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/real_data")
def get_real_data():
    """Retorna los últimos 100 datos reales"""
    print(f"Buscando datos en: {DATA_DIR}")
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not files:
        raise HTTPException(status_code=404, detail="No real data found")
    
    # Tomamos el primer archivo encontrado
    file_path = files[0]
    try:
        df = pd.read_csv(file_path)
        # Asumimos que la primera columna es Fecha si no tiene nombre explícito o index
        # En el script de entrenamiento se guardó con index=True, así que la fecha es la col 0 o index name
        # Pandas read_csv loads index as column unless index_col specified
        
        # Renombrar columnas para consistencia si es necesario
        # El formato esperado por el frontend será array de {date: ..., value: ...} o arrays separados
        # Plotly prefiere arrays.
        
        # Ultimos 100 datos
        df_tail = df.tail(100)
        
        # Preparar respuesta JSON orientada a records o list of lists
        # Vamos a devolver arrays para eficiencia en Plotly
        # Asumimos columna 'Date' (o la primera) y 'Close'
        
        cols = df_tail.columns.tolist()
        # Si la fecha está en el index o es col 0
        date_col = cols[0] 
        val_col = "Close"
        
        if val_col not in cols:
             raise HTTPException(status_code=500, detail="'Close' column not found in data")

        return {
            "dates": df_tail[date_col].tolist(),
            "values": df_tail[val_col].tolist(),
            "ticker": os.path.basename(file_path).replace("_data.csv", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predict/{features}")
def get_prediction(features: str):
    """
    Retorna la predicción para la combinación de features dada.
    Ejemplo features: "Close_High"
    """
    # Construir nombre del archivo. El script predict guardaba como 'BTC-USD_Close_High.csv'
    # Necesitamos saber el ticker. Podemos inferirlo o pedirlo.
    # Por simplicidad, buscaremos cualquier archivo que termine en _{features}.csv
    
    # Normalizar features string (ej: "High_Close" -> orden correcto?)
    # El script de entrenamiento ordena las combinaciones? 
    # itertools.combinations mantiene orden de input features.
    # Input features fix: ["Close", "High", "Low", "Open", "Volume"]
    # So "Close_High" is valid, "High_Close" is not.
    # El frontend debe enviar en orden correcto.
    
    search_pattern = os.path.join(PREDICTS_DIR, f"*_{features}.csv")
    files = glob.glob(search_pattern)
    
    if not files:
        raise HTTPException(status_code=404, detail=f"Prediction for features '{features}' not found")
    
    file_path = files[0]
    try:
        df = pd.read_csv(file_path)
        # Salida del predict script: date, cost_prediction
        
        return {
            "dates": df['date'].tolist(),
            "values": df['cost_prediction'].tolist(),
            "model_name": os.path.basename(file_path).replace(".csv", "")
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

# Montar archivos estáticos (Frontend)
static_dir = os.path.join(BASE_DIR, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
