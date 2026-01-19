import os
import glob
import numpy as np
import pandas as pd
from datetime import timedelta
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

# Configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')
DATA_DIR = os.path.join(ASSETS_DIR, 'real_data')
MODELS_DIR = os.path.join(ASSETS_DIR, 'models')
PREDICTS_DIR = os.path.join(ASSETS_DIR, 'predicts')

# Asegurar carpeta de salida
os.makedirs(PREDICTS_DIR, exist_ok=True)

def parse_features_from_filename(filename, ticker):
    """
    Ejemplo: BTC-USD_Close_High.keras -> features=['Close', 'High']
    Suponemos que el ticker empieza el nombre.
    """
    basename = os.path.basename(filename)
    name_no_ext = os.path.splitext(basename)[0]
    # Remove ticker prefix (e.g. "BTC-USD_")
    # Cuidado si el ticker tiene guiones bajos, pero el example del usuario es BTC-USD
    if name_no_ext.startswith(ticker + "_"):
        features_str = name_no_ext[len(ticker)+1:]
        return features_str.split("_")
    return None

def main():
    # 1. Cargar Datos Reales
    # Buscar el csv. Suponemos que hay uno solo o usamos el primero que coincida con lo esperado
    # El usuario dijo que el script anterior lo guarda en real_data.
    # Buscamos archivos CSV
    data_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not data_files:
        print("No se encontraron datos en assets/real_data")
        return
    
    data_path = data_files[0] # Tomamos el primero
    ticker_guess = os.path.basename(data_path).replace("_data.csv", "")
    print(f"Cargando datos históricos de: {data_path} (Ticker: {ticker_guess})")
    
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    if df.empty:
        print("Datos vacíos.")
        return

    # Verificar último timestamp
    last_timestamp = df.index[-1]
    print(f"Último dato conocido: {last_timestamp}")
    
    # Objetivo: Predecir todo el día siguiente a partir de last_timestamp
    # "19/01/2026 a partir de las 4:00" si el último es 3:55
    # Generamos los timestamps objetivo (cada 20m)
    # Primero determinamos el inicio del "día de mañana".
    # Si last_timestamp es 23:55, mañana empieza en +5m.
    # El usuario pidió explícitamente desde las 4:00.
    # Asumiremos la lógica del usuario: Start = last known + 5min (recursive base), 
    # pero solo guardar si matches condition.
    
    # Definir rango de predicción: Desde (last + 5m) hasta final del día del "start_time"
    # O simplemente 24 horas hacia adelante.
    # El usuario dijo: "predict de todo el dia de mana es decir 19/01/2026 a partir de las 4:00 ... hasta 23:40"
    
    start_prediction_stream = last_timestamp + timedelta(minutes=5)
    
    # 2. Iterar Modelos
    model_files = glob.glob(os.path.join(MODELS_DIR, "*.keras"))
    print(f"Encontrados {len(model_files)} modelos.")
    
    for model_path in model_files:
        features = parse_features_from_filename(model_path, ticker_guess)
        if not features:
            print(f"Saltando {model_path} (no coincide con formato esperado)")
            continue
            
        print(f"Procesando {os.path.basename(model_path)}... Features: {features}")
        
        # 3. Preparar Scalers y Datos para este modelo ESPECÍFICO
        # Requerimos re-fitar los scalers igual que en el entrenamiento
        df_subset = df[features]
        df_target = df[['Close']]
        
        scaler_x = MinMaxScaler(feature_range=(0, 1))
        scaler_y = MinMaxScaler(feature_range=(0, 1))
        
        # Fit con todo el historial
        scaler_x.fit(df_subset.values)
        scaler_y.fit(df_target.values)
        
        # Preparar secuencia inicial (últimos 30 pasos, según look_back del anterior script)
        # OJO: look_back es 30 en el script modificado por el usuario.
        look_back = 30 
        
        # Tomamos los últimos 30 registros
        last_window_df = df_subset.iloc[-look_back:]
        if len(last_window_df) < look_back:
            print("Datos insuficientes para look_back.")
            continue
            
        current_input_scaled = scaler_x.transform(last_window_df.values)
        # Shape: (30, n_features)
        # Necesitamos (1, 30, n_features) para el predict
        current_batch = np.array([current_input_scaled]) 
        
        # Cargar modelo
        try:
            model = load_model(model_path)
        except Exception as e:
            print(f"Error cargando {model_path}: {e}")
            continue

        # Lista para guardar (Timestamp, Prediction)
        predictions = []
        
        # Simulación recursiva
        # Tiempo actual en la simulación
        curr_time = start_prediction_stream
        
        # Definir límite: Fin del día en cuestión (23:59:59)
        # El día se define por start_prediction_stream
        end_time = curr_time.replace(hour=23, minute=59, second=59)
        
        # Feature indices
        try:
            close_idx = features.index("Close")
        except ValueError:
            close_idx = -1
            
        # Calcular volatilidad histórica (desviación estándar de los cambios) surte 'Close'
        step_std = df['Close'].diff().std()
        # Si es NaN (ej: data muy corta), usar 0
        if np.isnan(step_std):
            step_std = 0.0

        while curr_time <= end_time:
            # Predecir
            # current_batch shape: (1, 30, n_features)
            pred_scaled = model.predict(current_batch, verbose=0)
            pred_val = scaler_y.inverse_transform(pred_scaled)[0][0]
            
            # --- Inyectar Ruido Estocástico ---
            # Random Walk: La predicción es la media, añadimos varianza real
            noise = np.random.normal(0, step_std)
            pred_val += noise
            
            # Guardar si toca (todos los pasos de 5m)
            if curr_time.hour >= 4:
                predictions.append((curr_time, pred_val))
            
            # Actualizar ventana deslizante
            # Nuevo input row:
            last_row_scaled = current_batch[0, -1, :].copy()
            
            # Heurística + Ruido: Usamos el valor con ruido para la recursión
            if close_idx != -1:
                old_close = last_row_scaled[close_idx]
                
                # Necesitamos el valor escalado del NUEVO precio (con ruido)
                # Transformamos de vuelta manualmente: (val - min) / (max - min)
                # O usamos el scaler (más lento pero seguro)
                # scaler_y espera shape (n_samples, 1)
                
                # Optimizacion: calcular diff en escala original o re-escalar
                # Re-escalamos el pred_val ruidoso
                new_close_scaled = scaler_y.transform([[pred_val]])[0][0]
                
                diff_scaled = new_close_scaled - old_close
                
                # Actualizar Close
                last_row_scaled[close_idx] = new_close_scaled
                
                # Actualizar otros precios relacionados con el mismo delta ESCALADO
                # Nota: Esto asume que los scalers de High/Low son similares al de Close,
                # lo cual es cierto (MinMax sobre todo el dataset suele ser parecido).
                for price_feat in ["High", "Low", "Open"]:
                    if price_feat in features:
                        f_idx = features.index(price_feat)
                        last_row_scaled[f_idx] += diff_scaled
            
            # Desplazar y añadir
            new_row_reshaped = last_row_scaled.reshape(1, 1, -1)
            current_batch = np.concatenate([current_batch[:, 1:, :], new_row_reshaped], axis=1)
            
            # Avanzar tiempo
            curr_time += timedelta(minutes=5)
            
        # Guardar CSV
        if predictions:
            out_name = os.path.basename(model_path).replace('.keras', '.csv')
            out_path = os.path.join(PREDICTS_DIR, out_name)
            
            with open(out_path, 'w') as f:
                # Header? User output example: "2026-01-19 04:00:00+00:00, cost_prediction"
                # No header requested explicitly but usually good. User showed format.
                f.write("date,cost_prediction\n")
                for t, p in predictions:
                    f.write(f"{t},{p:.6f}\n")
            
            print(f" -> Resultados guardados en {out_path}")

if __name__ == "__main__":
    main()
