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

# Archivos de salida (Nombres actualizados para reflejar que usa Close y High)
LOG_FILE = os.path.join(DRIVE_PATH, 'training_log_Google_CH.csv')
MODEL_FILE = os.path.join(DRIVE_PATH, 'best_model_google_CH.keras')

# ---------------------------------------------------------
# 2. DESCARGA DE DATOS
# ---------------------------------------------------------
print("Descargando datos...")

ticker = "GOOG"
# Descargamos Close y High implícitamente al descargar todo, luego filtramos
data = yf.download(ticker, period="60d", interval="5m")

if data.empty:
    raise ValueError("No se descargaron datos. Verifica el intervalo o el ticker.")

# Seleccionamos las columnas 'Close' y 'High'
# Manejo de MultiIndex si yfinance devuelve (Price, Ticker)
if isinstance(data.columns, pd.MultiIndex):
    # Intentamos acceder directamente, si falla, usamos droplevel
    try:
        df = data[['Close', 'High']]
    except KeyError:
        # Si la estructura es compleja, a veces es necesario aplanar primero
        print("Ajustando formato de columnas...")
        df = data.xs(ticker, axis=1, level=1)[['Close', 'High']]
else:
    df = data[['Close', 'High']]

# Aseguramos el orden: Columna 0 = Close, Columna 1 = High
df = df[['Close', 'High']]

print(f"Datos descargados: {len(df)} registros.")
print(df.head())

# ---------------------------------------------------------
# 3. PREPROCESAMIENTO
# ---------------------------------------------------------
dataset = df.values # Ahora dataset es de forma (n_samples, 2)
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(dataset)

# Crear secuencias para LSTM
look_back = 60
X, y = [], []

# Recorremos los datos
for i in range(look_back, len(scaled_data)):
    # X incluye las últimas 60 velas de AMBAS columnas (Close y High)
    # scaled_data[i-look_back:i, :] toma todas las columnas (0 y 1)
    X.append(scaled_data[i-look_back:i, :])
    
    # y es el valor que queremos predecir. 
    # Generalmente queremos predecir el 'Close' siguiente.
    # Como 'Close' es la columna 0, usamos scaled_data[i, 0]
    y.append(scaled_data[i, 0])

X, y = np.array(X), np.array(y)

# Reshape para LSTM [samples, time steps, features]
# Features ahora es 2 (Close y High)
n_features = 2
X = np.reshape(X, (X.shape[0], X.shape[1], n_features))

print(f"Forma de los datos de entrenamiento: X={X.shape}, y={y.shape}")
# X.shape debería ser (muestras, 60, 2)

# ---------------------------------------------------------
# 4. DEFINICIÓN DEL MODELO
# ---------------------------------------------------------
model = Sequential()
# Input shape ahora recibe (look_back, 2)
model.add(LSTM(units=50, return_sequences=True, input_shape=(look_back, n_features)))
model.add(LSTM(units=50))
model.add(Dense(1)) # Salida de 1 valor (el precio Close predicho)

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
print(f"Iniciando entrenamiento. Los logs se guardarán en: {LOG_FILE}")

history = model.fit(
    X, y,
    epochs=100,
    batch_size=32,
    callbacks=[csv_logger, checkpoint],
    verbose=1
)

print("Entrenamiento finalizado.")
print(f"Mejor modelo guardado en: {MODEL_FILE}")