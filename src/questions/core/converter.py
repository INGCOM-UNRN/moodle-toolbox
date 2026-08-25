import re
import html
import xml.etree.ElementTree as ET
from pathlib import Path

from questions.core.parser import GiftParser, Question, FormattedText


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


# ============================================================================
# Conversores GIFT <-> Moodle XML sobre el modelo unificado de preguntas
# ============================================================================

_CD_OPEN = "\ue000"
_CD_CLOSE = "\ue001"


def _escape_gift(text: str, context: str = "stem") -> str:
    """Escapa caracteres especiales de GIFT según el contexto."""
    if not text:
        return ""
    out = text.replace('\\', '\\\\')
    specials = {
        "title": [':', '~', '=', '#', '{', '}'],
        "stem": ['~', '=', '#', '{', '}'],
        "answer": ['=', '#', '{', '}', '~'],
    }.get(context, ['~', '=', '#', '{', '}'])
    for ch in specials:
        out = out.replace(ch, '\\' + ch)
    return out


def _strip_html(text: str) -> str:
    """Convierte HTML simple de Moodle a texto plano legible."""
    if not text:
        return ""
    return convert_html_tags_to_markdown(text)


def _cdata(s: str) -> str:
    s = s.replace("]]>", "]]]]><![CDATA[>")
    return f"{_CD_OPEN}{s}{_CD_CLOSE}"


def _cdata_sub(parent, tag, text=None):
    """Agrega un subelemento cuyo texto se envolverá en CDATA al serializar."""
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = _cdata(text)
    return el


def _plain_sub(parent, tag, value=None, attrs=None):
    """Agrega un subelemento estructural con texto plano (sin CDATA)."""
    el = ET.SubElement(parent, tag, attrs or {})
    if value is not None:
        el.text = str(value)
    return el


def _formato_moodle(ft) -> str:
    fmt = (getattr(ft, "format", None) or "moodle").lower()
    return {"markdown": "markdown", "html": "html"}.get(fmt, "moodle_auto_format")


def _ft_text(ft) -> str:
    if ft is None:
        return ""
    return ft.text or ""


def _agregar_feedback(answer_el, feedback) -> None:
    if feedback is not None:
        fb = _plain_sub(answer_el, "feedback")
        fb.set("format", "html")
        _cdata_sub(fb, "text", _ft_text(feedback))


