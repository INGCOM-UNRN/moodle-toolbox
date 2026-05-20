import click
from questions.core.config import save_api_key, get_api_key, delete_api_key, save_model, get_model
from questions.core.ai import load_config, list_available_models

@click.group()
def config():
    """Configuración global de las herramientas."""
    pass

@config.command(name="set-key")
@click.argument('api_key')
def set_key_cmd(api_key):
    """Configura la GEMINI_API_KEY globalmente."""
    try:
        save_api_key(api_key)
        click.echo("✅ API Key guardada correctamente en ~/.questions/.env")
    except Exception as e:
        click.echo(f"❌ Error al guardar la API Key: {e}", err=True)

@config.command(name="set-model")
@click.argument('model')
def set_model_cmd(model):
    """Configura el modelo de Gemini por defecto."""
    try:
        save_model(model)
        click.echo(f"✅ Modelo por defecto configurado: {model}")
    except Exception as e:
        click.echo(f"❌ Error al guardar el modelo: {e}", err=True)

@config.command(name="list-models")
def list_models_cmd():
    """Lista los modelos disponibles en la API de Gemini."""
    try:
        client = load_config()
        models = list_available_models(client)
        if models:
            click.echo("Modelos disponibles (con soporte generateContent):")
            for m in models:
                click.echo(f" - {m}")
        else:
            click.echo("No se encontraron modelos disponibles.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

@config.command(name="show-key")
def show_key_cmd():
    """Muestra la API Key actual (parcialmente oculta)."""
    key = get_api_key()
    if key:
        hidden_key = key[:4] + "*" * (len(key) - 8) + key[-4:]
        click.echo(f"API Key configurada: {hidden_key}")
        click.echo(f"Modelo por defecto: {get_model()}")
    else:
        click.echo("No hay API Key configurada.")

@config.command(name="unset-key")
def unset_key_cmd():
    """Elimina la configuración de la API Key."""
    delete_api_key()
    click.echo("✅ Configuración eliminada.")
