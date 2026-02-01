import os
import yfinance as yf
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

# Tensorflow / Keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam


base_dir = os.getcwd() # Obtiene la carpeta actual
save_path = os.path.join(base_dir, 'assets', 'models')

if not os.path.exists(save_path):
    os.makedirs(save_path)
    print(f"📂 Carpeta creada en tu PC: {save_path}")
else:
    print(f"📂 Usando carpeta existente: {save_path}")

# ---------------------------------------------------------
# 2. Obtención y GUARDADO de Datos
# ---------------------------------------------------------
ticker = "BTC-USD"
print(f"⬇️ Descargando datos de alta frecuencia para {ticker}...")

# Descarga de datos
data = yf.download(ticker, period="7d", interval="1m", progress=False)

if data.empty:
    raise ValueError("❌ No se descargaron datos. Verifica tu conexión a internet.")

# Limpieza básica
data = data.ffill().bfill()

# --- GUARDAR CSV LOCALMENTE ---
# csv_filename = os.path.join(save_path, f'{ticker}_data_1min_7days.csv')
# data.to_csv(csv_filename)
# print(f"✅ CSV guardado: {csv_filename}")

# ---------------------------------------------------------
# 3. Preprocesamiento MULTIVARIABLE
# ---------------------------------------------------------
features = ['Open', 'High', 'Low', 'Close', 'Volume']

# Nos aseguramos de tener solo las columnas necesarias
dataset_df = data[features]
dataset = dataset_df.values

# Configuración del Scaler
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(dataset)

# --- GUARDAR SCALER LOCALMENTE ---
scaler_filename = os.path.join(save_path, f'{ticker}_scaler.gz')
joblib.dump(scaler, scaler_filename)
print(f"✅ Scaler guardado: {scaler_filename}")

# Ventana de predicción
prediction_days = 60

# El índice de 'Close' en nuestra lista ['Open', 'High', 'Low', 'Close', 'Volume'] es 3
target_col_index = features.index('Close')

def create_sequences_multivariate(dataset, prediction_days, target_col_idx):
    x, y = [], []
    for i in range(prediction_days, len(dataset)):
        # Input: 60 días anteriores con todas las variables
        x.append(dataset[i-prediction_days:i, :])
        # Output: El precio de cierre del día actual
        y.append(dataset[i, target_col_idx])
    return np.array(x), np.array(y)

x_train, y_train = create_sequences_multivariate(scaled_data, prediction_days, target_col_index)

# Split de validación (90% train, 10% validación)
split_idx = int(len(x_train) * 0.9)
x_tr, y_tr = x_train[:split_idx], y_train[:split_idx]
x_val, y_val = x_train[split_idx:], y_train[split_idx:]

print(f"📊 Forma de los datos de entrada (X): {x_tr.shape}")

# ---------------------------------------------------------
# 4. Arquitectura del Modelo
# ---------------------------------------------------------
model = Sequential()

# Input shape: (60 pasos de tiempo, 5 características)
model.add(Bidirectional(LSTM(units=128, return_sequences=True), input_shape=(x_tr.shape[1], x_tr.shape[2])))
model.add(Dropout(0.3))

model.add(LSTM(units=64, return_sequences=False))
model.add(Dropout(0.3))

model.add(Dense(units=32, activation='relu'))
model.add(Dense(units=1)) 

optimizer = Adam(learning_rate=0.001)
model.compile(optimizer=optimizer, loss='mean_squared_error')

# ---------------------------------------------------------
# 5. Callbacks y Entrenamiento
# ---------------------------------------------------------
model_filename = os.path.join(save_path, f'{ticker}_best_model_multi.keras')

callbacks = [
    EarlyStopping(monitor='val_loss', patience=6, verbose=1, restore_best_weights=True),
    ModelCheckpoint(model_filename, monitor='val_loss', save_best_only=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, verbose=1)
]

print("🚀 Iniciando entrenamiento multivariable (Local)...")
# Nota: Si tienes GPU NVIDIA configurada, esto será rápido. Si es CPU, tardará más.
history = model.fit(x_tr, y_tr,
                    batch_size=32,
                    epochs=20, # Reduje a 20 para pruebas rápidas, puedes subirlo
                    validation_data=(x_val, y_val),
                    callbacks=callbacks)

print(f"✅ Modelo guardado: {model_filename}")

# ---------------------------------------------------------
# 6. Visualización y Predicción
# ---------------------------------------------------------
plt.figure(figsize=(10, 5))
plt.plot(history.history['loss'], label='Loss Train')
plt.plot(history.history['val_loss'], label='Loss Val')
plt.title('Error de Entrenamiento (Multivariable)')
plt.legend()
plt.show()

# --- PREDICCIÓN CON SCALER MULTIVARIABLE ---
last_sequence = scaled_data[-prediction_days:] 
last_sequence = last_sequence.reshape(1, prediction_days, 5) 

predicted_scaled_price = model.predict(last_sequence) 

# Crear matriz dummy para des-escalar correctamente
dummy_row = np.zeros((1, len(features)))
dummy_row[0, target_col_index] = predicted_scaled_price[0][0]

inverted_prediction = scaler.inverse_transform(dummy_row)
final_price = inverted_prediction[0, target_col_index]

print(f"\n🔮 Predicción precio actual {ticker}: ${final_price:.2f}")