def _pregunta_a_xml(q: Question, defaultgrade: float = 1.0) -> ET.Element:
    """Serializa una Question del modelo unificado a un elemento <question> de Moodle."""
    if q.type == "Category":
        el = ET.Element("question", {"type": "category"})
        cat = _cdata_sub(el, "category")
        ruta = q.title or "$course$"
        if not ruta.startswith("$course$"):
            ruta = f"$course$/{ruta}"
        _cdata_sub(cat, "text", ruta)
        return el

    tipo_moodle = {
        "MC": "multichoice",
        "Short": "shortanswer",
        "TF": "truefalse",
        "Matching": "matching",
        "Numerical": "numerical",
        "Essay": "essay",
        "Description": "description",
    }
    qtype = tipo_moodle.get(q.type, q.type.lower())
    es_cloze = q.has_embedded_answers and "{" in _ft_text(q.stem)
    if q.type == "Description" and es_cloze:
        qtype = "cloze"

    el = ET.Element("question", {"type": qtype})
    _cdata_sub(_cdata_sub(el, "name"), "text", q.title or "Pregunta")

    qt = _cdata_sub(el, "questiontext")
    qt.set("format", _formato_moodle(q.stem))
    _cdata_sub(qt, "text", _ft_text(q.stem))

    if q.global_feedback is not None:
        gf = _cdata_sub(el, "generalfeedback")
        gf.set("format", "html")
        _cdata_sub(gf, "text", _ft_text(q.global_feedback))

    def respuesta(texto, fraccion, formato="moodle_auto_format"):
        ans = _plain_sub(el, "answer", attrs={"fraction": f"{fraccion:g}", "format": formato})
        _cdata_sub(ans, "text", texto)
        return ans

    if q.type == "MC":
        multiple = sum(1 for c in q.choices if c.is_correct) > 1
        _plain_sub(el, "single", "false" if multiple else "true")
        _plain_sub(el, "shuffleanswers", "true")
        for c in q.choices:
            frac = 100.0 if c.is_correct else 0.0
            if c.weight is not None:
                frac = float(c.weight)
            ans = respuesta(_ft_text(c.text), frac, _formato_moodle(c.text))
            _agregar_feedback(ans, c.feedback)
        _plain_sub(el, "defaultgrade", f"{defaultgrade:g}")
        _plain_sub(el, "penalty", "0.3333333")

    elif q.type == "Short":
        _plain_sub(el, "usecase", "0")
        for c in q.choices:
            ans = respuesta(_ft_text(c.text), 100.0 if c.is_correct else 0.0)
            _agregar_feedback(ans, c.feedback)
        _plain_sub(el, "defaultgrade", f"{defaultgrade:g}")
        _plain_sub(el, "penalty", "0.3333333")

    elif q.type == "TF":
        _plain_sub(el, "shuffleanswers", "false")
        for valor, es_verdadera in (("true", True), ("false", False)):
            acierto = (q.is_true == es_verdadera)
            ans = respuesta(valor, 100.0 if acierto else 0.0)
            fb = q.true_feedback if es_verdadera else q.false_feedback
            _agregar_feedback(ans, fb)
        _plain_sub(el, "defaultgrade", f"{defaultgrade:g}")
        _plain_sub(el, "penalty", "1")

    elif q.type == "Matching":
        _plain_sub(el, "shuffleanswers", "true")
        for par in q.match_pairs:
            sq = _cdata_sub(el, "subquestion")
            sq.set("format", _formato_moodle(par.subquestion))
            _cdata_sub(sq, "text", _ft_text(par.subquestion))
            ans = _cdata_sub(sq, "answer")
            _cdata_sub(ans, "text", par.subanswer or "")
        _plain_sub(el, "defaultgrade", f"{max(defaultgrade, len(q.match_pairs)):g}")
        _plain_sub(el, "penalty", "0.3333333")

    elif q.type == "Numerical":
        for c in q.choices:
            raw = (_ft_text(c.text) or "").strip()
            if raw.endswith("%") and ":" not in raw:
                continue  # residuo de peso porcentual, no un valor numérico
            m = re.match(r'^([+-]?\d+(?:\.\d+)?)\s*:\s*([+-]?\d+(?:\.\d+)?)$', raw)
            numero, tolerancia = (m.group(1), m.group(2)) if m else (raw or "0", "")
            frac = c.weight if c.weight is not None else (100.0 if c.is_correct else 0.0)
            ans = respuesta(numero, frac)
            if tolerancia:
                _plain_sub(ans, "tolerance", tolerancia)
            _agregar_feedback(ans, c.feedback)
        _plain_sub(el, "defaultgrade", f"{defaultgrade:g}")
        _plain_sub(el, "penalty", "0.3333333")

    elif q.type == "Essay":
        _plain_sub(el, "responseformat", "editor")
        _plain_sub(el, "responsefieldlines", "10")
        _plain_sub(el, "defaultgrade", f"{defaultgrade:g}")
        _plain_sub(el, "penalty", "0")

    return el


def _serializar_quiz(quiz: ET.Element) -> str:
    xml = ET.tostring(quiz, encoding="unicode")
    xml = html.unescape(xml)
    xml = xml.replace(_CD_OPEN, "<![CDATA[").replace(_CD_CLOSE, "]]>")
    cuerpo = "\n".join(line for line in xml.splitlines() if line.strip())
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{cuerpo}\n'


def gift_to_xml(gift_content: str) -> str:
    """Convierte contenido GIFT a Moodle XML usando el modelo unificado de preguntas."""
    preguntas = GiftParser()._manual_parse(gift_content or "")
    quiz = ET.Element("quiz")
    for q in preguntas:
        quiz.append(_pregunta_a_xml(q))
    return _serializar_quiz(quiz)


# ---------------------------------------------------------------------------
# Moodle XML -> GIFT
# ---------------------------------------------------------------------------

def _text_de(el, default=""):
    """Extrae texto del hijo <text> de un elemento (con o sin CDATA)."""
    if el is None:
        return default
    t = el.find("text")
    if t is None:
        return default
    return t.text if t.text is not None else default


def _texto_respuesta(ans: ET.Element) -> str:
    t = ans.find("text")
    return (t.text or "") if t is not None else ""


def _feedback_de(ans: ET.Element) -> str:
    fb = ans.find("feedback")
    return _text_de(fb).strip() if fb is not None else ""


def _simbolo_respuesta(fraccion) -> str:
    """Símbolo GIFT para una respuesta según su fracción ('=', '~' o '~%N%')."""
    try:
        frac = float(fraccion)
    except (TypeError, ValueError):
        return "="
    if abs(frac - 100.0) < 0.01:
        return "="
    if abs(frac) < 0.01:
        return "~"
    return f"~%{frac:g}%"


def _peso_gift(fraccion) -> str | None:
    """Peso explícito para la primera respuesta numérica; None si es '='."""
    try:
        frac = float(fraccion)
    except (TypeError, ValueError):
        return None
    if abs(frac - 100.0) < 0.01:
        return None
    if abs(frac) < 0.01:
        return ""
    return f"%{frac:g}%"


def _prefijo_formato(formato: str) -> str:
    # En GIFT el formato por defecto ya importa como html/auto_format;
    # sólo hace falta marcar los formatos no predeterminados.
    return "[markdown]" if formato == "markdown" else ""


