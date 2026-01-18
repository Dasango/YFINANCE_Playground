import gradio as gr
from ..config import TRANSLATIONS
from ..charts import create_styled_perf_chart, create_styled_loss_chart

def create_charts_section(lang):
    t = TRANSLATIONS[lang]
    with gr.Column(scale=3):
        # Performance Chart Card
        with gr.Column(elem_classes=["glass-card"]):
            with gr.Row():
                with gr.Column(scale=4):
                    title_perf = gr.Markdown(f"<div style='font-size:22px; font-weight:700;'>{t['chart_performance']}</div><div style='font-size:13px; color:var(--text-secondary);'>{t['asset_google']}</div>")
                with gr.Column(scale=1, min_width=100):
                    gr.HTML(f"<div class='livestream-badge'><span style='color:#64748B;'>•</span> {t['livestream']}</div>")
            
            perf_plot = gr.Plot(create_styled_perf_chart(lang), show_label=False, container=False)
            
        # Loss Chart Card
        with gr.Row(elem_classes=["glass-card"]):
            with gr.Column(scale=1):
                l_loss = gr.Markdown(f"<div class='section-title'>{t['chart_loss']}</div>")
                gr.Markdown("<div style='font-size:28px; color:var(--accent-green); font-weight:700;'>0.000000</div>")
                gr.Markdown(f"<div style='font-size:10px; color:var(--text-secondary);'>{t['iteration']} 0/30</div>")
            with gr.Column(scale=2):
                loss_plot = gr.Plot(create_styled_loss_chart(lang), show_label=False, container=False)
                
    return title_perf, perf_plot, l_loss, loss_plot

