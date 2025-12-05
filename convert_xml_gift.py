#!/usr/bin/env python3
"""
Conversor bidireccional entre formatos Moodle XML y GIFT.
Soporta conversión de archivos individuales y masiva preservando estructura de directorios.
"""

import argparse
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Dict
import html

# Diccionario de caracteres especiales para conversión
SPECIAL_CHARS = {
    "⩵": "==",
    "＝": "=",
    ";": ";",
    "＃": "#",
    "｛": "{",
    "｝": "}",
    " ": " ",
    "↵": "\n",
    "    ": "\t",
    "＞": ">",
    "＜": "<",
    "［": "[",
    "］": "]",
    " ": " ",
    "（": "(",
    "）": ")",
    "＊": "*",
    "＂": "\"",
    "：": ":",
}

# Diccionario inverso para conversión GIFT -> XML
SPECIAL_CHARS_INVERSE = {v: k for k, v in SPECIAL_CHARS.items()}


def convert_special_chars_in_code(text: str, to_gift: bool = True) -> str:
    """
    Convierte caracteres especiales dentro de bloques de código.
    
    Args:
        text: Texto a procesar
        to_gift: True para XML->GIFT, False para GIFT->XML
    """
    if not text:
        return text
    
    substitutions = SPECIAL_CHARS if to_gift else SPECIAL_CHARS_INVERSE
    
    def replace_in_match(match):
        content = match.group(2)
        for special, normal in substitutions.items():
            content = content.replace(special, normal)
        return match.group(1) + content + match.group(3)
    
    # Procesar bloques de código con ```
    text = re.sub(r'(```[a-z]*\n)(.*?)(\n```)', replace_in_match, text, flags=re.DOTALL)
    
    # Procesar bloques <pre>
    text = re.sub(r'(<pre>)(.*?)(</pre>)', replace_in_match, text, flags=re.DOTALL)
    
    # Procesar código inline con `
    text = re.sub(r'(`)(.*?)(`)', replace_in_match, text)
    
    return text


