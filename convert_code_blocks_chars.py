#!/usr/bin/env python3
"""
Script para convertir caracteres especiales dentro de bloques de código markdown.
Soporta conversión bidireccional entre caracteres normales y fullwidth.
"""

import argparse
import re
from pathlib import Path
import sys

# Mapeo de caracteres especiales fullwidth a caracteres normales
SPECIAL_CHARS_TO_NORMAL = {
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
    "＂": '"',
    "：": ":",
}

# Mapeo de entidades XML/HTML a caracteres fullwidth
XML_ENTITIES_TO_FULLWIDTH = {
    "&lt;": "＜",
    "&gt;": "＞",
    "&amp;": "＆",
    "&quot;": "＂",
    "&apos;": "＇",
    "&#39;": "＇",
    "&#34;": "＂",
    "&#60;": "＜",
    "&#62;": "＞",
    "&#38;": "＆",
    "&nbsp;": "　",
}

# Crear mapeos inversos
NORMAL_TO_SPECIAL_CHARS = {v: k for k, v in SPECIAL_CHARS_TO_NORMAL.items() if v != "\n" and v != "\t"}
FULLWIDTH_TO_XML_ENTITIES = {v: k for k, v in XML_ENTITIES_TO_FULLWIDTH.items()}


def convert_code_block_content(content: str, to_normal: bool = True) -> str:
    """
    Convierte el contenido de un bloque de código.
    
    Args:
        content: Contenido del bloque de código
        to_normal: True para fullwidth->normal, False para normal->fullwidth
    
    Returns:
        Contenido convertido
    """
    if to_normal:
        # Convertir caracteres especiales fullwidth a normales
        for fullwidth, normal in SPECIAL_CHARS_TO_NORMAL.items():
            content = content.replace(fullwidth, normal)
        
        # Convertir caracteres fullwidth a entidades XML (si corresponde)
        for fullwidth, entity in FULLWIDTH_TO_XML_ENTITIES.items():
            # Solo convertir si el caracter fullwidth no está en SPECIAL_CHARS_TO_NORMAL
            if fullwidth not in SPECIAL_CHARS_TO_NORMAL:
                content = content.replace(fullwidth, entity)
    else:
        # Primero convertir entidades XML a fullwidth
        for entity, fullwidth in XML_ENTITIES_TO_FULLWIDTH.items():
            content = content.replace(entity, fullwidth)
        
        # Luego convertir caracteres normales a fullwidth (evitando duplicados)
        for normal, fullwidth in NORMAL_TO_SPECIAL_CHARS.items():
            content = content.replace(normal, fullwidth)
    
    return content


def convert_markdown_code_blocks(text: str, to_normal: bool = True) -> tuple[str, int]:
    """
    Convierte caracteres especiales en bloques de código markdown.
    
    Args:
        text: Texto markdown
        to_normal: True para fullwidth->normal, False para normal->fullwidth
    
    Returns:
        Tupla de (texto convertido, número de bloques modificados)
    """
    blocks_modified = 0
    
    # Convertir bloques de código con ``` (multilinea)
    def replace_code_block(match):
        nonlocal blocks_modified
        lang = match.group(1) or ''
        content = match.group(2)
        converted = convert_code_block_content(content, to_normal)
        
        if converted != content:
            blocks_modified += 1
        
        return f"```{lang}\n{converted}\n```"
    
    # Usar DOTALL para capturar saltos de línea, pero ser más específico con el cierre
    text = re.sub(r'```([a-z]*)\n(.*?)```', replace_code_block, text, flags=re.DOTALL)
    
    # Convertir código inline con ` (una sola línea)
    def replace_inline_code(match):
        nonlocal blocks_modified
        content = match.group(1)
        converted = convert_code_block_content(content, to_normal)
        
        if converted != content:
            blocks_modified += 1
        
        return f"`{converted}`"
    
    text = re.sub(r'`([^`\n]+)`', replace_inline_code, text)
    
    return text, blocks_modified


