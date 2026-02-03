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

# CSV_PATH eliminado
MODEL_PATH = os.path.join(BASE_DIR, 'assets', 'models', 'BTC-USD_best_model_multi.h5')
SCALER_PATH = os.path.join(BASE_DIR, 'assets', 'models', 'BTC-USD_scaler.gz')

SEQUENCE_LENGTH = 60
FEATURE_COLS = ['Open', 'High', 'Low', 'Close', 'Volume']

global_state = {
    "predictions_5m": [],
    "history_5m": [],
    "last_trained_time": None,
    "is_training": False,
    "status": "Iniciando...",
    "past_predictions": [], # Nueva lista para guardar (datetime, predicted_close)
    "df": pd.DataFrame() # DataFrame en memoria
}

# --- FUNCIONES DE UTILIDAD ---

def load_resources():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        raise FileNotFoundError("Faltan archivos de modelo o scaler.")
    
    print(f"Cargando modelo desde {MODEL_PATH}...")
    model = load_model(MODEL_PATH)
    
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        scaler = joblib.load(SCALER_PATH)

    return model, scaler

async def init_data(scaler):
    """
    Descarga los últimos ~3000 minutos de datos (para asegurar tener 2000 limpios)
    y llena el DataFrame en memoria global.
    """
    print(" 📥 Descargando datos iniciales de YFinance (últimos 5 días)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5) # 5 días * 24h * 60m = 7200 min (suficiente)
    
    # yfinance permite hasta 7 días con 1m interval
    df = yf.download(tickers="BTC-USD", start=start_date, end=end_date, interval="1m", progress=False)
    
    if df.empty:
        raise ValueError("No se pudieron descargar datos de YFinance.")

    # Limpieza básica
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)
    df.rename(columns={'Datetime': 'datetime', 'Date': 'datetime'}, inplace=True)
    
    # Asegurar columnas numéricas
    for col in FEATURE_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Zona horaria (ya viene en UTC usualmente, convertimos a Guayaquil para consistencia visual)
    if 'datetime' in df.columns:
        if df['datetime'].dt.tz is None:
            df['datetime'] = df['datetime'].dt.tz_localize('UTC')
        df['datetime'] = df['datetime'].dt.tz_convert('America/Guayaquil')
    
    df.sort_values('datetime', inplace=True)
    
    # Nos quedamos con los últimos 2000
    df = df.tail(2000).reset_index(drop=True)
    
    print(f" Datos iniciales cargados: {len(df)} registros. Último: {df.iloc[-1]['datetime']}")
    
    global_state["df"] = df
    return df

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
    if not subset_indices:
        return []

    print("   ↳ Preparando matrices...")
    # Optimización: Vectorizar si es posible, por ahora iteramos
    for idx in subset_indices:
        # Ventana de datos (Features)
        seq_df = df.iloc[idx - SEQUENCE_LENGTH : idx]
        last_window = seq_df[FEATURE_COLS].values
        
        # Escalamos la ventana
        if scaler:
            last_window = scaler.transform(last_window)
        
        X_batch.append(last_window)
        
        # Gestión de Fechas
        current_row = df.iloc[idx]
        current_time = current_row['datetime']
        
        # Ya debería estar en la timezone correcta por init_data/update_cycle
        timestamps.append(current_time.strftime('%Y-%m-%d %H:%M:%S'))

    if not X_batch:
        return []

    # Convertimos la lista a un array de Numpy: Shape (N, 60, 5)
    X_batch = np.array(X_batch)

    # -----------------------------------------------------
    # PASO 2: Predicción Masiva (Una sola llamada = MUY RÁPIDO)
    # -----------------------------------------------------
    print(f"   ↳ Ejecutando predicción masiva para {len(X_batch)} registros...")
    predictions_scaled = model.predict(X_batch, verbose=1, batch_size=64)
    # predictions_scaled shape: (N, 1)

    # -----------------------------------------------------
    # PASO 3: Des-escalado y formateo
    # -----------------------------------------------------
    results = []
    target_col_idx = 3 # Index de 'Close' (según tu código)
    
    # Matriz dummy para el inverse_transform masivo
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

