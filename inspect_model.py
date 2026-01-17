import tensorflow as tf
import os

model_path = r'c:\Users\David\git\YFINANCE_Playground\assets\best_model_google.keras'

if os.path.exists(model_path):
    try:
        model = tf.keras.models.load_model(model_path)
        print("Model summary:")
        model.summary()
        print("\nInput shape:", model.input_shape)
    except Exception as e:
        print(f"Error loading model: {e}")
else:
    print("Model not found")
