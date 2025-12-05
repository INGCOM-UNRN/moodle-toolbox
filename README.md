# Moodle Toolbox

Conjunto de herramientas en Python para trabajar con preguntas de Moodle en formatos XML y GIFT. Facilita la conversión, análisis, limpieza y mantenimiento de bancos de preguntas.

## 📋 Índice

- [Instalación](#instalación)
- [Scripts Disponibles](#scripts-disponibles)
  - [Conversión de Formatos](#conversión-de-formatos)
  - [Análisis y Evaluación](#análisis-y-evaluación)
  - [Limpieza y Mantenimiento](#limpieza-y-mantenimiento)
- [Documentación Detallada](#documentación-detallada)
- [Flujo de Trabajo Recomendado](#flujo-de-trabajo-recomendado)
- [Requisitos](#requisitos)

## 🚀 Instalación

No se requieren dependencias externas. Solo necesitas Python 3.6+:

```bash
# Clonar el repositorio
git clone <repository-url>
cd moodle_toolbox

# Dar permisos de ejecución a los scripts
chmod +x *.py
```

## 📦 Scripts Disponibles

### Conversión de Formatos

#### 🔄 convert_xml_gift.py
**Conversor bidireccional entre Moodle XML y GIFT**

Convierte preguntas entre los formatos XML de Moodle y GIFT, soportando conversión masiva con preservación de estructura de directorios.

```bash
# Convertir archivo individual
./convert_xml_gift.py -i pregunta.xml -o pregunta.gift
./convert_xml_gift.py -i pregunta.gift -o pregunta.xml

# Conversión masiva de directorio
./convert_xml_gift.py -d ./preguntas_xml -o ./preguntas_gift --to-gift
./convert_xml_gift.py -d ./preguntas_gift -o ./preguntas_xml --to-xml
```

**Características:**
- ✅ Conversión bidireccional XML ↔ GIFT
- ✅ Preserva estructura de directorios
- ✅ Mantiene tags, IDs y feedback
- ✅ Soporta formato markdown

📖 [Ver documentación completa](README_convert_xml_gift.md)

---

#### 🔤 convert_code_blocks_chars.py
**Conversor de caracteres especiales en bloques de código**

Convierte caracteres especiales (fullwidth) dentro de bloques de código a caracteres normales y viceversa. Útil para manejar caracteres que tienen significado especial en GIFT (`{`, `}`, `=`, `#`, etc.).

```bash
# Convertir caracteres fullwidth a normales
./convert_code_blocks_chars.py -f archivo.xml --to-normal

# Convertir caracteres normales a fullwidth
./convert_code_blocks_chars.py -f archivo.gift --to-fullwidth

# Procesar directorio completo
./convert_code_blocks_chars.py -d ./preguntas -r -e xml gift --to-fullwidth
```

**Características:**
- ✅ Conversión bidireccional de caracteres especiales
- ✅ Procesa solo bloques de código (no corrompe el resto del archivo)
- ✅ Soporta XML (dentro de CDATA), GIFT y Markdown
- ✅ Sistema de backups automáticos

📖 [Ver documentación completa](README_convert_code_blocks_chars_fix.md)

---

#### 🏷️ convert_html_to_markdown.py y convert_xml_html_to_markdown.py
**Conversores de HTML a Markdown**

> **⚠️ NOTA:** Estos dos scripts son muy similares y pueden ser consolidados.

Convierten etiquetas HTML (`<code>`, `<p>`, `<strong>`, `<pre>`, etc.) a su equivalente en formato Markdown dentro de archivos XML de Moodle.

```bash
# Usando convert_xml_html_to_markdown.py (recomendado)
python3 convert_xml_html_to_markdown.py archivo.xml

# Procesar directorio
python3 convert_xml_html_to_markdown.py -d ./preguntas
```

**Diferencias:**
- `convert_html_to_markdown.py`: Trabaja con caracteres fullwidth (＜code＞)
- `convert_xml_html_to_markdown.py`: Trabaja con HTML normal (`<code>`)

---

### Análisis y Evaluación

#### 🔍 find_similar_questions.py
**Detector de preguntas similares o duplicadas**

Encuentra preguntas similares usando análisis TF-IDF y similitud de coseno. Útil para identificar duplicados antes de importar a Moodle.

```bash
# Analizar un archivo
./find_similar_questions.py parcial3_2025.xml

# Con threshold personalizado (0.0 - 1.0)
./find_similar_questions.py parcial3_2025.xml -t 0.85

# Modo verbose con detalles completos
./find_similar_questions.py parcial3_2025.xml -t 0.7 -v
```

**Características:**
- ✅ Threshold ajustable de similitud
- ✅ Análisis de texto, nombre y respuestas
- ✅ Estadísticas detalladas (promedio, máximo, mínimo)
- ✅ Modo verbose para debugging

---

#### 📊 evaluate_questions_directory.py
**Evaluador exhaustivo de bancos de preguntas**

Recorre directorios completos y genera informes detallados de evaluación con estadísticas, detección de problemas y recomendaciones.

```bash
# Análisis completo
./evaluate_questions_directory.py preguntas/

# Guardar informe en archivo
./evaluate_questions_directory.py preguntas/ -o informe.txt

# Con threshold personalizado para duplicados
./evaluate_questions_directory.py preguntas/ -s 0.9 -o informe.txt

# Sin recursividad
./evaluate_questions_directory.py preguntas/ --no-recursive
```

**Características:**
- ✅ Escaneo recursivo de directorios
- ✅ Estadísticas por tipo de pregunta
- ✅ Análisis de categorías y tags
- ✅ **Detección automática de duplicados** con threshold ajustable
- ✅ Detección de problemas y errores
- ✅ Métricas de calidad (feedback, tags, etc.)
- ✅ **Comandos Meld listos para resolver duplicados**
- ✅ Recomendaciones automáticas

**Salida incluye:**
```
📊 RESUMEN GENERAL
Total de archivos XML: 3782
Total de preguntas: 4253

🔄 PREGUNTAS DUPLICADAS O MUY SIMILARES
Total de duplicados encontrados: 13

📋 COMANDOS MELD PARA RESOLVER DUPLICADOS
meld -n 'preguntas/estructuras_1.xml' 'preguntas/estructuras_2.xml'
```

📖 [Ver documentación completa](README_scripts.md)

---

### Limpieza y Mantenimiento

#### 🛡️ ensure_cdata_in_text_blocks.py
**Asegurador de CDATA en bloques de texto**

Asegura que todos los bloques `<text>` tengan su contenido envuelto en CDATA, previniendo problemas con caracteres especiales XML.

```bash
# Procesar un archivo
./ensure_cdata_in_text_blocks.py -f pregunta.xml

# Procesar directorio (sin backups)
./ensure_cdata_in_text_blocks.py -d ./preguntas --no-backup

# Modo dry-run (ver qué haría sin modificar)
./ensure_cdata_in_text_blocks.py -d ./preguntas --dry-run
```

**Características:**
- ✅ Detecta bloques `<text>` sin CDATA
- ✅ Envuelve automáticamente en CDATA
- ✅ Sistema de backups (.bak)
- ✅ Modo dry-run

---

#### 🗑️ remove_tags_from_xml.py
**Eliminador de sección tags**

Elimina recursivamente la sección `<tags>` de archivos XML. Útil cuando se quiere reorganizar el sistema de etiquetado.

```bash
# Procesar un archivo
./remove_tags_from_xml.py -f pregunta.xml

# Procesar directorio completo
./remove_tags_from_xml.py -d ./preguntas

# Sin backups
./remove_tags_from_xml.py -d ./preguntas --no-backup

# Modo dry-run
./remove_tags_from_xml.py -d ./preguntas --dry-run
```

**Características:**
- ✅ Procesamiento recursivo
- ✅ Sistema de backups
- ✅ Modo dry-run
- ✅ Contador de archivos modificados

---

#### 📝 rename_xml_files_by_question_name.py
**Renombrador de archivos por nombre de pregunta**

Renombra archivos XML usando el nombre de la pregunta contenida, sanitizando caracteres especiales para nombres de archivo válidos.

```bash
# Renombrar un archivo
./rename_xml_files_by_question_name.py -f pregunta.xml

# Renombrar directorio completo
./rename_xml_files_by_question_name.py -d ./preguntas

# Sin backups (solo renombrar)
./rename_xml_files_by_question_name.py -d ./preguntas --no-backup

# Modo dry-run
./rename_xml_files_by_question_name.py -d ./preguntas --dry-run
```

**Características:**
- ✅ Sanitiza nombres de archivo (espacios → `_`, sin caracteres especiales)
- ✅ Maneja acentos y caracteres UTF-8
- ✅ Previene colisiones de nombres
- ✅ Modo dry-run
- ✅ Límite de longitud configurable

---

## 📚 Documentación Detallada

### Documentación por Categoría

- **[README_scripts.md](README_scripts.md)**: Scripts de análisis y evaluación (`find_similar_questions.py` y `evaluate_questions_directory.py`)
- **[README_convert_xml_gift.md](README_convert_xml_gift.md)**: Conversor bidireccional XML ↔ GIFT
- **[README_convert_code_blocks_chars_fix.md](README_convert_code_blocks_chars_fix.md)**: Conversor de caracteres especiales (fix documentado)
- **[README_html_to_markdown.md](README_html_to_markdown.md)**: Conversores de HTML a Markdown (incluye comparación de scripts)
- **[README_xml_maintenance.md](README_xml_maintenance.md)**: Scripts de limpieza y mantenimiento XML

### Referencias

- **[caracteres_especiales.md](caracteres_especiales.md)**: Tabla de referencia de caracteres especiales soportados
- **[DUPLICATES_ANALYSIS.md](DUPLICATES_ANALYSIS.md)**: Análisis de scripts duplicados y recomendaciones de consolidación

## 🔄 Flujo de Trabajo Recomendado

### Creación de Banco de Preguntas

```bash
# 1. Crear preguntas en formato GIFT (más fácil de editar)
vim nueva_pregunta.gift

# 2. Convertir a XML para Moodle
./convert_xml_gift.py -i nueva_pregunta.gift -o nueva_pregunta.xml

# 3. Asegurar CDATA en bloques de texto
./ensure_cdata_in_text_blocks.py -f nueva_pregunta.xml

# 4. Convertir caracteres especiales en código
./convert_code_blocks_chars.py -f nueva_pregunta.xml --to-fullwidth

# 5. Renombrar archivo por nombre de pregunta
./rename_xml_files_by_question_name.py -f nueva_pregunta.xml
```

### Mantenimiento de Banco Existente

```bash
# 1. Evaluar estado del banco
./evaluate_questions_directory.py ./banco_preguntas -o informe.txt

# 2. Revisar y resolver duplicados con los comandos Meld generados
grep "^meld -n" informe.txt > resolve_duplicates.sh
chmod +x resolve_duplicates.sh
./resolve_duplicates.sh

# 3. Limpiar tags si es necesario
./remove_tags_from_xml.py -d ./banco_preguntas --dry-run  # revisar primero
./remove_tags_from_xml.py -d ./banco_preguntas

# 4. Estandarizar nombres de archivos
./rename_xml_files_by_question_name.py -d ./banco_preguntas --dry-run
./rename_xml_files_by_question_name.py -d ./banco_preguntas
```

### Conversión Masiva XML → GIFT → XML

```bash
# 1. Convertir banco completo a GIFT para edición
./convert_xml_gift.py -d ./banco_xml -o ./banco_gift --to-gift

# 2. Editar archivos GIFT con tu editor favorito
vim ./banco_gift/**/*.gift

# 3. Reconvertir a XML
./convert_xml_gift.py -d ./banco_gift -o ./banco_xml_nuevo --to-xml

# 4. Evaluar cambios
./evaluate_questions_directory.py ./banco_xml_nuevo -o informe_nuevo.txt
```

## 📋 Requisitos

- **Python 3.6+**
- **Módulos estándar**: xml.etree.ElementTree, argparse, pathlib, collections, re

No se requieren dependencias externas.

### Herramientas Opcionales

- **Meld**: Para comparación visual de duplicados (recomendado)
  ```bash
  # Ubuntu/Debian
  sudo apt install meld
  
  # Fedora
  sudo dnf install meld
  ```

## 🔧 Resolución de Problemas Comunes

### Archivos XML corruptos después de conversión

Si los archivos XML se corrompen después de usar `convert_code_blocks_chars.py`, asegúrate de usar la versión corregida. El problema fue que versiones antiguas convertían todo el archivo en lugar de solo los bloques de código dentro de CDATA.

**Solución:** Ver [README_convert_code_blocks_chars_fix.md](README_convert_code_blocks_chars_fix.md)

### Duplicados no detectados

Si `evaluate_questions_directory.py` no encuentra duplicados esperados, prueba ajustar el threshold:

```bash
# Threshold más bajo = más sensible (más falsos positivos)
./evaluate_questions_directory.py preguntas/ -s 0.7

# Threshold más alto = menos sensible (más falsos negativos)
./evaluate_questions_directory.py preguntas/ -s 0.95
```

### Caracteres especiales en código no se convierten

Verifica que estés usando los bloques de código correctos:
- **GIFT**: Usa triple backtick (\`\`\`) o backtick simple (\`)
- **XML**: El contenido debe estar dentro de CDATA
- **Markdown**: Usa triple backtick (\`\`\`) o backtick simple (\`)

## 📝 Notas Importantes

### Scripts Duplicados Detectados

**convert_html_to_markdown.py** y **convert_xml_html_to_markdown.py** tienen funcionalidad muy similar. La diferencia principal:
- `convert_html_to_markdown.py`: Trabaja con caracteres fullwidth (＜code＞)
- `convert_xml_html_to_markdown.py`: Trabaja con HTML normal (`<code>`)

**Recomendación:** Usar `convert_xml_html_to_markdown.py` por defecto.

### Sistema de Backups

La mayoría de scripts crean backups automáticos con extensión `.bak` antes de modificar archivos. Puedes desactivar esto con `--no-backup`.

Para restaurar desde backup:
```bash
# Restaurar un archivo
cp archivo.xml.bak archivo.xml

# Restaurar todos los backups en un directorio
for f in *.bak; do cp "$f" "${f%.bak}"; done
```

## 🤝 Contribuir

Para agregar nuevas funcionalidades:

1. Mantener compatibilidad con Python 3.6+
2. Usar solo módulos de la biblioteca estándar cuando sea posible
3. Incluir documentación inline y docstrings
4. Agregar sistema de backups en scripts que modifiquen archivos
5. Implementar modo `--dry-run` para previsualización
6. Actualizar este README con el nuevo script

## 📄 Licencia

[Especificar licencia]

## ✍️ Autor

[Especificar autor]

---

**Última actualización:** Diciembre 2025
