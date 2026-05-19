#!/usr/bin/env python3
import argparse
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
import tatsu

# --- GIFT GRAMMAR ---
GIFT_PEG_GRAMMAR = r'''
@@grammar::GIFT
@@whitespace :: //

start = { item }+ $ ;

item = category | question_with_answers | description ;

category = __ '$CATEGORY:' ~ cat:/[^\n\r]+/ eol { blank_line }* ;

description = __ tags:{ tag_comment __ }* title:[ title __ ] stem:rich_text { blank_line }+ ;

question_with_answers = __ tags:{ tag_comment __ }* title:[ title __ ] stem1:[ question_stem ] _ '{' _ answers:answers _ '}' _ stem2:[ question_stem ] { blank_line }* ;

title = '::' @:/[^:]+(?::(?!:)[^:]*)*/ '::' ;

tag_comment = '//' @:/[^\n\r]*/ ;

question_stem = !'//' !'::' rich_text ;

answers = matching_answers | tf_answer | mc_answers | numerical_answers | short_answer | essay_answer ;

matching_answers = match:{ match }+ [ global_feedback ] ;
match = _ '=' _ [ match_text ] '->' _ plain_text _ ;
match_text = [ format ] /(?:(?!->)[^\n\r{}=~#])+/ ;

tf_answer = true_false:true_false [ feedback ] [ feedback ] [ global_feedback ] ;
true_false = 'TRUE' | 'T' | 'FALSE' | 'F' ;

mc_answers = choice:{ choice }+ [ global_feedback ] ;
choice = _ symbol:/[=~]/ [ weight ] _ text:rich_text [ feedback:feedback ] _ ;

weight = '%' ~ @:/[+-]?\d+(?:\.\d+)?/ '%' ;

numerical_answers = '#' ~ ( numerical_choice:{ numerical_choice }+ | single_numerical:single_numerical ) [ global_feedback ] ;
numerical_choice = _ /[=~]/ [ weight ] [ single_numerical ] [ feedback ] _ ;
single_numerical = number_range | number_high_low | number_alone ;
number_range = number ':' number ;
number_high_low = number '..' number ;
number_alone = number ;
number = /[+-]?\d+(?:\.\d+)?/ ;

short_answer = text:rich_text [ feedback ] [ global_feedback ] ;

essay_answer = [ global_feedback ] ;

feedback = '#' !'###' ~ [ rich_text ] ;

global_feedback = '####' ~ rich_text ;

rich_text = format:[ format ] text:text_content ;
format = '[' @/html|markdown|plain|moodle/ ']' ;
text_content = { text_char }+ ;
text_char = escape_sequence | /[^\n\r{}=~#\\]/ | /(?=#(?!#))/ ;

plain_text = { /[^\n\r{}=~#\\]/ | escape_sequence }+ ;

escape_sequence = /\\[:\\#={}~n\\]/ ;

_ = /[ \t\r\n]*/ ;
__ = { /[ \t\n\r]/ }* ;
eol = /\r\n|\n|\r/ ;
blank_line = /[ \t]*/ eol ;
'''

