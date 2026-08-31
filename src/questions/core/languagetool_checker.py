"""Módulo de verificación y corrección de ortografía y gramática con LanguageTool para bancos GIFT y XML en moodle-toolbox."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Set, Dict, Any

DEFAULT_LANGUAGETOOL_URL = "https://api.languagetool.org/v2/check"
DEFAULT_LANGUAGETOOL_PREMIUM_URL = "https://api.languagetoolplus.com/v2/check"
LOCAL_LANGUAGETOOL_URL = "http://localhost:8081/v2/check"

PALABRAS_IGNORADAS_DEFAULT = {
    "malloc", "calloc", "realloc", "free", "printf", "scanf", "sscanf", "sprintf",
    "snprintf", "fprintf", "fopen", "fclose", "fread", "fwrite", "fseek", "ftell",
    "sizeof", "typedef", "struct", "enum", "union", "const", "static", "volatile",
    "extern", "inline", "nullptr", "NULL", "size_t", "uint8_t", "uint16_t", "uint32_t",
    "uint64_t", "int8_t", "int16_t", "int32_t", "int64_t", "ssize_t", "bool", "true", "false",
    "argc", "argv", "main", "void", "char", "int", "float", "double", "short", "long",
    "unsigned", "signed", "myst", "markdown", "gcc", "clang", "gdb", "valgrind",
    "bwrap", "cátedra", "puntero", "punteros", "stack", "heap", "segfault", "sigsegv",
    "ripley", "dredd", "deckard", "daedalus", "gaff", "hal", "bishop", "kaneda", "spunkmeyer",
    "typst", "languagetool", "autofix", "callgraph", "endianness", "makefile", "tda", "tdas",
    "gift", "moodle", "cloze", "multichoice", "shortanswer", "truefalse", "numerical"
}


@dataclass
class LanguageToolIssue:
    """Representa una observación ortográfica o gramatical encontrada en un banco GIFT/XML."""
    file_path: Path
    pregunta_id: str
    campo: str
    line: int
    column: int
    message: str
    short_message: str
    rule_id: str
    category: str
    context: str
    replacements: List[str] = field(default_factory=list)
    length: int = 0
    original_word: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": str(self.file_path),
            "pregunta_id": self.pregunta_id,
            "campo": self.campo,
            "line": self.line,
            "column": self.column,
            "rule_id": self.rule_id,
            "category": self.category,
            "message": self.message,
            "context": self.context,
            "replacements": self.replacements,
            "original_word": self.original_word,
        }


def enmascarar_gift_xml(contenido: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Enmascara etiquetas XML/HTML, sintaxis GIFT, fórmulas LaTeX y bloques de código."""
    enmascarado = list(contenido)
    mascaras = []

    def _mask_range(start: int, end: int, preserve_newlines: bool = True):
        for i in range(start, end):
            if preserve_newlines and enmascarado[i] == '\n':
                continue
            enmascarado[i] = ' '
        mascaras.append({"start": start, "end": end})

    # 1. Etiquetas XML / HTML <...>
    for m in re.finditer(r'<[^>\n]+>', contenido):
        _mask_range(m.start(), m.end())

    # 2. Bloques CDATA <![CDATA[ ... ]]>
    for m in re.finditer(r'<!\[CDATA\[', contenido):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'\]\]>', contenido):
        _mask_range(m.start(), m.end())

    # 3. Fórmulas LaTeX \( ... \), \[ ... \], $$ ... $$, $ ... $
    for m in re.finditer(r'\\\(.*?\\\)', contenido, re.DOTALL):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'\\\[.*?\\\]', contenido, re.DOTALL):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'\$\$.*?\$\$', contenido, re.DOTALL):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'\$[^\$\n]+\$', contenido):
        _mask_range(m.start(), m.end())

    # 4. Sintaxis de preguntas GIFT { ... }
    for m in re.finditer(r'\{[^\}]+\}', contenido):
        _mask_range(m.start(), m.end())

    # 5. Títulos GIFT ::Título::
    for m in re.finditer(r'::[^:\n]+::', contenido):
        _mask_range(m.start(), m.end())

    # 6. Código inline `...` y bloques ```...```
    for m in re.finditer(r'(```|~~~)[^\n]*\n.*?\n\s*\1', contenido, re.DOTALL):
        _mask_range(m.start(), m.end())
    for m in re.finditer(r'`[^`\n]+`', contenido):
        _mask_range(m.start(), m.end())

    return "".join(enmascarado), mascaras


