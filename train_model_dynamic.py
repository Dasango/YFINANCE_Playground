import os
import argparse
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import Callback, ModelCheckpoint

# ---------------------------------------------------------
# CALLBACK PERSONALIZADO PARA LOGS
# ---------------------------------------------------------
class RobustCSVLogger(Callback):
    def __init__(self, filename):
        super(RobustCSVLogger, self).__init__()
        self.filename = filename

    def on_train_begin(self, logs=None):
        self._write_line("epoch,loss", mode='w')

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        loss = logs.get('loss')
        self._write_line(f"{epoch + 1},{loss:.5f}", mode='a')

    def _write_line(self, line, mode):
        try:
            dirname = os.path.dirname(self.filename)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname, exist_ok=True)
            
            with open(self.filename, mode) as f:
                f.write(line + "\n")
                
        except Exception as e:
            print(f"\n[Advertencia] No se pudo escribir en el log CSV: {e}")

# ---------------------------------------------------------
# FUNCIÓN PRINCIPAL DE ENTRENAMIENTO
# ---------------------------------------------------------
def train_model(args):
    # Configuración de rutas
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, 'assets', 'models')
    logs_dir = os.path.join(base_dir, 'assets', 'logs')
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    
    model_file = os.path.join(models_dir, f"best_model_{args.ticker}_{args.suffix}.keras")
    log_file = os.path.join(logs_dir, f"training_log_{args.ticker}_{args.suffix}.csv")
    
    print(f"\n--- Iniciando Proceso para {args.ticker} ---")
    print(f"Features: {args.features}")
    print(f"Target: Close")
    
    # 1. Descarga de datos
    print(f"Descargando datos ({args.period}, {args.interval})...")
    data = yf.download(args.ticker, period=args.period, interval=args.interval)
    
    if data.empty:
        raise ValueError(f"No se pudieron descargar datos para {args.ticker}.")
    
    # Manejo de MultiIndex (yfinance a veces devuelve esto)
    if isinstance(data.columns, pd.MultiIndex):
        df = data.xs(args.ticker, axis=1, level=1)
    else:
        df = data.copy()
    
    # Asegurar que las columnas existan
    available_cols = df.columns.tolist()
    for col in args.features:
        if col not in available_cols:
            raise ValueError(f"Columna '{col}' no encontrada en los datos. Disponibles: {available_cols}")
    
    # 2. Preprocesamiento
    # Seleccionamos features y target
    df_features = df[args.features]
    df_target = df[['Close']]
    
    # Escaladores independientes
    scaler_x = MinMaxScaler(feature_range=(0, 1))
    scaler_y = MinMaxScaler(feature_range=(0, 1))
    
    scaled_features = scaler_x.fit_transform(df_features.values)
    scaled_target = scaler_y.fit_transform(df_target.values)
    
    look_back = args.look_back
    X, y = [], []
    
    for i in range(look_back, len(scaled_features)):
        X.append(scaled_features[i-look_back:i, :])
        y.append(scaled_target[i, 0])
    
    X, y = np.array(X), np.array(y)
    
    # Reshape para LSTM: [muestras, pasos de tiempo, características]
    n_features = len(args.features)
    X = np.reshape(X, (X.shape[0], X.shape[1], n_features))
    
    print(f"Forma de X: {X.shape} | Forma de y: {y.shape}")
    
    # 3. Definición del Modelo
    print("Construyendo modelo...")
    model = Sequential()
    model.add(LSTM(units=args.units, return_sequences=True, input_shape=(look_back, n_features)))
    model.add(LSTM(units=args.units))
    model.add(Dense(1))
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    
    # 4. Callbacks
    csv_logger = RobustCSVLogger(log_file)
    checkpoint = ModelCheckpoint(
        model_file,
        monitor='loss',
        verbose=1,
        save_best_only=True,
        mode='min'
    )
    
    # 5. Entrenamiento
    print(f"Entrenando por {args.epochs} épocas...")
    print(f"Log: {log_file}")
    print(f"Modelo: {model_file}")
    
    model.fit(
        X, y,
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=[csv_logger, checkpoint],
        verbose=1
    )
    
    print("\n--- Entrenamiento Finalizado ---")
    print(f"Modelo guardado en: {model_file}")
    print(f"Logs guardados en: {log_file}")

# ---------------------------------------------------------
# CONFIGURACIÓN DE ARGUMENTOS
# ---------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrenamiento dinámico de modelos de Stocks")
    
    parser.add_argument("--ticker", type=str, default="GOOG", help="Ticker de la acción (ej: GOOG, MSFT)")
    parser.add_argument("--period", type=str, default="60d", help="Periodo de datos (ej: 60d, 1mo, 1y)")
    parser.add_argument("--interval", type=str, default="5m", help="Intervalo de datos (ej: 5m, 1h, 1d)")
    parser.add_argument("--look_back", type=int, default=60, help="Ventana de tiempo para la predicción")
    parser.add_argument("--epochs", type=int, default=30, help="Número de épocas de entrenamiento")
    parser.add_argument("--batch_size", type=int, default=32, help="Tamaño del batch")
    parser.add_argument("--units", type=int, default=5, help="Unidades en las capas LSTM")
    parser.add_argument("--features", type=str, default="Close,High,Low,Open,Volume", 
                        help="Lista de columnas separadas por coma (ej: Close,High)")
    parser.add_argument("--suffix", type=str, default="custom", help="Sufijo para identificar el modelo en los archivos")
    
    args = parser.parse_args()
     
    # Procesar features como lista
    args.features = [f.strip() for f in args.features.split(",")]
    
    train_model(args)
