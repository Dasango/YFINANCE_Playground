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
import random 

# --- CONFIGURACIÓN ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

CSV_PATH = os.path.join(BASE_DIR, 'assets', 'data', 'BTC-USD_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'assets', 'models', 'BTC-USD_best_model_multi.keras')
SCALER_PATH = os.path.join(BASE_DIR, 'assets', 'models', 'BTC-USD_scaler.gz')

SEQUENCE_LENGTH = 60
FEATURE_COLS = ['Open', 'High', 'Low', 'Close', 'Volume']

global_state = {
    "predictions_5m": [],
    "history_5m": [],
    "last_trained_time": None,
    "is_training": False,
    "status": "Iniciando...",
    "past_predictions": [] # Nueva lista para guardar (datetime, predicted_close)
}

# --- FUNCIONES DE UTILIDAD ---

def load_resources():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(CSV_PATH):
        raise FileNotFoundError("Faltan archivos.")
    
    print(f"Cargando modelo desde {MODEL_PATH}...")
    model = load_model(MODEL_PATH)
    
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

import numpy as np
import pandas as pd

def generate_past_predictions(model, scaler, df, count=2000):
    """
    Genera predicciones 'in-sample' optimizadas (por lotes).
    """
    print(f" ⚙️ Generando evaluaciones históricas para los últimos {count} puntos...")
    
    # 1. Validaciones iniciales
    if len(df) <= SEQUENCE_LENGTH:
        return []

    start_idx = len(df) - count
    if start_idx < SEQUENCE_LENGTH:
        start_idx = SEQUENCE_LENGTH
    
    subset_indices = range(start_idx, len(df))
    
    # Listas para almacenar los inputs y los metadatos temporales
    X_batch = []
    timestamps = []

    # -----------------------------------------------------
    # PASO 1: Preparamos TODOS los datos (sin predecir aún)
    # -----------------------------------------------------
    print("   ↳ Preparando matrices...")
    for idx in subset_indices:
        # Ventana de datos (Features)
        seq_df = df.iloc[idx - SEQUENCE_LENGTH : idx]
        last_window = seq_df[FEATURE_COLS].values
        
        # Escalamos la ventana
        if scaler:
            last_window = scaler.transform(last_window)
        
        X_batch.append(last_window)
        
        # Gestión de Fechas (Tu lógica original intacta)
        current_row = df.iloc[idx]
        current_time = current_row['datetime'] # Asegúrate que esta col existe
        
        if hasattr(current_time, 'tz_convert'):
             current_time_gyE = current_time.tz_convert('America/Guayaquil')
        else:
             current_time_gyE = current_time
             
        timestamps.append(current_time_gyE.strftime('%Y-%m-%d %H:%M:%S'))

    # Convertimos la lista a un array de Numpy: Shape (2000, 60, 5)
    X_batch = np.array(X_batch)

    # -----------------------------------------------------
    # PASO 2: Predicción Masiva (Una sola llamada = MUY RÁPIDO)
    # -----------------------------------------------------
    print(f"   ↳ Ejecutando predicción masiva para {len(X_batch)} registros...")
    predictions_scaled = model.predict(X_batch, verbose=1, batch_size=64)
    # predictions_scaled shape: (2000, 1)

    # -----------------------------------------------------
    # PASO 3: Des-escalado y formateo
    # -----------------------------------------------------
    results = []
    target_col_idx = 3 # Index de 'Close' (según tu código)
    
    # Matriz dummy para el inverse_transform masivo
    # Creamos una matriz de ceros del tamaño (2000, 5)
    dummy_matrix = np.zeros((len(predictions_scaled), len(FEATURE_COLS)))
    
    # Rellenamos la columna 'Close' con todas las predicciones a la vez
    dummy_matrix[:, target_col_idx] = predictions_scaled.flatten()
    
    # Des-escalamos todo de golpe
    predictions_final = scaler.inverse_transform(dummy_matrix)[:, target_col_idx]
    
    # Empaquetamos resultados
    for i in range(len(timestamps)):
        results.append({
            "datetime": timestamps[i],
            "predicted_close": float(predictions_final[i])
        })

    print(f" ✅ {len(results)} predicciones históricas generadas.")
    return results

def prepare_sequence(df, scaler, seq_len):
    if len(df) < seq_len: return None
    last_window = df[FEATURE_COLS].tail(seq_len).values
    if scaler:
        last_window = scaler.transform(last_window)
    return np.expand_dims(last_window, axis=0)


def predict_recursive(model, base_sequence, scaler, last_known_close, steps=5):
    """
    Predice pasos futuros con CORRECCIÓN DE ANCLAJE + RUIDO ESTOCÁSTICO.
    Evita la línea plana inyectando la volatilidad real del mercado en la proyección.
    """
    current_seq = base_sequence.copy() 
    future_prices = []

    # 1. Calcular la volatilidad reciente (Desviación Estándar de los últimos 20 precios)
    # Esto nos dice "qué tanto se está moviendo el mercado realmente"
    last_20_closes = base_sequence[0, -20:, 3] # Asumiendo índice 3 es Close
    volatility_scale = np.std(last_20_closes)
    
    # Si la volatilidad es muy baja (ej. 0), forzamos un mínimo para que no sea plano
    if volatility_scale < 0.005: volatility_scale = 0.01

    # Bias inicial (diferencia entre realidad y modelo)
    bias_correction = 0 
    
    # Acumulador de movimiento aleatorio (Random Walk)
    accumulated_noise = 0

    for i in range(steps):
        # A. Predicción base del modelo
        pred_scaled = model.predict(current_seq, verbose=0)[0][0]

        # Desescalar
        dummy_row = np.zeros((1, len(FEATURE_COLS)))
        dummy_row[0][3] = pred_scaled
        raw_price = scaler.inverse_transform(dummy_row)[0][3]

        # B. Cálculo del Anclaje (Solo en el primer paso)
        if i == 0:
            bias_correction = last_known_close - raw_price
            # El primer paso es EXACTO al real para continuidad visual
            final_price = last_known_close
        else:
            # C. Inyección de Ruido (Solo del paso 2 al 5)
            # Generamos un pequeño movimiento aleatorio basado en la volatilidad histórica
            # random.gauss(media, desviacion)
            step_noise = random.gauss(0, volatility_scale * 0.5) # 0.5 es un factor de suavizado
            accumulated_noise += step_noise
            
            # Precio final = Predicción Modelo + Corrección Inicial + Ruido Acumulado
            final_price = raw_price + bias_correction + accumulated_noise

        future_prices.append(float(final_price))

        # D. Preparar input para la siguiente vuelta
        # Es crucial que el modelo "vea" el precio con ruido para reaccionar a él
        dummy_row[0][3] = final_price 
        dummy_row[0][0] = final_price # Open
        
        # Generamos una vela sintética con cuerpo basado en la volatilidad
        half_vol = volatility_scale / 2
        dummy_row[0][1] = final_price + half_vol # High
        dummy_row[0][2] = final_price - half_vol # Low
        
        # Escalamos para el modelo
        row_scaled = scaler.transform(dummy_row)[0]
        
        # Actualizamos la secuencia
        last_row_input = current_seq[0, -1, :].copy()
        last_row_input[0] = row_scaled[0] # Open
        last_row_input[1] = row_scaled[1] # High
        last_row_input[2] = row_scaled[2] # Low
        last_row_input[3] = row_scaled[3] # Close
        # Volumen (index 4) lo dejamos igual o lo decaemos
        
        next_input = last_row_input.reshape(1, 1, len(FEATURE_COLS))
        current_seq = np.append(current_seq[:, 1:, :], next_input, axis=1)

    return future_prices

async def update_cycle(model, scaler, df):
    print(">>> SISTEMA ONLINE: Escuchando mercado... <<<")
    
    while True:
        try:
            last_time_in_db = df['datetime'].iloc[-1]
            last_close_real = df['Close'].iloc[-1] # <--- IMPORTANTE: Precio real actual
            
            global_state["last_trained_time"] = str(last_time_in_db)

            now = datetime.now(last_time_in_db.tzinfo)
            diff_seconds = (now - last_time_in_db).total_seconds()
            
            print(f"⏱️  Lag: {int(diff_seconds)}s | Precio DB: ${last_close_real:,.2f}")

            if diff_seconds > 60:
                print(f"   🔎 Buscando datos nuevos...")
                new_data = yf.download(tickers="BTC-USD", start=last_time_in_db + timedelta(minutes=1), interval="1m", progress=False)
                await asyncio.sleep(2) 
                
                if not new_data.empty:
                    if isinstance(new_data.columns, pd.MultiIndex):
                        new_data.columns = new_data.columns.get_level_values(0)
                    new_data.reset_index(inplace=True)
                    new_data.rename(columns={'Datetime': 'datetime', 'Date': 'datetime'}, inplace=True)
                    
                    count = 0
                    for index, row in new_data.iterrows():
                        X_input = prepare_sequence(df, scaler, SEQUENCE_LENGTH)
                        
                        if X_input is not None:
                            real_row_vals = row[FEATURE_COLS].values.reshape(1, -1)
                            row_scaled = scaler.transform(real_row_vals)
                            target_scaled = row_scaled[0][3]

                            if row['High'] == row['Low'] or row['Volume'] == 0:
                                print(f" ⚠️ Saltando entrenamiento: Datos planos.")
                            else:
                                global_state["is_training"] = True
                                model.fit(X_input, np.array([[target_scaled]]), epochs=1, verbose=0, batch_size=1)
                                global_state["is_training"] = False
                                model.save(MODEL_PATH) 

                        save_df = pd.DataFrame([row])
                        cols_ordered = ['datetime'] + FEATURE_COLS 
                        save_df[cols_ordered].to_csv(CSV_PATH, mode='a', header=False, index=False)
                        save_df['datetime'] = pd.to_datetime(save_df['datetime'], utc=True)
                        df = pd.concat([df, save_df], ignore_index=True)
                        
                        last_close_real = row['Close'] # Actualizamos precio real en memoria
                        global_state["last_trained_time"] = str(row['datetime'])
                        count += 1
                        print(f"   ✅ Dato entrenado: {row['datetime']}")
                    
                    if count > 0: print(f"   ✨ {count} minutos procesados.")
                    if count > 0: print(f"   ✨ {count} minutos procesados.")
                else:
                    print("   ⚠️ Sin datos nuevos.")
            
            # --- ACTUALIZAR PREDICCIÓN LIVE (La que se guarda en memoria) ---
            # Si llegó un dato nuevo (o al inicio), calculamos su predicción "histórica" inmediata
            # para añadirla a la lista y mantener la gráfica continua.
            
            # Verificamos si la última fecha en memoria ya tiene predicción
            current_last_date = str(df['datetime'].iloc[-1])
            last_stored_pred_date = global_state["past_predictions"][-1]["datetime"] if global_state["past_predictions"] else ""
            
            if current_last_date != last_stored_pred_date:
                # Generamos predicción solo para el ÚLTIMO punto disponible
                single_pred_list = generate_past_predictions(model, scaler, df, count=1)
                if single_pred_list:
                    global_state["past_predictions"].extend(single_pred_list)
                    # Mantenemos solo los últimos 100
                    if len(global_state["past_predictions"]) > 2000:
                        global_state["past_predictions"] = global_state["past_predictions"][-2000:]
            else:
                global_state["status"] = "Al día."

            # --- PREDICCIÓN ---
            X_future = prepare_sequence(df, scaler, SEQUENCE_LENGTH)
            if X_future is not None:
                last_15_history = df['Close'].tail(15).tolist()
                global_state["history_5m"] = last_15_history

                # PASAMOS EL PRECIO REAL PARA ANCLAR LA CURVA
                predictions = predict_recursive(model, X_future, scaler, last_known_close=last_close_real, steps=5)
                
                global_state["predictions_5m"] = predictions
                print(f"   🔮 Real: {last_close_real:.2f} -> Pred (adj): {predictions[0]:.2f}")

            await asyncio.sleep(20) 
            
        except Exception as e:
            print(f"🔥 ERROR en ciclo: {e}")
            await asyncio.sleep(10)

# --- RESTO DEL CODIGO IGUAL (LIFESPAN y ENDPOINTS) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- INICIANDO SISTEMA ---")
    try:
        model, scaler, df = load_resources()
        
        # Generar estado inicial
        initial_preds = generate_past_predictions(model, scaler, df, count=2000)
        global_state["past_predictions"] = initial_preds
        
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

@app.get("/api/data")
def get_data():
    if not os.path.exists(CSV_PATH): 
        return {"error": "File not found"}
    
    # --- CORRECCIÓN AQUÍ ---
    # 1. Leemos saltando las 3 filas de encabezado (skiprows=3)
    # 2. Asignamos nombres manuales basados en el orden que mostraste en tu CSV:
    #    (El orden en tu CSV era: Fecha, Close, High, Low, Open, Volume)
    df = pd.read_csv(
        CSV_PATH,
        skiprows=3,  
        names=['datetime', 'close', 'high', 'low', 'open', 'volume'],
        header=None
    )
    
    # 2. Convertimos a datetime
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # 3. AJUSTE DE ZONA HORARIA
    # Tu CSV ya trae zona (+00:00), así que entrará en el 'else' (Escenario B)
    if df['datetime'].dt.tz is None:
        df['datetime'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert('America/Guayaquil')
    else:
        df['datetime'] = df['datetime'].dt.tz_convert('America/Guayaquil')

    # 4. Formatear como string
    df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # 5. Devolvemos los últimos 100
    return df.tail(2000).to_dict(orient='records')

@app.get("/api/predict")
def get_next_prediction():
    return {
        "history": global_state["history_5m"],
        "predictions": global_state["predictions_5m"],
        "last_trained_time": global_state["last_trained_time"],
        "status": global_state["status"],
        "is_training": global_state["is_training"]
    }

@app.get("/api/predictions")
def get_past_predictions():
    """
    Devuelve las predicciones históricas (Train Set Eval) para los últimos 100 datos.
    Se mantiene en memoria.
    """
    return global_state["past_predictions"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)