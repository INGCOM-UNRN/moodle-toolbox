# Conversores HTML a Markdown

Documentación para los scripts que convierten etiquetas HTML a formato Markdown en archivos XML de Moodle.

## Scripts Disponibles

1. **convert_html_to_markdown.py**: Convierte caracteres fullwidth HTML (＜code＞) a markdown
2. **convert_xml_html_to_markdown.py**: Convierte HTML normal (`<code>`) a markdown

> **⚠️ NOTA IMPORTANTE:** Estos scripts tienen funcionalidad muy similar. Se recomienda usar `convert_xml_html_to_markdown.py` para casos normales.

---

## convert_xml_html_to_markdown.py (Recomendado)

### Descripción

Convierte etiquetas HTML estándar a su equivalente en formato Markdown dentro de secciones CDATA de archivos XML de Moodle. Ideal para estandarizar preguntas importadas desde otros sistemas o crear preguntas con formato markdown.

### Conversiones Soportadas

| HTML | Markdown | Ejemplo |
|------|----------|---------|
| `<code>...</code>` | `` `...` `` | `<code>var x</code>` → `` `var x` `` |
| `<strong>...</strong>` | `**...**` | `<strong>importante</strong>` → `**importante**` |
| `<em>...</em>` | `*...*` | `<em>énfasis</em>` → `*énfasis*` |
| `<i>...</i>` | `*...*` | `<i>itálica</i>` → `*itálica*` |
| `<pre>...</pre>` | ` ```...``` ` | `<pre>código</pre>` → ` ```código``` ` |
| `<p>...</p>` | texto | `<p>párrafo</p>` → `párrafo` |
| `<br>` o `<br/>` | `\n` | `línea1<br>línea2` → `línea1\nlínea2` |

### Uso

```bash
# Procesar un archivo individual
python3 convert_xml_html_to_markdown.py archivo.xml

# Procesar directorio completo
python3 convert_xml_html_to_markdown.py -d ./preguntas

# Ver estadísticas detalladas
python3 convert_xml_html_to_markdown.py -d ./preguntas -v
```

### Opciones

| Opción | Descripción |
|--------|-------------|
| `archivo.xml` | Archivo individual a procesar |
| `-d, --directory DIR` | Directorio a procesar recursivamente |
| `-v, --verbose` | Mostrar estadísticas detalladas |

### Ejemplo de Transformación

**Antes (HTML en CDATA):**
```xml
<text><![CDATA[
Para declarar una variable usa <code>int x = 10;</code>

<strong>Importante:</strong> No olvides el punto y coma.

<pre>
int main() {
    return 0;
}
</pre>
]]></text>
```

**Después (Markdown en CDATA):**
```xml
<text><![CDATA[
Para declarar una variable usa `int x = 10;`

**Importante:** No olvides el punto y coma.

```
int main() {
    return 0;
}
```
]]></text>
```

### Características

- ✅ Procesa solo contenido dentro de secciones CDATA
- ✅ Preserva la estructura XML
- ✅ Maneja tags huérfanos (sin cierre)
- ✅ Respeta el formato interno de bloques `<pre>`
- ✅ Crea backups automáticos (.bak)
- ✅ Contador de modificaciones

### Notas Importantes

- Solo procesa contenido dentro de `<![CDATA[...]]>`
- No modifica atributos XML ni estructura
- Tags HTML anidados se procesan correctamente
- Bloques `<pre>` mantienen formato interno

---

## convert_html_to_markdown.py

### Descripción

Similar a `convert_xml_html_to_markdown.py`, pero trabaja con **caracteres fullwidth** que se usan cuando los caracteres HTML normales necesitan ser escapados (＜code＞ en lugar de `<code>`).

### Diferencias con convert_xml_html_to_markdown.py

| Aspecto | convert_html_to_markdown.py | convert_xml_html_to_markdown.py |
|---------|----------------------------|--------------------------------|
| **Tipo de caracteres** | Fullwidth (＜＞) | Normal (`<>`) |
| **Uso típico** | Archivos ya escapados | Archivos HTML normales |
| **Conversión adicional** | También cambia `format="html"` a `format="markdown"` | Solo convierte contenido |

### Conversiones Fullwidth Soportadas

