import os
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

# Configuración
TICKER = "GOOG"
INTERVAL = "5m"
LOOK_BACK = 60
MODELS_DIR = r"c:\Users\David\git\YFINANCE_Playground\assets\models"

# Definición de los modelos y sus características
model_configs = [
    {"name": "best_model_google_C.keras", "features": ["Close"]},
    {"name": "best_model_google_CH.keras", "features": ["Close", "High"]},
    {"name": "best_model_google_CHL.keras", "features": ["Close", "High", "Low"]},
    {"name": "best_model_google_CHLO.keras", "features": ["Close", "High", "Low", "Open"]},
    {"name": "best_model_google_CHLOV.keras", "features": ["Close", "High", "Low", "Open", "Volume"]}
]

def get_latest_data(ticker, period="60d", interval="5m"):
    print(f"Descargando datos recientes para {ticker}...")
    data = yf.download(ticker, period=period, interval=interval)
    
    if data.empty:
        raise ValueError("No se pudieron descargar datos.")
    
    # Manejo de MultiIndex si es necesario
    if isinstance(data.columns, pd.MultiIndex):
        df = data.xs(ticker, axis=1, level=1)
    else:
        df = data.copy()
        
    return df

def predict_with_model(model_path, df, features):
    # Seleccionar columnas necesarias
    df_features = df[features].copy()
    
    # El valor real que queremos comparar es el último 'Close'
    real_value = df_features['Close'].iloc[-1]
    
    # Para la predicción, usamos los 60 pasos previos al último
    # Es decir, desde (fin - 60 - 1) hasta (fin - 1)
    input_df = df_features.iloc[-(LOOK_BACK + 1):-1]
    
    if len(input_df) < LOOK_BACK:
        return None, real_value

    # Preprocesamiento (Escalado)
    # Importante: Los modelos se entrenaron con un scaler fit sobre 60 días de datos.
    # Para ser consistentes, escalamos basándonos en los datos descargados.
    scaler = MinMaxScaler(feature_range=(0, 1))
    # Fit con todos los datos descargados para tener un rango similar al entrenamiento
    scaled_full_data = scaler.fit_transform(df_features.values)
    
    # Extraer la secuencia de entrada escalada
    # La secuencia de entrada está en las últimas LOOK_BACK filas de scaled_full_data (excluyendo la última)
    X_input = scaled_full_data[-(LOOK_BACK + 1):-1]
    X_input = np.reshape(X_input, (1, LOOK_BACK, len(features)))
    
    # Cargar modelo y predecir
    model = load_model(model_path)
    prediction_scaled = model.predict(X_input, verbose=0)
    
    # La predicción está en la escala del 'Close' (índice 0)
    # Para desescalar, necesitamos un array con la misma forma que el input del scaler
    # Creamos un dummy array para el inverse_transform
    dummy = np.zeros((1, len(features)))
    dummy[0, 0] = prediction_scaled[0, 0]
    prediction_unscaled = scaler.inverse_transform(dummy)[0, 0]
    
    return prediction_unscaled, real_value

def main():
    try:
        df = get_latest_data(TICKER)
        print(f"Última actualización de datos: {df.index[-1]}")
        print("-" * 50)
        
        results = []
        
        for config in model_configs:
            model_path = os.path.join(MODELS_DIR, config["name"])
            if not os.path.exists(model_path):
                print(f"Advertencia: No se encontró el modelo {config['name']}")
                continue
                
            print(f"Procesando modelo: {config['name']}...")
            pred, real = predict_with_model(model_path, df, config["features"])
            
            if pred is not None:
                diff = pred - real
                pct_diff = (diff / real) * 100
                results.append({
                    "Modelo": config["name"],
                    "Predicción": f"{pred:.4f}",
                    "Realidad": f"{real:.4f}",
                    "Diferencia": f"{diff:.4f}",
                    "Error %": f"{pct_diff:.2f}%"
                })
            else:
                print(f"Error: No hay suficientes datos para el modelo {config['name']}")
        
        # Mostrar resultados
        if results:
            results_df = pd.DataFrame(results)
            print("\nRESULTADOS DE LAS PREDICCIONES:")
            print(results_df.to_string(index=False))
        else:
            print("No se generaron resultados.")
            
    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    main()
