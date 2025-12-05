#!/usr/bin/env python3
"""
Script para renombrar archivos XML según el nombre de la pregunta contenida.
Sanitiza el nombre reemplazando espacios por _ y eliminando caracteres no alfanuméricos.
"""

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import sys


def sanitize_filename(text: str, max_length: int = 200) -> str:
    """
    Sanitiza un texto para usarlo como nombre de archivo.
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima del nombre de archivo
    
    Returns:
        Texto sanitizado apto para nombre de archivo
    """
    # Convertir a minúsculas
    text = text.lower()
    
    # Reemplazar caracteres con acento/tilde por su equivalente sin acento
    accent_map = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
        'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
        'ã': 'a', 'õ': 'o', 'ñ': 'n', 'ç': 'c'
    }
    
    for accented, unaccented in accent_map.items():
        text = text.replace(accented, unaccented)
    
    # Reemplazar espacios por guiones bajos
    text = text.replace(' ', '_')
    
    # Mantener solo caracteres alfanuméricos, guiones bajos y guiones
    text = re.sub(r'[^a-z0-9_-]', '', text)
    
    # Eliminar guiones bajos múltiples consecutivos
    text = re.sub(r'_+', '_', text)
    
    # Eliminar guiones bajos al inicio y final
    text = text.strip('_-')
    
    # Limitar longitud
    if len(text) > max_length:
        text = text[:max_length].rstrip('_-')
    
    # Si quedó vacío, usar un nombre por defecto
    if not text:
        text = 'unnamed_question'
    
    return text


def get_question_name_from_xml(xml_path: str) -> str:
    """
    Extrae el nombre de la pregunta de un archivo XML.
    
    Args:
        xml_path: Ruta al archivo XML
    
    Returns:
        Nombre de la pregunta o None si no se encuentra
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Buscar la primera pregunta
        question = root.find('question')
        if question is None:
            return None
        
        # Buscar el elemento name/text
        name_elem = question.find('name/text')
        if name_elem is not None and name_elem.text:
            return name_elem.text.strip()
        
        return None
        
    except Exception as e:
        raise Exception(f"Error al parsear XML: {e}")


def rename_xml_file(xml_path: str, dry_run: bool = False, force: bool = False, used_names: set = None) -> tuple[bool, str, str]:
    """
    Renombra un archivo XML según el nombre de su pregunta.
    
    Args:
        xml_path: Ruta al archivo XML
        dry_run: Si True, solo simula el cambio
        force: Si True, sobrescribe archivos existentes
        used_names: Conjunto de nombres ya utilizados para detectar colisiones
    
    Returns:
        Tupla de (éxito, nombre_antiguo, nombre_nuevo)
    """
    path = Path(xml_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {xml_path}")
    
    if used_names is None:
        used_names = set()
    
    # Obtener nombre de la pregunta
    question_name = get_question_name_from_xml(str(path))
    
    if not question_name:
        raise Exception("No se pudo encontrar el nombre de la pregunta en el XML")
    
    # Sanitizar nombre
    sanitized_name = sanitize_filename(question_name)
    
    # Manejar colisiones de nombres
    new_filename = f"{sanitized_name}.xml"
    new_path = path.parent / new_filename
    
    # Si el nombre es el mismo que el actual, no hacer nada
    if path.name == new_filename:
        used_names.add(new_filename)
        return False, str(path.name), str(new_filename)
    
    # Si hay colisión, agregar sufijo __n
    collision_counter = 1
    while (new_filename in used_names or new_path.exists()) and not force:
        new_filename = f"{sanitized_name}__{collision_counter}.xml"
        new_path = path.parent / new_filename
        collision_counter += 1
        
        # Protección contra loops infinitos
        if collision_counter > 1000:
            raise Exception(f"Demasiadas colisiones para el nombre: {sanitized_name}")
    
    # Marcar el nombre como usado
    used_names.add(new_filename)
    
    if dry_run:
        return True, str(path.name), str(new_filename)
    
    # Renombrar archivo
    if new_path.exists() and force:
        new_path.unlink()
    
    path.rename(new_path)
    
    return True, str(path.name), str(new_filename)


def process_directory(directory: str, recursive: bool = False, dry_run: bool = False, force: bool = False):
    """
    Procesa archivos XML en un directorio.
    
    Args:
        directory: Directorio a procesar
        recursive: Si True, procesa subdirectorios recursivamente
        dry_run: Si True, solo simula los cambios
        force: Si True, sobrescribe archivos existentes
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"Error: Directorio no encontrado: {directory}", file=sys.stderr)
        return
    
    # Encontrar todos los archivos XML
    if recursive:
        xml_files = list(dir_path.rglob('*.xml'))
    else:
        xml_files = list(dir_path.glob('*.xml'))
    
    if not xml_files:
        print(f"No se encontraron archivos XML en {directory}")
        return
    
    print(f"Encontrados {len(xml_files)} archivos XML")
    
    if dry_run:
        print("\n=== MODO DRY-RUN (no se realizarán cambios) ===\n")
    
    renamed_count = 0
    unchanged_count = 0
    error_count = 0
    collision_count = 0
    
    changes = []
    used_names = set()
    
    for xml_file in xml_files:
        try:
            success, old_name, new_name = rename_xml_file(str(xml_file), dry_run, force, used_names)
            
            if success:
                # Detectar si hubo colisión (tiene sufijo __n)
                is_collision = '__' in new_name and new_name.split('__')[-1].replace('.xml', '').isdigit()
                
                if dry_run:
                    prefix = "[DRY-RUN][COLISIÓN]" if is_collision else "[DRY-RUN]"
                    print(f"{prefix} {old_name} → {new_name}")
                else:
                    prefix = "✓ [COLISIÓN]" if is_collision else "✓"
                    print(f"{prefix} Renombrado: {old_name} → {new_name}")
                
                if is_collision:
                    collision_count += 1
                
                renamed_count += 1
                changes.append((old_name, new_name))
            else:
                print(f"○ Sin cambios: {old_name}")
                unchanged_count += 1
                
        except Exception as e:
            print(f"✗ Error procesando {xml_file.name}: {e}", file=sys.stderr)
            error_count += 1
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"Resumen:")
    print(f"  - Archivos procesados: {len(xml_files)}")
    print(f"  - Archivos renombrados: {renamed_count}")
    print(f"  - Colisiones resueltas: {collision_count}")
    print(f"  - Archivos sin cambios: {unchanged_count}")
    print(f"  - Errores: {error_count}")
    
    if dry_run and renamed_count > 0:
        print(f"\nPara aplicar los cambios, ejecute sin --dry-run")