def consultar_languagetool(
    texto: str,
    lang: str = "es-AR",
    server_url: Optional[str] = None,
    username: Optional[str] = None,
    api_key: Optional[str] = None,
    premium: bool = False,
    disabled_rules: Optional[Set[str]] = None,
    timeout_sec: float = 10.0,
) -> Dict[str, Any]:
    """Envía una petición a LanguageTool API (local, remota libre o remota paga)."""
    env_server = os.environ.get("LANGUAGETOOL_URL") or os.environ.get("LANGUAGETOOL_SERVER")
    env_user = os.environ.get("LANGUAGETOOL_USERNAME") or os.environ.get("LANGUAGETOOL_USER")
    env_key = os.environ.get("LANGUAGETOOL_API_KEY") or os.environ.get("LANGUAGETOOL_KEY")
    env_premium = os.environ.get("LANGUAGETOOL_PREMIUM", "").lower() in ("1", "true", "yes")

    final_server = server_url or env_server
    final_user = username or env_user
    final_key = api_key or env_key
    is_premium = premium or env_premium or bool(final_user and final_key)

    urls_to_try = []
    if final_server:
        urls_to_try.append(final_server)
    elif is_premium:
        urls_to_try.append(DEFAULT_LANGUAGETOOL_PREMIUM_URL)
        urls_to_try.append(DEFAULT_LANGUAGETOOL_URL)
    else:
        urls_to_try.append(LOCAL_LANGUAGETOOL_URL)
        urls_to_try.append(DEFAULT_LANGUAGETOOL_URL)

    data = {
        "text": texto,
        "language": lang,
    }
    if final_user:
        data["username"] = final_user
    if final_key:
        data["apiKey"] = final_key
    if disabled_rules:
        data["disabledRules"] = ",".join(sorted(disabled_rules))

    encoded_data = urllib.parse.urlencode(data).encode("utf-8")
    last_error = None

    for endpoint in urls_to_try:
        try:
            req = urllib.request.Request(
                endpoint,
                data=encoded_data,
                headers={"User-Agent": "moodle-toolbox/LanguageToolChecker", "Accept": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw)
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise RuntimeError(f"No se pudo contactar el servidor de LanguageTool ({urls_to_try}): {last_error}")
    return {"matches": []}


def analizar_archivo_banco(
    file_path: Path,
    lang: str = "es-AR",
    server_url: Optional[str] = None,
    username: Optional[str] = None,
    api_key: Optional[str] = None,
    premium: bool = False,
    ignore_words: Optional[Set[str]] = None,
    ignore_rules: Optional[Set[str]] = None,
) -> List[LanguageToolIssue]:
    """Audita la ortografía y gramática de un archivo de preguntas GIFT o Moodle XML."""
    if not file_path.is_file():
        return []

    contenido_original = file_path.read_text(encoding="utf-8", errors="replace")
    texto_limpio, _ = enmascarar_gift_xml(contenido_original)

    palabras_ignorar = PALABRAS_IGNORADAS_DEFAULT.copy()
    if ignore_words:
        palabras_ignorar.update(w.lower() for w in ignore_words)

    reglas_deshabilitadas = ignore_rules or set()

    try:
        resultado = consultar_languagetool(
            texto_limpio,
            lang=lang,
            server_url=server_url,
            username=username,
            api_key=api_key,
            premium=premium,
            disabled_rules=reglas_deshabilitadas,
        )
    except Exception:
        return []

    lineas = contenido_original.splitlines(keepends=True)
    line_offsets = []
    curr = 0
    for l in lineas:
        line_offsets.append(curr)
        curr += len(l)

    def offset_to_line_col(offset: int) -> Tuple[int, int]:
        for idx, start in enumerate(line_offsets):
            if idx + 1 < len(line_offsets):
                if start <= offset < line_offsets[idx + 1]:
                    return idx + 1, (offset - start) + 1
            else:
                if offset >= start:
                    return idx + 1, (offset - start) + 1
        return 1, offset + 1

    issues = []
    for match in resultado.get("matches", []):
        offset = match.get("offset", 0)
        length = match.get("length", 0)
        rule = match.get("rule", {})
        rule_id = rule.get("id", "UNKNOWN")
        category = rule.get("category", {}).get("name", "Gramática / Ortografía")
        message = match.get("message", "")
        short_msg = match.get("shortMessage", "")
        context_data = match.get("context", {})
        context_str = context_data.get("text", "")
        replacements = [r.get("value") for r in match.get("replacements", []) if "value" in r]

        palabra_afectada = contenido_original[offset:offset + length].strip()

        if palabra_afectada.lower() in palabras_ignorar or palabra_afectada in palabras_ignorar:
            continue

        lin, col = offset_to_line_col(offset)
        issues.append(LanguageToolIssue(
            file_path=file_path,
            pregunta_id=file_path.stem,
            campo="cuerpo",
            line=lin,
            column=col,
            message=message,
            short_message=short_msg,
            rule_id=rule_id,
            category=category,
            context=context_str,
            replacements=replacements[:5],
            length=length,
            original_word=palabra_afectada,
        ))

    return issues


def aplicar_autofix_archivo_banco(
    file_path: Path,
    issues: List[LanguageToolIssue],
) -> int:
    """Aplica sugerencias ortográficas sobre el archivo GIFT o XML."""
    if not issues or not file_path.is_file():
        return 0

    contenido = file_path.read_text(encoding="utf-8", errors="replace")
    lineas = contenido.splitlines(keepends=True)
    cambios = 0

    issues_por_linea: Dict[int, List[LanguageToolIssue]] = {}
    for iss in issues:
        if iss.replacements and iss.original_word:
            issues_por_linea.setdefault(iss.line, []).append(iss)

    nuevas_lineas = []
    for num_linea, linea_texto in enumerate(lineas, start=1):
        if num_linea in issues_por_linea:
            issues_linea = sorted(issues_por_linea[num_linea], key=lambda x: x.column, reverse=True)
            mod_linea = linea_texto
            for iss in issues_linea:
                sugerencia = iss.replacements[0]
                col_idx = iss.column - 1
                orig = iss.original_word
                if 0 <= col_idx < len(mod_linea) and mod_linea[col_idx:col_idx + len(orig)] == orig:
                    mod_linea = mod_linea[:col_idx] + sugerencia + mod_linea[col_idx + len(orig):]
                    cambios += 1
            nuevas_lineas.append(mod_linea)
        else:
            nuevas_lineas.append(linea_texto)

    if cambios > 0:
        file_path.write_text("".join(nuevas_lineas), encoding="utf-8")

    return cambios


def generar_reporte_markdown_languagetool(issues: List[LanguageToolIssue]) -> str:
    """Genera reporte Markdown de observaciones ortográficas en bancos de preguntas."""
    lines = ["## Auditoría Ortográfica y Gramatical de Bancos de Preguntas (LanguageTool)\n"]
    lines.append(f"- **Total de observaciones encontradas:** {len(issues)}\n")

    if not issues:
        lines.append("> [!TIP]\n> **Bancos Impecables:** No se detectaron faltas de ortografía ni errores gramaticales en los bancos analizados.\n")
        return "\n".join(lines)

    lines.append("| Archivo | Línea:Col | Categoría | Regla | Palabra / Contexto | Sugerencia |")
    lines.append("| :--- | :---: | :--- | :---: | :--- | :--- |")
    for iss in issues:
        sug = ", ".join(f"`{r}`" for r in iss.replacements[:3]) if iss.replacements else "*Ninguna*"
        ctx = iss.context.replace("\n", " ").replace("|", "\\|")
        lines.append(f"| `{iss.file_path.name}` | {iss.line}:{iss.column} | {iss.category} | `{iss.rule_id}` | `{iss.original_word}` ({ctx[:35]}...) | {sug} |")
    lines.append("")
    return "\n".join(lines)
