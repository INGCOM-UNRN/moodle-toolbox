# Scripts de Mantenimiento XML

Documentación para los scripts de limpieza y mantenimiento de archivos XML de Moodle.

## Scripts Incluidos

1. [ensure_cdata_in_text_blocks.py](#ensure_cdata_in_text_blockspy)
2. [remove_tags_from_xml.py](#remove_tags_from_xmlpy)
3. [rename_xml_files_by_question_name.py](#rename_xml_files_by_question_namepy)

---

## ensure_cdata_in_text_blocks.py

### Descripción

Asegura que todos los bloques `<text>` con contenido tengan su contenido envuelto en secciones CDATA. Esto previene problemas con caracteres especiales XML como `<`, `>`, `&`, etc.

### ¿Por qué usar CDATA?

Los bloques CDATA (`<![CDATA[...]]>`) permiten incluir caracteres especiales sin necesidad de escaparlos. Son especialmente importantes cuando el contenido incluye:
- Código fuente con operadores `<`, `>`, `&`
- Markdown con caracteres especiales
- HTML embebido
- Caracteres Unicode especiales

### Uso

```bash
# Procesar un archivo individual
./ensure_cdata_in_text_blocks.py -f pregunta.xml

# Procesar directorio recursivamente
./ensure_cdata_in_text_blocks.py -d ./preguntas

# Procesar sin crear backups
./ensure_cdata_in_text_blocks.py -d ./preguntas --no-backup

# Modo dry-run (ver qué haría sin modificar)
./ensure_cdata_in_text_blocks.py -d ./preguntas --dry-run

# Ver ayuda completa
./ensure_cdata_in_text_blocks.py -h
```

### Opciones

| Opción | Descripción |
|--------|-------------|
| `-f, --file FILE` | Procesar un archivo individual |
| `-d, --directory DIR` | Procesar directorio recursivamente |
| `--no-backup` | No crear archivos .bak antes de modificar |
| `--dry-run` | Simular sin hacer cambios reales |

### Ejemplo de Transformación

**Antes:**
```xml
<text>Código con operador: x < 10</text>
```

**Después:**
```xml
<text><![CDATA[Código con operador: x < 10]]></text>
```

### Notas

- Los bloques `<text>` vacíos no se modifican
- Si el contenido ya tiene CDATA, no se duplica
- Crea backups automáticos con extensión `.bak`
- El contador muestra cuántos bloques fueron modificados

---

## remove_tags_from_xml.py

### Descripción

Elimina recursivamente la sección `<tags>` de todos los archivos XML de preguntas de Moodle. Útil cuando se quiere reorganizar completamente el sistema de etiquetado o eliminar tags obsoletos.

### Uso

```bash
# Procesar un archivo individual
./remove_tags_from_xml.py -f pregunta.xml

# Procesar directorio recursivamente
./remove_tags_from_xml.py -d ./preguntas

# Sin crear backups
./remove_tags_from_xml.py -d ./preguntas --no-backup

# Modo dry-run (previsualización)
./remove_tags_from_xml.py -d ./preguntas --dry-run

# Ver ayuda
./remove_tags_from_xml.py -h
```

### Opciones

| Opción | Descripción |
|--------|-------------|
| `-f, --file FILE` | Procesar un archivo individual |
| `-d, --directory DIR` | Procesar directorio recursivamente |
| `--no-backup` | No crear archivos .bak antes de modificar |
| `--dry-run` | Simular sin hacer cambios reales |

### Ejemplo de Transformación

**Antes:**
```xml
<question type="multichoice">
  <name>
    <text>Mi Pregunta</text>
  </name>
  <questiontext format="markdown">
    <text><![CDATA[Texto de la pregunta]]></text>
  </questiontext>
  <tags>
    <tag><text>tag1</text></tag>
    <tag><text>tag2</text></tag>
    <tag><text>tag3</text></tag>
  </tags>
  <!-- ... más contenido ... -->
</question>
```

**Después:**
```xml
<question type="multichoice">
  <name>
    <text>Mi Pregunta</text>
  </name>
  <questiontext format="markdown">
    <text><![CDATA[Texto de la pregunta]]></text>
  </questiontext>
  <!-- ... más contenido ... -->
</question>
```

### Casos de Uso

- **Reorganización de tags**: Eliminar todos los tags para reorganizarlos desde cero
- **Migración**: Preparar preguntas para migración a otro sistema
- **Limpieza**: Eliminar tags obsoletos o incorrectos masivamente

### Notas

- Procesa todas las preguntas en un archivo XML
- Preserva el resto de la estructura XML
- Si no hay tags, el archivo no se modifica
- Contador de archivos modificados vs. omitidos

---

## rename_xml_files_by_question_name.py

### Descripción

Renombra archivos XML usando el nombre de la pregunta contenida en el XML. Sanitiza el nombre para crear nombres de archivo válidos y descriptivos.

### Reglas de Sanitización

1. **Conversión a minúsculas**: `Estructuras` → `estructuras`
2. **Eliminación de acentos**: `función` → `funcion`
3. **Espacios a guiones bajos**: `Mi Pregunta` → `mi_pregunta`
4. **Solo caracteres válidos**: Mantiene solo `a-z`, `0-9`, `_`, `-`
5. **Sin duplicados**: `pregunta___test` → `pregunta_test`
6. **Límite de longitud**: Máximo 200 caracteres por defecto
7. **Sin prefijos/sufijos**: `_pregunta_` → `pregunta`

### Uso

```bash
# Renombrar un archivo individual
./rename_xml_files_by_question_name.py -f pregunta_vieja.xml

# Renombrar todos los archivos en un directorio
./rename_xml_files_by_question_name.py -d ./preguntas

# Sin crear backups (solo renombrar)
./rename_xml_files_by_question_name.py -d ./preguntas --no-backup

# Modo dry-run (ver qué haría sin renombrar)
./rename_xml_files_by_question_name.py -d ./preguntas --dry-run

# Con longitud máxima personalizada
./rename_xml_files_by_question_name.py -d ./preguntas --max-length 150

# Ver ayuda
./rename_xml_files_by_question_name.py -h
```

### Opciones

| Opción | Descripción |
|--------|-------------|
| `-f, --file FILE` | Procesar un archivo individual |
| `-d, --directory DIR` | Procesar directorio recursivamente |
| `--no-backup` | No crear archivos .bak (solo renombrar) |
| `--dry-run` | Simular sin renombrar archivos |
| `--max-length N` | Longitud máxima del nombre (default: 200) |

### Ejemplos de Renombrado

| Nombre de pregunta en XML | Nombre de archivo resultante |
|---------------------------|------------------------------|
| `Estructuras` | `estructuras.xml` |
| `Función de Inicialización` | `funcion_de_inicializacion.xml` |
| `¿Qué es un puntero?` | `que_es_un_puntero.xml` |
| `Operador == vs ===` | `operador_vs.xml` |
| `typedef - Sintaxis Básica` | `typedef_sintaxis_basica.xml` |
| `C Programming: Arrays & Pointers` | `c_programming_arrays_pointers.xml` |

### Manejo de Colisiones

Si dos preguntas tienen el mismo nombre después de la sanitización, el script:
1. Detecta la colisión
2. No sobrescribe el archivo existente
3. Reporta el conflicto en la salida
4. Sugiere renombrar manualmente

```bash
✗ Archivo no renombrado (destino ya existe): pregunta_1.xml
  Destino: estructuras.xml (ya existe)
```

### Casos de Uso

#### Organización Inicial

```bash
# Directorio desorganizado
ls preguntas/
# pregunta_001.xml  pregunta_002.xml  test.xml  new_question.xml

./rename_xml_files_by_question_name.py -d ./preguntas

# Directorio organizado
ls preguntas/
# estructuras_basicas.xml  punteros_inicializacion.xml
# typedef_sintaxis.xml     operadores_comparacion.xml
```

#### Migración de Banco de Preguntas

```bash
# Antes de migrar, estandarizar nombres
./rename_xml_files_by_question_name.py -d ./banco_viejo --dry-run
# Revisar output
./rename_xml_files_by_question_name.py -d ./banco_viejo
```

#### Post-procesamiento de Exportación

```bash
# Después de exportar de Moodle con nombres UUID
./rename_xml_files_by_question_name.py -d ./exportado_desde_moodle
```

### Notas Importantes

- **Preserva directorios**: Solo renombra archivos, no mueve entre carpetas
- **XML válido requerido**: El archivo debe poder parsearse como XML
- **Primera pregunta**: Si hay múltiples preguntas en un XML, usa el nombre de la primera
- **Fallback**: Si no encuentra nombre, usa `unnamed_question.xml`
- **Seguridad**: Modo dry-run permite previsualizar antes de cambios reales

---

## Flujo de Trabajo Completo

### Limpieza Inicial de Banco de Preguntas

```bash
# 1. Asegurar CDATA en todos los bloques de texto
./ensure_cdata_in_text_blocks.py -d ./banco --dry-run
./ensure_cdata_in_text_blocks.py -d ./banco

# 2. Eliminar tags obsoletos
./remove_tags_from_xml.py -d ./banco --dry-run
./remove_tags_from_xml.py -d ./banco

# 3. Renombrar archivos por nombre de pregunta
./rename_xml_files_by_question_name.py -d ./banco --dry-run
./rename_xml_files_by_question_name.py -d ./banco
```

### Preparación para Importación a Moodle

```bash
# Verificar que todos los archivos tienen CDATA
./ensure_cdata_in_text_blocks.py -d ./para_importar --dry-run

# Si hay modificaciones pendientes, aplicarlas
./ensure_cdata_in_text_blocks.py -d ./para_importar
```

### Post-exportación desde Moodle

```bash
# Moodle exporta con nombres genéricos, renombrar descriptivamente
./rename_xml_files_by_question_name.py -d ./exportado --dry-run
./rename_xml_files_by_question_name.py -d ./exportado
```

## Recuperación de Backups

Todos los scripts crean backups con extensión `.bak`:

```bash
# Ver todos los backups
find . -name "*.bak"

# Restaurar un archivo específico
cp archivo.xml.bak archivo.xml

# Restaurar todos los backups en un directorio
for f in *.bak; do 
    cp "$f" "${f%.bak}"
done

# Eliminar todos los backups después de verificar
find . -name "*.bak" -delete
```

## Solución de Problemas

### Error: "XML mal formado"

Si un script reporta errores de parsing XML:

```bash
# Verificar manualmente el XML
python3 -c "import xml.etree.ElementTree as ET; ET.parse('archivo.xml')"

# Si está corrupto, restaurar desde backup
cp archivo.xml.bak archivo.xml
```

### Nombres de archivo muy largos

```bash
# Usar longitud máxima más corta
./rename_xml_files_by_question_name.py -d ./preguntas --max-length 100
```

### Colisiones de nombres

```bash
# Identificar todas las colisiones primero
./rename_xml_files_by_question_name.py -d ./preguntas --dry-run | grep "ya existe"

# Renombrar manualmente los archivos con colisión
# o editar los nombres de pregunta en los XML antes de renombrar
```

## Mejores Prácticas

1. **Siempre usar dry-run primero**: Ver los cambios antes de aplicarlos
2. **Mantener backups**: Los backups automáticos son tu red de seguridad
3. **Procesar en orden**: CDATA → Tags → Renombrar
4. **Verificar después**: Usar scripts de análisis para verificar integridad
5. **Control de versión**: Si usas git, hacer commit antes de cambios masivos

---

**Relacionado:**
- [README.md](README.md): Documentación principal del proyecto
- [README_scripts.md](README_scripts.md): Scripts de análisis
- [README_convert_xml_gift.md](README_convert_xml_gift.md): Conversión XML/GIFT
