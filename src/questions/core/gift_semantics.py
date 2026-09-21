"""Acciones semánticas y utilidades de llaves del parser GIFT."""

import re
from typing import Optional, Any

from questions.core.gift_model import *  # noqa: F401,F403
from questions.core.gift_model import FormattedText, Choice, MatchPair, NumericalAnswer, Question, QuestionType


def _llaves_balanceadas(texto: str) -> bool:
    """True si las llaves del texto están balanceadas (ignorando escapes \\{ \\})."""
    profundidad = 0
    escapado = False
    for ch in texto:
        if escapado:
            escapado = False
            continue
        if ch == "\\":
            escapado = True
            continue
        if ch == "{":
            profundidad += 1
        elif ch == "}":
            profundidad -= 1
            if profundidad < 0:
                return False
    return profundidad == 0


def _extraer_ultimo_grupo_llaves(texto: str):
    r"""Localiza el ÚLTIMO grupo balanceado {..} del texto (ignora \{ \}).

    Devuelve (antes, contenido) o None si no cierra al final.
    """
    texto = texto.rstrip()
    if not texto.endswith("}"):
        return None
    escapados = set()
    i = 0
    n = len(texto)
    while i < n:
        if texto[i] == "\\":
            escapados.add(i + 1)
            i += 2
        else:
            i += 1
    profundidad = 0
    for j in range(n - 1, -1, -1):
        if j in escapados:
            continue
        c = texto[j]
        if c == "}":
            profundidad += 1
        elif c == "{":
            profundidad -= 1
            if profundidad == 0:
                return texto[:j], texto[j + 1:-1]
    return None


class GiftSemantics:
    """Semantic actions for the GIFT parser."""
    
    def __init__(self):
        self.current_format = "moodle"
        self.current_id = None
        self.current_tags = []
    
    def _extract_tags_and_id(self, comments: list) -> tuple:
        """Extract tags and ID from comment lines."""
        tags = []
        question_id = None
        
        if not comments:
            return tags, question_id
            
        for comment in comments:
            if not comment:
                continue
            comment_str = str(comment)
            # Extract ID
            id_match = re.search(r'\[id:([^\]]+)\]', comment_str)
            if id_match:
                question_id = id_match.group(1).strip()
            # Extract tags
            for tag_match in re.finditer(r'\[tag:([^\]]+)\]', comment_str):
                tags.append(tag_match.group(1).strip())
        
        return tags, question_id
    
    def _decode_escapes(self, text: str) -> str:
        """Decode escaped characters in GIFT format."""
        if not text:
            return ""
        return (text
            .replace('\\\\', '\x00')  # Temporary placeholder
            .replace('\\:', ':')
            .replace('\\#', '#')
            .replace('\\=', '=')
            .replace('\\{', '{')
            .replace('\\}', '}')
            .replace('\\~', '~')
            .replace('\\n', '\n')
            .replace('\x00', '\\'))
    
    def _parse_formatted_text(self, ast) -> FormattedText:
        """Parse formatted text from AST."""
        if ast is None:
            return FormattedText()
        
        if isinstance(ast, str):
            return FormattedText(text=self._decode_escapes(ast.strip()))
        
        if isinstance(ast, list):
            text = ''.join(str(t) for t in ast)
            return FormattedText(text=self._decode_escapes(text.strip()))
        
        return FormattedText()
