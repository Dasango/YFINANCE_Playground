import gradio as gr
from ..config import TRANSLATIONS

def create_topbar(lang):
    t = TRANSLATIONS[lang]
    with gr.Row(elem_classes=["topbar"]):
        header = gr.Markdown(t["header"])
        # Adding a placeholder for the github corner if needed, or keep it in CSS
        gr.HTML("""
        <div class="github-corner">
            <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" alt="GitHub">
        </div>
        """)
    return header
