# Conversor Bidireccional Moodle XML ↔ GIFT

Script de Python para convertir preguntas entre los formatos Moodle XML y GIFT de manera bidireccional, con soporte para conversión masiva preservando estructura de directorios.

## Características

- ✅ **Conversión bidireccional**: XML → GIFT y GIFT → XML
- ✅ **Caracteres especiales**: Conversión automática de caracteres especiales en bloques de código
- ✅ **Conversión masiva**: Procesa directorios completos preservando la estructura
- ✅ **Formato Markdown**: Mantiene el formato markdown en preguntas y respuestas
- ✅ **Tags y metadatos**: Preserva tags, IDs de pregunta y feedback general

## Instalación

No requiere dependencias adicionales, solo Python 3.6+:

```bash
chmod +x convert_xml_gift.py
```

## Uso Básico

### Convertir archivo individual

**XML a GIFT:**
```bash
./convert_xml_gift.py -i pregunta.xml -o pregunta.gift
```

**GIFT a XML:**
```bash
./convert_xml_gift.py -i pregunta.gift -o pregunta.xml
```

**Autodetección de formato:**
```bash
# El script detecta automáticamente la dirección de conversión por la extensión
./convert_xml_gift.py -i pregunta.xml
# Genera: pregunta.gift

./convert_xml_gift.py -i pregunta.gift
# Genera: pregunta.xml
```

### Conversión masiva con preservación de estructura

**Convertir directorio completo XML → GIFT:**
```bash
./convert_xml_gift.py -d ./preguntas_xml -o ./preguntas_gift --to-gift
```

**Convertir directorio completo GIFT → XML:**
```bash
./convert_xml_gift.py -d ./preguntas_gift -o ./preguntas_xml --to-xml
```

La estructura de directorios se preserva completamente, lo cual es útil para mantener la categorización:

```
preguntas_xml/
├── algebra/
│   ├── basico/
│   │   └── pregunta1.xml
│   └── avanzado/
│       └── pregunta2.xml
└── geometria/
    └── pregunta3.xml

Convierte a →

preguntas_gift/
├── algebra/
│   ├── basico/
│   │   └── pregunta1.gift
│   └── avanzado/
│       └── pregunta2.gift
└── geometria/
    └── pregunta3.gift
```

## Caracteres Especiales en Código

El script maneja automáticamente la conversión de caracteres especiales dentro de bloques de código, basándose en el archivo `caracteres_especiales.md`:

### Dentro de bloques de código (```, `pre`, \`)

**XML → GIFT:** Convierte caracteres Unicode especiales a sus equivalentes normales:
- `⩵` → `==`
- `＝` → `=`
- `＃` → `#`
- `｛` → `{`
- `｝` → `}`
- Y más...

**GIFT → XML:** Convierte en la dirección opuesta para preservar los caracteres especiales en XML.

### Ejemplo:

**XML:**
```xml
<text>El operador `⩵⩵` compara valores en el código:
```python
if x ⩵⩵ 10:
    print("igual")
```
</text>
```

**GIFT generado:**
```
El operador `====` compara valores en el código:
```python
if x ==== 10:
    print("igual")
```
```

## Formatos Soportados

### Tipos de Pregunta
Actualmente soporta:
- ✅ **Opción múltiple** (multichoice)
- 🔜 Otros tipos en desarrollo

### Elementos Preservados
- ✅ ID de pregunta (en comentarios)
- ✅ Nombre de pregunta
- ✅ Texto de pregunta (markdown)
- ✅ Respuestas con feedback (markdown)
- ✅ Feedback general
- ✅ Tags
- ✅ Configuración de pregunta (penalty, shuffleanswers, etc.)

## Opciones de Línea de Comandos

```
-h, --help              Muestra ayuda
-i, --input INPUT       Archivo de entrada
-o, --output OUTPUT     Archivo/directorio de salida
-d, --directory DIR     Directorio para conversión masiva
--to-gift               Forzar conversión a GIFT
--to-xml                Forzar conversión a XML
```

## Ejemplos Avanzados

### Conversión con detección automática en directorio
```bash
# Si hay más archivos .xml que .gift, convierte a GIFT
./convert_xml_gift.py -d ./preguntas -o ./preguntas_convertidas
```

### Procesamiento por lotes con reporte
```bash
./convert_xml_gift.py -d ./banco_preguntas -o ./banco_gift --to-gift
# Muestra:
# Encontrados 150 archivos para convertir
# ✓ [1/150] categoria1/pregunta1.xml
# ✓ [2/150] categoria1/pregunta2.xml
# ...
# Conversión masiva completada:
#   - Archivos convertidos: 148/150
#   - Errores: 2
```

## Estructura de Archivos

### Formato GIFT esperado:
```gift
// question: 1854266  name: Nombre de la Pregunta
// [tag:tag1] [tag:tag2] [tag:tag3]
::Nombre de la Pregunta::[markdown]Texto de la pregunta con **markdown**{
	=Respuesta correcta#Feedback correcto
	~Respuesta incorrecta#Feedback incorrecto
	~Otra incorrecta#Otro feedback
	####Feedback general de la pregunta
}
```

### Formato XML esperado:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<quiz>
<!-- question: 1854266  -->
  <question type="multichoice">
    <name>
      <text>Nombre de la Pregunta</text>
    </name>
    <questiontext format="markdown">
      <text>Texto de la pregunta con **markdown**</text>
    </questiontext>
    <generalfeedback format="markdown">
      <text>Feedback general de la pregunta</text>
    </generalfeedback>
    <!-- ... más configuración ... -->
    <answer fraction="100" format="markdown">
      <text>Respuesta correcta</text>
      <feedback format="markdown">
        <text>Feedback correcto</text>
      </feedback>
    </answer>
    <!-- ... más respuestas ... -->
    <tags>
      <tag><text>tag1</text></tag>
      <tag><text>tag2</text></tag>
    </tags>
  </question>
</quiz>
```

## Notas Técnicas

### Preservación de Formato
- Las líneas en blanco dentro de preguntas se preservan
- El formato markdown se mantiene intacto
- La indentación en GIFT usa tabulaciones

### Manejo de Errores
- Archivos con errores se reportan pero no detienen la conversión masiva
- Se muestra un resumen al final con archivos exitosos y fallidos

### Limitaciones Actuales
- Solo soporta preguntas de opción múltiple
- No soporta imágenes embebidas (se mantienen las referencias)
- Asume formato markdown en texto y respuestas

## Contribuir

Para agregar soporte a más tipos de preguntas, editar la función correspondiente en el script:
- `xml_to_gift()`: Para tipos de pregunta adicionales en conversión XML → GIFT
- `gift_to_xml()`: Para tipos de pregunta adicionales en conversión GIFT → XML

## Referencias

- Basado en `ejemplo.xml` y `ejemplo.gift` como moldes de formato
- Caracteres especiales definidos en `caracteres_especiales.md`
- Formato GIFT: https://docs.moodle.org/en/GIFT_format
- Formato XML Moodle: https://docs.moodle.org/en/Moodle_XML_format