| Fullwidth HTML | Markdown | Ejemplo |
|----------------|----------|---------|
| `＜code＞...＜/code＞` | `` `...` `` | `＜code＞var x＜/code＞` → `` `var x` `` |
| `＜strong＞...＜/strong＞` | `**...**` | `＜strong＞texto＜/strong＞` → `**texto**` |
| `＜em＞...＜/em＞` | `*...*` | `＜em＞texto＜/em＞` → `*texto*` |
| `＜pre＞...＜/pre＞` | ` ```...``` ` | `＜pre＞código＜/pre＞` → ` ```código``` ` |
| `＜p＞...＜/p＞` | texto | `＜p＞párrafo＜/p＞` → `párrafo` |
| `＜br＞` o `＜br/＞` | `\n` | `línea1＜br＞línea2` → `línea1\nlínea2` |
| `＜ul＞＜li＞...＜/li＞＜/ul＞` | `- ...\n` | Listas no ordenadas |
| `＜ol＞＜li＞...＜/li＞＜/ol＞` | `1. ...\n` | Listas numeradas |

### Uso

```bash
# Procesar un archivo individual
python3 convert_html_to_markdown.py archivo.xml

# Procesar directorio completo
python3 convert_html_to_markdown.py directorio/

# Ver ayuda
python3 convert_html_to_markdown.py -h
```

### Ejemplo de Transformación

**Antes:**
```xml
<questiontext format="html">
  <text><![CDATA[
    ＜p＞Pregunta con código:＜/p＞
    ＜code＞int x = 10;＜/code＞
    
    ＜ul＞
      ＜li＞Opción 1＜/li＞
      ＜li＞Opción 2＜/li＞
    ＜/ul＞
  ]]></text>
</questiontext>
```

**Después:**
```xml
<questiontext format="markdown">
  <text><![CDATA[
    Pregunta con código:
    `int x = 10;`
    
    - Opción 1
    - Opción 2
  ]]></text>
</questiontext>
```

### Características Adicionales

- ✅ Convierte `format="html"` a `format="markdown"` en atributos
- ✅ Soporta listas ordenadas y no ordenadas
- ✅ Limpia múltiples saltos de línea
- ✅ Crea backups automáticos
- ✅ Contador de archivos modificados

---

## ¿Cuál Script Usar?

### Usar convert_xml_html_to_markdown.py si:

- ✅ Tus archivos XML tienen HTML normal (`<code>`, `<strong>`, etc.)
- ✅ Importaste preguntas desde otro sistema con HTML
- ✅ Creaste preguntas con editor HTML de Moodle
- ✅ Quieres el comportamiento más estándar

### Usar convert_html_to_markdown.py si:

- ✅ Tus archivos tienen caracteres fullwidth (＜code＞)
- ✅ Los archivos fueron procesados previamente con herramientas de escape
- ✅ Necesitas convertir el atributo `format="html"` a `format="markdown"`
- ✅ Trabajas con archivos que pasaron por `convert_code_blocks_chars.py`

### Ejemplo de Decisión

```bash
# Verificar qué tipo de caracteres tiene tu archivo
grep "＜code＞" archivo.xml && echo "Usar convert_html_to_markdown.py"
grep "<code>" archivo.xml && echo "Usar convert_xml_html_to_markdown.py"
```

---

## Flujo de Trabajo Completo

### Conversión HTML → Markdown en Banco de Preguntas

```bash
# 1. Verificar qué archivos tienen HTML
grep -r "format=\"html\"" ./preguntas

# 2. Hacer backup completo
cp -r ./preguntas ./preguntas_backup

# 3. Convertir HTML a Markdown (elegir el script apropiado)
python3 convert_xml_html_to_markdown.py -d ./preguntas

# 4. Verificar conversión
grep -r "format=\"markdown\"" ./preguntas

# 5. Asegurar CDATA en bloques de texto
./ensure_cdata_in_text_blocks.py -d ./preguntas

# 6. Evaluar resultado
./evaluate_questions_directory.py ./preguntas -o informe.txt
```

### Migración de Preguntas HTML a Markdown

```bash
# Si las preguntas vienen con HTML normal
python3 convert_xml_html_to_markdown.py -d ./importadas

# Si las preguntas tienen fullwidth HTML
python3 convert_html_to_markdown.py ./importadas
```

### Post-procesamiento de Caracteres Especiales

```bash
# 1. Convertir HTML a Markdown
python3 convert_xml_html_to_markdown.py -d ./preguntas

# 2. Convertir caracteres especiales en bloques de código
./convert_code_blocks_chars.py -d ./preguntas -r -e xml --to-fullwidth

# 3. Convertir a GIFT si es necesario
./convert_xml_gift.py -d ./preguntas -o ./preguntas_gift --to-gift
```

---

## Casos de Uso Comunes

### 1. Estandarizar Banco de Preguntas Mixto

Tienes un banco con preguntas en HTML y otras en Markdown:

```bash
# Convertir todas a Markdown
python3 convert_xml_html_to_markdown.py -d ./banco_mixto

# Verificar que todas usan markdown ahora
grep -r "format=" ./banco_mixto | grep -v "markdown"
```

### 2. Importación desde Otro Sistema

Importaste preguntas desde un sistema que usa HTML:

```bash
# Convertir todo el directorio importado
python3 convert_xml_html_to_markdown.py -d ./importado_desde_otro_sistema

# Asegurar CDATA
./ensure_cdata_in_text_blocks.py -d ./importado_desde_otro_sistema

# Evaluar calidad
./evaluate_questions_directory.py ./importado_desde_otro_sistema
```

### 3. Preparación para Edición Manual

Quieres editar preguntas HTML en formato más legible:

```bash
# 1. Convertir HTML a Markdown
python3 convert_xml_html_to_markdown.py -d ./para_editar

# 2. Convertir XML a GIFT (más fácil de editar)
./convert_xml_gift.py -d ./para_editar -o ./para_editar_gift --to-gift

# 3. Editar archivos GIFT con tu editor favorito
vim ./para_editar_gift/*.gift

# 4. Reconvertir a XML
./convert_xml_gift.py -d ./para_editar_gift -o ./editado --to-xml
```

---

## Solución de Problemas

### HTML no se convierte

**Síntoma:** El script no modifica nada.

**Causas posibles:**
1. El HTML no está dentro de CDATA
2. Usas caracteres fullwidth pero ejecutas el script normal (o viceversa)
3. El archivo ya está en formato markdown

**Solución:**
```bash
# Verificar si hay HTML en CDATA
grep -A5 "CDATA" archivo.xml | grep "<code>"

# Verificar tipo de caracteres
grep "＜" archivo.xml  # Fullwidth
grep "<code>" archivo.xml  # Normal

# Usar el script correcto según el resultado
```

### Se corrompen caracteres especiales

**Síntoma:** Después de la conversión, algunos caracteres se ven mal.

**Solución:**
```bash
# Restaurar desde backup
cp archivo.xml.bak archivo.xml

# Asegurar que el archivo tiene encoding UTF-8
file archivo.xml

# Reconvertir
python3 convert_xml_html_to_markdown.py archivo.xml
```

### Bloques <pre> pierden formato

**Síntoma:** El código dentro de `<pre>` pierde indentación.

**Nota:** Esto es normal. El script preserva el contenido pero puede normalizar espacios en blanco. Si es crítico:

```bash
# Editar manualmente los bloques problemáticos después de la conversión
vim archivo.xml
```

---

## Comparación de Scripts

### Tabla Comparativa

| Característica | convert_html_to_markdown.py | convert_xml_html_to_markdown.py |
|----------------|----------------------------|--------------------------------|
| **Caracteres soportados** | Fullwidth (＜＞) | Normal (`<>`) |
| **Cambia atributo format** | ✅ Sí | ❌ No |
| **Soporta listas** | ✅ Sí (`<ul>`, `<ol>`) | ❌ No |
| **Procesa CDATA** | ✅ Sí | ✅ Sí |
| **Backups automáticos** | ✅ Sí | ✅ Sí |
| **Procesamiento recursivo** | ✅ Sí | ✅ Sí |
| **Limpia espacios múltiples** | ✅ Sí | ❌ No |
| **Mejor para** | Archivos escapados | Archivos HTML normales |

### Recomendación de Consolidación

**Consideración para futuro:** Estos dos scripts podrían ser consolidados en uno solo con una opción `--fullwidth` para alternar entre los dos modos:

```bash
# Propuesta de diseño unificado
python3 convert_html_to_markdown.py archivo.xml  # HTML normal (default)
python3 convert_html_to_markdown.py archivo.xml --fullwidth  # HTML fullwidth
```

---

## Mejores Prácticas

1. **Siempre hacer backup antes**: Los scripts crean backups, pero tener un backup adicional es buena idea
2. **Verificar tipo de caracteres primero**: Usar el script correcto para tus archivos
3. **Procesar en orden**: HTML→Markdown, luego CDATA, luego caracteres especiales
4. **Probar con un archivo primero**: Antes de procesar todo el directorio
5. **Verificar resultado**: Usar `evaluate_questions_directory.py` después de conversiones masivas

---

**Relacionado:**
- [README.md](README.md): Documentación principal del proyecto
- [README_convert_code_blocks_chars_fix.md](README_convert_code_blocks_chars_fix.md): Conversión de caracteres especiales
- [README_xml_maintenance.md](README_xml_maintenance.md): Scripts de mantenimiento