def main():
    parser = argparse.ArgumentParser(
        description='Renombra archivos XML según el nombre de la pregunta contenida',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Ver qué archivos se renombrarían (sin hacer cambios)
  %(prog)s -d ./preguntas --dry-run
  
  # Renombrar archivos en un directorio (no recursivo)
  %(prog)s -d ./preguntas
  
  # Renombrar archivos recursivamente
  %(prog)s -d ./preguntas -r
  
  # Renombrar sobrescribiendo archivos existentes
  %(prog)s -d ./preguntas --force
  
  # Renombrar un archivo individual
  %(prog)s -f pregunta.xml
  
Reglas de sanitización:
  - Convierte a minúsculas
  - Reemplaza caracteres acentuados por su equivalente sin acento (á→a, é→e, etc.)
  - Reemplaza espacios por _
  - Elimina caracteres no alfanuméricos (excepto _ y -)
  - Elimina guiones bajos múltiples consecutivos
  - Limita a 200 caracteres
  - En caso de colisión, agrega sufijo __n (donde n es el número)
  
Ejemplos:
  "Recursión: Relación entre Llamada" → "recursion_relacion_entre_llamada.xml"
  "Análisis de Algoritmos" → "analisis_de_algoritmos.xml"
  Si hay colisión → "recursion_relacion_entre_llamada__1.xml"
  Segunda colisión → "recursion_relacion_entre_llamada__2.xml"
        """
    )
    
    parser.add_argument('-d', '--directory', help='Directorio a procesar')
    parser.add_argument('-f', '--file', help='Archivo XML individual a procesar')
    parser.add_argument('-r', '--recursive', action='store_true', help='Procesar subdirectorios recursivamente')
    parser.add_argument('--force', action='store_true', help='Sobrescribir archivos existentes')
    parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se haría sin realizar cambios')
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.directory and not args.file:
        parser.error("Debe especificar --directory o --file")
    
    if args.directory and args.file:
        parser.error("No puede especificar --directory y --file simultáneamente")
    
    if args.file and args.recursive:
        parser.error("La opción --recursive no aplica para archivos individuales")
    
    try:
        if args.file:
            # Procesar archivo individual
            success, old_name, new_name = rename_xml_file(args.file, args.dry_run, args.force, set())
            
            if success:
                if args.dry_run:
                    print(f"[DRY-RUN] {old_name} → {new_name}")
                else:
                    print(f"✓ Archivo renombrado: {old_name} → {new_name}")
            else:
                print(f"○ El archivo ya tiene el nombre correcto: {old_name}")
        else:
            # Procesar directorio
            process_directory(args.directory, args.recursive, args.dry_run, args.force)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
