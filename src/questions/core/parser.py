#!/usr/bin/env python3
"""
Parser para archivos GIFT: recorre el contenido por bloques y arma el modelo de preguntas
(el análisis es manual; no usa un generador de parsers).
"""

import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from enum import Enum

from questions.core.gift_model import (  # noqa: F401
    QuestionType, FormattedText, Choice, MatchPair, NumericalAnswer, Question,
)
from questions.core.gift_semantics import (  # noqa: F401
    GiftSemantics, _llaves_balanceadas, _extraer_ultimo_grupo_llaves,
)


class GiftParser:
    """Parser for GIFT format questions."""
    
    def _manual_parse(self, content: str) -> list:
        """Parsea contenido GIFT línea a línea y devuelve la lista de preguntas (único parser del paquete)."""
        questions = []
        lines = content.split('\n')
        
        current_block = []
        current_comments = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Separador: una línea vacía corta el bloque sólo si el bloque
            # actual tiene sus llaves balanceadas. Así, el código C embebido
            # (que suele tener líneas vacías y llaves propias) permanece junto.
            if not stripped:
                if current_block and _llaves_balanceadas("\n".join(current_block)):
                    q = self._parse_question_block(current_block, current_comments)
                    if q:
                        questions.append(q)
                    current_block = []
                    current_comments = []
                elif current_block:
                    current_block.append("")
                i += 1
                continue
            
            # Comments (may contain tags/ids)
            if stripped.startswith('//'):
                current_comments.append(stripped[2:])
                i += 1
                continue
            
            # Category
            if stripped.startswith('$CATEGORY:'):
                if current_block:
                    q = self._parse_question_block(current_block, current_comments)
                    if q:
                        questions.append(q)
                    current_block = []
                    current_comments = []
                
                cat_title = stripped[10:].strip()
                questions.append(Question(type="Category", title=cat_title))
                pending_blank = False
                i += 1
                continue
            
            # Accumulate question block
            current_block.append(line)
            i += 1
        
        # Process last block
        if current_block:
            q = self._parse_question_block(current_block, current_comments)
            if q:
                questions.append(q)
        
        return questions
    
    def _parse_question_block(self, lines: list, comments: list) -> Optional[Question]:
        """Parse a single question block."""
        if not lines:
            return None
        
        text = '\n'.join(lines)
        semantics = GiftSemantics()
        tags, question_id = semantics._extract_tags_and_id(comments)
        
        # Extract title
        title = None
        title_match = re.match(r'^::([^:]+(?::(?!:)[^:]*)*)::(.*)$', text, re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            text = title_match.group(2)
        
        # Extraer el bloque de respuestas como ÚLTIMO grupo balanceado de
        # llaves (tolera código C embebido en el enunciado). Si el bloque
        # previo contiene más llaves abiertas propias (cloze), caemos al
        # comportamiento clásico de primera-llave.
        partes = _extraer_ultimo_grupo_llaves(text)
        if partes is None:
            # Description (no answer block)
            stem = semantics._parse_formatted_text(text)
            return Question(
                type="Description",
                title=title,
                stem=stem,
                id=question_id,
                tags=tags
            )
        
        stem_before, answer_block = partes
        stem_before = stem_before.strip()
        answer_block = answer_block.strip()

        brace_end = len(text) - 1
        stem_after = ""
        brace_start_alt = text.find('{')
        hay_mas_grupos = "{" in stem_before and "}" in stem_before
        es_cloze_heuristico = (
            hay_mas_grupos
            and "```" not in stem_before
        )
        if es_cloze_heuristico:
            # cloze: las respuestas viven embebidas en el enunciado; se usa el
            # comportamiento clásico de primera-llave para capturar stem_after.
            brace_start = brace_start_alt
            brace_end = text.rfind('}')
            stem_before = text[:brace_start].strip()
            answer_block = text[brace_start+1:brace_end].strip()
        stem_after = text[brace_end+1:].strip() if brace_end+1 < len(text) else ""
        
        # Parse stem with format
        stem = self._parse_stem(stem_before, stem_after, semantics)
        
        # Parse answer block
        question = self._parse_answers(answer_block, semantics)
        question.title = title
        question.stem = stem
        question.id = question_id
        question.tags = tags
        question.has_embedded_answers = bool(stem_after)
        
        return question
    
    def _parse_stem(self, before: str, after: str, semantics: GiftSemantics) -> FormattedText:
        """Parse the question stem, handling format specification."""
        text = before
        fmt = "moodle"
        
        # Check for format at start
        format_match = re.match(r'^\[(html|markdown|plain|moodle)\](.*)$', text, re.DOTALL)
        if format_match:
            fmt = format_match.group(1)
            text = format_match.group(2)
        
        if after:
            text = text + " _____ " + after
        
        return FormattedText(format=fmt, text=semantics._decode_escapes(text.strip()))
    
    def _parse_answers(self, block: str, semantics: GiftSemantics) -> Question:
        """Parse the answer block and determine question type."""
        block = block.strip()
        
        # Essay (empty block)
        if not block:
            return Question(type="Essay")
        
        # True/False
        tf_match = re.match(r'^(TRUE|FALSE|T|F)\s*(?:#(.*))?$', block, re.IGNORECASE | re.DOTALL)
        if tf_match:
            is_true = tf_match.group(1).upper() in ('TRUE', 'T')
            feedback_text = tf_match.group(2) or ""
            feedbacks = self._parse_tf_feedback(feedback_text, semantics)
            
            q = Question(type="TF", is_true=is_true)
            if len(feedbacks) > 0:
                q.true_feedback = feedbacks[0]
            if len(feedbacks) > 1:
                q.false_feedback = feedbacks[1]
            
            # Check for global feedback
            gf_match = re.search(r'####(.+)$', block, re.DOTALL)
            if gf_match:
                q.global_feedback = semantics._parse_formatted_text(gf_match.group(1))
            
            return q
        
        # Numerical
        if block.startswith('#'):
            return self._parse_numerical(block[1:], semantics)
        
        # Matching (contains ->)
        if '->' in block:
            return self._parse_matching(block, semantics)
        
        # Multiple choice or short answer
        return self._parse_mc_or_short(block, semantics)
    
    def _parse_tf_feedback(self, text: str, semantics: GiftSemantics) -> list:
        """Parse True/False feedback."""
        feedbacks = []
        if not text:
            return feedbacks
        
        # Split by # but not ####
        parts = re.split(r'(?<!#)#(?!###)', text)
        for part in parts:
            if part.strip() and not part.strip().startswith('###'):
                feedbacks.append(semantics._parse_formatted_text(part))
        
        return feedbacks
    
    def _parse_numerical(self, block: str, semantics: GiftSemantics) -> Question:
        """Parse numerical answer."""
        choices = []

        # Check for global feedback
        global_feedback = None
        gf_match = re.search(r'####(.+)$', block, re.DOTALL)
        if gf_match:
            global_feedback = semantics._parse_formatted_text(gf_match.group(1))
            block = block[:gf_match.start()]

        # Primary answer without prefix (GIFT: {#23.5} o {#23.5:0.1 ~...})
        primaria = None
        m_primaria = re.match(r'^\s*([+-]?\d+(?:\.\d+)?(?::\s*[+-]?\d+(?:\.\d+)?)?)\s*(?=[=~]|$)', block, re.DOTALL)
        if m_primaria:
            primaria = m_primaria.group(1).strip()
            block = block[m_primaria.end():]

        # Multiple numerical choices
        choice_pattern = re.compile(r'([=~])(%[+-]?\d+(?:\.\d+)?%)?([^=~#]*?)(?:#([^=~]*))?(?=[=~]|$)', re.DOTALL)
        matches = list(choice_pattern.finditer(block))

        if matches:
            if primaria:
                choices.append(Choice(is_correct=True, text=FormattedText(text=primaria)))
            for m in matches:
                symbol, weight, num_str, feedback = m.groups()
                choice = Choice(
                    is_correct=(symbol == '='),
                    weight=float(weight[1:-1]) if weight else None,
                    feedback=semantics._parse_formatted_text(feedback) if feedback else None
                )
                # Parse numerical value
                num_str = num_str.strip() if num_str else ""
                if num_str:
                    choice.text = FormattedText(text=num_str)
                choices.append(choice)
        elif primaria:
            # Single numerical answer
            choices.append(Choice(is_correct=True, text=FormattedText(text=primaria)))

        return Question(type="Numerical", choices=choices, global_feedback=global_feedback)
    
    def _parse_matching(self, block: str, semantics: GiftSemantics) -> Question:
        """Parse matching question."""
        pairs = []
        
        # Check for global feedback
        global_feedback = None
        gf_match = re.search(r'####(.+)$', block, re.DOTALL)
        if gf_match:
            global_feedback = semantics._parse_formatted_text(gf_match.group(1))
            block = block[:gf_match.start()]
        
        # Parse match pairs
        match_pattern = re.compile(r'=\s*([^->=~]*?)\s*->\s*([^=~\n\r]+)', re.DOTALL)
        for m in match_pattern.finditer(block):
            left, right = m.groups()
            pairs.append(MatchPair(
                subquestion=semantics._parse_formatted_text(left),
                subanswer=semantics._decode_escapes(right.strip())
            ))
        
        return Question(type="Matching", match_pairs=pairs, global_feedback=global_feedback)
    
    def _parse_mc_or_short(self, block: str, semantics: GiftSemantics) -> Question:
        """Parse multiple choice or short answer question."""
        choices = []
        
        # Check for global feedback
        global_feedback = None
        gf_match = re.search(r'####(.+)$', block, re.DOTALL)
        if gf_match:
            global_feedback = semantics._parse_formatted_text(gf_match.group(1))
            block = block[:gf_match.start()]
        
        # Parse choices
        # Pattern: [=~] optional_weight text optional_feedback
        choice_pattern = re.compile(
            r'([=~])\s*(%[+-]?\d+(?:\.\d+)?%)?\s*([^=~#]*?)(?:#([^=~]*))?(?=[=~]|$)',
            re.DOTALL
        )
        
        for m in choice_pattern.finditer(block):
            symbol, weight, text, feedback = m.groups()
            if not text or not text.strip():
                continue
            
            choice = Choice(
                is_correct=(symbol == '='),
                weight=float(weight[1:-1]) if weight else None,
                text=semantics._parse_formatted_text(text),
                feedback=semantics._parse_formatted_text(feedback) if feedback else None
            )
            choices.append(choice)
        
        # If no = or ~ found, it might be a simple short answer
        if not choices and block.strip():
            choices.append(Choice(
                is_correct=True,
                text=semantics._parse_formatted_text(block)
            ))
        
        # Determine type: all correct = Short, mixed = MC
        if choices:
            all_correct = all(c.is_correct for c in choices)
            q_type = "Short" if all_correct else "MC"
        else:
            q_type = "Essay"
        
        return Question(type=q_type, choices=choices, global_feedback=global_feedback)
    
    def parse(self, content: str) -> dict:
        """Parse GIFT content and return result."""
        try:
            questions = self._manual_parse(content)
            return {
                "success": True,
                "questions": [q.to_dict() for q in questions],
                "questionCount": len(questions)
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "message": str(e)
                }
            }
    
    def parse_file(self, filepath: str) -> dict:
        """Parse a GIFT file."""
        path = Path(filepath)
        
        if not path.exists():
            return {
                "success": False,
                "filepath": str(filepath),
                "error": {"message": f"Archivo no encontrado: {filepath}"}
            }
        
        try:
            content = path.read_text(encoding='utf-8')
            result = self.parse(content)
            result["filepath"] = str(filepath)
            return result
        except Exception as e:
            return {
                "success": False,
                "filepath": str(filepath),
                "error": {"message": f"Error leyendo archivo: {e}"}
            }