class QuestionValidator:
    def __init__(self, check_tags: bool = False, check_title: bool = False, check_markdown: bool = False):
        self.check_tags = check_tags
        self.check_title = check_title
        self.check_markdown = check_markdown
        try:
            self.gift_parser = tatsu.compile(GIFT_PEG_GRAMMAR)
        except Exception as e:
            print(f"Error compiling GIFT grammar: {e}", file=sys.stderr)
            self.gift_parser = None

    def validate_gift(self, filepath: Path) -> Dict[str, Any]:
        report = {
            "file": str(filepath),
            "type": "GIFT",
            "errors": [],
            "status": "OK"
        }
        
        try:
            content = filepath.read_text(encoding='utf-8')
            if not content.strip():
                report["status"] = "EMPTY"
                report["errors"].append("El archivo está vacío.")
                return report

            # Check for 'split' questions (blank lines inside the question)
            lines = content.splitlines()
            # Find first real content line
            first_content_idx = -1
            for i, line in enumerate(lines):
                sline = line.strip()
                if sline and not sline.startswith('//') and not sline.startswith('$'):
                    first_content_idx = i
                    break
            
            # Find last real content line
            last_content_idx = -1
            for i in range(len(lines)-1, -1, -1):
                sline = lines[i].strip()
                if sline and not sline.startswith('//'):
                    last_content_idx = i
                    break
            
            if first_content_idx != -1 and last_content_idx != -1:
                for i in range(first_content_idx, last_content_idx):
                    if lines[i].strip() == "":
                        report["errors"].append(f"Pregunta dividida: detectada línea en blanco en la línea {i+1}.")
                        report["status"] = "ERROR"
                        break

            # Check for 'out of place' colons (:)
            # Reject any ':' that is not part of '::' and is not escaped '\:'
            # Pattern: find a ':' that is not preceded by ':' or '\' and not followed by ':'
            bad_colon_pattern = re.compile(r'(?<![:\\]):(?![ :])')
            # Note: We allow ': ' (colon space) sometimes? No, user said reject it.
            # Let's be more strict as requested.
            for i, line in enumerate(lines):
                # Ignore comments
                if line.strip().startswith('//'):
                    continue
                # Find colons that are not part of :: and not escaped \:
                # We can do this by replacing :: and \: temporarily
                temp_line = line.replace('::', 'XX').replace('\\:', 'YY')
                if ':' in temp_line:
                    # Found a naked colon
                    report["errors"].append(f"Línea {i+1}: Se detectó un uso de ':' fuera de lugar. Use la versión fullwidth '：' o elimínelo.")
                    report["status"] = "ERROR"
                    break

            if self.gift_parser:
                try:
                    ast = self.gift_parser.parse(content)
                    items = [item for item in ast if item.get('answers') or item.get('stem') or item.get('cat')]
                    
                    if not items:
                        if not report["errors"]:
                            report["status"] = "EMPTY"
                            report["errors"].append("No se detectaron preguntas ni categorías.")
                        return report

                    # Warn if multiple items (excluding category)
                    questions_count = sum(1 for item in items if item.get('answers') or (item.get('stem') and not item.get('cat')))
                    if questions_count > 1 and not any("dividida" in err for err in report["errors"]):
                        report["errors"].append(f"Se encontraron {questions_count} elementos independientes. Posible división por líneas en blanco.")
                        if report["status"] == "OK": report["status"] = "WARNING"

                    # Validation of flags for GIFT
                    for i, item in enumerate(items):
                        if item.get('cat'):
                            continue
                        
                        # Use title or fallback
                        item_title_raw = item.get('title')
                        item_title = None
                        if item_title_raw:
                            if isinstance(item_title_raw, list):
                                item_title = "".join(str(x) for x in item_title_raw if isinstance(x, str))
                            else:
                                item_title = str(item_title_raw)
                        
                        display_title = item_title or f"Elemento {i+1}"

                        # Check Title
                        if self.check_title:
                            if not item_title:
                                report["errors"].append(f"'{display_title}': Falta el título (::título::).")
                                report["status"] = "ERROR"
                        
                        # Check Tags
                        if self.check_tags:
                            has_tags = False
                            item_tags = item.get('tags', [])
                            if item_tags:
                                for tag_entry in item_tags:
                                    tag_str = str(tag_entry)
                                    if '[tag:' in tag_str:
                                        has_tags = True
                                        break
                            if not has_tags:
                                report["errors"].append(f"'{display_title}': Faltan etiquetas (// [tag:xxx]).")
                                report["status"] = "ERROR"
                        
                        # Check Markdown
                        if self.check_markdown:
                            # Target only the main stem (Description) or stem1 (Question)
                            main_stem = item.get('stem') or item.get('stem1')
                            
                            if main_stem:
                                fmt = main_stem.get('format')
                                if fmt != 'markdown':
                                    report["errors"].append(f"'{display_title}': Falta el formato [markdown] inmediatamente antes del enunciado.")
                                    report["status"] = "ERROR"

                except tatsu.exceptions.ParseException as e:
                    if not any("dividida" in err for err in report["errors"]):
                        report["status"] = "SYNTAX_ERROR"
                        report["errors"].append(f"Error de sintaxis: {e}")
            else:
                report["status"] = "CRITICAL_ERROR"
                report["errors"].append("El parser GIFT no está disponible.")

        except Exception as e:
            report["status"] = "CRITICAL_ERROR"
            report["errors"].append(f"Error inesperado: {e}")
            
        return report

    def validate_xml(self, filepath: Path) -> Dict[str, Any]:
        report = {
            "file": str(filepath),
            "type": "XML",
            "errors": [],
            "status": "OK"
        }
        
        try:
            content = filepath.read_text(encoding='utf-8')
            if not content.strip():
                report["status"] = "EMPTY"
                report["errors"].append("El archivo está vacío.")
                return report

            # 1. Check for CDATA (must be present in non-empty <text> blocks)
            missing_cdata_count = 0
            text_matches = re.finditer(r'<text>(.*?)</text>', content, re.DOTALL)
            for match in text_matches:
                block_content = match.group(1)
                if block_content.strip() and not block_content.strip().startswith('<![CDATA['):
                    missing_cdata_count += 1
            
            if missing_cdata_count > 0:
                report["errors"].append(f"Se encontraron {missing_cdata_count} bloques <text> sin sección CDATA.")
                report["status"] = "ERROR"

            # 2. Parse XML for structure checks
            try:
                root = ET.fromstring(content)
                questions = root.findall('.//question')
                if not questions and root.tag == 'question':
                    questions = [root]
                
                if not questions:
                    if root.tag == 'quiz':
                        report["errors"].append("El archivo <quiz> no contiene elementos <question>.")
                        report["status"] = "ERROR"
                
                for i, q in enumerate(questions):
                    q_type = q.get('type')
                    if q_type == 'category':
                        continue
                        
                    q_name_el = q.find('./name/text')
                    q_title = q_name_el.text if q_name_el is not None else f"Pregunta {i+1}"

                    # Check Title
                    if self.check_title:
                        if q_name_el is None or not (q_name_el.text or "").strip():
                            report["errors"].append(f"'{q_title}': Falta el título (<name><text>).")
                            report["status"] = "ERROR"
                    
                    # Check Tags
                    if self.check_tags:
                        tags = q.findall('./tags/tag')
                        if not tags:
                            report["errors"].append(f"'{q_title}': Faltan etiquetas (<tags><tag>).")
                            report["status"] = "ERROR"
                    
                    # Check Markdown
                    if self.check_markdown:
                        elements_with_format = q.findall('.//*[@format]')
                        non_markdown = [el.get('format') for el in elements_with_format if el.get('format') != 'markdown']
                        if non_markdown:
                            report["errors"].append(f"'{q_title}': Se encontraron formatos no-markdown: {', '.join(set(non_markdown))}.")
                            report["status"] = "ERROR"

            except ET.ParseError as e:
                report["status"] = "SYNTAX_ERROR"
                report["errors"].append(f"Error de parseo XML: {e}")

        except Exception as e:
            report["status"] = "CRITICAL_ERROR"
            report["errors"].append(f"Error inesperado: {e}")
            
        return report

    def validate(self, filepath: Path) -> Dict[str, Any]:
        if filepath.suffix.lower() == '.gift':
            return self.validate_gift(filepath)
        elif filepath.suffix.lower() == '.xml':
            return self.validate_xml(filepath)
        else:
            return {
                "file": str(filepath),
                "type": "Unknown",
                "errors": ["Extensión de archivo no soportada (usar .gift o .xml)."],
                "status": "ERROR"
            }