def process_xml_cdata(text: str, to_normal: bool = True) -> tuple[str, int]:
    """
    Procesa secciones CDATA en archivos XML, convirtiendo solo bloques de código dentro.
    
    Args:
        text: Contenido del archivo XML
        to_normal: True para fullwidth->normal, False para normal->fullwidth
    
    Returns:
        Tupla de (texto procesado, número de bloques modificados)
    """
    total_blocks = 0
    
    def replace_cdata(match):
        nonlocal total_blocks
        cdata_content = match.group(1)
        converted_content, blocks = convert_markdown_code_blocks(cdata_content, to_normal)
        total_blocks += blocks
        return f"<![CDATA[{converted_content}]]>"
    
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', replace_cdata, text, flags=re.DOTALL)
    
    return text, total_blocks


def process_file(file_path: str, to_normal: bool = True, backup: bool = True, dry_run: bool = False) -> int:
    """
    Procesa un archivo individual.
    
    Args:
        file_path: Ruta al archivo
        to_normal: True para fullwidth->normal, False para normal->fullwidth
        backup: Si True, crea un backup antes de modificar
        dry_run: Si True, solo muestra qué se haría sin modificar
    
    Returns:
        Número de bloques de código modificados
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Para archivos XML, procesar solo dentro de CDATA
        if file_path.lower().endswith('.xml'):
            converted_content, blocks_modified = process_xml_cdata(original_content, to_normal)
        else:
            converted_content, blocks_modified = convert_markdown_code_blocks(original_content, to_normal)
        
        if blocks_modified > 0:
            if dry_run:
                return blocks_modified
            
            if backup:
                backup_path = Path(file_path).with_suffix(Path(file_path).suffix + '.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                print(f"  Backup creado: {backup_path}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
            
            return blocks_modified
        
        return 0
        
    except Exception as e:
        print(f"✗ Error procesando {file_path}: {e}", file=sys.stderr)
        raise


def process_directory(directory: str, extensions: list, to_normal: bool = True, 
                     recursive: bool = False, backup: bool = True, dry_run: bool = False):
    """
    Procesa archivos en un directorio.
    
    Args:
        directory: Directorio a procesar
        extensions: Lista de extensiones de archivo a procesar
        to_normal: True para fullwidth->normal, False para normal->fullwidth
        recursive: Si True, procesa subdirectorios recursivamente
        backup: Si True, crea backups antes de modificar
        dry_run: Si True, solo muestra qué se haría sin modificar
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"Error: Directorio no encontrado: {directory}", file=sys.stderr)
        return
    
    # Encontrar todos los archivos con las extensiones especificadas
    files = []
    for ext in extensions:
        if recursive:
            files.extend(dir_path.rglob(f'*.{ext}'))
        else:
            files.extend(dir_path.glob(f'*.{ext}'))
    
    if not files:
        print(f"No se encontraron archivos con extensiones {extensions} en {directory}")
        return
    
    direction = "fullwidth → normal" if to_normal else "normal → fullwidth"
    print(f"Encontrados {len(files)} archivos")
    print(f"Dirección de conversión: {direction}")
    
    if dry_run:
        print("\n=== MODO DRY-RUN (no se realizarán cambios) ===\n")
    
    total_blocks_modified = 0
    files_modified_count = 0
    files_unchanged_count = 0
    error_count = 0
    
    for file_path in files:
        try:
            blocks_modified = process_file(str(file_path), to_normal, backup, dry_run)
            
            if blocks_modified > 0:
                if dry_run:
                    print(f"[DRY-RUN] Se modificarían {blocks_modified} bloques en: {file_path}")
                else:
                    print(f"✓ Modificados {blocks_modified} bloques de código en: {file_path}")
                files_modified_count += 1
                total_blocks_modified += blocks_modified
            else:
                print(f"○ Sin cambios necesarios: {file_path}")
                files_unchanged_count += 1
                
        except Exception as e:
            print(f"✗ Error procesando {file_path}: {e}", file=sys.stderr)
            error_count += 1
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"Resumen:")
    print(f"  - Archivos procesados: {len(files)}")
    print(f"  - Archivos modificados: {files_modified_count}")
    print(f"  - Archivos sin cambios: {files_unchanged_count}")
    print(f"  - Total bloques de código modificados: {total_blocks_modified}")
    print(f"  - Errores: {error_count}")
    
    if dry_run and files_modified_count > 0:
        print(f"\nPara aplicar los cambios, ejecute sin --dry-run")


