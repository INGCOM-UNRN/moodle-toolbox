#!/usr/bin/env python3
"""
Herramienta para verificar recursivamente un directorio de preguntas GIFT.
Genera un informe detallado con estadísticas, problemas detectados y recomendaciones.
"""

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from questions.core.parser import parse_gift_file, get_question_summary


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


class GiftAnalyzer:
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
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for comparison."""
        text = text.lower()
        # Mantener letras, números y espacios
        text = re.sub(r'[^a-záéíóúñü0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _tokenize(self, text: str) -> list:
        """Tokenize text into words, keeping all tokens."""
        words = text.split()
        # Mantener todas las palabras/tokens, incluyendo números
        return [w for w in words if w]
    
    def _compute_word_freq(self, text: str) -> dict:
        """Compute word frequency."""
        words = self._tokenize(text)
        freq = defaultdict(int)
        for word in words:
            freq[word] += 1
        return dict(freq)
    
    def _compute_idf(self, all_texts: list) -> dict:
        """Compute IDF (inverse document frequency)."""
        doc_count = defaultdict(int)
        num_docs = len(all_texts)
        
        for text in all_texts:
            words = set(self._tokenize(text))
            for word in words:
                doc_count[word] += 1
        
        idf = {}
        for word, count in doc_count.items():
            idf[word] = math.log(num_docs / (1 + count))
        
        return idf
    
    def _compute_tfidf_vector(self, text: str, idf: dict) -> dict:
        """Compute TF-IDF vector."""
        freq = self._compute_word_freq(text)
        total_words = sum(freq.values())
        
        if total_words == 0:
            return {}
        
        tfidf = {}
        for word, count in freq.items():
            tf = count / total_words
            tfidf[word] = tf * idf.get(word, 0)
        
        return tfidf
    
    def _cosine_similarity(self, vec1: dict, vec2: dict) -> float:
        """Compute cosine similarity."""
        if not vec1 or not vec2:
            return 0.0
        
        # Unión de todas las palabras
        all_words = set(vec1.keys()) | set(vec2.keys())
        
        if not all_words:
            return 0.0
        
        # Calcular producto punto y magnitudes considerando todas las palabras
        dot_product = sum(vec1.get(word, 0) * vec2.get(word, 0) for word in all_words)
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two texts."""
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _combined_similarity(self, q1: dict, q2: dict) -> float:
        """Compute combined similarity using multiple metrics."""
        # Similitud de coseno TF-IDF
        cosine_sim = self._cosine_similarity(q1["vector"], q2["vector"])
        
        # Similitud Jaccard (más sensible a diferencias en palabras individuales)
        jaccard_sim = self._jaccard_similarity(q1["clean_text"], q2["clean_text"])
        
        # Combinar: promedio ponderado (Jaccard es más estricto)
        combined = (cosine_sim * 0.4) + (jaccard_sim * 0.6)
        
        return combined
    
    def find_duplicates(self):
        """Find duplicate or very similar questions."""
        self.duplicates = []
        if len(self.all_questions) < 2:
            return
        
        if self.verbose:
            print(f"Buscando duplicados con threshold {self.similarity_threshold}...")
        
        # Prepare texts
        for q in self.all_questions:
            q["clean_text"] = self._clean_text(q["full_text"])
        
        # Compute IDF
        all_texts = [q["clean_text"] for q in self.all_questions]
        idf = self._compute_idf(all_texts)
        
        # Compute TF-IDF vectors
        for q in self.all_questions:
            q["vector"] = self._compute_tfidf_vector(q["clean_text"], idf)
        
        # Compare questions
        for i in range(len(self.all_questions)):
            for j in range(i + 1, len(self.all_questions)):
                # Usar similitud combinada (TF-IDF coseno + Jaccard)
                similarity = self._combined_similarity(
                    self.all_questions[i],
                    self.all_questions[j]
                )
                
                if similarity >= self.similarity_threshold:
                    self.duplicates.append({
                        "index1": i,
                        "index2": j,
                        "similarity": similarity
                    })
        
        # Sort by similarity
        self.duplicates.sort(key=lambda x: x["similarity"], reverse=True)
    
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
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate the analysis report."""
        lines = []
        
        lines.append("=" * 80)
        lines.append("INFORME DE EVALUACIÓN DE PREGUNTAS GIFT")
        lines.append("=" * 80)
        lines.append("")
        
        # General summary
        lines.append("📊 RESUMEN GENERAL")
        lines.append("-" * 80)
        lines.append(f"Total de archivos GIFT: {self.stats.total_files}")
        lines.append(f"  ✅ Archivos válidos: {self.stats.valid_files}")
        lines.append(f"  ❌ Archivos inválidos: {self.stats.invalid_files}")
        lines.append(f"Total de preguntas: {self.stats.total_questions}")
        lines.append("")
        
        # Question types
        lines.append("📝 TIPOS DE PREGUNTAS")
        lines.append("-" * 80)
        if self.stats.by_type:
            for q_type, count in self.stats.by_type.most_common():
                percentage = (count / self.stats.total_questions * 100) if self.stats.total_questions > 0 else 0
                lines.append(f"  {q_type:20s}: {count:5d} ({percentage:5.1f}%)")
        else:
            lines.append("  No hay preguntas")
        lines.append("")
        
        # Categories
        lines.append("📂 CATEGORÍAS")
        lines.append("-" * 80)
        if self.stats.by_category:
            for category, count in self.stats.by_category.most_common():
                lines.append(f"  {category[:60]:60s}: {count:4d}")
        else:
            lines.append("  No se encontraron categorías")
        lines.append("")
        
        # Tags
        lines.append("🏷️  TAGS MÁS COMUNES")
        lines.append("-" * 80)
        if self.stats.by_tag:
            for tag, count in self.stats.by_tag.most_common():
                lines.append(f"  {tag:30s}: {count:4d}")
        else:
            lines.append("  No se encontraron tags")
        lines.append("")
        
        # Content quality
        lines.append("✨ CALIDAD DE CONTENIDO")
        lines.append("-" * 80)
        lines.append(f"Preguntas con tags: {self.stats.with_tags}")
        lines.append(f"Preguntas sin tags: {self.stats.without_tags}")
        lines.append(f"Preguntas con feedback global: {self.stats.with_feedback}")
        lines.append(f"Preguntas sin feedback global: {self.stats.without_feedback}")
        lines.append(f"Preguntas vacías: {self.stats.empty_questions}")
        lines.append("")
        
        # Distribution by depth
        lines.append("📁 DISTRIBUCIÓN POR PROFUNDIDAD DE DIRECTORIOS")
        lines.append("-" * 80)
        if self.stats.files_by_depth:
            for depth in sorted(self.stats.files_by_depth.keys()):
                count = self.stats.files_by_depth[depth]
                lines.append(f"  Nivel {depth}: {count} archivos")
        lines.append("")
        
        # Detected issues
        if self.issues:
            lines.append("⚠️  PROBLEMAS DETECTADOS")
            lines.append("-" * 80)
            lines.append(f"Total de problemas: {len(self.issues)}")
            lines.append("")
            for issue in self.issues:
                lines.append(f"  {issue}")
            lines.append("")
        
        # Parse errors
        if self.stats.parse_errors:
            lines.append("❌ ERRORES DE PARSEO GIFT")
            lines.append("-" * 80)
            for error_info in self.stats.parse_errors:
                lines.append(f"  {error_info['filepath']}")
                lines.append(f"    Error: {error_info['error']['message']}")
            lines.append("")
        
        # Description questions (possible issues)
        if self.descriptions:
            lines.append("📄 PREGUNTAS TIPO DESCRIPTION (posibles problemas)")
            lines.append("-" * 80)
            lines.append(f"Total: {len(self.descriptions)}")
            lines.append("Nota: Las preguntas tipo 'Description' no tienen respuestas.")
            lines.append("      Esto puede indicar un error en el formato de la pregunta.")
            lines.append("")
            for desc in self.descriptions:
                lines.append(f"  📄 {desc['filepath']}")
                lines.append(f"     Título: {desc['title']}")
                if desc['text'] and desc['text'] != "<sin texto>":
                    text_preview = desc['text'].replace('\n', ' ')[:80]
                    lines.append(f"     Texto: {text_preview}...")
                lines.append("")
        
        # Duplicates
        if self.duplicates:
            lines.append("🔄 PREGUNTAS DUPLICADAS O MUY SIMILARES")
            lines.append("-" * 80)
            lines.append(f"Total de duplicados encontrados: {len(self.duplicates)}")
            lines.append(f"Threshold de similitud: {self.similarity_threshold}")
            lines.append("")
            
            for idx, dup in enumerate(self.duplicates, 1):
                q1 = self.all_questions[dup["index1"]]
                q2 = self.all_questions[dup["index2"]]
                
                lines.append(f"Duplicado {idx}: Similitud = {dup['similarity']:.3f}")
                lines.append(f"  Pregunta A ({q1['type']}): {q1['title'][:70]}")
                lines.append(f"    Archivo: {q1['filepath']}")
                lines.append(f"  Pregunta B ({q2['type']}): {q2['title'][:70]}")
                lines.append(f"    Archivo: {q2['filepath']}")
                lines.append(f"  Comando: meld -n '{q1['filepath']}' '{q2['filepath']}'")
                lines.append("")
        
        # Recommendations
        lines.append("💡 RECOMENDACIONES")
        lines.append("-" * 80)
        
        if self.stats.without_tags > 0:
            percentage = (self.stats.without_tags / self.stats.total_questions * 100) if self.stats.total_questions > 0 else 0
            lines.append(f"  • {percentage:.1f}% de preguntas sin tags - considera añadir tags para mejor organización")
        
        if self.stats.without_feedback > 0:
            percentage = (self.stats.without_feedback / self.stats.total_questions * 100) if self.stats.total_questions > 0 else 0
            lines.append(f"  • {percentage:.1f}% de preguntas sin feedback global - el feedback ayuda al aprendizaje")
        
        if self.stats.empty_questions > 0:
            lines.append(f"  • {self.stats.empty_questions} preguntas vacías detectadas - requieren revisión")
        
        if self.stats.invalid_files > 0:
            lines.append(f"  • {self.stats.invalid_files} archivos con errores - necesitan corrección")
        
        if self.duplicates:
            lines.append(f"  • {len(self.duplicates)} preguntas duplicadas detectadas - considera revisar para eliminar redundancias")
        
        if not self.issues and not self.stats.parse_errors and not self.duplicates:
            lines.append("  • ¡Todo se ve bien! No se detectaron problemas significativos")
        
        lines.append("")
        lines.append("=" * 80)
        
        report = "\n".join(lines)
        
        if output_file:
            Path(output_file).write_text(report, encoding='utf-8')
            print(f"\n✅ Informe guardado en: {output_file}")
        
        return report
    
    def to_json(self) -> dict:
        """Convert analysis results to JSON-serializable dict."""
        return {
            "stats": {
                "totalFiles": self.stats.total_files,
                "validFiles": self.stats.valid_files,
                "invalidFiles": self.stats.invalid_files,
                "totalQuestions": self.stats.total_questions,
                "byType": dict(self.stats.by_type),
                "byCategory": dict(self.stats.by_category),
                "withTags": self.stats.with_tags,
                "withoutTags": self.stats.without_tags,
                "byTag": dict(self.stats.by_tag),
                "withFeedback": self.stats.with_feedback,
                "withoutFeedback": self.stats.without_feedback,
                "emptyQuestions": self.stats.empty_questions,
                "parseErrors": self.stats.parse_errors,
                "filesByDepth": dict(self.stats.files_by_depth)
            },
            "issues": self.issues,
            "duplicates": [
                {
                    "similarity": d["similarity"],
                    "question1": {
                        "filepath": self.all_questions[d["index1"]]["filepath"],
                        "title": self.all_questions[d["index1"]]["title"],
                        "type": self.all_questions[d["index1"]]["type"]
                    },
                    "question2": {
                        "filepath": self.all_questions[d["index2"]]["filepath"],
                        "title": self.all_questions[d["index2"]]["title"],
                        "type": self.all_questions[d["index2"]]["type"]
                    }
                }
                for d in self.duplicates
            ],
            "descriptions": self.descriptions
        }


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
