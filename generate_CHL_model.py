import os
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import Callback, ModelCheckpoint
from google.colab import drive

# ---------------------------------------------------------
# 1. CONFIGURACIÓN Y MONTAJE DE DRIVE
# ---------------------------------------------------------
drive.mount('/content/drive')

# DEFINIR RUTA EN DRIVE
DRIVE_PATH = '/content/drive/My Drive/Colab Notebooks/Stocks'

if not os.path.exists(DRIVE_PATH):
    os.makedirs(DRIVE_PATH)
    print(f"Directorio creado: {DRIVE_PATH}")
else:
    print(f"Usando directorio: {DRIVE_PATH}")

# Archivos de salida (Actualizados para reflejar las 3 columnas)
LOG_FILE = os.path.join(DRIVE_PATH, 'training_log_Google_CHL.csv') # CHL = Close, High, Low
MODEL_FILE = os.path.join(DRIVE_PATH, 'best_model_google_CHL.keras')

# ---------------------------------------------------------
# 2. DESCARGA DE DATOS
# ---------------------------------------------------------
print("Descargando datos...")

ticker = "GOOG"
data = yf.download(ticker, period="60d", interval="5m")

if data.empty:
    raise ValueError("No se descargaron datos. Verifica el intervalo o el ticker.")

# Manejo robusto de columnas (MultiIndex de yfinance)
# Queremos asegurarnos de obtener Close, High y Low
try:
    if isinstance(data.columns, pd.MultiIndex):
        # Si tiene niveles (Price, Ticker), extraemos por nivel
        df = data.xs(ticker, axis=1, level=1)
        df = df[['Close', 'High', 'Low']]
    else:
        df = data[['Close', 'High', 'Low']]
except KeyError:
    # Fallback genérico si la estructura es distinta
    df = data[['Close', 'High', 'Low']]

# IMPORTANTE: Forzamos el orden de las columnas.
# Índice 0: Close (Target a predecir)
# Índice 1: High
# Índice 2: Low
df = df[['Close', 'High', 'Low']]

print(f"Datos descargados: {len(df)} registros.")
print("Primeras 5 filas:")
print(df.head())

# ---------------------------------------------------------
# 3. PREPROCESAMIENTO
# ---------------------------------------------------------
dataset = df.values # Ahora dataset es de forma (n_samples, 3)
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(dataset)

# Definir ventana de tiempo y número de features
look_back = 60
n_features = 3  # Close, High, Low

X, y = [], []

for i in range(look_back, len(scaled_data)):
    # X toma las últimas 60 velas con TODAS las columnas (0, 1, 2)
    X.append(scaled_data[i-look_back:i, :])
    
    # y toma solo el valor actual de 'Close' (índice 0)
    # Queremos predecir el Cierre basándonos en la historia de Cierre, Alto y Bajo
    y.append(scaled_data[i, 0])

X, y = np.array(X), np.array(y)

# Reshape para LSTM [samples, time steps, features]
X = np.reshape(X, (X.shape[0], X.shape[1], n_features))

print(f"Forma de los datos de entrenamiento: X={X.shape}, y={y.shape}")
# X.shape debería ser (muestras, 60, 3)

# ---------------------------------------------------------
# 4. DEFINICIÓN DEL MODELO
# ---------------------------------------------------------
model = Sequential()
# input_shape ahora es (60, 3)
model.add(LSTM(units=50, return_sequences=True, input_shape=(look_back, n_features)))
model.add(LSTM(units=50))
model.add(Dense(1)) # Salida de 1 valor (Precio Close)

model.compile(optimizer='adam', loss='mean_squared_error')

# ---------------------------------------------------------
# 5. CALLBACKS PERSONALIZADOS
# ---------------------------------------------------------

class CustomCSVLogger(Callback):
    def __init__(self, filename):
        super(CustomCSVLogger, self).__init__()
        self.filename = filename

    def on_train_begin(self, logs=None):
        with open(self.filename, 'w') as f:
            f.write("epoch,loss\n")

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        loss = logs.get('loss')
        with open(self.filename, 'a') as f:
            f.write(f"{epoch + 1},{loss:.5f}\n")

csv_logger = CustomCSVLogger(LOG_FILE)

checkpoint = ModelCheckpoint(
    MODEL_FILE,
    monitor='loss',
    verbose=1,
    save_best_only=True,
    mode='min'
)

# ---------------------------------------------------------
# 6. ENTRENAMIENTO
# ---------------------------------------------------------
print(f"Iniciando entrenamiento con 3 variables (Close, High, Low).")
print(f"Log: {LOG_FILE}")

history = model.fit(
    X, y,
    epochs=100,
    batch_size=32,
    callbacks=[csv_logger, checkpoint],
    verbose=1
)

print("Entrenamiento finalizado.")
print(f"Mejor modelo guardado en: {MODEL_FILE}")