# Traductor Gen-AI con Docker y MLflow

Aplicación de traducción de texto usando modelos generativos (OpenAI/Groq/Google AI), con interfaz Gradio y tracking de experimentos con MLflow.

## 📋 Descripción

Esta aplicación permite traducir texto entre diferentes idiomas utilizando modelos de lenguaje generativos. Cada interacción queda registrada en MLflow para análisis posterior de métricas y parámetros.

## 🏗️ Arquitectura

El proyecto consta de **2 contenedores Docker**:

1. **traductor-app** (Puerto 8080): Aplicación Gradio con el servicio de traducción
2. **mlflow-server** (Puerto 5000): Servidor MLflow para tracking de experimentos

Ambos contenedores se comunican a través de una red Docker personalizada.

## 🚀 Imagen Docker Hub

La imagen está disponible públicamente en:

```
jeni001/traductor-genai:1.0.1
```

**Link:** https://hub.docker.com/r/jeni001/traductor-genai

## 📦 Requisitos

- Docker Desktop instalado y corriendo
- API Key de uno de estos proveedores:
  - OpenAI (https://platform.openai.com/api-keys)
  - Groq (https://console.groq.com/keys) - **Recomendado (Gratis)**
  - Google AI (https://aistudio.google.com/app/apikey)

## 🛠️ Instalación y Ejecución

### Paso 1: Crear red Docker

```bash
docker network create traductor-network
```

### Paso 2: Levantar servidor MLflow

```bash
docker run -d \
  --name mlflow-server \
  --network traductor-network \
  -p 5000:5000 \
  -v mlflow-data:/mlflow \
  ghcr.io/mlflow/mlflow:v2.9.2 \
  mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri sqlite:///mlflow/mlflow.db \
  --default-artifact-root /mlflow/artifacts
```

### Paso 3: Levantar aplicación de traducción

#### Opción A: Con OpenAI

```bash
docker run -d \
  --name traductor-app \
  --network traductor-network \
  -p 8080:7860 \
  -e OPENAI_API_KEY="tu-openai-key-aqui" \
  -e MLFLOW_TRACKING_URI="http://mlflow-server:5000" \
  -e ENABLE_MLFLOW="1" \
  jeni001/traductor-genai:1.0.1
```

#### Opción B: Con Groq (Gratis)

```bash
docker run -d \
  --name traductor-app \
  --network traductor-network \
  -p 8080:7860 \
  -e OPENAI_API_KEY="tu-groq-key-aqui" \
  -e OPENAI_BASE_URL="https://api.groq.com/openai/v1" \
  -e MODEL="llama-3.1-8b-instant" \
  -e MLFLOW_TRACKING_URI="http://mlflow-server:5000" \
  -e ENABLE_MLFLOW="1" \
  jeni001/traductor-genai:1.0.1
```

#### Opción C: Con Google AI (Gratis)

```bash
docker run -d \
  --name traductor-app \
  --network traductor-network \
  -p 8080:7860 \
  -e OPENAI_API_KEY="tu-google-key-aqui" \
  -e OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/" \
  -e MODEL="gemini-2.0-flash-exp" \
  -e MLFLOW_TRACKING_URI="http://mlflow-server:5000" \
  -e ENABLE_MLFLOW="1" \
  jeni001/traductor-genai:1.0.1
```

### Paso 4: Acceder a las interfaces

- **Gradio (Traductor):** http://localhost:8080
- **MLflow (Tracking):** http://localhost:5000

## 🔧 Comandos Útiles

### Ver contenedores corriendo
```bash
docker ps
```

### Ver logs
```bash
docker logs traductor-app
docker logs mlflow-server
```

### Detener contenedores
```bash
docker stop traductor-app mlflow-server
```

### Eliminar contenedores
```bash
docker rm traductor-app mlflow-server
```

### Reiniciar aplicación
```bash
docker restart traductor-app
```

## 🏗️ Construcción desde código fuente

Si quieres modificar el código y construir tu propia imagen:

### 1. Clonar el repositorio
```bash
git clone <tu-repo-url>
cd Project-Docker
```

### 2. Construir la imagen
```bash
docker build -t traductor-genai:latest .
```

### 3. Taggear para Docker Hub
```bash
docker tag traductor-genai:latest tu-usuario/traductor-genai:1.0.0
```

### 4. Publicar en Docker Hub
```bash
docker login
docker push tu-usuario/traductor-genai:1.0.0
```

## 📊 Tracking con MLflow

Cada traducción registra:

### Parámetros
- `model`: Modelo utilizado (ej: gpt-4o-mini, llama-3.1-8b-instant)
- `source_lang`: Idioma de origen
- `target_lang`: Idioma de destino
- `text_length`: Longitud del texto original

### Métricas
- `inference_ms`: Tiempo de inferencia en milisegundos

### Artifacts
- `input_text.txt`: Texto original
- `translated_text.txt`: Texto traducido

## 🔒 Seguridad

**⚠️ IMPORTANTE:** 

- Pasa siempre las API keys como variables de entorno al ejecutar el contenedor
- Las keys se deben agregar al archivo `.gitignore`

## 🌐 Variables de Entorno

| Variable | Descripción | Requerido | Default |
|----------|-------------|-----------|---------|
| `OPENAI_API_KEY` | API key del proveedor | Sí | - |
| `OPENAI_BASE_URL` | URL base del API | No | OpenAI oficial |
| `MODEL` | Modelo a utilizar | No | gpt-4o-mini |
| `MLFLOW_TRACKING_URI` | URL del servidor MLflow | No | http://mlflow-server:5000 |
| `ENABLE_MLFLOW` | Activar tracking (1/0) | No | 0 |

## 📁 Estructura del Proyecto

```
Project-Docker/
├── Dockerfile              # Configuración de la imagen
├── requirements.txt        # Dependencias Python
├── app.py                 # Punto de entrada
├── config/
│   └── providers.py       # Configuración de proveedores
├── prompts/
│   └── tasks.py          # Prompts de traducción
├── services/
│   └── ai_service.py     # Servicio de IA con MLflow
└── ui/
    └── interface.py      # Interfaz Gradio
```

## 🐛 Troubleshooting

### El puerto 7860 no funciona
**Solución:** Usa el puerto 8080 como se indica en los comandos (`-p 8080:7860`)

### Error de API key inválida
**Solución:** Verifica que la API key esté correcta y tenga créditos disponibles

### MLflow no muestra runs
**Solución:** Verifica que `ENABLE_MLFLOW=1` y que ambos contenedores estén en la misma red

### Error "insufficient_quota"
**Solución:** Tu API key no tiene créditos. Usa Groq (gratis) o agrega créditos a OpenAI

## 📝 Licencia

Este proyecto fue desarrollado como parte de un taller académico sobre Docker y MLflow.

## 👤 Autor

- GitHub: jeni001
- Docker Hub: https://hub.docker.com/r/jeni001/traductor-genai
