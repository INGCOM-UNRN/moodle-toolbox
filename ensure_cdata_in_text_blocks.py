#!/usr/bin/env python3
"""
Script para asegurar que todos los bloques <text> tengan su contenido envuelto en CDATA.
Esto previene problemas con caracteres especiales XML en el contenido.
"""

import argparse
import re
from pathlib import Path
import sys


def ensure_cdata_in_text_blocks(xml_content: str) -> tuple[str, int]:
    """
    Asegura que todos los bloques <text> con contenido tengan CDATA.
    
    Args:
        xml_content: Contenido del archivo XML
    
    Returns:
        Tupla de (contenido modificado, número de bloques modificados)
    """
    modified_count = 0
    
    # Patrón para encontrar bloques <text>...</text> que NO tienen CDATA
    # Captura el contenido entre las etiquetas
    pattern = r'<text>(?!\s*<!\[CDATA\[)(.*?)</text>'
    
    def replace_with_cdata(match):
        nonlocal modified_count
        content = match.group(1)
        
        # Si el contenido está vacío o es solo espacios, no agregar CDATA
        if not content or content.strip() == '':
            return match.group(0)
        
        # Si ya tiene CDATA (por si acaso), no modificar
        if '<![CDATA[' in content:
            return match.group(0)
        
        modified_count += 1
        # Envolver el contenido en CDATA
        return f'<text><![CDATA[{content}]]></text>'
    
    # Aplicar la transformación
    modified_content = re.sub(pattern, replace_with_cdata, xml_content, flags=re.DOTALL)
    
    return modified_content, modified_count


def process_xml_file(xml_path: str, backup: bool = True, dry_run: bool = False) -> int:
    """
    Procesa un archivo XML individual.
    
    Args:
        xml_path: Ruta al archivo XML
        backup: Si True, crea un backup antes de modificar
        dry_run: Si True, solo muestra qué se haría sin modificar
    
    Returns:
        Número de bloques <text> modificados
    """
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        modified_content, modified_count = ensure_cdata_in_text_blocks(original_content)
        
        if modified_count > 0:
            if dry_run:
                return modified_count
            
            if backup:
                backup_path = Path(xml_path).with_suffix('.xml.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                print(f"  Backup creado: {backup_path}")
            
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            return modified_count
        
        return 0
        
    except Exception as e:
        print(f"✗ Error procesando {xml_path}: {e}", file=sys.stderr)
        raise


def process_directory(directory: str, backup: bool = True, dry_run: bool = False):
    """
    Procesa recursivamente todos los archivos XML en un directorio.
    
    Args:
        directory: Directorio raíz a procesar
        backup: Si True, crea backups antes de modificar
        dry_run: Si True, solo muestra qué se haría sin modificar
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"Error: Directorio no encontrado: {directory}", file=sys.stderr)
        return
    
    # Encontrar todos los archivos XML
    xml_files = list(dir_path.rglob('*.xml'))
    
    if not xml_files:
        print(f"No se encontraron archivos XML en {directory}")
        return
    
    print(f"Encontrados {len(xml_files)} archivos XML")
    
    if dry_run:
        print("\n=== MODO DRY-RUN (no se realizarán cambios) ===\n")
    
    total_blocks_modified = 0
    files_modified_count = 0
    files_unchanged_count = 0
    error_count = 0
    
    for xml_file in xml_files:
        try:
            blocks_modified = process_xml_file(str(xml_file), backup, dry_run)
            
            if blocks_modified > 0:
                if dry_run:
                    print(f"[DRY-RUN] Se modificarían {blocks_modified} bloques en: {xml_file}")
                else:
                    print(f"✓ Modificados {blocks_modified} bloques <text> en: {xml_file}")
                files_modified_count += 1
                total_blocks_modified += blocks_modified
            else:
                print(f"○ Sin cambios necesarios: {xml_file}")
                files_unchanged_count += 1
                
        except Exception as e:
            print(f"✗ Error procesando {xml_file}: {e}", file=sys.stderr)
            error_count += 1
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"Resumen:")
    print(f"  - Archivos procesados: {len(xml_files)}")
    print(f"  - Archivos modificados: {files_modified_count}")
    print(f"  - Archivos sin cambios: {files_unchanged_count}")
    print(f"  - Total bloques <text> con CDATA agregado: {total_blocks_modified}")
    print(f"  - Errores: {error_count}")
    
    if dry_run and files_modified_count > 0:
        print(f"\nPara aplicar los cambios, ejecute sin --dry-run")


def main():
    parser = argparse.ArgumentParser(
        description='Asegura que todos los bloques <text> tengan su contenido envuelto en CDATA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Ver qué archivos se modificarían (sin hacer cambios)
  %(prog)s -d ./preguntas --dry-run
  
  # Procesar directorio con backup automático
  %(prog)s -d ./preguntas
  
  # Procesar sin crear backup
  %(prog)s -d ./preguntas --no-backup
  
  # Procesar un archivo individual
  %(prog)s -f pregunta.xml
  
Nota: Los bloques <text> vacíos o con solo espacios no se modifican.
      El contenido con CDATA existente no se modifica.
        """
    )
    
    parser.add_argument('-d', '--directory', help='Directorio a procesar recursivamente')
    parser.add_argument('-f', '--file', help='Archivo XML individual a procesar')
    parser.add_argument('--no-backup', action='store_true', help='No crear archivos de backup')
    parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se haría sin realizar cambios')
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.directory and not args.file:
        parser.error("Debe especificar --directory o --file")
    
    if args.directory and args.file:
        parser.error("No puede especificar --directory y --file simultáneamente")
    
    try:
        if args.file:
            # Procesar archivo individual
            if args.dry_run:
                blocks = process_xml_file(args.file, backup=not args.no_backup, dry_run=True)
                if blocks > 0:
                    print(f"[DRY-RUN] Se modificarían {blocks} bloques <text> en: {args.file}")
                else:
                    print(f"○ No se requieren cambios en: {args.file}")
            else:
                blocks = process_xml_file(args.file, backup=not args.no_backup, dry_run=False)
                if blocks > 0:
                    print(f"✓ Modificados {blocks} bloques <text> en: {args.file}")
                else:
                    print(f"○ No se encontraron bloques <text> que modificar en: {args.file}")
        else:
            # Procesar directorio recursivamente
            process_directory(args.directory, backup=not args.no_backup, dry_run=args.dry_run)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
