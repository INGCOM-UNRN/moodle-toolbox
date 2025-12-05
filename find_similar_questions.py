#!/usr/bin/env python3
"""
Script para encontrar preguntas XML similares con threshold ajustable.
Usa similitud de texto basada en TF-IDF y similitud de coseno.
Soporta comparación de preguntas dentro de un archivo o entre archivos en una carpeta.
"""

import xml.etree.ElementTree as ET
import argparse
import re
from typing import List, Tuple, Dict
from collections import defaultdict
from pathlib import Path


def extract_text_from_cdata(text):
    """Extrae texto limpio de CDATA."""
    if text is None:
        return ""
    return text.strip()


def clean_text(text):
    """Limpia y normaliza el texto para comparación."""
    text = text.lower()
    text = re.sub(r'[^a-záéíóúñü0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_question_info(question_elem):
    """Extrae información relevante de una pregunta XML."""
    info = {
        'type': question_elem.get('type', ''),
        'name': '',
        'text': '',
        'answers': [],
        'feedbacks': [],
        'generalfeedback': ''
    }
    
    name_elem = question_elem.find('.//name/text')
    if name_elem is not None:
        info['name'] = extract_text_from_cdata(name_elem.text)
    
    text_elem = question_elem.find('.//questiontext/text')
    if text_elem is not None:
        info['text'] = extract_text_from_cdata(text_elem.text)
    
    # Extraer respuestas y sus feedbacks
    for answer in question_elem.findall('.//answer'):
        answer_text_elem = answer.find('text')
        if answer_text_elem is not None:
            answer_text = extract_text_from_cdata(answer_text_elem.text)
            if answer_text:
                info['answers'].append(answer_text)
        
        # Extraer feedback de la respuesta
        feedback_elem = answer.find('feedback/text')
        if feedback_elem is not None:
            feedback_text = extract_text_from_cdata(feedback_elem.text)
            if feedback_text:
                info['feedbacks'].append(feedback_text)
    
    # Extraer feedback general
    generalfeedback_elem = question_elem.find('.//generalfeedback/text')
    if generalfeedback_elem is not None:
        info['generalfeedback'] = extract_text_from_cdata(generalfeedback_elem.text)
    
    return info


def get_question_full_text(info):
    """Combina toda la información de la pregunta en un texto.
    
    Solo usa el texto de la pregunta (questiontext), las respuestas (answers),
    los feedbacks de las respuestas y el feedback general (generalfeedback).
    Excluye el nombre (name) para evitar desviar la comparación.
    """
    parts = [info['text']] + info['answers'] + info['feedbacks']
    if info.get('generalfeedback'):
        parts.append(info['generalfeedback'])
    return ' '.join(parts)


def compute_word_freq(text):
    """Calcula frecuencia de palabras."""
    words = text.split()
    freq = defaultdict(int)
    for word in words:
        if len(word) > 2:  # Ignora palabras muy cortas
            freq[word] += 1
    return freq


def compute_idf(all_texts):
    """Calcula IDF (inverse document frequency) para cada palabra.
    
    Usa una fórmula suavizada para evitar valores de 0 en colecciones pequeñas:
    IDF = log((num_docs + 1) / (doc_count + 1)) + 1
    """
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
        # Fórmula suavizada para evitar IDF de 0
        idf[word] = math.log((num_docs + 1) / (count + 1)) + 1
    
    return idf


def compute_tfidf_vector(text, idf):
    """Calcula vector TF-IDF."""
    freq = compute_word_freq(text)
    total_words = sum(freq.values())
    
    if total_words == 0:
        return {}
    
    tfidf = {}
    for word, count in freq.items():
        tf = count / total_words
        tfidf[word] = tf * idf.get(word, 0)
    
    return tfidf


def cosine_similarity(vec1, vec2):
    """Calcula similitud de coseno entre dos vectores TF-IDF."""
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


def load_questions_from_file(xml_file, base_dir=None):
    """Carga todas las preguntas de un archivo XML."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    questions = []
    file_path = Path(xml_file)
    
    # Calcular ruta relativa si se proporciona base_dir
    if base_dir:
        try:
            rel_path = file_path.relative_to(base_dir)
        except ValueError:
            rel_path = file_path
    else:
        rel_path = file_path
    
    for i, question_elem in enumerate(root.findall('question')):
        q_type = question_elem.get('type', '')
        if q_type == 'category':
            continue
        
        info = extract_question_info(question_elem)
        full_text = get_question_full_text(info)
        clean = clean_text(full_text)
        
        if clean:
            questions.append({
                'file': str(file_path.absolute()),
                'rel_file': str(rel_path),
                'index': i,
                'info': info,
                'text': clean,
                'full_text': full_text
            })
    
    return questions


def find_similar_questions_in_file(xml_file, threshold=0.7):
    """Encuentra preguntas similares dentro de un archivo XML."""
    questions = load_questions_from_file(xml_file, base_dir=None)
    
    print(f"Total de preguntas válidas encontradas: {len(questions)}")
    
    all_texts = [q['text'] for q in questions]
    idf = compute_idf(all_texts)
    
    for q in questions:
        q['vector'] = compute_tfidf_vector(q['text'], idf)
    
    similar_pairs = []
    
    for i in range(len(questions)):
        for j in range(i + 1, len(questions)):
            similarity = cosine_similarity(questions[i]['vector'], questions[j]['vector'])
            
            if similarity >= threshold:
                similar_pairs.append((i, j, similarity))
    
    similar_pairs.sort(key=lambda x: x[2], reverse=True)
    
    return questions, similar_pairs


def find_similar_questions_in_directory(directory, threshold=0.7, recursive=False):
    """Encuentra preguntas similares entre archivos XML en un directorio."""
    dir_path = Path(directory).resolve()
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {directory}")
    
    # Encontrar todos los archivos XML
    if recursive:
        xml_files = list(dir_path.rglob('*.xml'))
    else:
        xml_files = list(dir_path.glob('*.xml'))
    
    if not xml_files:
        print(f"No se encontraron archivos XML en {directory}")
        return [], []
    
    print(f"Encontrados {len(xml_files)} archivos XML")
    
    # Cargar todas las preguntas de todos los archivos
    all_questions = []
    file_question_count = {}
    
    for xml_file in xml_files:
        try:
            questions = load_questions_from_file(xml_file, base_dir=dir_path)
            file_question_count[str(xml_file)] = len(questions)
            all_questions.extend(questions)
            print(f"  {xml_file.name}: {len(questions)} preguntas")
        except Exception as e:
            print(f"  ✗ Error en {xml_file.name}: {e}")
    
    print(f"\nTotal de preguntas válidas cargadas: {len(all_questions)}")
    
    if len(all_questions) == 0:
        return [], []
    
    # Calcular IDF sobre todas las preguntas
    all_texts = [q['text'] for q in all_questions]
    idf = compute_idf(all_texts)
    
    # Calcular vectores TF-IDF
    for q in all_questions:
        q['vector'] = compute_tfidf_vector(q['text'], idf)
    
    # Encontrar pares similares
    similar_pairs = []
    
    for i in range(len(all_questions)):
        for j in range(i + 1, len(all_questions)):
            similarity = cosine_similarity(all_questions[i]['vector'], all_questions[j]['vector'])
            
            if similarity >= threshold:
                similar_pairs.append((i, j, similarity))
    
    similar_pairs.sort(key=lambda x: x[2], reverse=True)
    
    return all_questions, similar_pairs


def generate_diff(file1_path, file2_path):
    """
    Genera un diff entre dos archivos.
    
    Args:
        file1_path: Ruta al primer archivo
        file2_path: Ruta al segundo archivo
    
    Returns:
        String con el diff en formato unificado
    """
    import difflib
    
    try:
        with open(file1_path, 'r', encoding='utf-8') as f1:
            lines1 = f1.readlines()
        
        with open(file2_path, 'r', encoding='utf-8') as f2:
            lines2 = f2.readlines()
        
        diff = difflib.unified_diff(
            lines1, lines2,
            fromfile=str(file1_path),
            tofile=str(file2_path),
            lineterm=''
        )
        
        return '\n'.join(diff)
    except Exception as e:
        return f"Error generando diff: {e}"


def generate_markdown_report(report_path, questions, similar_pairs, base_dir, threshold):
    """
    Genera un informe en formato markdown con diffs de los duplicados.
    """
    from datetime import datetime
    
    with open(report_path, 'w', encoding='utf-8') as f:
        # Encabezado
        f.write("# Informe de Preguntas Similares\n\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Directorio analizado:** `{base_dir}`\n\n")
        f.write(f"**Threshold de similitud:** {threshold}\n\n")
        f.write(f"**Total de preguntas analizadas:** {len(questions)}\n\n")
        f.write(f"**Pares similares encontrados:** {len(similar_pairs)}\n\n")
        
        # Estadísticas
        if similar_pairs:
            avg_sim = sum(s for _, _, s in similar_pairs) / len(similar_pairs)
            cross_file = sum(1 for i, j, _ in similar_pairs 
                           if questions[i].get('file') != questions[j].get('file'))
            same_file = len(similar_pairs) - cross_file
            
            exact_dups = sum(1 for _, _, s in similar_pairs if s >= 0.99)
            
            f.write("## Estadísticas\n\n")
            f.write(f"- **Similitud promedio:** {avg_sim:.3f}\n")
            f.write(f"- **Similitud máxima:** {similar_pairs[0][2]:.3f}\n")
            f.write(f"- **Similitud mínima:** {similar_pairs[-1][2]:.3f}\n")
            f.write(f"- **Duplicados exactos (≥0.99):** {exact_dups}\n")
            f.write(f"- **Pares entre archivos diferentes:** {cross_file}\n")
            f.write(f"- **Pares dentro del mismo archivo:** {same_file}\n\n")
            
            f.write("---\n\n")
        
        # Detalles de cada par
        f.write("## Detalles de Preguntas Similares\n\n")
        
        for idx, (i, j, similarity) in enumerate(similar_pairs, 1):
            q1 = questions[i]
            q2 = questions[j]
            
            same_file = q1.get('file') == q2.get('file')
            cross_file = not same_file
            
            f.write(f"### Par {idx}: Similitud {similarity:.4f}\n\n")
            
            if cross_file:
                f.write("🔴 **Archivos diferentes**\n\n")
            else:
                f.write("🟡 **Mismo archivo**\n\n")
            
            # Información de la primera pregunta
            f.write("#### Pregunta 1\n\n")
            f.write(f"- **Archivo:** `{q1.get('rel_file', 'unknown')}`\n")
            f.write(f"- **Nombre:** {q1['info']['name']}\n")
            f.write(f"- **Tipo:** {q1['info']['type']}\n\n")
            
            f.write("**Texto de la pregunta:**\n\n")
            f.write(f"> {q1['info']['text']}\n\n")
            
            if q1['info']['answers']:
                f.write("**Respuestas:**\n\n")
                for ans_idx, ans in enumerate(q1['info']['answers'], 1):
                    f.write(f"{ans_idx}. {ans}\n")
                f.write("\n")
            
            if q1['info']['feedbacks']:
                f.write("<details>\n<summary>Ver feedbacks</summary>\n\n")
                for fb_idx, fb in enumerate(q1['info']['feedbacks'], 1):
                    f.write(f"{fb_idx}. {fb}\n")
                f.write("\n</details>\n\n")
            
            # Información de la segunda pregunta
            f.write("#### Pregunta 2\n\n")
            f.write(f"- **Archivo:** `{q2.get('rel_file', 'unknown')}`\n")
            f.write(f"- **Nombre:** {q2['info']['name']}\n")
            f.write(f"- **Tipo:** {q2['info']['type']}\n\n")
            
            f.write("**Texto de la pregunta:**\n\n")
            f.write(f"> {q2['info']['text']}\n\n")
            
            if q2['info']['answers']:
                f.write("**Respuestas:**\n\n")
                for ans_idx, ans in enumerate(q2['info']['answers'], 1):
                    f.write(f"{ans_idx}. {ans}\n")
                f.write("\n")
            
            if q2['info']['feedbacks']:
                f.write("<details>\n<summary>Ver feedbacks</summary>\n\n")
                for fb_idx, fb in enumerate(q2['info']['feedbacks'], 1):
                    f.write(f"{fb_idx}. {fb}\n")
                f.write("\n</details>\n\n")
            
            # Diff de los archivos
            if cross_file and 'file' in q1 and 'file' in q2:
                f.write("#### Diff de archivos\n\n")
                f.write("<details>\n<summary>Ver diff completo</summary>\n\n")
                f.write("```diff\n")
                diff_output = generate_diff(q1['file'], q2['file'])
                f.write(diff_output)
                f.write("\n```\n\n")
                f.write("</details>\n\n")
            
            f.write("---\n\n")
        
        # Archivos con duplicados
        if similar_pairs:
            f.write("## Archivos con Duplicados\n\n")
            f.write("Lista de archivos que contienen preguntas duplicadas en otros archivos:\n\n")
            
            files_with_dups = set()
            for i, j, _ in similar_pairs:
                if questions[i].get('file') != questions[j].get('file'):
                    if 'rel_file' in questions[i]:
                        files_with_dups.add(questions[i]['rel_file'])
                    if 'rel_file' in questions[j]:
                        files_with_dups.add(questions[j]['rel_file'])
            
            if files_with_dups:
                f.write("```bash\n")
                for file_path in sorted(files_with_dups):
                    f.write(f"# Revisar: {file_path}\n")
                    f.write(f"cat \"{file_path}\"\n\n")
                f.write("```\n\n")
                
                f.write("### Comandos para eliminar duplicados\n\n")
                f.write("```bash\n")
                for file_path in sorted(files_with_dups):
                    f.write(f"rm \"{file_path}\"\n")
                f.write("```\n\n")
    
    print(f"\n{'='*80}")
    print(f"INFORME MARKDOWN GENERADO")
    print(f"{'='*80}")
    print(f"Archivo: {report_path}")
    print(f"Pares documentados: {len(similar_pairs)}")
    print(f"\nPara ver el informe:")
    print(f"  cat {report_path}")
    print(f"O abrirlo en un visor de markdown.")


def generate_delete_script(script_path, questions, similar_pairs, base_dir, threshold):
    """
    Genera un script de bash para eliminar duplicados exactos.
    Solo incluye la segunda pregunta de cada par con similitud >= 0.99.
    """
    exact_duplicates = []
    files_to_delete = set()
    
    # Filtrar solo duplicados exactos (similitud >= 0.99)
    for i, j, similarity in similar_pairs:
        if similarity >= 0.99:
            q1 = questions[i]
            q2 = questions[j]
            
            # Solo incluir si son archivos diferentes
            if q1.get('file') != q2.get('file'):
                # Agregar la segunda pregunta para eliminar
                exact_duplicates.append((i, j, similarity))
                if 'rel_file' in q2:
                    files_to_delete.add(q2['rel_file'])
    
    if not exact_duplicates:
        print(f"\n⚠ No se encontraron duplicados exactos (similitud >= 0.99)")
        print(f"  No se generó el script de borrado")
        return
    
    # Crear el script
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n")
        f.write("# Script generado automáticamente para eliminar duplicados exactos\n")
        f.write(f"# Generado: {Path.cwd()}\n")
        f.write(f"# Directorio base: {base_dir}\n")
        f.write(f"# Threshold usado: {threshold}\n")
        f.write(f"# Duplicados exactos encontrados: {len(exact_duplicates)}\n")
        f.write("\n")
        f.write("set -e  # Salir si hay error\n")
        f.write("\n")
        f.write("echo 'Script de eliminación de duplicados exactos'\n")
        f.write(f"echo 'Se eliminarán {len(files_to_delete)} archivos'\n")
        f.write("echo ''\n")
        f.write("\n")
        
        # Agregar comentarios con los pares encontrados
        f.write("# Pares de duplicados exactos encontrados:\n")
        for idx, (i, j, similarity) in enumerate(exact_duplicates, 1):
            q1 = questions[i]
            q2 = questions[j]
            f.write(f"# Par {idx} (similitud: {similarity:.4f}):\n")
            f.write(f"#   Original: {q1.get('rel_file', 'unknown')} - {q1['info']['name'][:60]}\n")
            f.write(f"#   Duplicado: {q2.get('rel_file', 'unknown')} - {q2['info']['name'][:60]}\n")
            f.write("#\n")
        
        f.write("\n")
        f.write("# Cambiar al directorio base\n")
        f.write(f"cd \"{base_dir}\"\n")
        f.write("\n")
        
        # Agregar comandos de eliminación
        f.write("# Eliminar archivos duplicados (segunda ocurrencia de cada par)\n")
        for file_path in sorted(files_to_delete):
            f.write(f"echo 'Eliminando: {file_path}'\n")
            f.write(f"rm -f \"{file_path}\"\n")
        
        f.write("\n")
        f.write(f"echo ''\n")
        f.write(f"echo 'Proceso completado: {len(files_to_delete)} archivos eliminados'\n")
    
    # Hacer el script ejecutable
    import os
    os.chmod(script_path, 0o755)
    
    print(f"\n{'='*80}")
    print(f"SCRIPT DE BORRADO GENERADO")
    print(f"{'='*80}")
    print(f"Archivo: {script_path}")
    print(f"Duplicados exactos encontrados: {len(exact_duplicates)} pares")
    print(f"Archivos a eliminar: {len(files_to_delete)}")
    print(f"\nArchivos que serán eliminados:")
    for file_path in sorted(files_to_delete):
        print(f"  - {file_path}")
    print(f"\nPara ejecutar el script:")
    print(f"  bash {script_path}")
    print(f"\nO revisar primero:")
    print(f"  cat {script_path}")


def print_results(questions, similar_pairs, verbose=False, show_files=False):
    """Imprime los resultados de preguntas similares."""
    if not similar_pairs:
        print(f"\nNo se encontraron pares de preguntas con similitud >= threshold")
        return
    
    print(f"\n{'='*80}")
    print(f"PREGUNTAS SIMILARES ENCONTRADAS: {len(similar_pairs)} pares")
    print(f"{'='*80}\n")
    
    for idx, (i, j, similarity) in enumerate(similar_pairs, 1):
        q1 = questions[i]
        q2 = questions[j]
        
        # Determinar si son del mismo archivo
        same_file = q1.get('file') == q2.get('file')
        cross_file = not same_file and 'file' in q1 and 'file' in q2
        
        print(f"Par {idx}: Similitud = {similarity:.3f}")
        
        if cross_file:
            print(f"  [ARCHIVOS DIFERENTES]")
        elif same_file and show_files:
            print(f"  [MISMO ARCHIVO]")
        
        print(f"\nPregunta {i+1} ({q1['info']['type']}):")
        print(f"  Nombre: {q1['info']['name'][:100]}")
        
        # Mostrar ruta relativa o absoluta según el contexto
        if show_files and 'rel_file' in q1:
            print(f"  Ruta: {q1['rel_file']}")
        elif show_files and 'file' in q1:
            print(f"  Archivo: {Path(q1['file']).name}")
        
        if verbose:
            print(f"  Texto: {q1['info']['text'][:200]}")
            print(f"  Respuestas: {len(q1['info']['answers'])}")
        
        print(f"\nPregunta {j+1} ({q2['info']['type']}):")
        print(f"  Nombre: {q2['info']['name'][:100]}")
        
        # Mostrar ruta relativa o absoluta según el contexto
        if show_files and 'rel_file' in q2:
            print(f"  Ruta: {q2['rel_file']}")
        elif show_files and 'file' in q2:
            print(f"  Archivo: {Path(q2['file']).name}")
        
        if verbose:
            print(f"  Texto: {q2['info']['text'][:200]}")
            print(f"  Respuestas: {len(q2['info']['answers'])}")
        
        print(f"\n{'-'*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Encuentra preguntas XML similares con threshold ajustable',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Comparar preguntas dentro de un archivo
  %(prog)s parcial3_2025.xml
  %(prog)s parcial3_2025.xml --threshold 0.8
  %(prog)s parcial3_2025.xml -t 0.6 -v
  
  # Comparar preguntas entre archivos de una carpeta
  %(prog)s -d ./preguntas
  %(prog)s -d ./preguntas -t 0.8 -v
  
  # Comparar recursivamente en subdirectorios
  %(prog)s -d ./preguntas -r
  
  # Generar script para eliminar duplicados exactos
  %(prog)s -d ./preguntas -r -t 0.7 --generate-delete-script delete_duplicates.sh
  
  # Generar informe markdown con diffs
  %(prog)s -d ./preguntas -r -t 0.7 --markdown-report informe.md
        """
    )
    
    parser.add_argument('xml_file', nargs='?', help='Archivo XML con preguntas')
    parser.add_argument('-d', '--directory', help='Directorio con archivos XML')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Procesar subdirectorios recursivamente')
    parser.add_argument('-t', '--threshold', type=float, default=0.7,
                        help='Threshold de similitud (0.0-1.0, default: 0.7)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Muestra información detallada de las preguntas')
    parser.add_argument('--generate-delete-script', metavar='FILE',
                        help='Genera un script de bash para eliminar duplicados exactos (similitud >= 0.99)')
    parser.add_argument('--markdown-report', metavar='FILE',
                        help='Genera un informe en formato markdown con diffs de los duplicados')
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.xml_file and not args.directory:
        parser.error("Debe especificar un archivo XML o un directorio con -d/--directory")
    
    if args.xml_file and args.directory:
        parser.error("No puede especificar un archivo y un directorio simultáneamente")
    
    if not 0.0 <= args.threshold <= 1.0:
        parser.error("El threshold debe estar entre 0.0 y 1.0")
    
    print(f"Threshold de similitud: {args.threshold}")
    print(f"{'='*80}")
    
    try:
        if args.directory:
            # Modo directorio
            print(f"Analizando directorio: {args.directory}")
            if args.recursive:
                print("Modo recursivo activado")
            print()
            
            questions, similar_pairs = find_similar_questions_in_directory(
                args.directory, args.threshold, args.recursive
            )
            print_results(questions, similar_pairs, args.verbose, show_files=True)
        else:
            # Modo archivo único
            print(f"Analizando archivo: {args.xml_file}")
            print()
            
            questions, similar_pairs = find_similar_questions_in_file(args.xml_file, args.threshold)
            print_results(questions, similar_pairs, args.verbose, show_files=False)
        
        if similar_pairs:
            print(f"\nResumen: {len(similar_pairs)} pares de preguntas similares encontrados")
            print(f"Similitud promedio: {sum(s for _, _, s in similar_pairs) / len(similar_pairs):.3f}")
            print(f"Similitud máxima: {similar_pairs[0][2]:.3f}")
            print(f"Similitud mínima: {similar_pairs[-1][2]:.3f}")
            
            # Estadísticas adicionales para modo directorio
            if args.directory:
                cross_file_pairs = sum(1 for i, j, _ in similar_pairs 
                                      if questions[i].get('file') != questions[j].get('file'))
                same_file_pairs = len(similar_pairs) - cross_file_pairs
                
                print(f"\nEstadísticas de archivos:")
                print(f"  - Pares entre diferentes archivos: {cross_file_pairs}")
                print(f"  - Pares dentro del mismo archivo: {same_file_pairs}")
                
                # Lista de archivos con duplicados para facilitar limpieza
                print(f"\n{'='*80}")
                print("ARCHIVOS CON DUPLICADOS (para limpieza):")
                print(f"{'='*80}")
                
                files_with_duplicates = set()
                for i, j, similarity in similar_pairs:
                    q1 = questions[i]
                    q2 = questions[j]
                    
                    # Solo incluir archivos que tienen duplicados con otros archivos
                    if q1.get('file') != q2.get('file'):
                        if 'rel_file' in q1:
                            files_with_duplicates.add(q1['rel_file'])
                        if 'rel_file' in q2:
                            files_with_duplicates.add(q2['rel_file'])
                
                if files_with_duplicates:
                    print("\nArchivos con preguntas duplicadas en otros archivos:")
                    for file_path in sorted(files_with_duplicates):
                        print(f"  - {file_path}")
                    
                    print(f"\nComandos para revisar/eliminar:")
                    for file_path in sorted(files_with_duplicates):
                        print(f"  rm \"{file_path}\"  # o revisar: cat \"{file_path}\"")
                
                # Generar script de borrado si se solicitó
                if args.generate_delete_script:
                    generate_delete_script(args.generate_delete_script, questions, similar_pairs, 
                                          args.directory, args.threshold)
                
                # Generar informe markdown si se solicitó
                if args.markdown_report:
                    generate_markdown_report(args.markdown_report, questions, similar_pairs,
                                           args.directory, args.threshold)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ET.ParseError as e:
        print(f"Error al parsear XML: {e}")
        return 1
    except Exception as e:
        print(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
