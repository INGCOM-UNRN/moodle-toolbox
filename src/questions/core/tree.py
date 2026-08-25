"""Export/collect de bancos GIFT y Moodle XML hacia árboles de directorios.

Absorbe la funcionalidad de moodle-reorganizer sobre un diseño propio:
un banco monolítico se exporta a un árbol `<categoría>/<pregunta>.<ext>`
(1 archivo por pregunta) y puede recolectarse nuevamente a un archivo único,
preservando categorías ($CATEGORY / type="category"), escapes de GIFT y
bloques CDATA del XML.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from questions.core.converter import _serializar_quiz, _cdata_sub
from questions.core.xml_tools import sanitize_filename, ensure_cdata_in_text_blocks


def sanitize_dirname(part: str) -> str:
    """Sanitiza un segmento de ruta de categoría preservando las mayúsculas."""
    s = re.sub(r'[^\w\s-]', '', part.strip()).strip()
    s = re.sub(r'[-\s]+', '_', s)
    return s[:60]


# ---------------------------------------------------------------------------
# Utilidades GIFT
# ---------------------------------------------------------------------------

def _protect_backslashes_in_code(text: str) -> str:
    r"""Reemplaza backslashes (\) por ＼ dentro de bloques de código GIFT."""

    def en_bloque(match):
        return match.group(0).replace('\\', '＼')

    text = re.sub(r'```[^`]*```', en_bloque, text, flags=re.DOTALL)
    text = re.sub(r'(?<!`)(`[^`\n]+`)(?!`)', en_bloque, text)
    return text


def _format_gift_block(block: str) -> str:
    """Formatea un bloque GIFT con saltos de línea legibles."""
    try:
        title_start = block.index('::')
        title_end = block.index('::', title_start + 2)
        title_part = block[title_start:title_end + 2]
        content_after_title = block[title_end + 2:]

        if _is_cloze_question(content_after_title):
            return f"{title_part.strip()}\n{content_after_title.strip()}\n"

        brace_start = block.index('{')
        brace_end = block.rindex('}')

        if not (title_end < brace_start < brace_end):
            return block + '\n'

        stem_part = block[title_end + 2:brace_start]
        answer_part = block[brace_start + 1:brace_end]

        return (
            f"{title_part.strip()}\n"
            f"{stem_part.strip()}\n"
            f"{{\n"
            f"{answer_part.strip()}\n"
            f"}}\n"
        )
    except (ValueError, IndexError):
        return block + '\n'


def _is_cloze_question(content: str) -> bool:
    try:
        first_open = content.index('{')
        first_close = content.index('}', first_open)
        before_brace = content[:first_open].strip()
        after_close = content[first_close + 1:].strip()
        if before_brace and after_close:
            return True
        if content.count('{') > 1:
            return True
    except (ValueError, IndexError):
        pass
    return False


def gift_export(input_file: Path, base_output_dir: Path) -> int:
    """Exporta un banco GIFT monolítico a un árbol de directorios."""
    print(f"Exportando GIFT desde: {input_file}")
    contenido = input_file.read_text(encoding='utf-8')

    # División por bloques separados por líneas en blanco (convención de
    # `questions split`); cada bloque puede contener $CATEGORY y/o una pregunta.
    bloques = [b.strip() for b in re.split(r'\n\s*\n', contenido) if b.strip()]

    current_category = ''
    question_count = 0
    used_filenames: dict[str, int] = {}

    for bloque in bloques:
        cat_match = re.search(r'^\$CATEGORY:\s*(.*)', bloque, flags=re.MULTILINE)
        if cat_match:
            categoria = cat_match.group(1).strip()
            partes = [sanitize_dirname(p) for p in categoria.split('/')
                      if p.strip() and p != '$course$']
            current_category = '/'.join(partes)
            if not re.search(r'::.*?::', bloque, re.DOTALL):
                continue  # bloque sólo-declarativa de categoría

        title_match = re.search(r'::(.*?)::', bloque, re.DOTALL)
        if not title_match:
            continue

        formatted = _format_gift_block(bloque)
        titulo_completo = title_match.group(1).strip()

        categoria_del_titulo = ''
        titulo_real = titulo_completo
        if '/' in titulo_completo:
            partes_titulo = titulo_completo.split('/')
            if len(partes_titulo) > 1:
                titulo_real = partes_titulo[-1]
                categoria_del_titulo = '/'.join(
                    sanitize_dirname(p) for p in partes_titulo[:-1])

        categoria_final = categoria_del_titulo or current_category
        base_name = sanitize_filename(titulo_real)

        output_dir = base_output_dir / categoria_final if categoria_final else base_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        if base_name in used_filenames:
            used_filenames[base_name] += 1
            filename = f"{base_name}_{used_filenames[base_name]}.gift"
        else:
            used_filenames[base_name] = 0
            filename = f"{base_name}.gift"

        destino = output_dir / filename
        destino.write_text(formatted, encoding='utf-8')
        print(f"  Creado: {destino.relative_to(base_output_dir)}")
        question_count += 1

    print(f"\n✓ Exportación completada: {question_count} preguntas")
    return question_count


def gift_collect(base_input_dir: Path, output_file: Path) -> int:
    """Recolecta un árbol de preguntas GIFT en un archivo monolítico."""
    print(f"Recolectando GIFT desde: {base_input_dir}")

    gift_files = sorted(
        (str(p.relative_to(base_input_dir)), p)
        for p in base_input_dir.rglob('*.gift') if p.is_file()
    )

    if not gift_files:
        print("No se encontraron archivos .gift en el directorio indicado.")
        return 0

    question_count = 0
    current_category = None
    lineas_salida = []

    for rel_path, filepath in gift_files:
        dir_path = str(Path(rel_path).parent)
        dir_path = '' if dir_path == '.' else dir_path.replace(os.sep, '/')

        if dir_path != current_category:
            current_category = dir_path
            if dir_path:
                lineas_salida.append(f"\n$CATEGORY: $course$/{dir_path}\n")
            else:
                lineas_salida.append("\n$CATEGORY: $course$\n")

        content = filepath.read_text(encoding='utf-8')
        content = _protect_backslashes_in_code(content)

        lineas_salida.append(f"// {rel_path}")
        lineas_salida.append(content.strip() + '\n')
        question_count += 1
        print(f"  Agregada: {rel_path}")

    output_file.write_text('\n'.join(lineas_salida), encoding='utf-8')
    print(f"\n✓ Colección completada: {question_count} preguntas en {output_file}")
    return question_count


# ---------------------------------------------------------------------------
# Moodle XML
# ---------------------------------------------------------------------------

def _quiz_de_pregunta(question: ET.Element) -> ET.Element:
    quiz = ET.Element('quiz')
    quiz.append(question)
    return quiz


def xml_export(input_file: Path, base_output_dir: Path) -> int:
    """Exporta un banco Moodle XML monolítico a un árbol de directorios."""
    print(f"Exportando Moodle XML desde: {input_file}")

    try:
        root = ET.fromstring(input_file.read_text(encoding='utf-8'))
    except (ET.ParseError, UnicodeDecodeError) as e:
        print(f"Error: no se pudo interpretar el XML: {e}", file=sys.stderr)
        return -1

    current_category = ''
    question_count = 0
    used_filenames: dict[str, int] = {}

    for question in root.findall('question'):
        qtype = question.get('type')

        if qtype == 'category':
            texto = question.find('category/text')
            if texto is not None and texto.text:
                partes = [sanitize_dirname(p) for p in texto.text.split('/')
                          if p.strip() and p != '$course$']
                current_category = '/'.join(partes)
            continue

        nombre = question.find('name/text')
        if nombre is None or not nombre.text:
            continue

        base_name = sanitize_filename(nombre.text.strip())

        output_dir = base_output_dir / current_category if current_category else base_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        if base_name in used_filenames:
            used_filenames[base_name] += 1
            filename = f"{base_name}_{used_filenames[base_name]}.xml"
        else:
            used_filenames[base_name] = 0
            filename = f"{base_name}.xml"

        destino = output_dir / filename
        destino.write_text(_serializar_quiz(_quiz_de_pregunta(question)), encoding='utf-8')
        print(f"  Creado: {destino.relative_to(base_output_dir)}")
        question_count += 1

    print(f"\n✓ Exportación completada: {question_count} preguntas")
    return question_count


def xml_collect(base_input_dir: Path, output_file: Path) -> int:
    """Recolecta un árbol de preguntas Moodle XML en un archivo monolítico."""
    print(f"Recolectando Moodle XML desde: {base_input_dir}")

    xml_files = sorted(
        (str(p.relative_to(base_input_dir)), p)
        for p in base_input_dir.rglob('*.xml')
        if p.is_file() and not p.name.startswith('.')
    )

    if not xml_files:
        print("No se encontraron archivos .xml en el directorio indicado.")
        return 0

    quiz_root = ET.Element('quiz')
    current_category = None
    question_count = 0

    for rel_path, filepath in xml_files:
        dir_path = str(Path(rel_path).parent)
        dir_path = '' if dir_path == '.' else dir_path.replace(os.sep, '/')

        if dir_path != current_category:
            current_category = dir_path
            cat_q = ET.SubElement(quiz_root, 'question', {'type': 'category'})
            cat = _cdata_sub(cat_q, 'category')
            ruta = f"$course$/{dir_path}" if dir_path else "$course$"
            _cdata_sub(cat, "text", ruta)

        try:
            tree = ET.parse(filepath)
            for question in tree.getroot().findall('question'):
                if question.get('type') == 'category':
                    continue
                quiz_root.append(question)
                question_count += 1
                print(f"  Agregada: {rel_path}")
        except (ET.ParseError, UnicodeDecodeError) as e:
            print(f"  Error interpretando {filepath}: {e}", file=sys.stderr)

    xml = _serializar_quiz(quiz_root)
    xml, _ = ensure_cdata_in_text_blocks(xml)
    output_file.write_text(xml, encoding='utf-8')
    print(f"\n✓ Colección completada: {question_count} preguntas en {output_file}")
    return question_count


# ---------------------------------------------------------------------------
# Punto de entrada unificado por formato
# ---------------------------------------------------------------------------

def exportar(archivo: Path, dir_destino: Path, formato: str | None = None) -> int:
    """Exporta un banco a un árbol de directorios según su formato."""
    formato = (formato or ('gift' if archivo.suffix.lower() == '.gift' else 'xml')).lower()
    dir_destino.mkdir(parents=True, exist_ok=True)
    if formato == 'gift':
        return gift_export(archivo, dir_destino)
    if formato == 'xml':
        return xml_export(archivo, dir_destino)
    raise ValueError(f"Formato desconocido: {formato}")


def recolectar(directorio: Path, archivo_destino: Path, formato: str | None = None) -> int:
    """Recolecta un árbol de directorios en un banco según el formato."""
    formato = (formato or ('gift' if archivo_destino.suffix.lower() == '.gift' else 'xml')).lower()
    if formato == 'gift':
        return gift_collect(directorio, archivo_destino)
    if formato == 'xml':
        return xml_collect(directorio, archivo_destino)
    raise ValueError(f"Formato desconocido: {formato}")