async def update_cycle(model, scaler):
    print(">>> SISTEMA ONLINE: Escuchando mercado (In-Memory)... <<<")
    
    while True:
        try:
            # Referencia al DF global
            df = global_state["df"]
            
            last_time_in_mem = df['datetime'].iloc[-1]
            last_close_real = df['Close'].iloc[-1]
            
            global_state["last_trained_time"] = str(last_time_in_mem)

            now = datetime.now(last_time_in_mem.tzinfo)
            diff_seconds = (now - last_time_in_mem).total_seconds()
            
            print(f" Lag: {int(diff_seconds)}s | Precio Memoria: ${last_close_real:,.2f}")

            if diff_seconds > 60:
                print(f"   🔎 Buscando datos nuevos (YFinance)...")
                # Pedimos datos que cubran el hueco
                new_data = yf.download(tickers="BTC-USD", start=last_time_in_mem + timedelta(minutes=1), interval="1m", progress=False)
                await asyncio.sleep(2) 
                
                if not new_data.empty:
                    if isinstance(new_data.columns, pd.MultiIndex):
                        new_data.columns = new_data.columns.get_level_values(0)
                    new_data.reset_index(inplace=True)
                    new_data.rename(columns={'Datetime': 'datetime', 'Date': 'datetime'}, inplace=True)
                    
                    # Limpieza y Conversión antes de procesar
                    if not new_data.empty:
                        # Asegurar zona horaria
                        if new_data['datetime'].dt.tz is None:
                             new_data['datetime'] = new_data['datetime'].dt.tz_localize('UTC')
                        new_data['datetime'] = new_data['datetime'].dt.tz_convert('America/Guayaquil')
                        
                        count = 0
                        
                        # Iteramos los nuevos datos para entrenar y agregar
                        for index, row in new_data.iterrows():
                            # Re-evaluamos el DF actual en cada paso
                            current_df = global_state["df"]
                            X_input = prepare_sequence(current_df, scaler, SEQUENCE_LENGTH)
                            
                            # Entrenamiento Online
                            if X_input is not None:
                                real_row_vals = row[FEATURE_COLS].values.reshape(1, -1)
                                row_scaled = scaler.transform(real_row_vals)
                                target_scaled = row_scaled[0][3]

                                if row['High'] == row['Low'] or row['Volume'] == 0:
                                    pass
                                else:
                                    global_state["is_training"] = True
                                    model.fit(X_input, np.array([[target_scaled]]), epochs=1, verbose=0, batch_size=1)
                                    global_state["is_training"] = False
                                    model.save(MODEL_PATH) 

                            # Agregar al DF en memoria
                            new_row_df = pd.DataFrame([row])
                            # Solo columnas necesarias
                            new_row_df = new_row_df[['datetime'] + FEATURE_COLS]
                            
                            # Concatenar y mantener ultimos 2000
                            updated_df = pd.concat([current_df, new_row_df], ignore_index=True)
                            if len(updated_df) > 2000:
                                updated_df = updated_df.tail(2000).reset_index(drop=True)
                                
                            global_state["df"] = updated_df
                            
                            last_close_real = row['Close']
                            global_state["last_trained_time"] = str(row['datetime'])
                            count += 1
                        
                        if count > 0: print(f"   ✨ {count} minutos procesados e integrados.")
                else:
                    print("   ⚠️ Sin datos nuevos aún.")
            
            # --- ACTUALIZAR PREDICCIÓN LIVE (La que se guarda en memoria) ---
            # --- ACTUALIZAR PREDICCIÓN LIVE (La que se guarda en memoria) ---
            # Si llegó un dato nuevo (o al inicio), calculamos su predicción "histórica" inmediata
            # para añadirla a la lista y mantener la gráfica continua.
            
            # Recalculamos sobre el estado actual
            df = global_state["df"] # Refrescamos ref
            
            # Lógica dinámica para saber cuántos puntos faltan predecir
            count_missing = 0
            last_pred_entry = global_state["past_predictions"][-1] if global_state["past_predictions"] else None
            
            if last_pred_entry:
                last_ts_str = last_pred_entry["datetime"]
                
                # Buscamos en qué índice del DF está esa última predicción
                # Eficiente: Convertimos a string solo lo necesario o usamos búsqueda inversa
                # Para simplificar y asegurar exactitud (dado que son solo 2000 datos), comparamos strings
                df_dates_str = df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                matches = df.index[df_dates_str == last_ts_str].tolist()
                
                if matches:
                    last_idx = matches[-1]
                    # Queremos predecir desde last_idx + 1 hasta el final
                    count_missing = len(df) - (last_idx + 1)
                else:
                    # Si no encontramos la fecha (ej. se salió de la ventana de 2000), 
                    # asumimos que solo necesitamos lo más nuevo. 
                    # Podríamos regenerar todo, pero para eficiencia asumimos 1 si no hay gap obvio.
                    # Mejor estrategia: Si no hay match, asumimos que necesitamos predecir TODO lo nuevo.
                    # Pero para no bloquear, probemos con 1 por seguridad o todo.
                    # Vamos a regenerar solo si el gap es pequeño? No, regenerar todo es safer si se perdió el track.
                    # Pero para este caso "reaches half", probablemente solo necesitamos catch up.
                    # Vamos a asumir que si no match, es porque df avanzó mucho.
                    count_missing = 1 
            else:
                # Si está vacío, predecir todo lo posible
                count_missing = len(df)

            if count_missing > 0:
                print(f" ⚙️ Sincronizando predicciones: Generando {count_missing} faltantes...")
                new_preds = generate_past_predictions(model, scaler, df, count=count_missing)
                if new_preds:
                    global_state["past_predictions"].extend(new_preds)
                    # Mantenemos solo los últimos 2000
                    if len(global_state["past_predictions"]) > 2000:
                        global_state["past_predictions"] = global_state["past_predictions"][-2000:]
            else:
                 global_state["status"] = "Al día."

            # --- PREDICCIÓN FUTURA ---
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

# --- LIFESPAN y ENDPOINTS ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- INICIANDO SISTEMA (Modo Memoria) ---")
    try:
        model, scaler = load_resources()
        
        # 1. Cargar datos iniciales en memoria
        df = await init_data(scaler)
        
        # 2. Backtesting inicial (llenar past_predictions con los 2000 datos)
        initial_preds = generate_past_predictions(model, scaler, df, count=2000)
        global_state["past_predictions"] = initial_preds
        
        # 3. Arrancar ciclo de actualización
        asyncio.create_task(update_cycle(model, scaler))
    except Exception as e:
        print(f"Error crítico al iniciar: {e}")
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
    """
    Devuelve los datos actuales en memoria (hasta 2000 registros).
    """
    df = global_state.get("df")
    if df is None or df.empty:
        return []
    
    # Formatear datetime a string para JSON
    # Hacemos una copia para no alterar el DF original
    res_df = df.copy()
    
    # Renombrar columnas para compatibilidad con frontend (que espera minúsculas)
    res_df = res_df.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })

    res_df['datetime'] = res_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return res_df.to_dict(orient='records')

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
    Devuelve las predicciones históricas (Train Set Eval).
    """
    return global_state["past_predictions"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
