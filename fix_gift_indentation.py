#!/usr/bin/env python3
"""
Script para ajustar la indentación en bloques de código de archivos GIFT.
Reemplaza 4 espacios de indentación por '····' dentro de bloques de código (```)
"""

import argparse
import re
from pathlib import Path


def fix_code_indentation(content: str) -> tuple[str, int]:
    """
    Reemplaza 4 espacios de indentación por '····' dentro de bloques de código.
    
    Args:
        content: Contenido del archivo GIFT
        
    Returns:
        Tupla con (contenido modificado, número de reemplazos)
    """
    lines = content.split('\n')
    result_lines = []
    in_code_block = False
    total_replacements = 0
    
    for line in lines:
        # Detectar inicio/fin de bloque de código
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result_lines.append(line)
            continue
        
        if in_code_block:
            # Contar espacios al inicio de la línea
            original_line = line
            new_line = ""
            i = 0
            
            # Procesar grupos de 4 espacios al inicio
            while i + 4 <= len(line) and line[i:i+4] == "    ":
                new_line += "····"
                i += 4
                total_replacements += 1
            
            # Agregar el resto de la línea
            new_line += line[i:]
            result_lines.append(new_line)
        else:
            result_lines.append(line)
    
    return '\n'.join(result_lines), total_replacements


def process_file(filepath: Path, dry_run: bool = False) -> tuple[bool, int]:
    """
    Procesa un archivo GIFT.
    
    Args:
        filepath: Ruta al archivo
        dry_run: Si es True, no modifica el archivo
        
    Returns:
        Tupla con (archivo modificado, número de reemplazos)
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        new_content, replacements = fix_code_indentation(content)
        
        if replacements > 0 and not dry_run:
            filepath.write_text(new_content, encoding='utf-8')
        
        return replacements > 0, replacements
    except Exception as e:
        print(f"  ❌ Error procesando {filepath}: {e}")
        return False, 0


def process_directory(directory: Path, recursive: bool = True, dry_run: bool = False, verbose: bool = False) -> dict:
    """
    Procesa todos los archivos .gift en un directorio.
    
    Args:
        directory: Directorio a procesar
        recursive: Buscar recursivamente
        dry_run: Si es True, no modifica archivos
        verbose: Mostrar información detallada
        
    Returns:
        Estadísticas del procesamiento
    """
    stats = {
        'total_files': 0,
        'modified_files': 0,
        'total_replacements': 0,
        'errors': 0
    }
    
    pattern = '**/*.gift' if recursive else '*.gift'
    gift_files = list(directory.glob(pattern))
    
    if not gift_files:
        print(f"⚠️  No se encontraron archivos .gift en {directory}")
        return stats
    
    print(f"Procesando {len(gift_files)} archivos GIFT...")
    if dry_run:
        print("(Modo simulación - no se modificarán archivos)")
    print()
    
    for filepath in gift_files:
        stats['total_files'] += 1
        modified, replacements = process_file(filepath, dry_run)
        
        if modified:
            stats['modified_files'] += 1
            stats['total_replacements'] += replacements
            if verbose:
                print(f"  ✅ {filepath}: {replacements} reemplazos")
        elif verbose and replacements == 0:
            print(f"  ⏭️  {filepath}: sin cambios")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Reemplaza indentación de 4 espacios por ···· en bloques de código GIFT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s preguntas/
  %(prog)s preguntas/ --dry-run
  %(prog)s preguntas/ -v
  %(prog)s archivo.gift
        """
    )
    
    parser.add_argument('path', help='Directorio o archivo a procesar')
    parser.add_argument('-r', '--no-recursive', action='store_true',
                        help='No buscar recursivamente en subdirectorios')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='Simular sin modificar archivos')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if not path.exists():
        print(f"❌ Error: '{args.path}' no existe")
        return 1
    
    if path.is_file():
        if not path.suffix == '.gift':
            print(f"⚠️  Advertencia: '{args.path}' no tiene extensión .gift")
        
        print(f"Procesando archivo: {path}")
        if args.dry_run:
            print("(Modo simulación - no se modificará el archivo)")
        
        modified, replacements = process_file(path, args.dry_run)
        
        if modified:
            action = "se modificarían" if args.dry_run else "modificados"
            print(f"✅ {replacements} reemplazos {action}")
        else:
            print("⏭️  Sin cambios necesarios")
        
        return 0
    
    if path.is_dir():
        stats = process_directory(
            path,
            recursive=not args.no_recursive,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        
        print()
        print("=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"Archivos procesados: {stats['total_files']}")
        action = "modificarían" if args.dry_run else "modificados"
        print(f"Archivos {action}: {stats['modified_files']}")
        print(f"Total de reemplazos: {stats['total_replacements']}")
        
        return 0
    
    print(f"❌ Error: '{args.path}' no es un archivo ni directorio válido")
    return 1


if __name__ == '__main__':
    exit(main())
