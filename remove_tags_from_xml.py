#!/usr/bin/env python3
"""
Script para eliminar recursivamente la sección de tags de preguntas XML en el repositorio.
"""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
import sys


def remove_tags_from_xml(xml_path: str, dest_path: str = None, backup: bool = True, dry_run: bool = False) -> bool:
    """
    Elimina la sección <tags> de un archivo XML de Moodle.
    
    Args:
        xml_path: Ruta al archivo XML origen
        dest_path: Ruta al archivo destino (si None, modifica in-place)
        backup: Si True, crea un backup antes de modificar (solo si in-place)
        dry_run: Si True, solo muestra qué se haría
    
    Returns:
        True si se modificó el contenido (o se copiaría modificado), False si no había tags
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
        
        if dry_run:
            if modified:
                print(f"[DRY-RUN] Se eliminarían tags de: {xml_path}" + (f" -> {dest_path}" if dest_path else " (in-place)"))
                return True
            elif dest_path:
                print(f"[DRY-RUN] Copiar sin cambios: {xml_path} -> {dest_path}")
                return False
            else:
                 return False

        if dest_path:
            # Si hay destino, escribimos allí
            dest = Path(dest_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            if modified:
                tree.write(str(dest), encoding='utf-8', xml_declaration=True)
                print(f"✓ Tags eliminados: {xml_path} -> {dest}")
                return True
            else:
                # Si no hay tags, copiamos el original
                import shutil
                shutil.copy2(xml_path, dest)
                print(f"Copiado sin cambios: {xml_path} -> {dest}")
                return False
        
        # In-place modification
        if modified:
            if backup:
                backup_path = Path(xml_path).with_suffix('.xml.bak')
                # Renombrar original a backup
                # OJO: Si usamos rename, perdemos el original si write falla?
                # Mejor leer, escribir y luego si todo bien, mover?
                # El script original usaba rename. Mantengamos simplicidad.
                
                # Para seguridad: escribir a temporal primero o copiar a backup
                import shutil
                shutil.copy2(xml_path, backup_path)
                print(f"  Backup creado: {backup_path}")
            
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            print(f"✓ Tags eliminados (in-place): {xml_path}")
            return True
        else:
             print(f"○ Sin tags: {xml_path}")
             return False
        
    except Exception as e:
        print(f"✗ Error procesando {xml_path}: {e}", file=sys.stderr)
        return False


def process_directory(source_dir: str, dest_dir: str = None, backup: bool = True, dry_run: bool = False):
    """
    Procesa recursivamente todos los archivos XML en un directorio.
    """
    source_path = Path(source_dir)
    dest_path = Path(dest_dir) if dest_dir else None

    if not source_path.exists():
        print(f"Error: Directorio no encontrado: {source_dir}", file=sys.stderr)
        return
    
    # Encontrar todos los archivos XML
    xml_files = list(source_path.rglob('*.xml'))
    
    if not xml_files:
        print(f"No se encontraron archivos XML en {source_dir}")
        return
    
    print(f"Encontrados {len(xml_files)} archivos XML")
    
    if dry_run:
        print("\n=== MODO DRY-RUN (no se realizarán cambios) ===\n")
    
    modified_count = 0
    skipped_count = 0
    error_count = 0
    
    for xml_file in xml_files:
        try:
            current_dest = None
            if dest_path:
                rel_path = xml_file.relative_to(source_path)
                current_dest = dest_path / rel_path

            if remove_tags_from_xml(str(xml_file), str(current_dest) if current_dest else None, backup, dry_run):
                modified_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            print(f"✗ Error procesando {xml_file}: {e}", file=sys.stderr)
            error_count += 1
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"Resumen:")
    print(f"  - Archivos procesados: {len(xml_files)}")
    print(f"  - Archivos modificados: {modified_count}")
    print(f"  - Archivos sin tags (o copiados): {skipped_count}")
    print(f"  - Errores: {error_count}")
    
    if dry_run and modified_count > 0:
        print(f"\nPara aplicar los cambios, ejecute sin --dry-run")


def main():
    parser = argparse.ArgumentParser(
        description='Elimina recursivamente la sección de tags de archivos XML de Moodle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Ver qué archivos se modificarían
  %(prog)s ./preguntas --dry-run
  
  # Eliminar tags in-place
  %(prog)s ./preguntas
  
  # Guardar versión limpia en otro directorio
  %(prog)s ./preguntas ./preguntas_clean
  
  # Procesar un archivo individual
  %(prog)s pregunta.xml
        """
    )
    
    parser.add_argument('source', help='Archivo o directorio origen')
    parser.add_argument('destination', nargs='?', help='Archivo o directorio destino (opcional)')
    
    parser.add_argument('--no-backup', action='store_true', help='No crear archivos de backup (solo in-place)')
    parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se haría sin realizar cambios')
    
    # Legacy flags
    parser.add_argument('-d', '--directory', help=argparse.SUPPRESS)
    parser.add_argument('-f', '--file', help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    
    # Handle legacy
    if not args.source:
        if args.directory:
            args.source = args.directory
        elif args.file:
            args.source = args.file
        else:
            parser.error("Debe especificar source")

    source_path = Path(args.source)
    
    try:
        if source_path.is_file():
            # Procesar archivo individual
            remove_tags_from_xml(
                str(source_path), 
                args.destination, 
                backup=not args.no_backup, 
                dry_run=args.dry_run
            )
        elif source_path.is_dir():
            # Procesar directorio
            process_directory(
                str(source_path), 
                args.destination, 
                backup=not args.no_backup, 
                dry_run=args.dry_run
            )
        else:
             print(f"Error: Source no encontrado: {args.source}", file=sys.stderr)
             return 1
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