def escape_gift_special_chars(text: str) -> str:
    """Escapa caracteres especiales de GIFT fuera de bloques de código."""
    if not text:
        return text
    
    # Proteger bloques de código
    code_blocks = []
    
    def save_code_block(match):
        code_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(code_blocks)-1}__"
    
    text = re.sub(r'```[a-z]*\n.*?\n```', save_code_block, text, flags=re.DOTALL)
    text = re.sub(r'<pre>.*?</pre>', save_code_block, text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', save_code_block, text)
    
    # Escapar caracteres especiales de GIFT
    for char in ['=', '#', '{', '}', '~', ':']:
        text = text.replace(char, '\\' + char)
    
    # Restaurar bloques de código
    for i, block in enumerate(code_blocks):
        text = text.replace(f"__CODE_BLOCK_{i}__", block)
    
    return text


def unescape_gift_special_chars(text: str) -> str:
    """Remueve escapes de caracteres especiales de GIFT."""
    if not text:
        return text
    
    for char in ['=', '#', '{', '}', '~', ':']:
        text = text.replace('\\' + char, char)
    
    return text


def xml_to_gift(xml_path: str, output_path: str = None) -> str:
    """
    Convierte un archivo XML de Moodle a formato GIFT.
    
    Args:
        xml_path: Ruta al archivo XML
        output_path: Ruta del archivo GIFT de salida (opcional)
    
    Returns:
        Contenido en formato GIFT
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    gift_content = []
    
    # Buscar comentarios en el árbol completo
    for i, question in enumerate(root.findall('question')):
        q_type = question.get('type')
        
        if q_type != 'multichoice':
            print(f"Advertencia: Tipo de pregunta '{q_type}' no soportado aún")
            continue
        
        # Extraer información básica
        name_elem = question.find('name/text')
        name = name_elem.text if name_elem is not None else "Sin nombre"
        
        # Buscar ID de pregunta del comentario anterior en el XML
        question_id = ""
        question_index = list(root).index(question)
        if question_index > 0:
            prev_elem = root[question_index - 1]
            if isinstance(prev_elem.tag, type(ET.Comment)):
                match = re.search(r'question:\s*(\d+)', prev_elem.text if hasattr(prev_elem, 'text') else str(prev_elem))
                if match:
                    question_id = match.group(1)
        
        # Alternativa: buscar en la fuente del XML
        if not question_id:
            try:
                with open(xml_path, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                    # Buscar comentarios antes de <question
                    pattern = r'<!--\s*question:\s*(\d+)\s*-->'
                    matches = list(re.finditer(pattern, xml_content))
                    if i < len(matches):
                        question_id = matches[i].group(1)
            except:
                pass
        
        # Extraer tags
        tags = []
        tags_elem = question.find('tags')
        if tags_elem is not None:
            for tag in tags_elem.findall('tag/text'):
                if tag.text:
                    tags.append(tag.text)
        
        # Construir header
        if question_id:
            gift_content.append(f"// question: {question_id}  name: {name}")
        
        if tags:
            tags_str = ' '.join([f"[tag:{tag}]" for tag in tags])
            gift_content.append(f"// {tags_str}")
        
        # Extraer texto de la pregunta
        questiontext_elem = question.find('questiontext/text')
        questiontext = questiontext_elem.text if questiontext_elem is not None else ""
        questiontext = convert_special_chars_in_code(questiontext, to_gift=True)
        
        # Extraer general feedback
        generalfeedback_elem = question.find('generalfeedback/text')
        generalfeedback = generalfeedback_elem.text if generalfeedback_elem is not None else ""
        generalfeedback = convert_special_chars_in_code(generalfeedback, to_gift=True)
        
        # Escapar caracteres especiales en el título
        escaped_name = name
        for char in [':', '=', '#', '{', '}', '~']:
            escaped_name = escaped_name.replace(char, '\\' + char)
        
        # Construir pregunta GIFT
        gift_content.append(f"::{escaped_name}::[markdown]{questiontext}{{")
        
        # Procesar respuestas
        for answer in question.findall('answer'):
            fraction = answer.get('fraction', '0')
            answer_text_elem = answer.find('text')
            answer_text = answer_text_elem.text if answer_text_elem is not None else ""
            answer_text = convert_special_chars_in_code(answer_text, to_gift=True)
            
            feedback_elem = answer.find('feedback/text')
            feedback = feedback_elem.text if feedback_elem is not None else ""
            feedback = convert_special_chars_in_code(feedback, to_gift=True)
            
            # Determinar símbolo (= para correcta, ~ para incorrecta)
            symbol = '=' if fraction == '100' else '~'
            
            if feedback:
                gift_content.append(f"\t{symbol}{answer_text}#{feedback}")
            else:
                gift_content.append(f"\t{symbol}{answer_text}")
        
        # Agregar general feedback si existe
        if generalfeedback:
            gift_content.append(f"\t####{generalfeedback}")
        
        gift_content.append("}")
        gift_content.append("")  # Línea en blanco entre preguntas
    
    result = '\n'.join(gift_content)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
    
    return result


def gift_to_xml(gift_path: str, output_path: str = None) -> str:
    """
    Convierte un archivo GIFT a formato XML de Moodle.
    
    Args:
        gift_path: Ruta al archivo GIFT
        output_path: Ruta del archivo XML de salida (opcional)
    
    Returns:
        Contenido en formato XML
    """
    with open(gift_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    root = ET.Element('quiz')
    
    # Dividir por preguntas usando un enfoque más robusto
    # Buscar patrones ::name::[markdown]...{ ... }
    questions = []
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Buscar inicio de pregunta
        if '::' in line and '[markdown]' in line:
            # Capturar comentarios previos
            comments = []
            j = i - 1
            while j >= 0 and lines[j].strip().startswith('//'):
                comments.insert(0, lines[j])
                j -= 1
            
            # Capturar toda la pregunta
            question_start = i
            brace_count = 0
            found_opening = False
            
            # Buscar la llave de apertura
            k = i
            while k < len(lines):
                brace_count += lines[k].count('{')
                if '{' in lines[k]:
                    found_opening = True
                if found_opening:
                    brace_count -= lines[k].count('}')
                    if brace_count == 0:
                        # Encontramos el cierre
                        question_lines = lines[question_start:k+1]
                        questions.append({
                            'comments': '\n'.join(comments),
                            'content': '\n'.join(question_lines)
                        })
                        i = k + 1
                        break
                k += 1
            
            if not found_opening or brace_count != 0:
                i += 1
        else:
            i += 1
    
    # Procesar cada pregunta
    for q_data in questions:
        comments = q_data['comments']
        q_content = q_data['content']
        
        # Parsear el contenido de la pregunta con un patrón más permisivo
        match = re.match(r'::(.*?)::\[markdown\](.*?)\{(.+)\}', q_content, re.DOTALL)
        if not match:
            print(f"Advertencia: No se pudo parsear pregunta")
            continue
        
        name = match.group(1).strip()
        questiontext = match.group(2).strip()
        answers_block = match.group(3).strip()
    
        # Extraer question ID de los comentarios
        question_id = ""
        tags = []
        for line in comments.split('\n'):
            if line.startswith('//'):
                line = line[2:].strip()
                
                # Buscar question ID
                id_match = re.search(r'question:\s*(\d+)', line)
                if id_match:
                    question_id = id_match.group(1)
                
                # Buscar tags
                tag_matches = re.findall(r'\[tag:(.*?)\]', line)
                tags.extend(tag_matches)
        
        # Crear elemento de pregunta
        if question_id:
            root.append(ET.Comment(f' question: {question_id}  '))
        
        question = ET.SubElement(root, 'question', type='multichoice')
        
        # Name
        name_elem = ET.SubElement(question, 'name')
        name_text = ET.SubElement(name_elem, 'text')
        name_text.text = name
        
        # Question text
        questiontext_elem = ET.SubElement(question, 'questiontext', format='markdown')
        questiontext_text = ET.SubElement(questiontext_elem, 'text')
        questiontext_text.text = convert_special_chars_in_code(questiontext, to_gift=False)
        
        # General feedback (extraer de ####)
        generalfeedback = ""
        answers_lines = []
        
        for line in answers_block.split('\n'):
            line = line.strip()
            if line.startswith('####'):
                generalfeedback = line[4:].strip()
            elif line and (line.startswith('=') or line.startswith('~')):
                answers_lines.append(line)
        
        generalfeedback_elem = ET.SubElement(question, 'generalfeedback', format='markdown')
        generalfeedback_text = ET.SubElement(generalfeedback_elem, 'text')
        generalfeedback_text.text = convert_special_chars_in_code(generalfeedback, to_gift=False)
        
        # Configuración de pregunta
        ET.SubElement(question, 'defaultgrade').text = '1'
        ET.SubElement(question, 'penalty').text = '0.3333333'
        ET.SubElement(question, 'hidden').text = '0'
        ET.SubElement(question, 'idnumber').text = ''
        ET.SubElement(question, 'single').text = 'true'
        ET.SubElement(question, 'shuffleanswers').text = 'true'
        ET.SubElement(question, 'answernumbering').text = 'abc'
        ET.SubElement(question, 'showstandardinstruction').text = '1'
        
        # Feedbacks vacíos
        for fb_type in ['correctfeedback', 'partiallycorrectfeedback', 'incorrectfeedback']:
            fb = ET.SubElement(question, fb_type, format='markdown')
            ET.SubElement(fb, 'text').text = ''
        
        # Procesar respuestas
        for ans_line in answers_lines:
            symbol = ans_line[0]
            rest = ans_line[1:]
            
            # Dividir por # para separar respuesta y feedback
            parts = rest.split('#', 1)
            answer_text = parts[0].strip()
            feedback_text = parts[1].strip() if len(parts) > 1 else ""
            
            fraction = '100' if symbol == '=' else '0'
            
            answer = ET.SubElement(question, 'answer', fraction=fraction, format='markdown')
            ans_text = ET.SubElement(answer, 'text')
            ans_text.text = convert_special_chars_in_code(answer_text, to_gift=False)
            
            feedback_elem = ET.SubElement(answer, 'feedback', format='markdown')
            feedback_elem_text = ET.SubElement(feedback_elem, 'text')
            feedback_elem_text.text = convert_special_chars_in_code(feedback_text, to_gift=False)
        
        # Tags
        if tags:
            tags_elem = ET.SubElement(question, 'tags')
            for tag in tags:
                tag_elem = ET.SubElement(tags_elem, 'tag')
                tag_text = ET.SubElement(tag_elem, 'text')
                tag_text.text = tag
    
    # Generar XML con formato
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_str += ET.tostring(root, encoding='unicode', method='xml')
    
    # Formatear el XML para que sea más legible
    xml_str = format_xml(xml_str)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
    
    return xml_str


def format_xml(xml_str: str) -> str:
    """Formatea el XML para mejor legibilidad."""
    import xml.dom.minidom as minidom
    
    try:
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='  ', encoding='UTF-8').decode('UTF-8')
        
        # Eliminar líneas en blanco extras
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        return '\n'.join(lines)
    except:
        return xml_str


def convert_file(input_path: str, output_path: str = None, to_gift: bool = True):
    """
    Convierte un archivo individual.
    
    Args:
        input_path: Archivo de entrada
        output_path: Archivo de salida (opcional)
        to_gift: True para XML->GIFT, False para GIFT->XML
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")
    
    # Determinar output_path si no se especificó
    if output_path is None:
        if to_gift:
            output_path = input_path.with_suffix('.gift')
        else:
            output_path = input_path.with_suffix('.xml')
    
    output_path = Path(output_path)
    
    # Realizar conversión
    if to_gift:
        print(f"Convirtiendo {input_path} -> {output_path} (XML -> GIFT)")
        xml_to_gift(str(input_path), str(output_path))
    else:
        print(f"Convirtiendo {input_path} -> {output_path} (GIFT -> XML)")
        gift_to_xml(str(input_path), str(output_path))
    
    print(f"✓ Conversión completada: {output_path}")


def convert_directory(input_dir: str, output_dir: str, to_gift: bool = True):
    """
    Convierte todos los archivos en un directorio preservando la estructura.
    
    Args:
        input_dir: Directorio de entrada
        output_dir: Directorio de salida
        to_gift: True para XML->GIFT, False para GIFT->XML
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {input_dir}")
    
    # Determinar extensión de archivos a buscar
    extension = '.xml' if to_gift else '.gift'
    new_extension = '.gift' if to_gift else '.xml'
    
    # Encontrar todos los archivos
    files = list(input_dir.rglob(f'*{extension}'))
    
    if not files:
        print(f"No se encontraron archivos {extension} en {input_dir}")
        return
    
    print(f"Encontrados {len(files)} archivos para convertir")
    
    converted = 0
    errors = []
    
    for file_path in files:
        try:
            # Calcular ruta relativa y ruta de salida
            rel_path = file_path.relative_to(input_dir)
            out_path = output_dir / rel_path.with_suffix(new_extension)
            
            # Crear directorio de salida si no existe
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convertir archivo
            if to_gift:
                xml_to_gift(str(file_path), str(out_path))
            else:
                gift_to_xml(str(file_path), str(out_path))
            
            converted += 1
            print(f"✓ [{converted}/{len(files)}] {rel_path}")
            
        except Exception as e:
            errors.append((file_path, str(e)))
            print(f"✗ Error en {file_path}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Conversión masiva completada:")
    print(f"  - Archivos convertidos: {converted}/{len(files)}")
    print(f"  - Errores: {len(errors)}")
    
    if errors:
        print(f"\nErrores encontrados:")
        for file_path, error in errors:
            print(f"  - {file_path}: {error}")


def main():
    parser = argparse.ArgumentParser(
        description='Conversor bidireccional entre formatos Moodle XML y GIFT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Convertir XML a GIFT
  %(prog)s -i pregunta.xml -o pregunta.gift
  
  # Convertir GIFT a XML
  %(prog)s -i pregunta.gift -o pregunta.xml
  
  # Conversión masiva XML -> GIFT preservando estructura
  %(prog)s -d ./preguntas_xml -o ./preguntas_gift --to-gift
  
  # Conversión masiva GIFT -> XML preservando estructura
  %(prog)s -d ./preguntas_gift -o ./preguntas_xml --to-xml
        """
    )
    
    parser.add_argument('-i', '--input', help='Archivo de entrada')
    parser.add_argument('-o', '--output', help='Archivo/directorio de salida')
    parser.add_argument('-d', '--directory', help='Directorio para conversión masiva')
    parser.add_argument('--to-gift', action='store_true', help='Forzar conversión a GIFT')
    parser.add_argument('--to-xml', action='store_true', help='Forzar conversión a XML')
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.input and not args.directory:
        parser.error("Debe especificar --input o --directory")
    
    if args.input and args.directory:
        parser.error("No puede especificar --input y --directory simultáneamente")
    
    if args.to_gift and args.to_xml:
        parser.error("No puede especificar --to-gift y --to-xml simultáneamente")
    
    try:
        if args.directory:
            # Conversión masiva
            if not args.output:
                parser.error("Debe especificar --output para conversión masiva")
            
            # Determinar dirección de conversión
            if args.to_xml:
                to_gift = False
            elif args.to_gift:
                to_gift = True
            else:
                # Auto-detectar por contenido del directorio
                input_dir = Path(args.directory)
                xml_count = len(list(input_dir.rglob('*.xml')))
                gift_count = len(list(input_dir.rglob('*.gift')))
                
                if xml_count > gift_count:
                    to_gift = True
                elif gift_count > xml_count:
                    to_gift = False
                else:
                    parser.error("No se pudo determinar la dirección de conversión. Use --to-gift o --to-xml")
            
            convert_directory(args.directory, args.output, to_gift)
        
        else:
            # Conversión de archivo individual
            input_path = Path(args.input)
            
            # Determinar dirección de conversión
            if args.to_xml:
                to_gift = False
            elif args.to_gift:
                to_gift = True
            else:
                # Auto-detectar por extensión
                to_gift = input_path.suffix.lower() == '.xml'
            
            convert_file(args.input, args.output, to_gift)
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
