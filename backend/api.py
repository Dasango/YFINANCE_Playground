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
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

CSV_PATH = os.path.join(BASE_DIR, 'assets', 'data', 'BTC-USD_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'assets', 'models', 'BTC-USD_best_model_multi.keras')
SCALER_PATH = os.path.join(BASE_DIR, 'assets', 'models', 'BTC-USD_scaler.gz')

SEQUENCE_LENGTH = 60
FEATURE_COLS = ['Open', 'High', 'Low', 'Close', 'Volume']

# Modificamos el estado global para guardar una lista de predicciones y la fecha clara
global_state = {
    "predictions_5m": [],      # Lista con los precios de los prox 5 min
    "last_trained_time": None, # String con la fecha del ultimo dato real usado
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

    print("Leyendo CSV...")
    df = pd.read_csv(CSV_PATH, header=0, skiprows=[1, 2])

    if 'Price' in df.columns: df.rename(columns={'Price': 'datetime'}, inplace=True)
    if 'Date' in df.columns: df.rename(columns={'Date': 'datetime'}, inplace=True)

    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    
    for col in FEATURE_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.sort_values('datetime')
    return model, scaler, df

def prepare_sequence(df, scaler, seq_len):
    """Prepara la última ventana de datos."""
    if len(df) < seq_len:
        return None
    last_window = df[FEATURE_COLS].tail(seq_len).values
    if scaler:
        last_window = scaler.transform(last_window)
    return np.expand_dims(last_window, axis=0)

def predict_recursive(model, base_sequence, scaler, steps=5):
    """
    Realiza predicciones recursivas para los próximos 'steps' minutos.
    Asume que Open, High, Low son similares al Close predicho para avanzar.
    """
    current_seq = base_sequence.copy() # Shape (1, 60, 5)
    future_prices = []

    for _ in range(steps):
        # 1. Predecir el siguiente paso (valor escalado)
        pred_scaled = model.predict(current_seq, verbose=0)[0][0]

        # 2. Desescalar para obtener el precio real y guardarlo
        dummy_row = np.zeros((1, len(FEATURE_COLS)))
        dummy_row[0][3] = pred_scaled # Asumimos que Close está en índice 3
        price_final = scaler.inverse_transform(dummy_row)[0][3]
        future_prices.append(float(price_final))

        # 3. Construir la nueva fila de entrada para la siguiente vuelta
        # Tomamos la última fila actual para copiar el volumen u otras caracteristicas
        last_row = current_seq[0, -1, :].copy()
        
        # Actualizamos con la predicción (Asumimos vela plana para simplificar futuro)
        # Open=Pred, High=Pred, Low=Pred, Close=Pred
        last_row[0] = pred_scaled 
        last_row[1] = pred_scaled 
        last_row[2] = pred_scaled 
        last_row[3] = pred_scaled 
        # last_row[4] (Volume) se queda igual al anterior por defecto

        # 4. Actualizar secuencia: Quitar el primero, agregar el nuevo al final
        next_input = last_row.reshape(1, 1, len(FEATURE_COLS))
        current_seq = np.append(current_seq[:, 1:, :], next_input, axis=1)

    return future_prices

async def update_cycle(model, scaler, df):
    print(">>> SISTEMA ONLINE: Escuchando mercado... <<<")
    
    while True:
        try:
            # Actualizamos la referencia de tiempo en el estado global
            last_time_in_db = df['datetime'].iloc[-1]
            global_state["last_trained_time"] = str(last_time_in_db)

            now = datetime.now(last_time_in_db.tzinfo)
            diff_seconds = (now - last_time_in_db).total_seconds()
            
            print(f"⏱️  Lag: {int(diff_seconds)}s | Último DB: {last_time_in_db.strftime('%H:%M')}")

            if diff_seconds > 60:
                print(f"   🔎 Buscando datos nuevos...")
                new_data = yf.download(tickers="BTC-USD", start=last_time_in_db + timedelta(minutes=1), interval="1m", progress=False)
                await asyncio.sleep(2) 
                
                if not new_data.empty:
                    # Limpieza estándar
                    if isinstance(new_data.columns, pd.MultiIndex):
                        new_data.columns = new_data.columns.get_level_values(0)
                    new_data.reset_index(inplace=True)
                    new_data.rename(columns={'Datetime': 'datetime', 'Date': 'datetime'}, inplace=True)
                    
                    count = 0
                    for index, row in new_data.iterrows():
                        # --- ENTRENAMIENTO INCREMENTAL ---
                        X_input = prepare_sequence(df, scaler, SEQUENCE_LENGTH)
                        
                        if X_input is not None:
                            # Preparamos target
                            real_row_vals = row[FEATURE_COLS].values.reshape(1, -1)
                            row_scaled = scaler.transform(real_row_vals)
                            target_scaled = row_scaled[0][3] # Close

                            global_state["is_training"] = True
                            model.fit(X_input, np.array([[target_scaled]]), epochs=1, verbose=0, batch_size=1)
                            global_state["is_training"] = False
                            
                            # Guardamos en disco cada cierto tiempo o siempre (aquí siempre para seguridad)
                            model.save(MODEL_PATH) 

                        # Guardar en CSV y DF en memoria
                        save_df = pd.DataFrame([row])
                        cols_ordered = ['datetime'] + FEATURE_COLS 
                        save_df[cols_ordered].to_csv(CSV_PATH, mode='a', header=False, index=False)
                        
                        save_df['datetime'] = pd.to_datetime(save_df['datetime'], utc=True)
                        df = pd.concat([df, save_df], ignore_index=True)
                        
                        # Actualizamos la fecha de entrenamiento tras procesar
                        global_state["last_trained_time"] = str(row['datetime'])
                        count += 1
                        print(f"   ✅ Dato entrenado: {row['datetime']}")
                    
                    if count > 0:
                        print(f"   ✨ {count} minutos procesados.")
                else:
                    print("   ⚠️ Sin datos nuevos en Yahoo.")
            else:
                global_state["status"] = "Al día."

            # --- PREDICCIÓN 5 MINUTOS ---
            X_future = prepare_sequence(df, scaler, SEQUENCE_LENGTH)
            if X_future is not None:
                # Llamamos a la nueva función recursiva
                predictions = predict_recursive(model, X_future, scaler, steps=5)
                global_state["predictions_5m"] = predictions
                print(f"   🔮 Predicción +1 min: ${predictions[0]:,.2f} | +5 min: ${predictions[-1]:,.2f}")

            await asyncio.sleep(20) 
            
        except Exception as e:
            print(f"🔥 ERROR en ciclo: {e}")
            await asyncio.sleep(10)

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- INICIANDO SISTEMA ---")
    try:
        model, scaler, df = load_resources()
        asyncio.create_task(update_cycle(model, scaler, df))
    except Exception as e:
        print(f"Error crítico: {e}")
    yield
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
    if not os.path.exists(CSV_PATH): return {"error": "File not found"}
    df = pd.read_csv(CSV_PATH)
    return df.tail(100).to_dict(orient='records')

@app.get("/api/predict")
def get_next_prediction():
    """
    Devuelve:
    - predictions: Lista de 5 precios float (minuto 1 al 5).
    - last_trained_time: Timestamp del último dato real usado.
    """
    return {
        "predictions": global_state["predictions_5m"],
        "last_trained_time": global_state["last_trained_time"],
        "status": global_state["status"],
        "is_training": global_state["is_training"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)