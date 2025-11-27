# Documento de Arquitectura - Traductor Gen-AI

**Proyecto:** Aplicación de Traducción con Docker y MLflow  
**Autor:** jeni001  
**Fecha:** Noviembre 2024  
**Docker Hub:** `jeni001/traductor-genai:1.0.1`

---

## 1. Arquitectura del Sistema

El sistema está compuesto por **2 contenedores Docker** que se comunican a través de una red personalizada:

```
┌─────────────────────────────────────────────────────┐
│                    Host Machine                      │
│                                                       │
│  ┌─────────────────────────────────────────────┐   │
│  │       Docker Network: traductor-network      │   │
│  │                                               │   │
│  │  ┌──────────────────┐  ┌──────────────────┐ │   │
│  │  │  traductor-app   │  │  mlflow-server   │ │   │
│  │  │  (Gradio + AI)   │  │   (Tracking)     │ │   │
│  │  │                  │  │                  │ │   │
│  │  │  Puerto: 7860    │  │  Puerto: 5000    │ │   │
│  │  │  Expuesto: 8080  │  │  Expuesto: 5000  │ │   │
│  │  └──────────────────┘  └──────────────────┘ │   │
│  │          │                      │            │   │
│  │          └──────────HTTP────────┘            │   │
│  └─────────────────────────────────────────────┘   │
│           │                      │                  │
│      localhost:8080        localhost:5000           │
└─────────────────────────────────────────────────────┘
```

### 1.1 Contenedor: traductor-app
- **Imagen:** `jeni001/traductor-genai:1.0.1`
- **Puerto interno:** 7860
- **Puerto expuesto:** 8080
- **Función:** Interfaz Gradio + servicio de traducción con IA
- **Dependencias:** OpenAI SDK, Gradio, MLflow client

### 1.2 Contenedor: mlflow-server
- **Imagen:** `ghcr.io/mlflow/mlflow:v2.9.2`
- **Puerto interno:** 5000
- **Puerto expuesto:** 5000
- **Función:** Servidor de tracking de experimentos
- **Persistencia:** Volumen Docker (`mlflow-data`)

---

## 2. Flujo de Datos

```
┌─────────┐        ┌──────────────┐        ┌─────────┐        ┌──────────┐
│ Usuario │───────▶│    Gradio    │───────▶│   AI    │───────▶│  MLflow  │
│ (Web)   │◀───────│  (Puerto     │◀───────│ Service │◀───────│  Server  │
└─────────┘        │   8080)      │        └─────────┘        └──────────┘
                   └──────────────┘             │
                                                 │
                                                 ▼
                                          ┌────────────┐
                                          │  OpenAI/   │
                                          │  Groq API  │
                                          └────────────┘
```

