import os
from dotenv import load_dotenv

load_dotenv(override=True)

PROVIDERS = {
    "OpenRouter AI": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "models": ["deepseek/deepseek-chat-v3.1:free"]
    },
    "Groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": os.getenv("GROQ_API_KEY"),
        "models": ["llama-3.1-8b-instant"]
    },
    "Google AI": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": os.getenv("GOOGLE_API_KEY"),
        "models": ["gemini-2.0-flash-exp"]
    }
}


def get_provider_config(provider_name):
    return PROVIDERS.get(provider_name, {})


def get_available_models(provider_name):
    provider = PROVIDERS.get(provider_name, {})
    return provider.get("models", [])


def get_all_providers():
    return list(PROVIDERS.keys())