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
# Montamos Google Drive
drive.mount('/content/drive')

# DEFINIR RUTA EN DRIVE
# Cambia esto a la carpeta donde quieras guardar los archivos
DRIVE_PATH = '/content/drive/My Drive/Colab Notebooks/Stocks'

# Crear el directorio si no existe
if not os.path.exists(DRIVE_PATH):
    os.makedirs(DRIVE_PATH)
    print(f"Directorio creado: {DRIVE_PATH}")
else:
    print(f"Usando directorio: {DRIVE_PATH}")

# Archivos de salida
LOG_FILE = os.path.join(DRIVE_PATH, 'training_log_Google_C.csv')
MODEL_FILE = os.path.join(DRIVE_PATH, 'best_model_google_C.keras')

# ---------------------------------------------------------
# 2. DESCARGA DE DATOS
# ---------------------------------------------------------
print("Descargando datos...")

# NOTA IMPORTANTE: Yahoo Finance limita los datos de intervalo '5m' a los últimos 60 días.
# Aunque pidas desde 2025-10-20, si esa fecha tiene más de 60 días de antigüedad,
# yfinance solo devolverá los últimos 60 días disponibles.
ticker = "GOOG"
data = yf.download(ticker, period="60d", interval="5m")

if data.empty:
    raise ValueError("No se descargaron datos. Verifica el intervalo o el ticker.")

# Seleccionamos solo la columna 'Close'
# yfinance a veces devuelve MultiIndex, nos aseguramos de aplanar si es necesario
if isinstance(data.columns, pd.MultiIndex):
    df = data['Close']
else:
    df = data[['Close']]

print(f"Datos descargados: {len(df)} registros.")

# ---------------------------------------------------------
# 3. PREPROCESAMIENTO
# ---------------------------------------------------------
dataset = df.values
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(dataset)

# Crear secuencias para LSTM
# Usaremos una ventana de tiempo (look_back). Por ejemplo, 60 pasos (5 horas de datos a 5m)
look_back = 60
X, y = [], []

for i in range(look_back, len(scaled_data)):
    X.append(scaled_data[i-look_back:i, 0])
    y.append(scaled_data[i, 0])

X, y = np.array(X), np.array(y)

# Reshape para LSTM [samples, time steps, features]
X = np.reshape(X, (X.shape[0], X.shape[1], 1))

print(f"Forma de los datos de entrenamiento: X={X.shape}, y={y.shape}")

# ---------------------------------------------------------
# 4. DEFINICIÓN DEL MODELO
# ---------------------------------------------------------
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], 1)))
model.add(LSTM(units=50))
model.add(Dense(1))

model.compile(optimizer='adam', loss='mean_squared_error')

# ---------------------------------------------------------
# 5. CALLBACKS PERSONALIZADOS
# ---------------------------------------------------------

class CustomCSVLogger(Callback):
    def __init__(self, filename):
        super(CustomCSVLogger, self).__init__()
        self.filename = filename

    def on_train_begin(self, logs=None):
        # Crear el archivo y escribir la cabecera
        with open(self.filename, 'w') as f:
            f.write("epoch,loss\n")

    def on_epoch_end(self, epoch, logs=None):
        # Guardar epoch (empezando en 1) y loss
        logs = logs or {}
        loss = logs.get('loss')
        with open(self.filename, 'a') as f:
            # epoch + 1 para que empiece en 1 como pediste
            f.write(f"{epoch + 1},{loss:.5f}\n")

# Callback para guardar el log en CSV
csv_logger = CustomCSVLogger(LOG_FILE)

# Callback para guardar el mejor modelo (monitorizando loss)
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