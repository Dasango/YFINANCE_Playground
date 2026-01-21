import os
import asyncio
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tensorflow.keras.models import load_model
import joblib

# --- CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ajusta estas rutas según tu estructura
CSV_PATH = os.path.join(BASE_DIR, 'assets', 'data', 'BTC-USD_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'assets', 'models', 'BTC-USD_best_model_pro.keras')
SCALER_PATH = os.path.join(BASE_DIR, 'assets', 'models', 'scaler_BTC-USD.gz')

# Hiperparámetros (¡AJUSTA ESTO A TU ENTRENAMIENTO ORIGINAL!)
SEQUENCE_LENGTH = 60  # Cuántos minutos atrás mira el modelo para predecir
FEATURE_COLS = ['Open', 'High', 'Low', 'Close', 'Volume'] # Las columnas que usaste

# Variables Globales (Estado en memoria)
global_state = {
    "current_prediction": None,
    "last_update": None,
    "is_training": False,
    "status": "Iniciando..."
}

# --- FUNCIONES DE UTILIDAD ---

def load_resources():
    """Carga el modelo, el scaler y los datos iniciales."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(CSV_PATH):
        raise FileNotFoundError("Modelo o CSV no encontrados.")
    
    model = load_model(MODEL_PATH)
    # Asumimos que tienes el scaler guardado. Si no, el modelo no entenderá los datos crudos.
    try:
        scaler = joblib.load(SCALER_PATH)
    except:
        print("ADVERTENCIA: No se encontró scaler.pkl. Usando datos crudos (probablemente fallará).")
        scaler = None

    df = pd.read_csv(CSV_PATH)
    # Limpieza básica
    if 'Price' in df.columns: df.rename(columns={'Price': 'datetime'}, inplace=True)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df = df.sort_values('datetime')
    
    return model, scaler, df

def prepare_sequence(df, scaler, seq_len):
    """Prepara los últimos N datos para que el modelo prediga."""
    if len(df) < seq_len:
        return None
    
    last_window = df[FEATURE_COLS].tail(seq_len).values
    if scaler:
        last_window = scaler.transform(last_window)
    
    # Reshape a (1, seq_len, features)
    return np.expand_dims(last_window, axis=0)

async def update_cycle(model, scaler, df):
    """
    Lógica del ciclo: 
    1. Predecir siguiente minuto.
    2. Esperar/Verificar si ya existe dato real en yfinance.
    3. Si hay dato real: Fine-tuning -> Guardar CSV -> Repetir.
    """
    
    while True:
        global_state["status"] = "Verificando nuevos datos..."
        
        # 1. ¿Cuál es el último dato que tenemos?
        last_time = df['datetime'].iloc[-1]
        now = datetime.now(last_time.tzinfo)
        
        # Calculamos el minuto que deberíamos tener ahora (retraso de 1-2 min por seguridad de yfinance)
        # yfinance a veces tarda un poco en cerrar la vela del minuto.
        target_time = last_time + timedelta(minutes=1)
        
        # Si estamos en el futuro respecto a los datos, intentamos descargar
        if now >= target_time:
            print(f"Buscando datos desde {last_time}...")
            
            # Descargamos datos faltantes desde el último punto conocido
            # Intervalo 1m. 'start' debe ser el ultimo timestamp + un delta pequeño para no duplicar
            new_data = yf.download(tickers="BTC-USD", start=last_time + timedelta(minutes=1), interval="1m", progress=False)
            
            if not new_data.empty:
                # Estandarizar columnas de yfinance
                new_data.reset_index(inplace=True)
                new_data.rename(columns={'Datetime': 'datetime'}, inplace=True)
                # Asegurarse que estén las columnas correctas
                
                # --- CICLO DE FINE TUNING (Iterar fila por fila) ---
                for index, row in new_data.iterrows():
                    row_df = pd.DataFrame([row]) # Convertir a DF para facilitar manejo
                    
                    # A) PREDECIR (Antes de que el modelo vea este dato real)
                    X_input = prepare_sequence(df, scaler, SEQUENCE_LENGTH)
                    if X_input is not None:
                        prediction_scaled = model.predict(X_input, verbose=0)
                        # Des-escalar predicción (asumiendo que predecimos 'Close' que es la col index 3)
                        # Esto es complejo si el scaler es de 5 columnas. 
                        # Simplificación: Guardamos el valor crudo escalado o des-escalamos si tienes lógica
                        global_state["current_prediction"] = float(prediction_scaled[0][0]) 

                    # B) FINE TUNING (Entrenar con el dato real que acabamos de "descubrir")
                    # Preparamos X (secuencia anterior) e y (valor actual real)
                    if X_input is not None:
                        # Asumiendo que predecimos el 'Close' actual basado en los 60 anteriores
                        actual_value = row['Close']
                        
                        # Escalar el objetivo
                        if scaler:
                            # Truco: necesitamos escalar todo el row para obtener el valor escalado de 'Close'
                            row_values = row[FEATURE_COLS].values.reshape(1, -1)
                            row_scaled = scaler.transform(row_values)
                            y_target = row_scaled[0][3] # Index 3 es Close
                        else:
                            y_target = actual_value

                        print(f"Fine-tuning para {row['datetime']}...")
                        global_state["is_training"] = True
                        # Entrenamos solo con esta muestra (batch_size=1)
                        model.fit(X_input, np.array([[y_target]]), epochs=1, verbose=0, batch_size=1)
                        global_state["is_training"] = False
                    
                    # C) ACTUALIZAR HISTÓRICO (Agregar al DF y al CSV)
                    # Formatear row para que coincida con tu CSV original
                    save_row = row_df[['datetime'] + FEATURE_COLS].copy()
                    
                    # Append memoria
                    df = pd.concat([df, save_row], ignore_index=True)
                    
                    # Append disco (mode='a')
                    # Asegúrate que el formato de fecha sea string en el CSV
                    save_row.to_csv(CSV_PATH, mode='a', header=False, index=False)
                    
                    print(f"Dato {row['datetime']} procesado y guardado.")

            else:
                print("yfinance no tiene datos nuevos aún. Esperando...")
        
        # D) PREDICCIÓN FINAL (Para el futuro inmediato)
        # Una vez al día con los datos, predecimos el minuto que aun no existe
        X_next = prepare_sequence(df, scaler, SEQUENCE_LENGTH)
        if X_next is not None:
            p = model.predict(X_next, verbose=0)
            global_state["current_prediction"] = f"Predicción escalada: {p[0][0]}" 
            # Nota: Aquí deberías aplicar scaler.inverse_transform para tener el precio real

        # Esperar 60 segundos antes de volver a intentar descargar
        await asyncio.sleep(60)

# --- LIFESPAN (GESTOR DE CONTEXTO) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Cargar recursos e iniciar el loop
    print("--- INICIANDO SISTEMA PREDICTIVO ---")
    try:
        model, scaler, df = load_resources()
        # Iniciar la tarea en background sin bloquear
        asyncio.create_task(update_cycle(model, scaler, df))
    except Exception as e:
        print(f"Error crítico al iniciar: {e}")
    
    yield # Aquí corre la aplicación
    
    # 2. Shutdown
    print("--- APAGANDO SISTEMA ---")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS ---

@app.get("/api/data")
def get_data():
    """Devuelve los datos históricos (incluyendo los nuevos agregados)."""
    if not os.path.exists(CSV_PATH):
        return {"error": "File not found"}
    try:
        # Leemos directo del disco para asegurar consistencia
        df = pd.read_csv(CSV_PATH)
        # Convertir a dict
        return df.tail(1000).to_dict(orient='records') # Limitamos a los ultimos 1000 para no saturar
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/predict")
def get_next_prediction():
    """Devuelve la predicción del próximo minuto y el estado del sistema."""
    return {
        "next_minute_prediction": global_state["current_prediction"],
        "status": global_state["status"],
        "is_training": global_state["is_training"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)