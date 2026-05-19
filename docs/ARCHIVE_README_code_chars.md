# Fix para convert_code_blocks_chars.py

## Problema detectado

La versión anterior de `convert_code_blocks_chars.py` tenía un bug crítico que corrompía archivos XML al convertir caracteres **fuera de los bloques de código**.

### Síntoma
Al ejecutar el script, los archivos XML se volvían inválidos con errores como:
```
Error parsing file.xml: mismatched tag: line 221, column 6
```

### Causa raíz
El script convertía **todo el contenido del archivo**, no solo los bloques de código dentro de secciones CDATA. Esto causaba:

1. **Corrupción de caracteres españoles**: `inválidos` → `invM-CM-!lidos`
2. **Rotura de tags XML**: Caracteres especiales en atributos y tags se corrompían
3. **Pérdida de encoding**: Caracteres multibyte se malinterpretaban

### Ejemplo del problema

**Antes (incorrecto):**
```python
# Convertía TODO el archivo
converted_content, blocks_modified = convert_markdown_code_blocks(original_content, to_normal)
```

Esto convertía:
- ✗ Tags XML: `<text>` podría convertirse incorrectamente
- ✗ Atributos: `format="markdown"` se corrompía
- ✗ Texto fuera de código: "inválidos" se corrompía
- ✓ Bloques de código: Se convertían correctamente (pero el daño ya estaba hecho)

## Solución implementada

### 1. Nueva función `process_xml_cdata()`

Se agregó una función que procesa **solo** las secciones CDATA en archivos XML:

```python
def process_xml_cdata(text: str, to_normal: bool = True) -> tuple[str, int]:
    """
    Procesa secciones CDATA en archivos XML, convirtiendo solo bloques de código dentro.
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
```

### 2. Detección de archivos XML

Se modificó `process_file()` para detectar archivos XML y usar la nueva función:

```python
# Para archivos XML, procesar solo dentro de CDATA
if file_path.lower().endswith('.xml'):
    converted_content, blocks_modified = process_xml_cdata(original_content, to_normal)
else:
    converted_content, blocks_modified = convert_markdown_code_blocks(original_content, to_normal)
```

### 3. Mejora en regex de bloques de código

Se ajustó el regex para ser más preciso:

```python
# Antes: r'```([a-z]*)\n(.*?)\n```'
# Después: r'```([a-z]*)\n(.*?)```'
```

Esto evita problemas con el cierre de bloques de código.

## Archivos reparados

Los siguientes 12 archivos fueron restaurados desde backup y reconvertidos correctamente:

1. `enums_-_buenas_practicas_-_nombres_descriptivos.xml` (7 bloques)
2. `enums_-_uso_-_declaracion_de_variables.xml` (10 bloques)
3. `preprocesador_-_macros_-_multilinea_backslash.xml` (7 bloques)
4. `preprocesador_-_operadores_-_limitaciones_general.xml` (2 bloques)
5. `punteros_-_buena_practica_-_inicializacion_con_null.xml` (7 bloques)
6. `typedef_anonimos_-_sintaxis_struct.xml` (8 bloques)
7. `typedef_enum_-_sintaxis_basica.xml` (12 bloques)
8. `typedef_struct_-_sintaxis_basica.xml` (8 bloques)
9. `typedef_union_-_sintaxis_basica.xml` (9 bloques)
10. `declaracion_typedef_-_sintaxis_basica.xml` (8 bloques)
11. `sintaxis_function_pointers_-_anatomia.xml` (5 bloques)
12. `patrones_typedef_-_sufijo_t.xml` (7 bloques)

**Total:** 90 bloques de código procesados correctamente

## Verificación

Todos los archivos ahora:
- ✅ Parsean correctamente como XML válido
- ✅ Mantienen caracteres españoles intactos (á, é, í, ó, ú, ñ, etc.)
- ✅ Preservan la estructura XML correcta
- ✅ Solo convierten caracteres dentro de bloques de código (\`\`\` y \`)

## Proceso de restauración

```bash
# 1. Restaurar desde backups
for file in ...; do
  cp "${file}.bak" "${file}"
done

# 2. Reconvertir con script corregido
python3 convert_code_blocks_chars.py -f archivo.xml --to-fullwidth

# 3. Verificar XML válido
python3 -c "import xml.etree.ElementTree as ET; ET.parse('archivo.xml')"
```

## Lecciones aprendidas

1. **Scope limitado**: Las conversiones deben limitarse estrictamente al scope objetivo (solo CDATA para XML)
2. **Preservar encoding**: Nunca modificar contenido fuera de los bloques de código
3. **Validación inmediata**: Siempre validar la estructura del archivo después de modificarlo
4. **Backups automáticos**: El sistema de backups (.bak) salvó los archivos

## Uso correcto del script

### Para archivos XML
```bash
# El script ahora procesa automáticamente solo CDATA
python3 convert_code_blocks_chars.py -f archivo.xml --to-fullwidth
```

### Para archivos GIFT/Markdown
```bash
# Procesa todo el contenido (como antes)
python3 convert_code_blocks_chars.py -f archivo.gift --to-fullwidth
```

### Procesamiento en lote
```bash
# Procesar múltiples tipos de archivos
python3 convert_code_blocks_chars.py -d ./preguntas -r -e xml gift md --to-fullwidth
```

## Diferencias clave

| Aspecto | Antes (Buggy) | Después (Fixed) |
|---------|---------------|-----------------|
| **Archivos XML** | Convierte todo el archivo | Solo convierte dentro de CDATA |
| **Tags XML** | Se corrompen | Se preservan intactos |
| **Caracteres españoles** | Se corrompen | Se preservan intactos |
| **Validación XML** | Falla | Pasa exitosamente |
| **Archivos GIFT/MD** | Funciona | Funciona (sin cambios) |

## Estado actual

✅ **Script corregido y probado**  
✅ **12 archivos restaurados y reconvertidos**  
✅ **Todos los archivos validan como XML correcto**  
✅ **Caracteres especiales preservados**  

El script ahora es seguro de usar en archivos XML y no causará corrupción de datos.
