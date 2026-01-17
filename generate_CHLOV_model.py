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

# Archivos de salida (Actualizados para reflejar las 5 columnas: CHLOV)
LOG_FILE = os.path.join(DRIVE_PATH, 'training_log_Google_CHLOV.csv')
MODEL_FILE = os.path.join(DRIVE_PATH, 'best_model_google_CHLOV.keras')

# ---------------------------------------------------------
# 2. DESCARGA DE DATOS
# ---------------------------------------------------------
print("Descargando datos...")

ticker = "GOOG"
data = yf.download(ticker, period="60d", interval="5m")

if data.empty:
    raise ValueError("No se descargaron datos. Verifica el intervalo o el ticker.")

# Manejo de MultiIndex y selección de columnas
try:
    if isinstance(data.columns, pd.MultiIndex):
        # Seleccionamos el nivel del Ticker
        df = data.xs(ticker, axis=1, level=1)
    else:
        df = data.copy()

    # Seleccionamos explícitamente las 5 columnas
    # Es vital mantener 'Close' en la posición 0 para la predicción
    columnas_deseadas = ['Close', 'High', 'Low', 'Open', 'Volume']
    df = df[columnas_deseadas]

except KeyError as e:
    print(f"Error al procesar columnas: {e}")
    # Intento de fallback
    df = data[['Close', 'High', 'Low', 'Open', 'Volume']]

# Aseguramos el orden final
df = df[['Close', 'High', 'Low', 'Open', 'Volume']]

print(f"Datos descargados: {len(df)} registros.")
print("Primeras 5 filas:")
print(df.head())

# ---------------------------------------------------------
# 3. PREPROCESAMIENTO
# ---------------------------------------------------------
dataset = df.values # Ahora dataset es de forma (n_samples, 5)

# MinMaxScaler escalará cada columna independientemente.
# Esto es crucial porque el Volumen (millones) y el Precio (cientos) tienen escalas muy distintas.
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(dataset)

# Definir ventana de tiempo y número de features
look_back = 60
n_features = 5  # Close, High, Low, Open, Volume

X, y = [], []

for i in range(look_back, len(scaled_data)):
    # X toma las últimas 60 velas con TODAS las columnas (0, 1, 2, 3, 4)
    X.append(scaled_data[i-look_back:i, :])
    
    # y toma solo el valor actual de 'Close' (índice 0)
    y.append(scaled_data[i, 0])

X, y = np.array(X), np.array(y)

# Reshape para LSTM [samples, time steps, features]
# X.shape final será (muestras, 60, 5)
X = np.reshape(X, (X.shape[0], X.shape[1], n_features))

print(f"Forma de los datos de entrenamiento: X={X.shape}, y={y.shape}")

# ---------------------------------------------------------
# 4. DEFINICIÓN DEL MODELO
# ---------------------------------------------------------
model = Sequential()
# Input shape recibe (look_back, n_features) -> (60, 5)
model.add(LSTM(units=50, return_sequences=True, input_shape=(look_back, n_features)))
model.add(LSTM(units=50))
model.add(Dense(1)) # Salida de 1 valor (Precio Close predicho)

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
print(f"Iniciando entrenamiento con 5 variables (Close, High, Low, Open, Volume).")
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