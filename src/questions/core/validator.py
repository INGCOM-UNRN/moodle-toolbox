#!/usr/bin/env python3
"""
Herramienta para verificar recursivamente un directorio de preguntas GIFT.
Genera un informe detallado con estadísticas, problemas detectados y recomendaciones.
"""

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path


from questions.core.parser import parse_gift_file
from questions.core.validator_informe import InformeMixin
from questions.core.validator_similitud import SimilitudMixin


@dataclass
class GiftStats:
    """Statistics for GIFT analysis."""
    total_files: int = 0
    valid_files: int = 0
    invalid_files: int = 0
    total_questions: int = 0
    by_type: Counter = field(default_factory=Counter)
    by_category: Counter = field(default_factory=Counter)
    with_tags: int = 0
    without_tags: int = 0
    by_tag: Counter = field(default_factory=Counter)
    with_feedback: int = 0
    without_feedback: int = 0
    empty_questions: int = 0
    parse_errors: list = field(default_factory=list)
    files_by_depth: Counter = field(default_factory=Counter)


class GiftAnalyzer(SimilitudMixin, InformeMixin):
    """Analyzer for GIFT question directories."""
    
    def __init__(self, similarity_threshold: float = 0.85, recursive: bool = True, verbose: bool = False):
        self.similarity_threshold = similarity_threshold
        self.recursive = recursive
        self.verbose = verbose
        
        self.stats = GiftStats()
        self.categories: dict = defaultdict(list)
        self.issues: list = []
        self.all_questions: list = []
        self.duplicates: list = []
        self.descriptions: list = []  # Preguntas tipo Description (posibles problemas)
        self.base_path: Path = Path('.')
    
    def find_gift_files(self, directory: Path) -> list:
        """Find all .gift files in directory."""
        if self.recursive:
            return list(directory.rglob('*.gift'))
        return list(directory.glob('*.gift'))
    
    def analyze_file(self, filepath: Path):
        """Analyze a single GIFT file."""
        self.stats.total_files += 1
        
        # Calculate depth
        try:
            rel_path = filepath.relative_to(self.base_path)
            depth = len(rel_path.parts) - 1
        except ValueError:
            depth = 0
        self.stats.files_by_depth[depth] += 1
        
        result = parse_gift_file(str(filepath))
        
        if not result["success"]:
            self.stats.invalid_files += 1
            self.stats.parse_errors.append({
                "filepath": str(filepath),
                "error": result["error"]
            })
            self.issues.append(f"❌ {filepath}: Error de parseo - {result['error']['message']}")
            if result["error"].get("location"):
                loc = result["error"]["location"]
                self.issues.append(f"   Línea: {loc.get('line', '?')}, Columna: {loc.get('column', '?')}")
            return
        
        self.stats.valid_files += 1
        
        if not result["questions"]:
            self.issues.append(f"⚠️  {filepath}: No contiene preguntas")
        
        for question in result["questions"]:
            self.analyze_question(question, filepath)
    
    def analyze_question(self, question: dict, filepath: Path):
        """Analyze a single question."""
        q_type = question.get("type", "Unknown")
        
        # Handle categories
        if q_type == "Category":
            category = question.get("title", "Sin categoría")
            self.stats.by_category[category] += 1
            self.categories[category].append(str(filepath))
            return
        
        # Handle descriptions
        if q_type == "Description":
            self.stats.total_questions += 1
            self.stats.by_type[q_type] += 1
            title = question.get("title", "")
            stem = question.get("stem", {})
            stem_text = stem.get("text", "") if isinstance(stem, dict) else ""
            self.descriptions.append({
                "filepath": str(filepath),
                "title": title or "<sin título>",
                "text": stem_text[:100] if stem_text else "<sin texto>"
            })
            return
        
        self.stats.total_questions += 1
        self.stats.by_type[q_type] += 1
        
        # Analyze title and content
        title = question.get("title", "")
        stem = question.get("stem", {})
        stem_text = stem.get("text", "") if isinstance(stem, dict) else ""
        
        if not title and not stem_text:
            self.stats.empty_questions += 1
            self.issues.append(f"⚠️  {filepath}: Pregunta sin título ni texto")
        
        # Analyze feedback
        if question.get("globalFeedback"):
            self.stats.with_feedback += 1
        else:
            self.stats.without_feedback += 1
        
        # Analyze tags
        tags = question.get("tags", [])
        if tags:
            self.stats.with_tags += 1
            for tag in tags:
                self.stats.by_tag[tag] += 1
        else:
            self.stats.without_tags += 1
        
        # Type-specific validations
        self._validate_by_type(question, filepath)
        
        # Store for duplicate analysis
        answer_texts = self._extract_answer_texts(question)
        self.all_questions.append({
            "filepath": str(filepath),
            "type": q_type,
            "title": title,
            "text": stem_text,
            "answers": answer_texts,
            "full_text": f"{title} {stem_text} {' '.join(answer_texts)}"
        })
    
    def _extract_answer_texts(self, question: dict) -> list:
        """Extract answer texts from question."""
        texts = []
        
        for choice in question.get("choices", []):
            text = choice.get("text", {})
            if isinstance(text, dict):
                texts.append(text.get("text", ""))
            elif isinstance(text, str):
                texts.append(text)
        
        for pair in question.get("matchPairs", []):
            subq = pair.get("subquestion", {})
            if isinstance(subq, dict):
                texts.append(subq.get("text", ""))
            texts.append(pair.get("subanswer", ""))
        
        return texts
    
    def _validate_by_type(self, question: dict, filepath: Path):
        """Type-specific validations."""
        title = question.get("title", "<sin título>")[:50]
        q_type = question.get("type")
        
        if q_type == "MC":
            choices = question.get("choices", [])
            correct_count = sum(1 for c in choices if c.get("is_correct"))
            total_weight = sum(
                c.get("weight", 100 if c.get("is_correct") else 0)
                for c in choices
                if c.get("is_correct") or (c.get("weight") and c.get("weight") > 0)
            )
            
            if correct_count == 0 and total_weight < 95:
                self.issues.append(f"⚠️  {filepath}: Pregunta MC sin respuesta correcta - {title}")
        
        elif q_type == "Matching":
            pairs = question.get("matchPairs", [])
            if len(pairs) < 2:
                self.issues.append(f"⚠️  {filepath}: Pregunta Matching con menos de 2 pares - {title}")
        
        elif q_type == "Short":
            choices = question.get("choices", [])
            if not choices:
                self.issues.append(f"⚠️  {filepath}: Pregunta Short sin respuestas - {title}")

    def scan_directory(self, directory: str):
        """Scan a directory for GIFT files."""
        self.base_path = Path(directory)
        
        gift_files = self.find_gift_files(self.base_path)
        
        if not gift_files:
            print(f"⚠️  No se encontraron archivos .gift en {directory}")
            return
        
        print(f"Escaneando {len(gift_files)} archivos GIFT...")
        
        for i, filepath in enumerate(gift_files, 1):
            if self.verbose and i % 10 == 0:
                print(f"  Procesados {i}/{len(gift_files)} archivos...")
            self.analyze_file(filepath)
        
        self.find_duplicates()


