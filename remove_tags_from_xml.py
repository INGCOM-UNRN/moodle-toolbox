#!/usr/bin/env python3
"""
Script para eliminar recursivamente la sección de tags de preguntas XML en el repositorio.
"""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
import sys


def remove_tags_from_xml(xml_path: str, backup: bool = True) -> bool:
    """
    Elimina la sección <tags> de un archivo XML de Moodle.
    
    Args:
        xml_path: Ruta al archivo XML
        backup: Si True, crea un backup antes de modificar
    
    Returns:
        True si se modificó el archivo, False si no había tags
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        modified = False
        
        # Buscar y eliminar todas las secciones <tags> en todas las preguntas
        for question in root.findall('question'):
            tags_elem = question.find('tags')
            if tags_elem is not None:
                question.remove(tags_elem)
                modified = True
        
        if modified:
            if backup:
                backup_path = Path(xml_path).with_suffix('.xml.bak')
                Path(xml_path).rename(backup_path)
                print(f"  Backup creado: {backup_path}")
            
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            return True
        
        return False
        
    except Exception as e:
        print(f"✗ Error procesando {xml_path}: {e}", file=sys.stderr)
        return False


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
    
    modified_count = 0
    skipped_count = 0
    error_count = 0
    
    for xml_file in xml_files:
        try:
            # Verificar si tiene tags antes de procesar
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            has_tags = False
            for question in root.findall('question'):
                if question.find('tags') is not None:
                    has_tags = True
                    break
            
            if has_tags:
                if dry_run:
                    print(f"[DRY-RUN] Se eliminarían tags de: {xml_file}")
                    modified_count += 1
                else:
                    if remove_tags_from_xml(str(xml_file), backup):
                        print(f"✓ Tags eliminados: {xml_file}")
                        modified_count += 1
            else:
                print(f"○ Sin tags: {xml_file}")
                skipped_count += 1
                
        except Exception as e:
            print(f"✗ Error procesando {xml_file}: {e}", file=sys.stderr)
            error_count += 1
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"Resumen:")
    print(f"  - Archivos procesados: {len(xml_files)}")
    print(f"  - Archivos modificados: {modified_count}")
    print(f"  - Archivos sin tags: {skipped_count}")
    print(f"  - Errores: {error_count}")
    
    if dry_run and modified_count > 0:
        print(f"\nPara aplicar los cambios, ejecute sin --dry-run")


def main():
    parser = argparse.ArgumentParser(
        description='Elimina recursivamente la sección de tags de archivos XML de Moodle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Ver qué archivos se modificarían (sin hacer cambios)
  %(prog)s -d ./preguntas --dry-run
  
  # Eliminar tags con backup automático
  %(prog)s -d ./preguntas
  
  # Eliminar tags sin crear backup
  %(prog)s -d ./preguntas --no-backup
  
  # Procesar un archivo individual
  %(prog)s -f pregunta.xml
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
                print(f"[DRY-RUN] Se procesaría: {args.file}")
            else:
                if remove_tags_from_xml(args.file, backup=not args.no_backup):
                    print(f"✓ Tags eliminados de: {args.file}")
                else:
                    print(f"○ No se encontraron tags en: {args.file}")
        else:
            # Procesar directorio recursivamente
            process_directory(args.directory, backup=not args.no_backup, dry_run=args.dry_run)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
