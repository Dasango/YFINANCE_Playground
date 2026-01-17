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

DRIVE_PATH = '/content/drive/My Drive/Colab Notebooks/Stocks'

# Aseguramos que el directorio base exista al inicio
if not os.path.exists(DRIVE_PATH):
    os.makedirs(DRIVE_PATH)
    print(f"Directorio creado: {DRIVE_PATH}")
else:
    print(f"Usando directorio: {DRIVE_PATH}")

# Archivos de salida (Solo Log y Modelo)
LOG_FILE = os.path.join(DRIVE_PATH, 'training_log_Google_HLOV.csv')
MODEL_FILE = os.path.join(DRIVE_PATH, 'best_model_google_HLOV.keras')

# ---------------------------------------------------------
# 2. DESCARGA DE DATOS
# ---------------------------------------------------------
print("Descargando datos...")

ticker = "GOOG"
data = yf.download(ticker, period="60d", interval="5m")

if data.empty:
    raise ValueError("No se descargaron datos.")

try:
    if isinstance(data.columns, pd.MultiIndex):
        df = data.xs(ticker, axis=1, level=1)
    else:
        df = data.copy()
except KeyError:
    df = data[['Close', 'High', 'Low', 'Open', 'Volume']]

# ---------------------------------------------------------
# 3. PREPROCESAMIENTO
# ---------------------------------------------------------
# INPUTS: High, Low, Open, Volume
df_features = df[['High', 'Low', 'Open', 'Volume']]
# TARGET: Close
df_target = df[['Close']]

print(f"Features (Inputs): {df_features.columns.tolist()}")
print(f"Target (Output): {df_target.columns.tolist()}")

# Escaladores independientes (Necesarios para el entrenamiento, aunque no se guarden)
scaler_x = MinMaxScaler(feature_range=(0, 1))
scaler_y = MinMaxScaler(feature_range=(0, 1))

scaled_features = scaler_x.fit_transform(df_features.values)
scaled_target = scaler_y.fit_transform(df_target.values)

look_back = 60
X, y = [], []

for i in range(look_back, len(scaled_features)):
    X.append(scaled_features[i-look_back:i, :])
    y.append(scaled_target[i, 0])

X, y = np.array(X), np.array(y)

n_features = 4  # H, L, O, V
X = np.reshape(X, (X.shape[0], X.shape[1], n_features))

print(f"Forma de X: {X.shape} | Forma de y: {y.shape}")

# ---------------------------------------------------------
# 4. DEFINICIÓN DEL MODELO
# ---------------------------------------------------------
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(look_back, n_features)))
model.add(LSTM(units=50))
model.add(Dense(1)) 

model.compile(optimizer='adam', loss='mean_squared_error')

# ---------------------------------------------------------
# 5. CALLBACKS ROBUSTOS
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
            if not os.path.exists(dirname):
                os.makedirs(dirname, exist_ok=True)
            
            with open(self.filename, mode) as f:
                f.write(line + "\n")
                
        except Exception as e:
            print(f"\n[Advertencia] No se pudo escribir en el log CSV: {e}")

csv_logger = RobustCSVLogger(LOG_FILE)

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
print(f"Iniciando entrenamiento...")
print(f"Log: {LOG_FILE}")
print(f"Modelo: {MODEL_FILE}")

history = model.fit(
    X, y,
    epochs=100,
    batch_size=32,
    callbacks=[csv_logger, checkpoint],
    verbose=1
)

print("\nEntrenamiento finalizado exitosamente.")
print(f"Modelo guardado en: {MODEL_FILE}")