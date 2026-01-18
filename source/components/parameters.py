import gradio as gr
from ..config import TRANSLATIONS

def create_parameters_section(lang):
    t = TRANSLATIONS[lang]
    with gr.Column(scale=1):
        # Assets Card
        with gr.Column(elem_classes=["glass-card"]):
            l_assets = gr.Markdown(f"<div class='section-title'>{t['section_assets']}</div>")
            with gr.Row():
                btn_g = gr.Button("G", elem_classes=["asset-icon-btn"])
                btn_m = gr.Button("M", elem_classes=["asset-icon-btn"])
                btn_t = gr.Button("T", elem_classes=["asset-icon-btn", "active"])
                btn_b = gr.Button("B", elem_classes=["asset-icon-btn"])
                
        # Parameters Card
        with gr.Column(elem_classes=["glass-card"]):
            l_params = gr.Markdown(f"<div class='section-title'>{t['section_params']}</div>")
            gr.Button("Open", elem_classes=["param-item"])
            gr.Button("High", elem_classes=["param-item"])
            gr.Button("Low", elem_classes=["param-item"])
            gr.Button("Close", elem_classes=["param-item", "active"])
            gr.Button("Volume", elem_classes=["param-item"])
            
        # Training Progress Card
        with gr.Column(elem_classes=["glass-card"]):
            l_epoch = gr.Markdown(f"<div class='section-title' style='text-align:center;'>{t['section_epoch']}</div>")
            gr.Markdown("<div style='font-size:32px; color:var(--accent-green); text-align:center; font-weight:700; margin-bottom:10px;'>0.0000</div>")
            btn_train = gr.Button(t["btn_train"], elem_classes=["btn-train"])
            
    return l_assets, l_params, l_epoch, btn_train
