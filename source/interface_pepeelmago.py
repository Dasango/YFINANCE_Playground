import gradio as gr
import subprocess
import sys
import os
from monitor_training import create_monitor_ui
from realtime_active_data_linechart import create_realtime_chart_component

def start_training():
    """
    Starts the training script in a separate process.
    """
    try:
        # Use sys.executable to ensure we use the same Python environment
        script_path = os.path.abspath("train_model_dynamic.py")
        # Run strictly with default values as requested
        process = subprocess.Popen([sys.executable, script_path])
        return f"Entrenamiento iniciado (PID: {process.pid})"
    except Exception as e:
        return f"Error al iniciar: {str(e)}"

# Defaults for the realtime chart (matching train_model_dynamic defaults)
DEFAULT_TICKER = "GOOG"
DEFAULT_PERIOD = "60d" 
DEFAULT_INTERVAL = "5m"

with gr.Blocks(title="Interfaz PepeElMago", theme=gr.themes.Default(primary_hue="emerald", secondary_hue="slate")) as demo:
    # 1. Título
    gr.Markdown("# 🧙‍♂️ Interfaz PepeElMago")
    
    # 2. Botón
    with gr.Row():
        train_btn = gr.Button("🚀 Entrenar Modelo (Default)", variant="primary", scale=0)
        train_status = gr.Textbox(label="Estado", interactive=False, scale=1)
    
    train_btn.click(fn=start_training, outputs=[train_status])
    
    # 3. Monitor Training Linechart
    # (El usuario pidió primero la gráfica de monitoreo)
    gr.Markdown("## 📊 Monitor de Entrenamiento")
    create_monitor_ui()
    
    # 4. Realtime Active Data Linechart
    gr.Markdown("## 📈 Datos en Tiempo Real (Últimas 24h)")
    create_realtime_chart_component(ticker=DEFAULT_TICKER, period=DEFAULT_PERIOD, interval=DEFAULT_INTERVAL)

if __name__ == "__main__":
    demo.launch(server_port=7862)
