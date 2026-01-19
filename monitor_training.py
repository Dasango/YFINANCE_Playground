import gradio as gr
import pandas as pd
import plotly.express as px
import os
import time


# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'assets', 'logs')

def get_latest_log_file():
    if not os.path.exists(LOGS_DIR):
        return None
    files = [os.path.join(LOGS_DIR, f) for f in os.listdir(LOGS_DIR) if f.endswith('.csv')]
    if not files:
        return None
    # Retornar el archivo modificado más recientemente
    return max(files, key=os.path.getmtime)

def update_chart():
    log_file = get_latest_log_file()
    if not log_file:
        return px.line(title="No logs found"), "Esperando datos..."
    
    try:
        df = pd.read_csv(log_file)
        if df.empty:
            return px.line(), "Cargando datos..."
        
        # Filtrar cada 5 batches para que no sea tan larga
        df_filtered = df.iloc[::5, :].copy()
        
        # Si el último punto no está incluido por el filtro, lo añadimos para ver el final real
        if not df.empty and df.index[-1] not in df_filtered.index:
            df_filtered = pd.concat([df_filtered, df.iloc[[-1]]])

        # Resumen de estado (Preservamos esto)
        latest = df.iloc[-1]
        epoch_val = int(latest['epoch'])
        batch_val = int(latest['batch'])
        loss_val = latest['loss']
        
        # Crear la gráfica minimalista
        fig = px.line(df_filtered, x="step", y="loss")
        
        # 1. Curva más suave (spline) y línea negra
        fig.update_traces(
            line_shape='spline', 
            line_color='black', 
            line_width=3
        )
        
        # 2. Fondo totalmente blanco y quitar títulos
        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            title_text="", # Sin título
            margin=dict(l=40, r=20, t=20, b=40), # Espacio para ver los ejes
            showlegend=False
        )
        
        # 3. Ejes X y Y negros, sin cuadros, sin números, sin etiquetas
        fig.update_xaxes(
            title_text="",      # Sin "Total Batches"
            showticklabels=False, # Sin números
            showgrid=False,     # Sin cuadros/rejilla
            linecolor='black',  # Eje negro
            linewidth=2,
            zeroline=False
        )
        fig.update_yaxes(
            title_text="",      # Sin "Loss"
            showticklabels=False, # Sin números
            showgrid=False,     # Sin cuadros/rejilla
            linecolor='black',  # Eje negro
            linewidth=2,
            zeroline=False
        )
        
        status_text = f"Época {epoch_val} | Batch {batch_val} | Loss: {loss_val:.6f}"
        
        return fig, status_text
    except Exception as e:
        return px.line(), str(e)

def create_monitor_ui():
    """Crea y retorna los componentes de la interfaz del monitor."""
    with gr.Column(elem_id="main-container"):
        gr.Markdown("""
        # 🚀 Model Training Monitor
        *Visualización en tiempo real del progreso del modelo.*
        """)
        
        with gr.Row():
            with gr.Column(scale=4):
                plot = gr.Plot(label="Curva de Loss (MSE)", show_label=False)
            with gr.Column(scale=1):
                status = gr.Label(label="Último Estado", value="Esperando datos...")
                gr.Markdown("### 📊 Controles")
                gr.Markdown("La gráfica se actualiza automáticamente cada 0.5 segundos para reflejar el progreso del entrenamiento.")
    
    # Gradio 6.x: Timer para actualizaciones periódicas (0.5s para mayor fluidez)
    timer = gr.Timer(0.5)
    timer.tick(update_chart, outputs=[plot, status])
    
    # Carga inicial
    # Note: In newer Gradio versions, we might need to handle this differently if not in Blocks directly, 
    # but timer should trigger it. Adding a load event manually if needed.
    # However, create_monitor_ui is intended to be called inside a Blocks context.
    # We can't use demo.load here because demo is not defined. 
    # We can rely on the Timer to start updates, or use a load on the component?
    # gr.Plot doesn't have a load event. 
    # Leaving it to the timer is fine for now, or the parent can handle load.
    
    return plot, status

if __name__ == "__main__":
    with gr.Blocks(
        title="Monitor de Entrenamiento",
        theme=gr.themes.Default(primary_hue="emerald", secondary_hue="slate")
    ) as demo:
        create_monitor_ui()
        
        # CSS para el look premium (Ajustado para el gráfico blanco)
        demo.css = """
            #main-container { padding: 20px; background-color: #f8f9fa; color: #1a1a1b; border-radius: 15px; border: 1px solid #ddd; }
            .gradio-container { background-color: #ffffff !important; }
            footer { display: none !important; }
        """
        
    demo.launch(server_port=7861)

