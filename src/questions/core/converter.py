import re
import html
import xml.etree.ElementTree as ET
from pathlib import Path

def convert_html_tags_to_markdown(text):
    """Convierte tags HTML (y sus versiones fullwidth) a markdown."""
    # Versiones fullwidth (comunes en algunos de estos archivos)
    text = re.sub(r'＜p＞(.*?)＜/p＞', r'\1\n', text, flags=re.DOTALL)
    text = re.sub(r'＜code＞(.*?)＜/code＞', r'`\1`', text, flags=re.DOTALL)
    text = re.sub(r'＜strong＞(.*?)＜/strong＞', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'＜pre＞(.*?)＜/pre＞', r'```\n\1\n```', text, flags=re.DOTALL)
    
    # Versiones normales
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)
    text = re.sub(r'<p>(.*?)</p>', r'\1\n', text, flags=re.DOTALL)
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<pre>(.*?)</pre>', r'```\n\1\n```', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', r'\n', text)
    
    return text.strip()

def xml_to_gift(xml_content: str) -> str:
    """Convierte un archivo Moodle XML a GIFT (simplificado)."""
    # Esta es una implementación compleja, por ahora usaré una versión simplificada
    # o integraré la del script original si es necesario.
    # Por brevedad, aquí iría el grueso de convert_xml_gift.py
    return "Not implemented yet in this refactor"

def gift_to_xml(gift_content: str) -> str:
    """Convierte GIFT a Moodle XML (simplificado)."""
    return "Not implemented yet in this refactor"