def get_question_summary(question: dict) -> dict:
    """Extract summary information from a question."""
    summary = {
        "type": question.get("type", "Unknown"),
        "title": question.get("title"),
        "id": question.get("id"),
        "tags": question.get("tags", []),
        "hasGlobalFeedback": bool(question.get("globalFeedback")),
        "hasEmbeddedAnswers": question.get("hasEmbeddedAnswers", False)
    }
    
    q_type = question.get("type")
    
    if q_type == "MC":
        choices = question.get("choices", [])
        summary["choicesCount"] = len(choices)
        summary["correctChoices"] = sum(1 for c in choices if c.get("is_correct"))
    elif q_type == "TF":
        summary["isTrue"] = question.get("isTrue")
    elif q_type == "Matching":
        summary["matchPairsCount"] = len(question.get("matchPairs", []))
    elif q_type in ("Short", "Numerical"):
        summary["answersCount"] = len(question.get("choices", []))
    
    return summary


# Singleton parser instance
_parser = None

def get_parser() -> GiftParser:
    """Get or create the GIFT parser instance."""
    global _parser
    if _parser is None:
        _parser = GiftParser()
    return _parser


def parse_gift(content: str) -> dict:
    """Parse GIFT content."""
    return get_parser().parse(content)


def parse_gift_file(filepath: str) -> dict:
    """Parse a GIFT file."""
    return get_parser().parse_file(filepath)


