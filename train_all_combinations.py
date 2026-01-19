import os
import argparse
import itertools
import shutil
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import Callback, ModelCheckpoint

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
class RobustCSVLogger(Callback):
    def __init__(self, filename):
        super(RobustCSVLogger, self).__init__()
        self.filename = filename
        self.current_epoch = 0
        self.global_step = 0

    def on_train_begin(self, logs=None):
        self._write_line("step,epoch,batch,loss", mode='w')

    def on_epoch_begin(self, epoch, logs=None):
        self.current_epoch = epoch + 1

    def on_batch_end(self, batch, logs=None):
        self.global_step += 1
        logs = logs or {}
        loss = logs.get('loss', 0)
        self._write_line(f"{self.global_step},{self.current_epoch},{batch + 1},{loss:.5f}", mode='a')

    def _write_line(self, line, mode):
        try:
            dirname = os.path.dirname(self.filename)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname, exist_ok=True)
            with open(self.filename, mode) as f:
                f.write(line + "\n")
        except Exception as e:
            print(f"\n[Advertencia] No se pudo escribir en el log CSV: {e}")

def get_all_combinations(features):
    combinations = []
    for r in range(1, len(features) + 1):
        combinations.extend(itertools.combinations(features, r))
    return combinations

def clear_directory_content(directory):
    if not os.path.exists(directory):
        return
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'No se pudo borrar {file_path}. Razón: {e}')

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main(args):
    # Dirs
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, 'assets')
    data_dir = os.path.join(assets_dir, 'real_data')
    models_dir = os.path.join(assets_dir, 'models')
    logs_dir = os.path.join(assets_dir, 'logs')
    
    # Limpiar directorios antes de empezar
    print("--- Limpiando directorios de assets ---")
    clear_directory_content(data_dir)
    clear_directory_content(models_dir)
    clear_directory_content(logs_dir)
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    # 1. DATA LOADING / CACHING
    data_file = os.path.join(data_dir, f"{args.ticker}_data.csv")
    
    print(f"--- Gestionando datos para {args.ticker} ---")
    if os.path.exists(data_file):
        print(f"Cargando datos locales de: {data_file}")
        df = pd.read_csv(data_file, index_col=0, parse_dates=True)
    else:
        print(f"Descargando datos ({args.period}, {args.interval})...")
        df = yf.download(args.ticker, period=args.period, interval=args.interval)
        if df.empty:
            raise ValueError(f"No se pudieron descargar datos para {args.ticker}.")
        
        # Handle MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            try:
                df = df.xs(args.ticker, axis=1, level=1)
            except:
                pass # might already be correct if single ticker
        
        # Save cache
        print(f"Guardando datos en: {data_file}")
        df.to_csv(data_file)
    
    if df.empty:
        print("El DataFrame está vacío. Abortando.")
        return

    # Check available features
    possible_features = ["Close", "High", "Low", "Open", "Volume"]
    available = [c for c in possible_features if c in df.columns]
    if len(available) != 5:
        print(f"Advertencia: No todas las columnas esperadas están en los datos. Disponibles: {df.columns.tolist()}")

    # 2. ITERATE COMBINATIONS
    combos = get_all_combinations(available)
    print(f"--- Iniciando entrenamiento de {len(combos)} modelos ---")
    
    for i, features_tuple in enumerate(combos, 1):
        features = list(features_tuple)
        features_str = "_".join(features)
        model_name = f"{args.ticker}_{features_str}"
        
        print(f"\n[{i}/{len(combos)}] Entrenando modelo: {model_name}")
        
        # Files
        model_file = os.path.join(models_dir, f"{model_name}.keras")
        log_file = os.path.join(logs_dir, f"{model_name}.csv")
        
        # Preprocessing
        df_subset = df[features].copy()
        target_col = 'Close' # Always predicting Close? Or predicting next step of features? 
                             # Assuming target is "Close" based on previous script.
                             # But if "Close" is not in features? 
                             # Requirement: "entrene todos los modelos posibles con esos 5 posibles"
                             # Usually we predict one specific thing (Close). 
                             # If "Close" is not in input features, we can still predict it if it's in df (which it is).
                             # So inputs = features combination, Output = Close.
        
        df_target = df[[target_col]]
        
        scaler_x = MinMaxScaler(feature_range=(0, 1))
        scaler_y = MinMaxScaler(feature_range=(0, 1))
        
        X_scaled = scaler_x.fit_transform(df_subset.values)
        y_scaled = scaler_y.fit_transform(df_target.values)
        
        look_back = args.look_back
        X_train, y_train = [], []
        
        if len(X_scaled) <= look_back:
            print(f"Datos insuficientes para look_back={look_back}. Saltando.")
            continue

        for j in range(look_back, len(X_scaled)):
            X_train.append(X_scaled[j-look_back:j, :])
            y_train.append(y_scaled[j, 0])
            
        X_train, y_train = np.array(X_train), np.array(y_train)
        
        # Reshape [samples, time steps, features]
        # X_train is already [samples, look_back, n_features] if constructed correctly above?
        # range logic: X_scaled[0:60] is one sample (60, n_features).
        # X_train will be list of (60, n_features).
        # np.array(X_train) -> (samples, 60, n_features).
        
        n_features_in = len(features)
        
        # Define Model
        model = Sequential()
        model.add(LSTM(units=args.units, return_sequences=True, input_shape=(look_back, n_features_in)))
        model.add(LSTM(units=args.units))
        model.add(Dense(1))
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        
        csv_logger = RobustCSVLogger(log_file)
        # Note: Removing ModelCheckpoint for every single epoch if not needed, 
        # or keeping it to save best result? User said "save models to assets/models".
        # I'll save the final model or best? "best_model" implies best.
        checkpoint = ModelCheckpoint(
            model_file, monitor='loss', verbose=0, save_best_only=True, mode='min'
        )
        
        model.fit(
            X_train, y_train,
            epochs=args.epochs,
            batch_size=args.batch_size,
            callbacks=[csv_logger, checkpoint],
            verbose=0 # Less noise
        )
        print(f"   -> Guardado en {model_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Defaults defaults
    parser.add_argument("--ticker", type=str, default="BTC-USD", help="Ticker symbol (default: BTC-USD)")
    parser.add_argument("--period", type=str, default="60d")
    parser.add_argument("--interval", type=str, default="5m")
    parser.add_argument("--look_back", type=int, default=60)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=20)
    parser.add_argument("--units", type=int, default=50) # Default units wasn't specified, picking reasonable default or similar to prev
    
    args = parser.parse_args()
    main(args)
