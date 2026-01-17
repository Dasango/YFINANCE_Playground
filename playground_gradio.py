import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import os

# Load data
csv_path = r"c:\Users\David\git\YFINANCE_Playground\assets\datos_google_5m_2026-01-16.csv"
try:
    df = pd.read_csv(csv_path, skiprows=3, names=["Datetime", "Close", "High", "Low", "Open", "Volume"])
    df["Datetime"] = pd.to_datetime(df["Datetime"])
    df_chart = df.tail(150) # Use a portion for clearer visualization
except Exception as e:
    print(f"Error loading CSV: {e}")
    df_chart = pd.DataFrame({"Datetime": [], "Close": []})

# CSS to match the requested colors and layout
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-main: #020617;
    --sidebar-bg: #0F172A;
    --topbar-bg: #0F172A;
    --card-bg: #0C1327;
    --text-primary: #ffffff;
    --text-secondary: #64748B;
    --accent-green: #059669;
    --accent-red: #E11D48;
    --border-color: rgba(255, 255, 255, 0.05);
}

body, .gradio-container {
    background-color: var(--bg-main) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Layout Setup */
.main-wrapper {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

/* Topbar Styling */
.topbar {
    background-color: var(--topbar-bg) ;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    border-bottom: 1px solid var(--border-color);
}

.header-msg {
    color: var(--accent-green);
    font-size: 14px;
    font-weight: 500;
}

/* GitHub Ribbon (Inverted Triangle in TopBar) */
.github-corner {
    position: absolute;
    top: 0;
    right: 0;
    width: 50px;
    height: 50px;
    background-color: var(--accent-green);
    clip-path: polygon(100% 0, 0 0, 100% 100%);
    display: flex;
    align-items: flex-start;
    justify-content: flex-end;
    padding: 6px;
    z-index: 1001;
}
.github-corner img {
    width: 22px;
    height: 22px;
    filter: invert(1);
}

/* Content Layout */
.content-body {
    display: flex;
    flex: 1;
}

/* Sidebar Styling */
.sidebar-container {
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border-color);
    padding: 20px !important;
    min-width: 220px !important;
    max-width: 220px !important;
}

.logo-text {
    font-size: 18px;
    font-weight: 700;
    color: var(--accent-green);
}

.sub-logo-text {
    font-size: 9px;
    color: var(--text-secondary);
    letter-spacing: 2px;
    margin-bottom: 30px;
}

.nav-btn {
    text-align: left !important;
    justify-content: flex-start !important;
    background: transparent !important;
    border: none !important;
    color: var(--text-secondary) !important;
    margin-bottom: 4px !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
}

.nav-btn.active {
    background: rgba(5, 150, 105, 0.1) !important;
    color: var(--accent-green) !important;
    border-left: 3px solid var(--accent-green) !important;
    border-radius: 2px 8px 8px 2px !important;
}

/* Main Main Styling */
.main-content {
    flex: 1;
    padding: 30px !important;
    background-color: var(--bg-main);
}

.glass-card {
    background-color: var(--card-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    margin-bottom: 16px;
}

.section-title {
    font-size: 10px;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
}

/* Param Buttons (Same color as Card, not black) */
.param-item {
    background: var(--card-bg) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-secondary) !important;
    font-size: 14px !important;
    padding: 12px !important;
    border-radius: 8px !important;
    text-align: left !important;
    margin-bottom: 6px !important;
}

.param-item.active {
    background: var(--accent-red) !important;
    color: white !important;
    border: none !important;
}

.asset-icon-btn {
    min-width: 40px !important;
    background: var(--card-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
}

.asset-icon-btn.active {
    border-color: var(--accent-green) !important;
    background: rgba(5, 150, 105, 0.1) !important;
}

.btn-train {
    background: var(--accent-green) !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 14px !important;
}

.lang-btn {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-secondary) !important;
    font-size: 10px !important;
}

/* Badges */
.livestream-badge {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    font-size: 10px;
    color: var(--text-secondary);
    padding: 3px 10px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
"""

translations = {
    "es": {
        "header": "Entrena un modelo directamente en el navegador.",
        "sidebar_predictor": "Predictor",
        "sidebar_network": "Red Neuronal",
        "sidebar_lstm": "LSTM",
        "sidebar_collab": "Colaborar",
        "sidebar_credits": "Créditos",
        "section_assets": "ACTIVOS",
        "section_params": "PARAMETROS",
        "section_epoch": "EPOCH PROGRESS",
        "btn_train": "TRAIN",
        "chart_performance": "Rendimiento del Modelo",
        "chart_loss": "LOSS (MSE)",
        "lang_btn": "CAMBIAR A INGLES EN",
        "livestream": "LIVE STREAM"
    },
    "en": {
        "header": "Train a model directly in the browser.",
        "sidebar_predictor": "Predictor",
        "sidebar_network": "Neural Network",
        "sidebar_lstm": "LSTM",
        "sidebar_collab": "Collaborate",
        "sidebar_credits": "Credits",
        "section_assets": "ASSETS",
        "section_params": "PARAMETERS",
        "section_epoch": "EPOCH PROGRESS",
        "btn_train": "TRAIN",
        "chart_performance": "Model Performance",
        "chart_loss": "LOSS (MSE)",
        "lang_btn": "SWITCH TO SPANISH ES",
        "livestream": "LIVE STREAM"
    }
}

def create_styled_perf_chart(lang):
    title = translations[lang]["chart_performance"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_chart["Datetime"],
        y=df_chart["Close"],
        mode='lines',
        line=dict(color='#059669', width=2),
        fill='tozeroy',
        fillcolor='rgba(5, 150, 105, 0.05)'
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#0C1327',
        plot_bgcolor='#0C1327',
        showlegend=False,
        margin=dict(l=40, r=20, t=20, b=40),
        height=380,
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#64748B', size=10)),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.05)',
            gridwidth=1,
            griddash='dot',
            zeroline=False,
            tickprefix="$",
            tickfont=dict(color='#64748B', size=10),
        ),
        font=dict(family="Inter", color="white")
    )
    return fig

def create_styled_loss_chart(lang):
    iters = list(range(30))
    vals = [max(0.0001, 2.5 * (0.82**i)) for i in iters]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=iters, y=vals, mode='lines', line=dict(color='#059669', width=2)))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#0C1327',
        plot_bgcolor='#0C1327',
        showlegend=False,
        margin=dict(l=40, r=20, t=10, b=40),
        height=200,
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#64748B', size=10)),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.05)',
            gridwidth=1,
            griddash='dot',
            zeroline=False,
            tickfont=dict(color='#64748B', size=10)
        ),
        font=dict(family="Inter", color="white")
    )
    return fig

with gr.Blocks(css=custom_css, title="LSTM Playground") as demo:
    lang_state = gr.State("es")
    
    with gr.Column(elem_classes=["main-wrapper"]):
        # TOPBAR
        with gr.Row(elem_classes=["topbar"]):
            header = gr.Markdown(translations["es"]["header"])

        # Main Layout (Sidebar + Content)
        with gr.Row(elem_classes=["content-body"]):
            # SIDEBAR
            with gr.Column(scale=1, elem_classes=["sidebar-container"]):
                gr.Markdown("<div class='logo-text'>LSTM playground</div><div class='sub-logo-text'>UCE CS</div>")
                
                nav_1 = gr.Button(translations["es"]["sidebar_predictor"], elem_classes=["nav-btn", "active"])
                nav_2 = gr.Button(translations["es"]["sidebar_network"], elem_classes=["nav-btn"])
                nav_3 = gr.Button(translations["es"]["sidebar_lstm"], elem_classes=["nav-btn"])
                nav_4 = gr.Button(translations["es"]["sidebar_collab"], elem_classes=["nav-btn"])
                nav_5 = gr.Button(translations["es"]["sidebar_credits"], elem_classes=["nav-btn"])
                
                gr.HTML("<div style='flex-grow: 1;'></div>")
                lang_toggle = gr.Button(translations["es"]["lang_btn"], elem_classes=["lang-btn"])

            # MAIN CONTENT
            with gr.Column(scale=5, elem_classes=["main-content"]):
                with gr.Row():
                    # Left Params
                    with gr.Column(scale=1):
                        with gr.Column(elem_classes=["glass-card"]):
                            l_assets = gr.Markdown(f"<div class='section-title'>{translations['es']['section_assets']}</div>")
                            with gr.Row():
                                gr.Button("G", elem_classes=["asset-icon-btn"])
                                gr.Button("M", elem_classes=["asset-icon-btn"])
                                gr.Button("T", elem_classes=["asset-icon-btn", "active"])
                                gr.Button("B", elem_classes=["asset-icon-btn"])
                                
                        with gr.Column(elem_classes=["glass-card"]):
                            l_params = gr.Markdown(f"<div class='section-title'>{translations['es']['section_params']}</div>")
                            gr.Button("Open", elem_classes=["param-item"])
                            gr.Button("High", elem_classes=["param-item"])
                            gr.Button("Low", elem_classes=["param-item"])
                            gr.Button("Close", elem_classes=["param-item", "active"])
                            gr.Button("Volume", elem_classes=["param-item"])
                            
                        with gr.Column(elem_classes=["glass-card"]):
                            l_epoch = gr.Markdown(f"<div class='section-title' style='text-align:center;'>{translations['es']['section_epoch']}</div>")
                            gr.Markdown("<div style='font-size:32px; color:var(--accent-green); text-align:center; font-weight:700; margin-bottom:10px;'>0.0000</div>")
                            btn_train = gr.Button(translations["es"]["btn_train"], elem_classes=["btn-train"])

                    # Right Charts
                    with gr.Column(scale=3):
                        with gr.Column(elem_classes=["glass-card"]):
                            with gr.Row():
                                with gr.Column(scale=4):
                                    title_perf = gr.Markdown(f"<div style='font-size:22px; font-weight:700;'>{translations['es']['chart_performance']}</div><div style='font-size:13px; color:var(--text-secondary);'>Google — GOOGL</div>")
                                with gr.Column(scale=1, min_width=100):
                                    gr.HTML(f"<div class='livestream-badge'><span style='color:#64748B;'>•</span> {translations['es']['livestream']}</div>")
                            
                            perf_plot = gr.Plot(create_styled_perf_chart("es"), show_label=False, container=False)
                            
                        with gr.Row(elem_classes=["glass-card"]):
                            with gr.Column(scale=1):
                                l_loss = gr.Markdown(f"<div class='section-title'>{translations['es']['chart_loss']}</div>")
                                gr.Markdown("<div style='font-size:28px; color:var(--accent-green); font-weight:700;'>0.000000</div>")
                                gr.Markdown("<div style='font-size:10px; color:var(--text-secondary);'>ITERATION 0/30</div>")
                            with gr.Column(scale=2):
                                loss_plot = gr.Plot(create_styled_loss_chart("es"), show_label=False, container=False)

    # Multi-language action
    def switch_language(lang):
        new_lang = "en" if lang == "es" else "es"
        t = translations[new_lang]
        return [
            new_lang,
            gr.update(value=t['header']),
            gr.update(value=t["sidebar_predictor"]),
            gr.update(value=t["sidebar_network"]),
            gr.update(value=t["sidebar_lstm"]),
            gr.update(value=t["sidebar_collab"]),
            gr.update(value=t["sidebar_credits"]),
            gr.update(value=t["lang_btn"]),
            gr.update(value=f"<div class='section-title'>{t['section_assets']}</div>"),
            gr.update(value=f"<div class='section-title'>{t['section_params']}</div>"),
            gr.update(value=f"<div class='section-title' style='text-align:center;'>{t['section_epoch']}</div>"),
            gr.update(value=t["btn_train"]),
            gr.update(value=f"<div style='font-size:22px; font-weight:700;'>{t['chart_performance']}</div><div style='font-size:13px; color:var(--text-secondary);'>Google — GOOGL</div>"),
            gr.update(value=f"<div class='section-title'>{t['chart_loss']}</div>"),
            create_styled_perf_chart(new_lang),
            create_styled_loss_chart(new_lang)
        ]

    lang_toggle.click(
        switch_language, inputs=[lang_state],
        outputs=[lang_state, header, nav_1, nav_2, nav_3, nav_4, nav_5, lang_toggle, l_assets, l_params, l_epoch, btn_train, title_perf, l_loss, perf_plot, loss_plot]
    )

if __name__ == "__main__":
    demo.launch()
