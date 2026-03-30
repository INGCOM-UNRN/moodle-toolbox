#!/usr/bin/env python3
import argparse
import sys
import re
from pathlib import Path
import tatsu
import json
from typing import Dict, Any, List, Optional

# Gramática PEG optimizada para validación estricta
GIFT_PEG_GRAMMAR = r'''
@@grammar::GIFT
@@whitespace :: //

start = { item }+ $ ;

item = category | question_with_answers | description ;

category = __ '$CATEGORY:' ~ cat:/[^\n\r]+/ eol { blank_line }* ;

description = __ { tag_comment }* [ title ] stem:rich_text { blank_line }+ ;

question_with_answers = __ { tag_comment }* [ title ] stem1:[ question_stem ] _ '{' _ answers:answers _ '}' _ stem2:[ question_stem ] { blank_line }* ;

title = '::' ~ @:/[^:]+(?::(?!:)[^:]*)*/ '::' ;

tag_comment = '//' ~ @:/[^\n\r]*/ eol ;

question_stem = rich_text ;

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

rich_text = [ format ] text_content ;
format = '[' @/html|markdown|plain|moodle/ ']' ;
text_content = { text_char }+ ;
text_char = escape_sequence | /[^\n\r{}=~#\\]/ | /(?=#(?!#))/ ;

plain_text = { /[^\n\r{}=~#\\]/ | escape_sequence }+ ;

escape_sequence = /\\[:\\#={}~n\\]/ ;

_ = /[ \t\r\n]*/ ;
__ = { /[ \t\n\r]/ | tag_comment_skip }* ;
tag_comment_skip = '//' /[^\n\r]*/ eol ;
eol = /\r\n|\n|\r/ ;
blank_line = /[ \t]*/ eol ;
'''

class GiftValidator:
    def __init__(self):
        self.parser = tatsu.compile(GIFT_PEG_GRAMMAR)

    def get_answers_count(self, node: Any) -> int:
        if not node or not hasattr(node, 'answers'): return 0
        ans = node.answers
        if not ans: return 0
        
        if hasattr(ans, 'choice') and ans.choice: return len(ans.choice)
        if hasattr(ans, 'match') and ans.match: return len(ans.match)
        if hasattr(ans, 'numerical_choice') and ans.numerical_choice: return len(ans.numerical_choice)
        if hasattr(ans, 'true_false') and ans.true_false: return 1
        if hasattr(ans, 'single_numerical') and ans.single_numerical: return 1
        if hasattr(ans, 'text') and ans.text: return 1
        return 0

    def get_question_type(self, node: Any) -> str:
        if hasattr(node, 'answers') and node.answers:
            ans = node.answers
            if hasattr(ans, 'choice'): return "MC"
            if hasattr(ans, 'match'): return "Matching"
            if hasattr(ans, 'true_false'): return "TF"
            if hasattr(ans, 'numerical_choice') or hasattr(ans, 'single_numerical'): return "Numerical"
            if hasattr(ans, 'text'): return "Short"
            return "Essay"
        if hasattr(node, 'cat'): return "Category"
        if hasattr(node, 'stem'): return "Description"
        return "Unknown"

    def validate_file(self, filepath: Path, expected_answers: Optional[int] = None) -> Dict[str, Any]:
        report = {
            "file": str(filepath),
            "status": "OK",
            "errors": [],
            "answers_found": 0,
            "type": "Unknown"
        }
        
        try:
            content = filepath.read_text(encoding='utf-8').strip()
            if not content:
                report["status"] = "EMPTY"
                return report

            ast = self.parser.parse(content)
            items = [item for item in ast if hasattr(item, 'answers') or hasattr(item, 'stem') or hasattr(item, 'cat')]
            
            if not items:
                report["status"] = "EMPTY"
                return report

            # Analizar el primer elemento relevante (asumiendo 1 pregunta por archivo)
            main_item = items[0]
            report["type"] = self.get_question_type(main_item)
            report["answers_found"] = self.get_answers_count(main_item)
            
            if len(items) > 1:
                report["errors"].append(f"Se encontraron {len(items)} elementos, se esperaba 1.")
                report["status"] = "WARNING"

            if expected_answers is not None and report["answers_found"] != expected_answers:
                report["errors"].append(f"Número de respuestas incorrecto: detectadas {report['answers_found']}, esperadas {expected_answers}.")
                report["status"] = "ERROR"

        except tatsu.exceptions.ParseException as e:
            report["status"] = "SYNTAX_ERROR"
            err_msg = str(e)
            match = re.search(r"\((\d+):(\d+)\)", err_msg)
            if match:
                line = match.group(1)
                col = match.group(2)
            else:
                line = getattr(e, 'line', getattr(e, 'lineno', '?'))
                col = getattr(e, 'column', getattr(e, 'col', '?'))
            report["errors"].append(f"Error de sintaxis (L{line}, C{col}): {err_msg}")
        except Exception as e:
            report["status"] = "CRITICAL_ERROR"
            report["errors"].append(f"Error inesperado ({type(e).__name__}): {str(e)}")
            
        return report

