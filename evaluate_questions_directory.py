#!/usr/bin/env python3
"""
Script para recorrer un directorio de preguntas XML y generar un informe de evaluación.
Analiza estructura, tipos de preguntas, estadísticas y posibles problemas.
"""

import xml.etree.ElementTree as ET
import argparse
import os
from collections import defaultdict, Counter
from pathlib import Path
import re


class QuestionAnalyzer:
    def __init__(self, similarity_threshold=0.85):
        self.stats = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'total_questions': 0,
            'by_type': Counter(),
            'by_category': Counter(),
            'with_tags': 0,
            'without_tags': 0,
            'by_tag': Counter(),
            'with_feedback': 0,
            'without_feedback': 0,
            'empty_questions': 0,
            'parse_errors': [],
            'xml_validation_errors': [],
            'files_by_depth': defaultdict(int),
            'avg_answers_per_question': [],
            'question_lengths': [],
            'html_format_questions': [],
        }
        self.categories = defaultdict(list)
        self.issues = []
        self.similarity_threshold = similarity_threshold
        self.all_questions = []
        self.duplicates = []
        
    def extract_text(self, elem):
        """Extrae texto de un elemento XML."""
        if elem is None:
            return ""
        text = elem.text or ""
        return text.strip()
    
    def validate_xml_structure(self, filepath, root):
        """Valida la estructura del XML."""
        validation_errors = []
        
        # Verificar estructura básica de quiz
        if root.tag != 'quiz':
            validation_errors.append("El elemento raíz debe ser 'quiz'")
            return validation_errors
        
        questions = root.findall('question')
        for idx, question in enumerate(questions, 1):
            q_type = question.get('type')
            
            if not q_type:
                validation_errors.append(f"Pregunta {idx}: Falta atributo 'type'")
                continue
            
            # Validar según tipo de pregunta
            if q_type == 'category':
                category = question.find('.//category/text')
                if category is None:
                    validation_errors.append(f"Pregunta {idx}: Categoría sin texto")
            
            elif q_type != 'description':
                # Todas las preguntas (excepto description) deben tener nombre
                name = question.find('.//name/text')
                if name is None or not name.text or not name.text.strip():
                    validation_errors.append(f"Pregunta {idx} (tipo: {q_type}): Falta nombre")
                
                # Deben tener texto de pregunta
                questiontext = question.find('.//questiontext/text')
                if questiontext is None or not questiontext.text or not questiontext.text.strip():
                    validation_errors.append(f"Pregunta {idx} (tipo: {q_type}): Falta texto de pregunta")
                
                # Validar respuestas según tipo
                if q_type in ['multichoice', 'truefalse', 'matching', 'shortanswer']:
                    answers = question.findall('.//answer')
                    if not answers:
                        validation_errors.append(f"Pregunta {idx} (tipo: {q_type}): Sin respuestas")
        
        return validation_errors
    
    def analyze_file(self, filepath):
        """Analiza un archivo XML de preguntas."""
        self.stats['total_files'] += 1
        
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            if root.tag != 'quiz':
                self.issues.append(f"⚠️  {filepath}: No es un archivo quiz válido")
                self.stats['invalid_files'] += 1
                return
            
            # Validar estructura XML
            validation_errors = self.validate_xml_structure(filepath, root)
            if validation_errors:
                self.stats['xml_validation_errors'].append((filepath, validation_errors))
                for error in validation_errors:
                    self.issues.append(f"⚠️  {filepath}: {error}")
            
            self.stats['valid_files'] += 1
            depth = len(Path(filepath).parts) - len(Path(self.base_path).parts)
            self.stats['files_by_depth'][depth] += 1
            
            questions = root.findall('question')
            if not questions:
                self.issues.append(f"⚠️  {filepath}: No contiene preguntas")
            
            for question in questions:
                self.analyze_question(question, filepath)
                
        except ET.ParseError as e:
            self.stats['invalid_files'] += 1
            self.stats['parse_errors'].append((filepath, str(e)))
            self.issues.append(f"❌ {filepath}: Error de parseo XML - {e}")
        except Exception as e:
            self.stats['invalid_files'] += 1
            self.issues.append(f"❌ {filepath}: Error inesperado - {e}")
    
    def analyze_question(self, question, filepath):
        """Analiza una pregunta individual."""
        q_type = question.get('type', 'unknown')
        
        if q_type == 'category':
            category_elem = question.find('.//category/text')
            if category_elem is not None:
                category = self.extract_text(category_elem)
                self.stats['by_category'][category] += 1
                self.categories[category].append(filepath)
            return
        
        self.stats['total_questions'] += 1
        self.stats['by_type'][q_type] += 1
        
        # Analizar nombre y texto
        name_elem = question.find('.//name/text')
        text_elem = question.find('.//questiontext/text')
        
        name = self.extract_text(name_elem)
        text = self.extract_text(text_elem)
        
        if not name and not text:
            self.stats['empty_questions'] += 1
            self.issues.append(f"⚠️  {filepath}: Pregunta sin nombre ni texto")
        
        question_length = len(name) + len(text)
        self.stats['question_lengths'].append(question_length)
        
        # Detectar formato HTML en questiontext
        questiontext_elem = question.find('.//questiontext')
        if questiontext_elem is not None and questiontext_elem.get('format') == 'html':
            self.stats['html_format_questions'].append({
                'file': filepath,
                'name': name,
                'type': q_type
            })
        
        # Analizar respuestas
        answers = question.findall('.//answer')
        if answers:
            self.stats['avg_answers_per_question'].append(len(answers))
            
            # Verificar respuesta correcta en multichoice
            if q_type == 'multichoice':
                # Calcular suma de fracciones positivas
                total_fraction = 0.0
                for ans in answers:
                    try:
                        fraction = float(ans.get('fraction', '0'))
                        if fraction > 0:
                            total_fraction += fraction
                    except ValueError:
                        pass
                
                # Considerar correcto si suma al menos 95% (tolerancia para redondeo)
                if total_fraction < 95.0:
                    self.issues.append(f"⚠️  {filepath}: Pregunta multichoice sin respuesta correcta (suma: {total_fraction:.1f}%) - {name[:50]}")
        
        # Analizar feedback
        feedback_elems = question.findall('.//feedback')
        if feedback_elems and any(self.extract_text(f.find('text')) for f in feedback_elems):
            self.stats['with_feedback'] += 1
        else:
            self.stats['without_feedback'] += 1
        
        # Analizar tags
        tags = question.findall('.//tag/text')
        if tags:
            self.stats['with_tags'] += 1
            for tag in tags:
                tag_text = self.extract_text(tag)
                if tag_text:
                    self.stats['by_tag'][tag_text] += 1
        else:
            self.stats['without_tags'] += 1
        
        # Guardar pregunta para análisis de duplicados
        answer_texts = [self.extract_text(ans.find('text')) for ans in answers if ans.find('text') is not None]
        self.all_questions.append({
            'filepath': filepath,
            'type': q_type,
            'name': name,
            'text': text,
            'answers': answer_texts,
            'full_text': f"{name} {text} {' '.join(answer_texts)}"
        })
    
    def scan_directory(self, directory, recursive=True):
        """Escanea un directorio en busca de archivos XML."""
        self.base_path = directory
        
        if recursive:
            pattern = "**/*.xml"
        else:
            pattern = "*.xml"
        
        xml_files = list(Path(directory).glob(pattern))
        
        if not xml_files:
            print(f"⚠️  No se encontraron archivos XML en {directory}")
            return
        
        print(f"Escaneando {len(xml_files)} archivos XML...")
        
        for i, filepath in enumerate(xml_files, 1):
            if i % 100 == 0:
                print(f"  Procesados {i}/{len(xml_files)} archivos...")
            self.analyze_file(str(filepath))
        
        print(f"\nBuscando duplicados con threshold {self.similarity_threshold}...")
        self.find_duplicates()
    
    def clean_text(self, text):
        """Limpia y normaliza el texto para comparación."""
        text = text.lower()
        text = re.sub(r'[^a-záéíóúñü0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def compute_word_freq(self, text):
        """Calcula frecuencia de palabras."""
        words = text.split()
        freq = defaultdict(int)
        for word in words:
            if len(word) > 2:
                freq[word] += 1
        return freq
    
    def compute_idf(self, all_texts):
        """Calcula IDF (inverse document frequency)."""
        import math
        doc_count = defaultdict(int)
        num_docs = len(all_texts)
        
        for text in all_texts:
            words = set(text.split())
            for word in words:
                if len(word) > 2:
                    doc_count[word] += 1
        
        idf = {}
        for word, count in doc_count.items():
            idf[word] = math.log(num_docs / (1 + count))
        
        return idf
    
    def compute_tfidf_vector(self, text, idf):
        """Calcula vector TF-IDF."""
        freq = self.compute_word_freq(text)
        total_words = sum(freq.values())
        
        if total_words == 0:
            return {}
        
        tfidf = {}
        for word, count in freq.items():
            tf = count / total_words
            tfidf[word] = tf * idf.get(word, 0)
        
        return tfidf
    
    def cosine_similarity(self, vec1, vec2):
        """Calcula similitud de coseno."""
        import math
        
        if not vec1 or not vec2:
            return 0.0
        
        common_words = set(vec1.keys()) & set(vec2.keys())
        
        if not common_words:
            return 0.0
        
        dot_product = sum(vec1[word] * vec2[word] for word in common_words)
        
        mag1 = math.sqrt(sum(val**2 for val in vec1.values()))
        mag2 = math.sqrt(sum(val**2 for val in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def find_duplicates(self):
        """Encuentra preguntas duplicadas o muy similares."""
        if len(self.all_questions) < 2:
            return
        
        # Preparar textos
        for q in self.all_questions:
            q['clean_text'] = self.clean_text(q['full_text'])
        
        # Calcular IDF
        all_texts = [q['clean_text'] for q in self.all_questions]
        idf = self.compute_idf(all_texts)
        
        # Calcular vectores TF-IDF
        for q in self.all_questions:
            q['vector'] = self.compute_tfidf_vector(q['clean_text'], idf)
        
        # Comparar preguntas
        for i in range(len(self.all_questions)):
            for j in range(i + 1, len(self.all_questions)):
                similarity = self.cosine_similarity(
                    self.all_questions[i]['vector'],
                    self.all_questions[j]['vector']
                )
                
                if similarity >= self.similarity_threshold:
                    self.duplicates.append((i, j, similarity))
        
        # Ordenar por similitud
        self.duplicates.sort(key=lambda x: x[2], reverse=True)
    
    def generate_report(self, output_file=None):
        """Genera el informe de evaluación."""
        lines = []
        
        lines.append("=" * 80)
        lines.append("INFORME DE EVALUACIÓN DE PREGUNTAS XML")
        lines.append("=" * 80)
        lines.append("")
        
        # Resumen general
        lines.append("📊 RESUMEN GENERAL")
        lines.append("-" * 80)
        lines.append(f"Total de archivos XML: {self.stats['total_files']}")
        lines.append(f"  ✅ Archivos válidos: {self.stats['valid_files']}")
        lines.append(f"  ❌ Archivos inválidos: {self.stats['invalid_files']}")
        lines.append(f"Total de preguntas: {self.stats['total_questions']}")
        lines.append("")
        
        # Estadísticas de preguntas
        lines.append("📝 TIPOS DE PREGUNTAS")
        lines.append("-" * 80)
        if self.stats['by_type']:
            for q_type, count in self.stats['by_type'].most_common():
                percentage = (count / self.stats['total_questions'] * 100) if self.stats['total_questions'] > 0 else 0
                lines.append(f"  {q_type:20s}: {count:5d} ({percentage:5.1f}%)")
        else:
            lines.append("  No hay preguntas")
        lines.append("")
        
        # Categorías
        lines.append("📂 CATEGORÍAS")
        lines.append("-" * 80)
        if self.stats['by_category']:
            for category, count in self.stats['by_category'].most_common(20):
                lines.append(f"  {category[:60]:60s}: {count:4d}")
            if len(self.stats['by_category']) > 20:
                lines.append(f"  ... y {len(self.stats['by_category']) - 20} categorías más")
        else:
            lines.append("  No se encontraron categorías")
        lines.append("")
        
        # Tags
        lines.append("🏷️  TAGS MÁS COMUNES")
        lines.append("-" * 80)
        if self.stats['by_tag']:
            for tag, count in self.stats['by_tag'].most_common(20):
                lines.append(f"  {tag:30s}: {count:4d}")
            if len(self.stats['by_tag']) > 20:
                lines.append(f"  ... y {len(self.stats['by_tag']) - 20} tags más")
        else:
            lines.append("  No se encontraron tags")
        lines.append("")
        
        # Estadísticas de calidad
        lines.append("✨ CALIDAD DE CONTENIDO")
        lines.append("-" * 80)
        lines.append(f"Preguntas con tags: {self.stats['with_tags']}")
        lines.append(f"Preguntas sin tags: {self.stats['without_tags']}")
        lines.append(f"Preguntas con feedback: {self.stats['with_feedback']}")
        lines.append(f"Preguntas sin feedback: {self.stats['without_feedback']}")
        lines.append(f"Preguntas vacías: {self.stats['empty_questions']}")
        lines.append(f"Preguntas con formato HTML: {len(self.stats['html_format_questions'])}")
        
        if self.stats['avg_answers_per_question']:
            avg = sum(self.stats['avg_answers_per_question']) / len(self.stats['avg_answers_per_question'])
            lines.append(f"Promedio de respuestas por pregunta: {avg:.2f}")
        
        if self.stats['question_lengths']:
            avg_length = sum(self.stats['question_lengths']) / len(self.stats['question_lengths'])
            max_length = max(self.stats['question_lengths'])
            min_length = min(self.stats['question_lengths'])
            lines.append(f"Longitud promedio de preguntas: {avg_length:.0f} caracteres")
            lines.append(f"Longitud máxima: {max_length} caracteres")
            lines.append(f"Longitud mínima: {min_length} caracteres")
        lines.append("")
        
        # Distribución por profundidad
        lines.append("📁 DISTRIBUCIÓN POR PROFUNDIDAD DE DIRECTORIOS")
        lines.append("-" * 80)
        if self.stats['files_by_depth']:
            for depth in sorted(self.stats['files_by_depth'].keys()):
                count = self.stats['files_by_depth'][depth]
                lines.append(f"  Nivel {depth}: {count} archivos")
        lines.append("")
        
        # Problemas detectados
        if self.issues:
            lines.append("⚠️  PROBLEMAS DETECTADOS")
            lines.append("-" * 80)
            lines.append(f"Total de problemas: {len(self.issues)}")
            lines.append("")
            for issue in self.issues[:50]:
                lines.append(f"  {issue}")
            if len(self.issues) > 50:
                lines.append(f"  ... y {len(self.issues) - 50} problemas más")
            lines.append("")
        
        # Errores de parseo
        if self.stats['parse_errors']:
            lines.append("❌ ERRORES DE PARSEO XML")
            lines.append("-" * 80)
            for filepath, error in self.stats['parse_errors'][:20]:
                lines.append(f"  {filepath}")
                lines.append(f"    Error: {error}")
            if len(self.stats['parse_errors']) > 20:
                lines.append(f"  ... y {len(self.stats['parse_errors']) - 20} errores más")
            lines.append("")
        
        # Errores de validación XML
        if self.stats['xml_validation_errors']:
            lines.append("⚠️  ERRORES DE VALIDACIÓN XML")
            lines.append("-" * 80)
            lines.append(f"Archivos con errores de validación: {len(self.stats['xml_validation_errors'])}")
            lines.append("")
            for filepath, errors in self.stats['xml_validation_errors'][:20]:
                lines.append(f"  📄 {filepath}")
                for error in errors[:10]:
                    lines.append(f"     • {error}")
                if len(errors) > 10:
                    lines.append(f"     ... y {len(errors) - 10} errores más")
            if len(self.stats['xml_validation_errors']) > 20:
                lines.append(f"  ... y {len(self.stats['xml_validation_errors']) - 20} archivos más")
            lines.append("")
        
        # Preguntas con formato HTML
        if self.stats['html_format_questions']:
            lines.append("🌐 PREGUNTAS CON FORMATO HTML")
            lines.append("-" * 80)
            lines.append(f"Total de preguntas con formato HTML: {len(self.stats['html_format_questions'])}")
            lines.append("")
            
            # Agrupar por archivo
            by_file = defaultdict(list)
            for q in self.stats['html_format_questions']:
                by_file[q['file']].append(q)
            
            lines.append(f"Archivos afectados: {len(by_file)}")
            lines.append("")
            
            for filepath, questions in sorted(by_file.items())[:50]:
                lines.append(f"  📄 {filepath}")
                for q in questions[:5]:
                    q_name = q['name'][:60] if q['name'] else '<sin nombre>'
                    lines.append(f"     • [{q['type']}] {q_name}")
                if len(questions) > 5:
                    lines.append(f"     ... y {len(questions) - 5} preguntas más")
            
            if len(by_file) > 50:
                remaining_files = len(by_file) - 50
                remaining_questions = sum(len(q) for f, q in list(by_file.items())[50:])
                lines.append(f"  ... y {remaining_files} archivos más con {remaining_questions} preguntas")
            lines.append("")
        
        # Preguntas duplicadas
        if self.duplicates:
            lines.append("🔄 PREGUNTAS DUPLICADAS O MUY SIMILARES")
            lines.append("-" * 80)
            lines.append(f"Total de duplicados encontrados: {len(self.duplicates)}")
            lines.append(f"Threshold de similitud: {self.similarity_threshold}")
            lines.append("")
            
            for idx, (i, j, similarity) in enumerate(self.duplicates, 1):
                q1 = self.all_questions[i]
                q2 = self.all_questions[j]
                
                lines.append(f"Duplicado {idx}: Similitud = {similarity:.3f}")
                lines.append(f"  Pregunta A ({q1['type']}): {q1['name'][:70]}")
                lines.append(f"    Archivo: {q1['filepath']}")
                lines.append(f"  Pregunta B ({q2['type']}): {q2['name'][:70]}")
                lines.append(f"    Archivo: {q2['filepath']}")
                lines.append(f"  Comando: meld -n '{q1['filepath']}' '{q2['filepath']}'")
                lines.append("")
            
            # Estadísticas de duplicados
            if self.duplicates:
                avg_sim = sum(sim for _, _, sim in self.duplicates) / len(self.duplicates)
                lines.append(f"Estadísticas de duplicados:")
                lines.append(f"  Similitud promedio: {avg_sim:.3f}")
                lines.append(f"  Similitud máxima: {self.duplicates[0][2]:.3f}")
                lines.append(f"  Similitud mínima: {self.duplicates[-1][2]:.3f}")
                lines.append("")
            
            # Script de comandos meld
            lines.append("📋 COMANDOS MELD PARA RESOLVER DUPLICADOS")
            lines.append("-" * 80)
            lines.append("# Copia y ejecuta estos comandos para revisar y resolver duplicados:")
            lines.append("")
            for idx, (i, j, similarity) in enumerate(self.duplicates, 1):
                q1 = self.all_questions[i]
                q2 = self.all_questions[j]
                lines.append(f"# Duplicado {idx} - Similitud: {similarity:.3f}")
                lines.append(f"meld -n '{q1['filepath']}' '{q2['filepath']}'")
                lines.append("")
        
        # Recomendaciones
        lines.append("💡 RECOMENDACIONES")
        lines.append("-" * 80)
        
        if self.stats['without_tags'] > 0:
            percentage = (self.stats['without_tags'] / self.stats['total_questions'] * 100) if self.stats['total_questions'] > 0 else 0
            lines.append(f"  • {percentage:.1f}% de preguntas sin tags - considera añadir tags para mejor organización")
        
        if self.stats['without_feedback'] > 0:
            percentage = (self.stats['without_feedback'] / self.stats['total_questions'] * 100) if self.stats['total_questions'] > 0 else 0
            lines.append(f"  • {percentage:.1f}% de preguntas sin feedback - el feedback ayuda al aprendizaje")
        
        if self.stats['empty_questions'] > 0:
            lines.append(f"  • {self.stats['empty_questions']} preguntas vacías detectadas - requieren revisión")
        
        if self.stats['invalid_files'] > 0:
            lines.append(f"  • {self.stats['invalid_files']} archivos con errores - necesitan corrección")
        
        if self.stats['xml_validation_errors']:
            lines.append(f"  • {len(self.stats['xml_validation_errors'])} archivos con errores de validación XML - revisar estructura")
        
        if self.duplicates:
            lines.append(f"  • {len(self.duplicates)} preguntas duplicadas detectadas - considera revisar para eliminar redundancias")
        
        if self.stats['html_format_questions']:
            percentage = (len(self.stats['html_format_questions']) / self.stats['total_questions'] * 100) if self.stats['total_questions'] > 0 else 0
            lines.append(f"  • {percentage:.1f}% de preguntas usan formato HTML - considera migrar a markdown para mejor portabilidad")
        
        if not self.issues and not self.stats['parse_errors'] and not self.duplicates:
            lines.append("  • ¡Todo se ve bien! No se detectaron problemas significativos")
        
        lines.append("")
        lines.append("=" * 80)
        
        report = "\n".join(lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n✅ Informe guardado en: {output_file}")
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description='Recorre un directorio y genera informe de evaluación de preguntas XML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s preguntas/
  %(prog)s preguntas/ -o informe.txt
  %(prog)s preguntas/ --no-recursive -v
  %(prog)s preguntas/ -s 0.9 -o informe.txt
        """
    )
    
    parser.add_argument('directory', help='Directorio a analizar')
    parser.add_argument('-o', '--output', help='Archivo de salida para el informe')
    parser.add_argument('-r', '--no-recursive', action='store_true',
                        help='No buscar recursivamente en subdirectorios')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Mostrar información detallada durante el análisis')
    parser.add_argument('-s', '--similarity', type=float, default=0.85,
                        help='Threshold de similitud para duplicados (0.0-1.0, default: 0.85)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"❌ Error: '{args.directory}' no es un directorio válido")
        return 1
    
    if not 0.0 <= args.similarity <= 1.0:
        print(f"❌ Error: El threshold debe estar entre 0.0 y 1.0")
        return 1
    
    print(f"Analizando directorio: {args.directory}")
    print(f"Modo recursivo: {'No' if args.no_recursive else 'Sí'}")
    print(f"Threshold de similitud: {args.similarity}")
    print("=" * 80)
    print()
    
    analyzer = QuestionAnalyzer(similarity_threshold=args.similarity)
    
    try:
        analyzer.scan_directory(args.directory, recursive=not args.no_recursive)
        
        print()
        print("Generando informe...")
        print()
        
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
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
