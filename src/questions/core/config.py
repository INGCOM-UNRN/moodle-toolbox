import os
from pathlib import Path
from dotenv import load_dotenv, set_key

CONFIG_DIR = Path.home() / ".questions"
ENV_FILE = CONFIG_DIR / ".env"

def get_api_key() -> str:
    """Obtiene la API Key desde el entorno o el archivo de configuración global."""
    # 1. Intentar desde el entorno (incluye .env local si existe)
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    # 2. Intentar desde el archivo de configuración global
    if not api_key and ENV_FILE.exists():
        load_dotenv(ENV_FILE)
        api_key = os.getenv("GEMINI_API_KEY")
        
    return api_key

def save_api_key(api_key: str):
    """Guarda la API Key en el archivo de configuración global."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not ENV_FILE.exists():
        ENV_FILE.touch(mode=0o600)
    
    # Usar python-dotenv para guardar de forma persistente
    set_key(str(ENV_FILE), "GEMINI_API_KEY", api_key)

def delete_api_key():
    """Elimina la API Key configurada."""
    if ENV_FILE.exists():
        ENV_FILE.unlink()