1. Usuario ingresa texto en Gradio (http://localhost:8080)
2. Gradio envía solicitud al servicio de AI
3. AI Service llama al modelo generativo (OpenAI/Groq)
4. AI Service registra parámetros y métricas en MLflow
5. Respuesta se muestra al usuario en Gradio

---

## 3. Gestión de API Keys

**Método utilizado:** Variables de entorno

La API key se pasa al contenedor mediante el flag `-e` al momento de ejecutar:

```bash
docker run -e OPENAI_API_KEY="sk-..." jeni001/traductor-genai:1.0.1
```

**Ventajas de este enfoque:**
- ✅ No se incluye en la imagen Docker
- ✅ No se sube al repositorio Git
- ✅ Fácil de cambiar sin reconstruir imagen
- ✅ Compatible con Docker Secrets en producción

**Alternativas evaluadas:**
- Docker Secrets (solo para Swarm/Kubernetes)
- Archivos `.env` (menos seguro, puede subirse por error)
- Hardcoded en código (❌ NUNCA hacer esto)

---

## 4. Comandos Principales Utilizados

### 4.1 Construcción de Imagen
```bash
# Construir imagen local
docker build -t traductor-genai:latest .

# Taggear para Docker Hub
docker tag traductor-genai:latest jeni001/traductor-genai:1.0.1

# Publicar en Docker Hub
docker login
docker push jeni001/traductor-genai:1.0.1
```

### 4.2 Ejecución de Contenedores
```bash
# Crear red
docker network create traductor-network

# Levantar MLflow
docker run -d \
  --name mlflow-server \
  --network traductor-network \
  -p 5000:5000 \
  -v mlflow-data:/mlflow \
  ghcr.io/mlflow/mlflow:v2.9.2 \
  mlflow server --host 0.0.0.0 --port 5000 \
  --backend-store-uri sqlite:///mlflow/mlflow.db \
  --default-artifact-root /mlflow/artifacts

# Levantar aplicación (con Groq)
docker run -d \
  --name traductor-app \
  --network traductor-network \
  -p 8080:7860 \
  -e OPENAI_API_KEY="gsk-..." \
  -e OPENAI_BASE_URL="https://api.groq.com/openai/v1" \
  -e MODEL="llama-3.1-8b-instant" \
  -e MLFLOW_TRACKING_URI="http://mlflow-server:5000" \
  -e ENABLE_MLFLOW="1" \
  jeni001/traductor-genai:1.0.1
```

### 4.3 Descarga y Ejecución Remota
```bash
# En otra máquina
docker pull jeni001/traductor-genai:1.0.1

# Crear red y MLflow (igual que arriba)
docker network create traductor-network
docker run -d --name mlflow-server ...

# Ejecutar app con API key local
docker run -d --name traductor-app \
  -p 8080:7860 \
  -e OPENAI_API_KEY="$MI_API_KEY" \
  jeni001/traductor-genai:1.0.1
```

---

## 5. Observaciones sobre Latencia y Calidad

### 5.1 Latencia de Traducción

| Proveedor | Modelo | Latencia Promedio | Observaciones |
|-----------|--------|-------------------|---------------|
| OpenAI | gpt-4o-mini | 800-1500ms | Mejor calidad, requiere créditos |
| Groq | llama-3.1-8b-instant | 300-600ms | Muy rápido, gratis, buena calidad |
| Google AI | gemini-2.0-flash | 500-1000ms | Intermedio, límites por día |

**Factores que afectan la latencia:**
- Longitud del texto (más texto = más tiempo)
- Carga del servidor del proveedor
- Latencia de red
- Tiempo de inferencia del modelo

### 5.2 Calidad de Traducción

**Observaciones generales:**
- **OpenAI GPT-4o-mini:** Mejor manejo de contexto y modismos
- **Groq Llama 3.1:** Muy buena calidad general, ocasionalmente literal
- **Google Gemini:** Buena para idiomas populares, menor en idiomas raros

**Recomendación:** Para producción con presupuesto, usar OpenAI. Para desarrollo/pruebas, usar Groq (gratis y rápido).

---

## 6. Tracking con MLflow

Cada traducción genera un **run** en MLflow con:

### Parámetros registrados:
- `model`: Modelo utilizado
- `source_lang`: Idioma origen
- `target_lang`: Idioma destino  
- `text_length`: Número de caracteres

### Métricas registradas:
- `inference_ms`: Tiempo de respuesta en milisegundos

### Artifacts guardados:
- `input_text.txt`: Texto original
- `translated_text.txt`: Traducción generada

**Utilidad del tracking:**
- Comparar rendimiento entre modelos
- Detectar degradación de latencia
- Auditoría de uso
- Análisis de costos por modelo

---

## 7. Mejoras Futuras

1. **Caché de traducciones:** Redis para evitar llamadas repetidas
2. **Rate limiting:** Proteger contra uso excesivo
3. **Múltiples idiomas simultáneos:** Traducir a varios destinos en paralelo
4. **UI mejorada:** Historial de traducciones, copiar al portapapeles
5. **Despliegue en Kubernetes:** Para alta disponibilidad
6. **CI/CD:** GitHub Actions para build y push automático

---

## 8. Conclusiones

✅ **Logros del proyecto:**
- Aplicación funcional containerizada
- Tracking completo de experimentos con MLflow
- Imagen publicada en Docker Hub
- Ejecución reproducible en cualquier máquina
- Gestión segura de credenciales

⚠️ **Desafíos encontrados:**
- Mapeo de puertos en Docker Desktop (resuelto usando 8080:7860)
- Límites de cuota en APIs gratuitas (resuelto con múltiples proveedores)
- Configuración de red entre contenedores

📚 **Aprendizajes:**
- Docker networking es esencial para comunicación entre contenedores
- Variables de entorno son el método estándar para secretos
- MLflow facilita enormemente el tracking de modelos de IA
- Tener múltiples proveedores de IA aumenta resiliencia
