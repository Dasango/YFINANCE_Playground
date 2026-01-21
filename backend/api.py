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
MODEL_PATH = os.path.join(BASE_DIR, 'assets', 'models', 'BTC-USD_best_model_multi.keras')
SCALER_PATH = os.path.join(BASE_DIR, 'assets', 'models', 'BTC-USD_scaler.gz')

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
    if not os.path.exists(MODEL_PATH) or not os.path.exists(CSV_PATH):
        raise FileNotFoundError("Faltan archivos (modelo o csv).")
    
    print(f"Cargando modelo desde {MODEL_PATH}...")
    model = load_model(MODEL_PATH)
    
    print(f"Cargando scaler desde {SCALER_PATH}...")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        scaler = joblib.load(SCALER_PATH)

    print("Leyendo CSV y limpiando cabeceras extra de yfinance...")
    
    df = pd.read_csv(CSV_PATH, header=0, skiprows=[1, 2])

    if 'Price' in df.columns:
        df.rename(columns={'Price': 'datetime'}, inplace=True)
    
    if 'Date' in df.columns:
        df.rename(columns={'Date': 'datetime'}, inplace=True)

    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    cols_datos = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in cols_datos:
        df[col] = pd.to_numeric(df[col], errors='coerce')

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
    print(">>> SISTEMA ONLINE: Escuchando mercado (MODO HABLADOR)... <<<")
    
    while True:
        try:
            # 1. Diagnóstico de tiempo
            last_time = df['datetime'].iloc[-1]
            now = datetime.now(last_time.tzinfo)
            diff_seconds = (now - last_time).total_seconds()
            
            print(f"⏱️  Check: {now.strftime('%H:%M:%S')} | Último dato en DB: {last_time.strftime('%H:%M:%S')} | Lag: {int(diff_seconds)}s")

            # Bajamos el umbral a 60 segundos para ser más agresivos en la búsqueda
            if diff_seconds > 60:
                print(f"   🔎 Buscando datos nuevos en Yahoo...")
                
                # Descarga segura
                new_data = yf.download(tickers="BTC-USD", start=last_time + timedelta(minutes=1), interval="1m", progress=False)
                
                if not new_data.empty:
                    # Limpieza YFinance
                    if isinstance(new_data.columns, pd.MultiIndex):
                        new_data.columns = new_data.columns.get_level_values(0)
                    new_data.reset_index(inplace=True)
                    new_data.rename(columns={'Datetime': 'datetime', 'Date': 'datetime'}, inplace=True)
                    
                    count = 0
                    for index, row in new_data.iterrows():
                        current_time = row['datetime']
                        
                        # --- LÓGICA DE APRENDIZAJE ---
                        X_input = prepare_sequence(df, scaler, SEQUENCE_LENGTH)
                        
                        if X_input is not None:
                            real_close = row['Close']
                            row_values = row[FEATURE_COLS].values.reshape(1, -1)
                            row_scaled = scaler.transform(row_values)
                            target_scaled = row_scaled[0][3]

                            global_state["is_training"] = True
                            model.fit(X_input, np.array([[target_scaled]]), epochs=1, verbose=0, batch_size=1)
                            global_state["is_training"] = False

                        # Guardar
                        save_df = pd.DataFrame([row])
                        cols_ordered = ['datetime'] + FEATURE_COLS 
                        save_df[cols_ordered].to_csv(CSV_PATH, mode='a', header=False, index=False)
                        
                        save_df['datetime'] = pd.to_datetime(save_df['datetime'], utc=True)
                        df = pd.concat([df, save_df], ignore_index=True)
                        
                        print(f"   ✅ NUEVO DATO CAPTURADO: {current_time.strftime('%H:%M')} | Precio: {row['Close']:.2f}")
                        count += 1
                        global_state["last_update"] = str(current_time)
                        
                    if count > 0:
                        print(f"   ✨ Se actualizaron {count} minutos.")
                    
                else:
                    print("   ⚠️ Yahoo dice: 'No hay vela cerrada todavía'. Esperando...")
            else:
                global_state["status"] = "Al día."
                print("   👍 Estamos al día. Esperando que cierre el minuto actual.")

            # --- PREDICCIÓN ---
            X_future = prepare_sequence(df, scaler, SEQUENCE_LENGTH)
            if X_future is not None:
                pred_scaled = model.predict(X_future, verbose=0)[0][0]
                dummy_row = np.zeros((1, len(FEATURE_COLS))) 
                dummy_row[0][3] = pred_scaled 
                pred_final_price = scaler.inverse_transform(dummy_row)[0][3]
                
                global_state["current_prediction"] = float(pred_final_price)
                # print(f"   🔮 Predicción actual: ${pred_final_price:,.2f}") # Descomenta si quieres ver esto siempre

            # CAMBIO IMPORTANTE: Esperar solo 10 segundos en lugar de 60
            # Esto hará que veas logs todo el tiempo y sepas que no murió.
            await asyncio.sleep(10) 
            
        except Exception as e:
            print(f"🔥 ERROR: {e}")
            await asyncio.sleep(10)

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