def main():
    parser = argparse.ArgumentParser(
        description='Parser para archivos GIFT de Moodle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s archivo.gift
  %(prog)s archivo.gift --json
  %(prog)s archivo.gift --json --summary
        """
    )
    
    parser.add_argument('filepath', nargs='?', help='Archivo GIFT a parsear')
    parser.add_argument('-j', '--json', action='store_true', help='Salida en formato JSON')
    parser.add_argument('-s', '--summary', action='store_true', help='Mostrar solo resumen')
    
    args = parser.parse_args()
    
    if not args.filepath:
        parser.print_help()
        return 1
    
    # Verificar si es un directorio
    filepath = Path(args.filepath)
    if filepath.is_dir():
        print(f"❌ Error: '{args.filepath}' es un directorio")
        print(f"   Para analizar directorios usa: gift-verify {args.filepath}")
        return 1
    
    result = parse_gift_file(args.filepath)
    
    if args.json:
        if args.summary and result["success"]:
            summaries = [get_question_summary(q) for q in result["questions"]]
            output = {
                "success": True,
                "filepath": result["filepath"],
                "questionCount": result["questionCount"],
                "questions": summaries
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["success"]:
            print(f"✅ Archivo parseado correctamente: {args.filepath}")
            print(f"   Total de preguntas: {result['questionCount']}")
            print()
            
            for idx, q in enumerate(result["questions"], 1):
                summary = get_question_summary(q)
                title = summary["title"] or "<sin título>"
                print(f"   {idx}. [{summary['type']}] {title}")
                if summary["tags"]:
                    print(f"      Tags: {', '.join(summary['tags'])}")
        else:
            print(f"❌ Error parseando archivo: {args.filepath}")
            print(f"   {result['error']['message']}")
            return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