def _xml_pregunta_a_gift(q: ET.Element) -> str:
    qtype = (q.get("type") or "").lower()

    if qtype == "category":
        ruta = _text_de(q.find("category")).replace("$course$", "").strip()
        return f"$CATEGORY: $course${'/' + ruta.lstrip('/') if ruta else ''}".rstrip()

    titulo = _escape_gift(_text_de(q.find("name")).strip(), "title")

    qt_el = q.find("questiontext")
    stem = _text_de(qt_el).strip()
    formato = (qt_el.get("format") if qt_el is not None else "") or "html"
    if formato == "html":
        stem = _strip_html(stem)
    prefijo = _prefijo_formato(formato)

    gf = _strip_html(_text_de(q.find("generalfeedback"))).strip()
    global_fb = f"####{_escape_gift(gf, 'answer')}" if gf else ""

    bloque = ""

    if qtype in ("multichoice", "shortanswer"):
        partes = []
        for ans in q.findall("answer"):
            texto = _strip_html(_texto_respuesta(ans)).strip() if qtype == "multichoice" else _texto_respuesta(ans).strip()
            feedback = _strip_html(_feedback_de(ans)).strip()
            parte = f"{_simbolo_respuesta(ans.get('fraction', '0'))}{_escape_gift(texto, 'answer')}"
            if feedback:
                parte += f" #{_escape_gift(feedback, 'answer')}"
            partes.append(parte)
        bloque = "{" + "\n".join(partes) + "}" if partes else "{}"

    elif qtype == "truefalse":
        verdadera = None
        retro = {"true": "", "false": ""}
        for ans in q.findall("answer"):
            bajo = _texto_respuesta(ans).strip().lower()
            if bajo not in retro:
                continue
            if ans.get("fraction") == "100":
                verdadera = (bajo == "true")
            retro[bajo] = _strip_html(_feedback_de(ans)).strip()
        letra = "T" if verdadera else "F"
        partes_fb = []
        if retro["true"]:
            partes_fb.append(f"{_escape_gift(retro['true'], 'answer')}")
        if retro["false"]:
            partes_fb.append(f"{_escape_gift(retro['false'], 'answer')}")
        cuerpo_fb = "#" + "#".join(partes_fb) if partes_fb else ""
        bloque = "{" + letra + cuerpo_fb + "}"

    elif qtype == "matching":
        partes = []
        for sq in q.findall("subquestion"):
            izq = _strip_html(_text_de(sq)).strip()
            der = _strip_html(_text_de(sq.find("answer"))).strip()
            partes.append(f"={_escape_gift(izq, 'answer')} -> {_escape_gift(der, 'answer')}")
        bloque = "{" + "\n".join(partes) + "}" if partes else "{}"

    elif qtype == "numerical":
        partes = []
        primera = True
        for ans in q.findall("answer"):
            numero = _texto_respuesta(ans).strip()
            tol_el = ans.find("tolerance")
            if tol_el is not None and (tol_el.text or "").strip():
                numero = f"{numero}:{tol_el.text.strip()}"
            feedback = _strip_html(_feedback_de(ans)).strip()
            peso = _peso_gift(ans.get("fraction", "0"))
            if primera and peso is None:
                simbolo = ""  # forma canónica: {#23.5 ...} sin prefijo
            elif peso is None:
                simbolo = "="
            else:
                simbolo = "~" + peso
            primera = False
            parte = f"{simbolo}{_escape_gift(numero, 'answer')}"
            if feedback:
                parte += f" #{_escape_gift(feedback, 'answer')}"
            partes.append(parte)
        bloque = "{#" + "\n".join(partes) + "}" if partes else "{}"

    elif qtype == "cloze":
        # Los bloques {...} viven embebidos en el enunciado: se preservan tal cual.
        bloque = ""

    elif qtype == "essay":
        bloque = "{}"

    elif qtype == "description":
        linea = f"::{titulo}::{prefijo}{_escape_gift(stem, 'stem')}".rstrip()
        if global_fb:
            linea += "\n" + global_fb
        return linea

    else:
        bloque = "{}"

    encabezado = f"::{titulo}:: " if titulo else ""
    cuerpo = f"{prefijo}{_escape_gift(stem, 'stem')} {bloque}".rstrip()
    salida = encabezado + cuerpo
    if global_fb:
        salida += "\n" + global_fb
    return salida


def xml_to_gift(xml_content: str) -> str:
    """Convierte contenido Moodle XML a GIFT usando el modelo unificado de preguntas."""
    raiz = ET.fromstring(xml_content)
    bloques = [_xml_pregunta_a_gift(q) for q in raiz.findall("question")]
    return "\n\n".join(b for b in bloques if b.strip()) + ("\n" if bloques else "")
