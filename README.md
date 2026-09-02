# Moodle Toolbox (Questions CLI)

Conjunto de herramientas unificadas en Python para gestionar preguntas de Moodle en formatos XML y GIFT. Facilita la conversión, análisis, limpieza, mantenimiento y generación de preguntas mediante IA.

Todas las herramientas anteriores han sido consolidadas en un único comando raíz: `questions`.

---

## 🎯 Alcance

### Qué cubre
- Gestión integral, validación y mantenimiento de bancos de preguntas pedagógicas de Moodle.
- Conversión bidireccional fiel y sin pérdida entre formatos GIFT y Moodle XML.
- Normalización tipográfica de delimitadores de fórmulas matemáticas (LaTeX `\(...\)` y `\[...\]`) y bloques de código Markdown.
- Validación sintáctica y de completitud de metadatos de preguntas (retroalimentación, pesos porcentuales, categorías).
- Reorganización y sincronización de estructuras de directorios de categorías de preguntas.

### Qué no cubre (Límites y Delegación)
- Síntesis procedimental de variantes con validación de GCC (delegado a `idkfa`).
- Generación de exámenes en PDF con reconocimiento OMR (delegado a `alucard`).
- Creación de módulos de aprendizaje SCORM (delegado a `scorm-tools`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Multiplataforma. Python >= 3.10.

### Dependencias Externas y Binarios
- Ninguno obligatorio.

### Integración en el Ecosistema
- CLI `moodle-toolbox` (y alias `questions`). Subcomando `doctor`.

---

## 🚀 Instalación y Uso

Este proyecto utiliza [uv](https://docs.astral.sh/uv/) para la gestión de dependencias y ejecución.

```bash
# Clonar el repositorio
git clone <repository-url>
cd moodle-toolbox

# Ejecutar la ayuda principal
uv run questions --help
```

## 📦 Comandos Disponibles

El CLI `questions` se organiza en subcomandos especializados:

### 1. Validación y Análisis
- `questions validate`: Valida archivos o directorios GIFT, genera informes detallados y detecta duplicados.
- `questions analyze stats`: Genera estadísticas completas sobre un banco de preguntas.
- `questions analyze similar`: Encuentra preguntas similares usando análisis TF-IDF.

### 2. Formateo y Corrección
- `questions format`: Estandariza el formato visual de archivos GIFT y ajusta bloques de código.
- `questions fix code-indent`: Corrige la indentación dentro de bloques de código (```).
- `questions fix code-chars`: Convierte caracteres especiales entre normal y fullwidth.
- `questions fix slugify`: Normaliza nombres de archivos (minúsculas, sin acentos).
- `questions fix name-from-title`: Renombra archivos según el título de la pregunta.
- `questions fix title-from-name`: Actualiza el título interno según el nombre del archivo.

### 3. Conversión
- `questions convert html-to-md`: Convierte etiquetas HTML a Markdown en archivos XML o GIFT.
- `questions convert xml-to-gift`: Convierte Moodle XML a GIFT (soporta categorías, selección múltiple con pesos, V/F, emparejamiento, numérica con tolerancia, ensayo y descripción).
- `questions convert gift-to-xml`: Convierte GIFT a Moodle XML con bloques CDATA correctos. Ambos conversores viajan sobre el modelo unificado de preguntas del parser PEG y son estables en round-trip.

### 4. Árboles de Directorios (absorbe moodle-reorganizer)
- `questions tree export banco.gift|xml -o dir/`: Exporta un banco monolítico a un árbol de carpetas por categoría (1 archivo por pregunta).
- `questions tree collect dir/ -o reconstruido.gift|xml`: Recolecta el árbol nuevamente a un archivo único, restaurando las categorías.

### 5. Editor Web (absorbe moodle-visor / mxviz)
- `questions ui [dir]`: Abre un editor web local para navegar y editar preguntas organizadas en directorios, con soporte nativo de **Moodle XML y GIFT**. Requiere el extra opcional: `pip install questions[ui]`.

### 6. Mantenimiento XML
- `questions xml cdata`: Asegura que los bloques `<text>` usen secciones CDATA.
- `questions xml clean-tags`: Elimina secciones de etiquetas (`<tags>`) redundantes.
- `questions xml rename`: Renombra archivos XML basándose en el nombre interno de la pregunta.

### 7. Inteligencia Artificial (Gemini)
- `questions ai`: Mejora la calidad pedagógica (`improve`) o crea variaciones (`multiply`) de preguntas usando modelos de Google Gemini.

## 📚 Documentación Detallada

Para más información sobre funcionalidades específicas, consulta la carpeta [docs/](./docs):

- **[Guía de Inicio Rápido](./docs/QUICK_START.md)**
- **[Validación y Análisis](./docs/README_validate_questions.md)**
- **[Mantenimiento XML](./docs/README_xml_maintenance.md)**
- **[Referencia de Caracteres Especiales](./docs/caracteres_especiales.md)**

## ✍️ Autor

[Especificar autor]

---

**Última actualización:** Mayo 2026 (Refactorización a CLI Unificado)
