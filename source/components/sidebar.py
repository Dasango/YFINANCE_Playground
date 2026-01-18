import gradio as gr
from ..config import TRANSLATIONS

def create_sidebar(lang):
    t = TRANSLATIONS[lang]
    with gr.Column(scale=1, elem_classes=["sidebar-container"]):
        gr.Markdown("<div class='logo-text'>LSTM playground</div><div class='sub-logo-text'>UCE CS</div>")
        
        nav_1 = gr.Button(t["sidebar_predictor"], elem_classes=["nav-btn", "active"])
        nav_2 = gr.Button(t["sidebar_network"], elem_classes=["nav-btn"])
        nav_3 = gr.Button(t["sidebar_lstm"], elem_classes=["nav-btn"])
        nav_4 = gr.Button(t["sidebar_collab"], elem_classes=["nav-btn"])
        nav_5 = gr.Button(t["sidebar_credits"], elem_classes=["nav-btn"])
        
        gr.HTML("<div style='flex-grow: 1;'></div>")
        lang_toggle = gr.Button(t["lang_btn"], elem_classes=["lang-btn"])
        
    return nav_1, nav_2, nav_3, nav_4, nav_5, lang_toggle
