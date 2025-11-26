"""Servicio mínimo centrado en traducción usando OpenAI.

Esta versión NO utiliza MLflow. Requiere que la variable de entorno
OPENAI_API_KEY o API_KEY esté definida para usar el cliente de OpenAI.
"""

import os
import time
from openai import OpenAI

# MLflow is optional: import safely so the service still works when mlflow
# is not installed or not configured.
try:
    import mlflow
except Exception:
    mlflow = None


class AIService:
    def __init__(self):
        # First try to load Docker Secret if present (Swarm mounts secrets to /run/secrets/<name>)
        for secret_name in ("OPENAI_API_KEY", "openai_api_key", "api_key"):
            secret_path = f"/run/secrets/{secret_name}"
            if os.path.exists(secret_path):
                try:
                    with open(secret_path, "r") as sf:
                        secret_val = sf.read().strip()
                    if secret_val:
                        os.environ["OPENAI_API_KEY"] = secret_val
                        os.environ["API_KEY"] = secret_val
                        break
                except Exception:
                    # ignore errors reading secret file
                    pass

        # Leer API key desde la variable de entorno OPENAI_API_KEY o API_KEY
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("API_KEY")
        if not api_key:
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception:
                # Si la creación del cliente falla, mantenemos self.client = None
                self.client = None

        # --- Logging/diagnóstico mínimo (no exponemos la API key) ---
        try:
            has_key = bool(api_key)
            print(f"[ai_service] OpenAI API key present: {has_key}")
        except Exception:
            pass

        # Configuración opcional de MLflow: si el entorno define
        # MLFLOW_TRACKING_URI o ENABLE_MLFLOW=1 intentaremos usar mlflow.
        self.mlflow_enabled = False
        self.mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI")
        if not self.mlflow_uri and os.environ.get("ENABLE_MLFLOW") == "1":
            # valor por defecto si ENABLE_MLFLOW=1 pero no se indicó URI
            self.mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow-server:5000")

        if self.mlflow_uri and mlflow is not None:
            try:
                mlflow.set_tracking_uri(self.mlflow_uri)
                self.mlflow_enabled = True
            except Exception:
                # no bloquear la app si mlflow no es accesible
                self.mlflow_enabled = False
        # Informar estado de MLflow para facilitar debug
        try:
            print(f"[ai_service] mlflow_enabled={self.mlflow_enabled} mlflow_uri={self.mlflow_uri}")
        except Exception:
            pass

    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "español", model: str = None, timeout_sec: float = 30.0) -> str:
        """Traduce `text` desde `source_lang` a `target_lang` usando el SDK de OpenAI.

        No se realiza tracking en MLflow en esta versión.
        """
        if not text or not str(text).strip():
            return "Por favor, ingresa un texto para traducir."

        model = model or os.environ.get("MODEL", "gpt-4o-mini")

        system_prompt = "Eres un asistente de traducción. Devuelve únicamente el texto traducido, sin comentarios."
        user_prompt = f"Traduce el siguiente texto del idioma {source_lang} al {target_lang}:\n\n{text}"

        start = time.time()
        # Realizamos la llamada al modelo y, si está activado, registramos un run en MLflow.
        try:
            if not self.client:
                raise RuntimeError("No se encontró API key para OpenAI. Exporta OPENAI_API_KEY o API_KEY.")

            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.0,
            )
            translated = response.choices[0].message.content
        finally:
            elapsed_ms = int((time.time() - start) * 1000)

        # Si MLflow está habilitado intentamos registrar el run de manera no bloqueante.
        if self.mlflow_enabled:
            try:
                # Usamos un run y guardamos parámetros y duración.
                with mlflow.start_run():
                    mlflow.set_tag("component", "ai_service.translate")
                    mlflow.log_param("model", model)
                    mlflow.log_param("source_lang", source_lang)
                    mlflow.log_param("target_lang", target_lang)
                    mlflow.log_param("text_length", len(text))
                    mlflow.log_metric("inference_ms", elapsed_ms)
                    # Guardar una versión corta del texto (si no es muy grande).
                    try:
                        snippet = text if len(text) <= 4000 else text[:4000]
                        mlflow.log_text(snippet, "input_text.txt")
                        mlflow.log_text(translated or "", "translated_text.txt")
                    except Exception:
                        # no bloquear por problemas de artefactos
                        pass
            except Exception:
                # Ignorar problemas con MLflow para no romper la respuesta al usuario
                pass

        return (translated or "(respuesta vacía)") + f"\n\n⏱️ Tiempo de inferencia: {elapsed_ms} ms"



ai_service = AIService()
