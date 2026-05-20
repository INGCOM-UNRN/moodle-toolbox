import click
from questions.core.config import save_api_key, get_api_key, delete_api_key

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

@config.command(name="show-key")
def show_key_cmd():
    """Muestra la API Key actual (parcialmente oculta)."""
    key = get_api_key()
    if key:
        hidden_key = key[:4] + "*" * (len(key) - 8) + key[-4:]
        click.echo(f"API Key configurada: {hidden_key}")
    else:
        click.echo("No hay API Key configurada.")

@config.command(name="unset-key")
def unset_key_cmd():
    """Elimina la configuración de la API Key."""
    delete_api_key()
    click.echo("✅ Configuración eliminada.")