def main():
    parser = argparse.ArgumentParser(
        description='Convierte caracteres especiales en bloques de código markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Ver qué archivos se modificarían (conversión a normal)
  %(prog)s -d ./preguntas --dry-run
  
  # Convertir fullwidth a normal en archivos .gift
  %(prog)s -d ./preguntas --to-normal
  
  # Convertir normal a fullwidth en archivos .md
  %(prog)s -d ./docs --to-fullwidth -e md
  
  # Procesar recursivamente múltiples extensiones
  %(prog)s -d ./preguntas -r -e gift md xml --to-normal
  
  # Procesar un archivo individual
  %(prog)s -f pregunta.gift --to-normal
  
  # Sin crear backup
  %(prog)s -f pregunta.gift --to-normal --no-backup

Conversiones soportadas:
  Caracteres fullwidth ↔ normales:
    ＝ ↔ =, ＃ ↔ #, ｛ ↔ {, ｝ ↔ }, ＞ ↔ >, ＜ ↔ <, etc.
  
  Entidades XML ↔ fullwidth:
    &lt; ↔ ＜, &gt; ↔ ＞, &amp; ↔ ＆, &quot; ↔ ＂, etc.

Nota: Solo se modifican caracteres dentro de bloques de código (``` y `)
        """
    )
    
    parser.add_argument('-d', '--directory', help='Directorio a procesar')
    parser.add_argument('-f', '--file', help='Archivo individual a procesar')
    parser.add_argument('-r', '--recursive', action='store_true', help='Procesar subdirectorios recursivamente')
    parser.add_argument('-e', '--extensions', nargs='+', default=['gift', 'md'], 
                       help='Extensiones de archivo a procesar (default: gift md)')
    parser.add_argument('--to-normal', action='store_true', help='Convertir fullwidth a caracteres normales (default)')
    parser.add_argument('--to-fullwidth', action='store_true', help='Convertir caracteres normales a fullwidth')
    parser.add_argument('--no-backup', action='store_true', help='No crear archivos de backup')
    parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se haría sin realizar cambios')
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.directory and not args.file:
        parser.error("Debe especificar --directory o --file")
    
    if args.directory and args.file:
        parser.error("No puede especificar --directory y --file simultáneamente")
    
    if args.to_normal and args.to_fullwidth:
        parser.error("No puede especificar --to-normal y --to-fullwidth simultáneamente")
    
    # Determinar dirección de conversión (por defecto: to_normal)
    to_normal = not args.to_fullwidth
    
    try:
        if args.file:
            # Procesar archivo individual
            blocks = process_file(args.file, to_normal, backup=not args.no_backup, dry_run=args.dry_run)
            
            direction = "fullwidth → normal" if to_normal else "normal → fullwidth"
            
            if blocks > 0:
                if args.dry_run:
                    print(f"[DRY-RUN] Se modificarían {blocks} bloques de código en: {args.file}")
                    print(f"Dirección: {direction}")
                else:
                    print(f"✓ Modificados {blocks} bloques de código en: {args.file}")
                    print(f"Dirección: {direction}")
            else:
                print(f"○ No se encontraron bloques de código que modificar en: {args.file}")
        else:
            # Procesar directorio
            process_directory(args.directory, args.extensions, to_normal, 
                            args.recursive, not args.no_backup, args.dry_run)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
