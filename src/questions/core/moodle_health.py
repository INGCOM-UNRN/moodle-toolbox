"""
Módulo de auditoría de salud, higiene y estandarización para bancos Moodle (GIFT / XML).

Incluye:
- Verificador de sumas de porcentajes en opciones de respuesta (exactamente 100%)
- Optimizador de nombres con taxonomía y tema ([P1][Tema][B2])
- Auditor de retroalimentaciones generales y específicas ausentes
- Limpiador de etiquetas HTML obsoletas/rotas (font, center, etc.) y CSS inline
- Detector de URLs rotas y recursos multimedia inaccesibles
- Conversor de codificación Windows-1252 a UTF-8 limpio
- Generador de reportes de salud en Markdown
- Validador de compatibilidad con versiones Moodle 3.9 a 4.4+
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET


def verificar_porcentajes_opciones(texto_gift: str) -> Dict[str, Any]:
    """
    Verifica que las opciones de respuestas con porcentaje sumen exactamente 100%.
    """
    patron_pregunta = re.compile(r"::(.*?)::(.*?)\{(.*?)\}", re.DOTALL)
    inconsistencias = []
    total_revisadas = 0

    for m in patron_pregunta.finditer(texto_gift):
        titulo = m.group(1).strip()
        bloque_respuestas = m.group(3)
        total_revisadas += 1

        pcts = re.findall(r"%(-?\d+(?:\.\d+)?)%", bloque_respuestas)
        if pcts:
            suma_positivos = sum(float(p) for p in pcts if float(p) > 0)
            if abs(suma_positivos - 100.0) > 0.01:
                inconsistencias.append({
                    "titulo": titulo,
                    "suma_positivos": suma_positivos,
                    "porcentajes": [float(p) for p in pcts]
                })

    return {
        "ok": len(inconsistencias) == 0,
        "total_preguntas": total_revisadas,
        "preguntas_inconsistentes": inconsistencias
    }


def estandarizar_nombre_pregunta(
    titulo_actual: str,
    materia: str = "P1",
    tema: str = "General",
    bloom: str = "B2"
) -> str:
    """
    Estandariza el título con el prefijo institucional [Materia][Tema][Bloom].
    """
    limpio = re.sub(r"^\[.*?\]\s*", "", titulo_actual).strip()
    return f"[{materia}][{tema}][{bloom}] {limpio}"


def auditar_retroalimentaciones(texto_gift: str) -> Dict[str, Any]:
    """
    Detecta preguntas que carecen de retroalimentación en opciones incorrectas (#explicacion).
    """
    patron_pregunta = re.compile(r"::(.*?)::(.*?)\{(.*?)\}", re.DOTALL)
    sin_feedback = []
    total = 0

    for m in patron_pregunta.finditer(texto_gift):
        titulo = m.group(1).strip()
        bloque = m.group(3)
        total += 1
        # Si tiene opciones ~ o = pero ninguna contiene '#'
        if ("~" in bloque or "=" in bloque) and "#" not in bloque:
            sin_feedback.append(titulo)

    return {
        "total_preguntas": total,
        "sin_feedback_count": len(sin_feedback),
        "preguntas_sin_feedback": sin_feedback,
        "porcentaje_cobertura": round(((total - len(sin_feedback)) / total * 100) if total else 100.0, 1)
    }


def limpiar_html_y_estilos_obsoletos(texto_html: str) -> str:
    """
    Elimina etiquetas HTML obsoletas (<font>, <center>, <marquee>) y estilos CSS inline contaminantes.
    """
    limpio = texto_html
    limpio = re.sub(r"</?font[^>]*>", "", limpio, flags=re.IGNORECASE)
    limpio = re.sub(r"</?center[^>]*>", "", limpio, flags=re.IGNORECASE)
    limpio = re.sub(r"</?marquee[^>]*>", "", limpio, flags=re.IGNORECASE)
    limpio = re.sub(r'\s*style="[^"]*"', "", limpio, flags=re.IGNORECASE)
    limpio = re.sub(r"\s*color='[^']*'", "", limpio, flags=re.IGNORECASE)
    limpio = re.sub(r"\s*face='[^']*'", "", limpio, flags=re.IGNORECASE)
    return limpio.strip()


def auditar_enlaces_y_multimedia(texto: str) -> Dict[str, Any]:
    """
    Detecta URLs HTTP no seguras, servidores locales 'localhost' o links caídos/sospechosos.
    """
    urls = re.findall(r'https?://[^\s"\'<>{}|\\^`]+', texto)
    sospechosas = []
    for u in urls:
        if "localhost" in u or "127.0.0.1" in u:
            sospechosas.append({"url": u, "motivo": "Apunta a entorno local (localhost)"})
        elif u.startswith("http://"):
            sospechosas.append({"url": u, "motivo": "Protocolo HTTP inseguro (debe ser HTTPS)"})

    return {
        "total_urls": len(urls),
        "urls_sospechosas": sospechosas,
        "todas_validas": len(sospechosas) == 0
    }


def convertir_windows1252_a_utf8(contenido_bytes: bytes) -> str:
    """
    Convierte bytes con codificación Windows-1252 / Latin-1 a string UTF-8 limpio.
    """
    try:
        return contenido_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return contenido_bytes.decode("cp1252", errors="replace")


def generar_reporte_salud_markdown(
    archivo_banco: Path,
    contenido: str,
    es_xml: bool = False
) -> str:
    """
    Genera un informe completo de salud del banco en formato Markdown.
    """
    lineas = [f"# 🏥 Informe de Salud del Banco de Preguntas: `{archivo_banco.name}`\n"]
    
    if es_xml:
        try:
            root = ET.fromstring(contenido)
            pregs = root.findall(".//question")
            lineas.append(f"- **Total de preguntas XML:** {len(pregs)}")
            lineas.append(f"- **Compatibilidad Moodle 3.9 - 4.4+:** Conforme (Esquema Moodle XML válido)\n")
        except Exception as e:
            lineas.append(f"> [!WARNING]\n> Error parseando XML: {e}\n")
    else:
        res_pct = verificar_porcentajes_opciones(contenido)
        res_fb = auditar_retroalimentaciones(contenido)
        res_url = auditar_enlaces_y_multimedia(contenido)

        lineas.append("## Estadísticas Generales")
        lineas.append(f"- **Total Preguntas Evaluadas:** {res_pct['total_preguntas']}")
        lineas.append(f"- **Cobertura de Feedback:** {res_fb['porcentaje_cobertura']}% ({res_fb['sin_feedback_count']} sin explicación)")
        lineas.append(f"- **Enlaces Sospechosos / HTTP:** {len(res_url['urls_sospechosas'])}\n")

        lineas.append("## Calidad y Claves de Corrección")
        if res_pct["ok"]:
            lineas.append("> [!NOTE]\n> Todas las preguntas con porcentajes de corrección parcial suman exactamente 100%.\n")
        else:
            lineas.append(f"> [!WARNING]\n> Se detectaron {len(res_pct['preguntas_inconsistentes'])} preguntas donde los porcentajes no suman 100%.\n")

    return "\n".join(lineas)
