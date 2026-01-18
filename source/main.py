import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
from source.config import TRANSLATIONS
from source.charts import create_styled_perf_chart, create_styled_loss_chart
from source.components.sidebar import create_sidebar
from source.components.topbar import create_topbar
from source.components.parameters import create_parameters_section
from source.components.charts_layout import create_charts_section

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
with open(css_path, "r") as f:
    custom_css = f.read()

def switch_language(lang):
    new_lang = "en" if lang == "es" else "es"
    t = TRANSLATIONS[new_lang]
    
    # Return updates for all components that depend on language
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
        gr.update(value=f"<div style='font-size:22px; font-weight:700;'>{t['chart_performance']}</div><div style='font-size:13px; color:var(--text-secondary);'>{t['asset_google']}</div>"),
        gr.update(value=f"<div class='section-title'>{t['chart_loss']}</div>"),
        create_styled_perf_chart(new_lang),
        create_styled_loss_chart(new_lang)
    ]

with gr.Blocks(css=custom_css, title="LSTM Playground - Source") as demo:
    lang_state = gr.State("es")
    
    with gr.Column(elem_classes=["main-wrapper"]):
        # TOPBAR
        header = create_topbar("es")

        # Main Layout (Sidebar + Content)
        with gr.Row(elem_classes=["content-body"]):
            # SIDEBAR
            nav_1, nav_2, nav_3, nav_4, nav_5, lang_toggle = create_sidebar("es")

            # MAIN CONTENT
            with gr.Column(scale=5, elem_classes=["main-content"]):
                with gr.Row():
                    # Left Params
                    l_assets, l_params, l_epoch, btn_train = create_parameters_section("es")

                    # Right Charts
                    title_perf, perf_plot, l_loss, loss_plot = create_charts_section("es")

    # Multi-language action
    lang_toggle.click(
        switch_language, 
        inputs=[lang_state],
        outputs=[
            lang_state, header, 
            nav_1, nav_2, nav_3, nav_4, nav_5, lang_toggle, 
            l_assets, l_params, l_epoch, btn_train, 
            title_perf, l_loss, perf_plot, loss_plot
        ]
    )

if __name__ == "__main__":
    demo.launch()

