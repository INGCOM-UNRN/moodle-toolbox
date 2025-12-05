# Análisis de Scripts Duplicados

Este documento identifica scripts con funcionalidad similar o duplicada en el proyecto.

## Scripts Duplicados Detectados

### convert_html_to_markdown.py vs convert_xml_html_to_markdown.py

**Nivel de duplicación:** Alta (~85% similar)

#### Funcionalidad Común
Ambos scripts convierten etiquetas HTML a formato Markdown dentro de archivos XML de Moodle.

#### Diferencias Clave

| Aspecto | convert_html_to_markdown.py | convert_xml_html_to_markdown.py |
|---------|----------------------------|--------------------------------|
| **Tipo de caracteres** | Fullwidth (＜code＞) | HTML normal (`<code>`) |
| **Conversión de atributo** | Cambia `format="html"` a `format="markdown"` | No cambia atributos |
| **Soporte de listas** | Sí (`<ul>`, `<ol>`, `<li>`) | No |
| **Limpieza de espacios** | Limpia múltiples `\n` | No |
| **Líneas de código** | 113 líneas | 125 líneas |
| **Última modificación** | Dec 2, 2025 | Dec 2, 2025 |

#### Ejemplos de Uso

**convert_html_to_markdown.py:**
```xml
<!-- INPUT -->
<text><![CDATA[＜code＞var x＜/code＞]]></text>

<!-- OUTPUT -->
<text><![CDATA[`var x`]]></text>
```

**convert_xml_html_to_markdown.py:**
```xml
<!-- INPUT -->
<text><![CDATA[<code>var x</code>]]></text>

<!-- OUTPUT -->
<text><![CDATA[`var x`]]></text>
```

#### Recomendación

**Opción 1: Consolidación (Recomendado)**
Crear un único script con un flag para alternar entre modos:

```python
# Propuesta de diseño unificado
./convert_html_to_markdown.py archivo.xml  # HTML normal (default)
./convert_html_to_markdown.py archivo.xml --fullwidth  # HTML fullwidth
./convert_html_to_markdown.py archivo.xml --no-format-change  # No cambiar atributo format
```

**Opción 2: Mantener separados con documentación clara**
- Renombrar para claridad:
  - `convert_html_to_markdown.py` → `convert_fullwidth_html_to_markdown.py`
  - `convert_xml_html_to_markdown.py` → `convert_html_to_markdown.py` (mantener como principal)
- Documentar claramente cuándo usar cada uno

**Opción 3: Deprecar uno**
- Mantener solo `convert_xml_html_to_markdown.py` (caso más común)
- Mover `convert_html_to_markdown.py` a `deprecated/`
- Agregar warning en el script deprecado

#### Implementación de Consolidación

```python
#!/usr/bin/env python3
"""
Script unificado para convertir HTML a Markdown en archivos XML de Moodle.
Soporta HTML normal y fullwidth.
"""

import argparse

def convert_html_to_markdown(text, use_fullwidth=False, change_format=False):
    """Convierte HTML a markdown."""
    
    if use_fullwidth:
        # Usar patrones fullwidth
        patterns = {
            'code': (r'＜code＞(.*?)＜/code＞', r'`\1`'),
            'strong': (r'＜strong＞(.*?)＜/strong＞', r'**\1**'),
            # ... más patrones fullwidth
        }
    else:
        # Usar patrones HTML normales
        patterns = {
            'code': (r'<code>(.*?)</code>', r'`\1`'),
            'strong': (r'<strong>(.*?)</strong>', r'**\1**'),
            # ... más patrones normales
        }
    
    # Aplicar conversiones...
    
    if change_format:
        # Cambiar format="html" a format="markdown"
        pass
    
    return text

def main():
    parser = argparse.ArgumentParser(description='Convertir HTML a Markdown')
    parser.add_argument('input', help='Archivo o directorio de entrada')
    parser.add_argument('--fullwidth', action='store_true', 
                       help='Usar caracteres fullwidth (＜＞)')
    parser.add_argument('--change-format', action='store_true',
                       help='Cambiar format="html" a format="markdown"')
    args = parser.parse_args()
    
    # Procesar...

if __name__ == '__main__':
    main()
```

---

## Otros Scripts con Funcionalidad Relacionada

### Scripts de Conversión de Caracteres

Aunque no son duplicados, estos scripts trabajan en áreas relacionadas:

1. **convert_code_blocks_chars.py**: Convierte caracteres especiales en bloques de código
2. **convert_html_to_markdown.py**: Convierte HTML fullwidth a markdown
3. **convert_xml_html_to_markdown.py**: Convierte HTML normal a markdown

**Relación:** Estos tres scripts podrían ser parte de un pipeline:
```bash
# Pipeline de conversión completo
1. convert_xml_html_to_markdown.py  # HTML → Markdown
2. convert_code_blocks_chars.py     # Caracteres normales → fullwidth en código
3. convert_xml_gift.py              # XML → GIFT (si se necesita)
```