def main():
    parser = argparse.ArgumentParser(description="Verificador de preguntas GIFT usando gramática PEG.")
    parser.add_argument("paths", nargs='+', help="Directorios o archivos a verificar.")
    parser.add_argument("-r", "--recursive", action="store_true", help="Procesar subdirectorios recursivamente.")
    parser.add_argument("-a", "--answers", type=int, help="Número total de respuestas esperado por pregunta.")
    parser.add_argument("-j", "--json", action="store_true", help="Salida en formato JSON.")
    parser.add_argument("-e", "--errors-list", action="store_true", help="Salida sucinta de archivos con errores (ruta:linea:columna).")
    
    args = parser.parse_args()
    
    all_files = []
    for p in args.paths:
        path = Path(p)
        if not path.exists():
            print(f"Error: La ruta {path} no existe.")
            continue

        if path.is_file():
            all_files.append(path)
        else:
            pattern = "**/*.gift" if args.recursive else "*.gift"
            all_files.extend(list(path.glob(pattern)))

    all_files = sorted(list(set(all_files)))

    validator = GiftValidator()
    results = []
    
    for f in all_files:
        results.append(validator.validate_file(f, args.answers))

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.errors_list:
        for r in results:
            if r["status"] in ["ERROR", "SYNTAX_ERROR", "CRITICAL_ERROR"]:
                for err in r["errors"]:
                    match = re.search(r"\(L([0-9\?]+), C([0-9\?]+)\)", err)
                    abs_path = Path(r['file']).resolve()
                    if match and match.group(1) != '?':
                        print(f"{abs_path}:{match.group(1)}:{match.group(2)}")
                    else:
                        print(f"{abs_path}")
    else:
        print(f"\n{'ARCHIVO':<50} | {'TIPO':<12} | {'RESP.'} | {'ESTADO'}")
        print("-" * 85)
        for r in results:
            print(f"{str(r['file'])[:50]:<50} | {str(r['type']):<12} | {r['answers_found']:<5} | {r['status']}")
            for err in r["errors"]:
                print(f"  └── ❌ {err}")
                match = re.search(r"\(L([0-9\?]+), C([0-9\?]+)\)", err)
                abs_path = Path(r['file']).resolve()
                if match and match.group(1) != '?':
                    print(f"      📍 {abs_path}:{match.group(1)}:{match.group(2)}")
                else:
                    print(f"      📍 {abs_path}")
        
        total = len(results)
        errors = sum(1 for r in results if r["status"] in ["ERROR", "SYNTAX_ERROR", "CRITICAL_ERROR"])
        print(f"\nResumen: {total} archivos procesados, {errors} con errores.\n")

if __name__ == "__main__":
    main()