MANUAL_TEXT = """
# Manual de validate-questions
Validador unificado para archivos de preguntas en formato GIFT y XML (Moodle).

## Validaciones XML
- CDATA: Obligatorio en bloques <text> no vacíos.
- Estructura: Tags en question/tags/tag/text, Título en question/name/text.

## Validaciones GIFT
- Preguntas Divididas: Detecta líneas en blanco accidentales dentro de una pregunta.
- Dos Puntos (:): Prohíbe ':' sin escapar fuera de títulos ::tit::.
- Sintaxis: Validación estricta contra gramática PEG.

## Flags
--tags: Verifica presencia de etiquetas.
--title: Verifica presencia de título.
--markdown: Asegura formato [markdown] entre el título y el enunciado.
"""

LLM_INSTRUCTIONS = r"""
# Instrucciones para LLMs (validate-questions)
1. XML: Envuelve SIEMPRE los nodos <text> en <![CDATA[ ... ]]> .
2. GIFT: No insertes líneas en blanco entre el título, enunciado y llaves.
3. GIFT: Usa \: para el carácter ':' o la versión fullwidth '：'.
4. Formato: Usa [markdown] después del título en GIFT.
5. Validación: Ejecuta siempre 'validate-questions <file> --tags --title --markdown' antes de terminar.
"""

def main():
    parser = argparse.ArgumentParser(description="Validador de archivos GIFT y XML para Moodle.")
    parser.add_argument("paths", nargs='*', help="Archivos o directorios a validar.")
    parser.add_argument("--tags", action="store_true", help="Validar presencia de etiquetas.")
    parser.add_argument("--title", action="store_true", help="Validar presencia de título.")
    parser.add_argument("--markdown", action="store_true", help="Validar que el formato sea markdown.")
    parser.add_argument("-r", "--recursive", action="store_true", help="Buscar archivos recursivamente en directorios.")
    parser.add_argument("--manual", action="store_true", help="Muestra el manual completo.")
    parser.add_argument("--llm", action="store_true", help="Muestra instrucciones para LLMs.")
    
    args = parser.parse_args()

    if args.manual:
        print(MANUAL_TEXT)
        return
    if args.llm:
        print(LLM_INSTRUCTIONS)
        return
    
    if not args.paths:
        parser.print_help()
        return

    validator = QuestionValidator(
        check_tags=args.tags,
        check_title=args.title,
        check_markdown=args.markdown
    )
    
    files = []
    for p in args.paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            pattern = "**/*" if args.recursive else "*"
            files.extend([f for f in path.glob(pattern) if f.suffix.lower() in ('.gift', '.xml')])
    
    if not files:
        print("No se encontraron archivos para validar.")
        return

    print(f"Validando {len(files)} archivos...")
    print("-" * 70)
    
    error_count = 0
    total_files_with_errors = 0
    for f in sorted(files):
        report = validator.validate(f)
        # Use simple format without truncation
        status_line = f"{f} [{report['type']}] -> {report['status']}"
        print(status_line)
        if report['errors']:
            for err in report['errors']:
                print(f"  └── ❌ {err}")
            total_files_with_errors += 1
            error_count += len(report['errors'])
            
    print("-" * 70)
    print(f"Resumen: {len(files)} archivos procesados, {total_files_with_errors} con errores ({error_count} fallos detectados).")
    
    if total_files_with_errors > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
