#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

def format_gift_content(content: str) -> str:
    """
    Formatea el contenido de un archivo GIFT según las reglas especificadas:
    - Título en una línea sola.
    - Enunciado en la siguiente línea.
    - Llaves { } en líneas propias.
    - Respuestas indentadas a 4 espacios.
    """
    # Expresión regular para capturar los componentes de una pregunta GIFT
    # 1. Comentarios opcionales (//)
    # 2. Título opcional (::título::)
    # 3. Enunciado (stem)
    # 4. Bloque de respuestas ({...})
    # 5. Texto post-respuestas (opcional, para respuestas embebidas)
    
    # Dividimos por preguntas (basado en líneas en blanco dobles)
    questions = re.split(r'\n\s*\n', content.strip())
    formatted_questions = []
    
    for q in questions:
        if not q.strip():
            continue
            
        # Extraer comentarios iniciales
        comments = []
        q_lines = q.splitlines()
        content_start_idx = 0
        for line in q_lines:
            if line.strip().startswith('//') or line.strip().startswith('$'):
                comments.append(line.strip())
                content_start_idx += 1
            elif not line.strip():
                content_start_idx += 1
            else:
                break
        
        remaining_content = "\n".join(q_lines[content_start_idx:]).strip()
        
        # Extraer título
        title = ""
        title_match = re.match(r'^::(.*?)::(.*)', remaining_content, re.DOTALL)
        if title_match:
            title = f"::{title_match.group(1).strip()}::"
            remaining_content = title_match.group(2).strip()
            
        # Encontrar el bloque de respuestas { ... }
        # Buscamos la primera llave abierta que no esté escapada
        brace_start = -1
        for i in range(len(remaining_content)):
            if remaining_content[i] == '{' and (i == 0 or remaining_content[i-1] != '\\'):
                brace_start = i
                break
        
        if brace_start == -1:
            # Es una descripción o algo sin bloque de respuestas
            stem = remaining_content.strip()
            answers_block = ""
            post_stem = ""
        else:
            stem = remaining_content[:brace_start].strip()
            # Encontrar la llave de cierre correspondiente
            # (Simplificado: buscamos la última llave de cierre no escapada)
            brace_end = -1
            for i in range(len(remaining_content) - 1, brace_start, -1):
                if remaining_content[i] == '}' and (i == 0 or remaining_content[i-1] != '\\'):
                    brace_end = i
                    break
            
            if brace_end == -1:
                # Mal formado, pero intentamos procesar
                answers_block = remaining_content[brace_start+1:].strip()
                post_stem = ""
            else:
                answers_block = remaining_content[brace_start+1:brace_end].strip()
                post_stem = remaining_content[brace_end+1:].strip()

        # Formatear la pregunta
        parts = []
        if comments:
            parts.extend(comments)
        
        if title:
            parts.append(title)
            
        if stem:
            parts.append(stem)
            
        if brace_start != -1:
            parts.append("{")
            # Formatear respuestas
            # Las respuestas suelen empezar con =, ~, #
            # Dividimos por estos caracteres pero manteniendo el carácter
            ans_lines = []
            
            # Unir líneas rotas dentro del bloque de respuestas para procesar mejor
            # pero respetando si ya están indentadas o tienen un formato previo
            raw_answers = answers_block.splitlines()
            current_ans = ""
            for line in raw_answers:
                line = line.strip()
                if not line: continue
                
                if line[0] in ('=', '~', '#', '{') or (line.startswith('####')):
                    if current_ans:
                        ans_lines.append("    " + current_ans)
                    current_ans = line
                else:
                    if current_ans:
                        current_ans += " " + line
                    else:
                        current_ans = line
            
            if current_ans:
                ans_lines.append("    " + current_ans)
                
            parts.extend(ans_lines)
            parts.append("}")
        
        if post_stem:
            parts.append(post_stem)
            
        formatted_questions.append("\n".join(parts))
        
    return "\n\n".join(formatted_questions) + "\n"

def process_file(filepath: Path, dry_run: bool = False):
    try:
        content = filepath.read_text(encoding='utf-8')
        formatted = format_gift_content(content)
        
        if content != formatted:
            if not dry_run:
                filepath.write_text(formatted, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error procesando {filepath}: {e}", file=sys.stderr)
        return False

MANUAL_TEXT = """
# Manual de format-gift
Herramienta para estandarizar el formato visual de archivos GIFT.

## Estándares de Formato
1. Título: En su propia línea inicial (::Título::).
2. Enunciado: En la línea inmediatamente siguiente al título.
3. Bloque: Llaves { y } en líneas propias.
4. Indentación: 4 espacios para cada respuesta/opción.

## Uso
format-gift [RUTAS...] [-r] [-n]
"""

LLM_INSTRUCTIONS = """
# Instrucciones para LLMs (format-gift)
Al generar archivos GIFT, sigue este esquema:
::Título::
[markdown]Enunciado
{
    =Respuesta correcta
    ~Opción incorrecta
}
No insertes líneas en blanco adicionales dentro de la estructura de la pregunta.
"""

def main():
    parser = argparse.ArgumentParser(description="Formatea archivos GIFT para mejorar su legibilidad.")
    parser.add_argument("paths", nargs="*", help="Archivos o directorios a formatear.")
    parser.add_argument("-r", "--recursive", action="store_true", help="Procesar directorios recursivamente.")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Mostrar qué se cambiaría sin aplicar cambios.")
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

    files = []
    for p in args.paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            pattern = "**/*.gift" if args.recursive else "*.gift"
            files.extend(list(path.glob(pattern)))
            
    if not files:
        print("No se encontraron archivos GIFT.")
        return

    modified_count = 0
    for f in sorted(files):
        was_modified = process_file(f, args.dry_run)
        if was_modified:
            status = "[SIMULACIÓN]" if args.dry_run else "[FORMATEADO]"
            print(f"{status} {f}")
            modified_count += 1
        else:
            # print(f"[OK] {f}")
            pass
            
    print(f"\nResumen: {len(files)} archivos procesados, {modified_count} modificados.")

if __name__ == "__main__":
    main()
