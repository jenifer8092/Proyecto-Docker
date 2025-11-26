import gradio as gr
from services.ai_service import ai_service


# Idiomas disponibles (simple lista para la UI de traducción)
AVAILABLE_LANGUAGES = [
    "auto",
    "español",
    "inglés",
    "francés",
    "alemán",
    "italiano",
    "portugués",
    "chino",
]


def translate_fn(text, source_lang, target_lang):
    # Llamamos al servicio minimalista que también registra en MLflow.
    # Capturamos excepciones para que la UI muestre un mensaje legible
    # en lugar de la pantalla de error de Gradio.
    try:
        return ai_service.translate(text=text, source_lang=source_lang, target_lang=target_lang)
    except RuntimeError as re:
        # Errores esperados (p. ej. falta de API key)
        msg = f"Error: {str(re)}\n\nAsegúrate de exportar OPENAI_API_KEY o crear el secret en Swarm."
        print(msg)
        return msg
    except Exception as e:
        # Errores inesperados: loguear y devolver mensaje genérico
        print("Error en translate_fn:", repr(e))
        return f"Error al procesar la traducción: {str(e)}"


def create_interface():
    with gr.Blocks(title="Traductor - Desarrollo local") as app:
        gr.Markdown("# Traductor simple (local)")

        with gr.Row():
            input_text = gr.Textbox(lines=6, label="Texto a traducir")

        with gr.Row():
            source = gr.Dropdown(choices=AVAILABLE_LANGUAGES, value="auto", label="Idioma origen")
            target = gr.Dropdown(choices=AVAILABLE_LANGUAGES[1:], value="español", label="Idioma destino")

        translate_btn = gr.Button("Traducir")
        output = gr.Textbox(lines=6, label="Traducción")

        translate_btn.click(fn=translate_fn, inputs=[input_text, source, target], outputs=output)

    return app