**Oportunidad de integración:** Crear un script wrapper que ejecute la cadena completa:

```bash
./convert_pipeline.py -d ./preguntas --html-to-md --chars-to-fullwidth --to-gift
```

---

## Scripts Sin Duplicación Detectada

Los siguientes scripts tienen funcionalidad única y no se solapan significativamente:

### ✅ Únicos y bien diferenciados

- **convert_xml_gift.py**: Conversión XML ↔ GIFT (único en su función)
- **find_similar_questions.py**: Detección de similitud (único)
- **evaluate_questions_directory.py**: Evaluación exhaustiva (único)
- **ensure_cdata_in_text_blocks.py**: Wrapper de CDATA (único)
- **remove_tags_from_xml.py**: Eliminación de tags (único)
- **rename_xml_files_by_question_name.py**: Renombrado inteligente (único)

---

## Plan de Acción Recomendado

### Corto Plazo (Inmediato)

1. ✅ **Documentar claramente las diferencias** entre scripts similares
2. ✅ **Crear README_html_to_markdown.md** explicando cuándo usar cada uno
3. ⬜ **Agregar warnings en los scripts** indicando alternativas

### Medio Plazo (Próxima versión)

4. ⬜ **Consolidar** `convert_html_to_markdown.py` y `convert_xml_html_to_markdown.py`
5. ⬜ **Crear tests** para validar que la consolidación no rompe funcionalidad
6. ⬜ **Actualizar documentación** con el nuevo script unificado

### Largo Plazo (Futuro)

7. ⬜ **Crear script pipeline** que ejecute múltiples conversiones en secuencia
8. ⬜ **Refactorizar funciones comunes** en un módulo compartido
9. ⬜ **Agregar tests automatizados** para todos los scripts

---

## Métricas de Duplicación

### Análisis de Código

```bash
# Similitud entre scripts HTML→Markdown
$ diff -u convert_html_to_markdown.py convert_xml_html_to_markdown.py | wc -l
238 líneas de diff

# Funciones comunes identificadas
- convert_html_tags_to_markdown() / convert_html_to_markdown()
- process_cdata() (presente en ambos)
- convert_file() / process_xml_file() (muy similar)
```

### Código Duplicado Estimado

- **Lógica de conversión**: ~60% duplicada
- **Procesamiento de archivos**: ~80% duplicada  
- **Manejo de CDATA**: ~90% duplicada
- **Gestión de backups**: ~100% duplicada

### Oportunidad de Reducción

**Reducción estimada después de consolidación:**
- De 238 líneas totales → ~140 líneas (41% reducción)
- Eliminar ~100 líneas de código duplicado
- Mejorar mantenibilidad

---

## Beneficios de la Consolidación

### Ventajas

1. **Mantenibilidad**: Un solo lugar para corregir bugs
2. **Consistencia**: Comportamiento uniforme
3. **Claridad**: Los usuarios no necesitan elegir entre dos scripts similares
4. **Testing**: Más fácil de testear un solo script con opciones
5. **Documentación**: Más simple documentar un script con flags que dos separados

### Desventajas Potenciales

1. **Complejidad**: Script único más complejo que scripts especializados
2. **Retrocompatibilidad**: Romper scripts existentes en pipelines
3. **Curva de aprendizaje**: Usuarios deben aprender nuevos flags

### Mitigación de Desventajas

- Mantener scripts antiguos como wrappers que llaman al nuevo
- Documentación clara con ejemplos de migración
- Warnings en scripts antiguos indicando el nuevo método

---

## Ejemplo de Migración

### Script Wrapper para Retrocompatibilidad

**convert_html_to_markdown_legacy.py:**
```python
#!/usr/bin/env python3
"""
DEPRECATED: Usar convert_html_to_markdown.py --fullwidth en su lugar.
Este script se mantiene para retrocompatibilidad.
"""
import sys
import subprocess
import warnings

warnings.warn(
    "Este script está deprecado. Use: convert_html_to_markdown.py --fullwidth",
    DeprecationWarning
)

# Llamar al nuevo script con el flag correcto
args = sys.argv[1:]
cmd = ['./convert_html_to_markdown.py', '--fullwidth'] + args
subprocess.run(cmd)
```

---

## Conclusión

La duplicación detectada es manejable y hay una oportunidad clara de consolidación que mejoraría el proyecto. La documentación actual (incluyendo este análisis) mitiga el problema mientras se decide si implementar la consolidación.

**Estado actual: Documentado y funcional** ✅  
**Acción recomendada: Consolidación en próxima versión mayor** 🔄

---

**Fecha de análisis:** Diciembre 2025  
**Versión del proyecto:** 1.0  
**Analista:** Documentación automática