def main():
    parser = argparse.ArgumentParser(
        description='Verifica recursivamente un directorio de preguntas GIFT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s preguntas/
  %(prog)s preguntas/ -o informe.txt
  %(prog)s preguntas/ --no-recursive -v
  %(prog)s preguntas/ -s 0.9 --json
        """
    )
    
    parser.add_argument('directory', nargs='?', help='Directorio a analizar')
    parser.add_argument('-o', '--output', help='Archivo de salida para el informe')
    parser.add_argument('-r', '--no-recursive', action='store_true',
                        help='No buscar recursivamente en subdirectorios')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Mostrar información detallada durante el análisis')
    parser.add_argument('-s', '--similarity', type=float, default=0.85,
                        help='Threshold de similitud para duplicados (0.0-1.0, default: 0.85)')
    parser.add_argument('-j', '--json', action='store_true', help='Salida en formato JSON')
    
    args = parser.parse_args()
    
    if not args.directory:
        parser.print_help()
        return 1
    
    directory = Path(args.directory)
    
    if not directory.is_dir():
        print(f"❌ Error: '{args.directory}' no es un directorio válido")
        return 1
    
    if not 0.0 <= args.similarity <= 1.0:
        print("❌ Error: El threshold debe estar entre 0.0 y 1.0")
        return 1
    
    if not args.json:
        print(f"Analizando directorio: {args.directory}")
        print(f"Modo recursivo: {'No' if args.no_recursive else 'Sí'}")
        print(f"Threshold de similitud: {args.similarity}")
        print("=" * 80)
        print()
    
    analyzer = GiftAnalyzer(
        similarity_threshold=args.similarity,
        recursive=not args.no_recursive,
        verbose=args.verbose
    )
    
    try:
        analyzer.scan_directory(args.directory)
        
        if not args.json:
            print()
            print("Generando informe...")
            print()
        
        if args.json:
            print(json.dumps(analyzer.to_json(), indent=2, ensure_ascii=False))
        else:
            report = analyzer.generate_report(args.output)
            if not args.output:
                print(report)
            else:
                print(report)
    
    except KeyboardInterrupt:
        print("\n⚠️  Análisis interrumpido por el usuario")
        return 1
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
