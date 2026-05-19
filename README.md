# Moodle Toolbox (Questions CLI)

Conjunto de herramientas unificadas en Python para gestionar preguntas de Moodle en formatos XML y GIFT. Facilita la conversión, análisis, limpieza, mantenimiento y generación de preguntas mediante IA.

Todas las herramientas anteriores han sido consolidadas en un único comando raíz: `questions`.

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

### 3. Conversión
- `questions convert html-to-md`: Convierte etiquetas HTML a Markdown en archivos XML o GIFT.
- *Nota: La conversión bidireccional XML ↔ GIFT está en proceso de integración completa.*

### 4. Mantenimiento XML
- `questions xml cdata`: Asegura que los bloques `<text>` usen secciones CDATA.
- `questions xml clean-tags`: Elimina secciones de etiquetas (`<tags>`) redundantes.
- `questions xml rename`: Renombra archivos XML basándose en el nombre interno de la pregunta.

### 5. Inteligencia Artificial (Gemini)
- `questions ai`: Mejora la calidad pedagógica (`improve`) o crea variaciones (`multiply`) de preguntas usando modelos de Google Gemini.

## 📚 Documentación Detallada

Para más información sobre funcionalidades específicas, consulta la carpeta [docs/](./docs):

- **[Guía de Inicio Rápido](./docs/QUICK_START.md)**
- **[Validación y Análisis](./docs/README_validate_questions.md)**
- **[Mantenimiento XML](./docs/README_xml_maintenance.md)**
- **[Referencia de Caracteres Especiales](./docs/caracteres_especiales.md)**

## 📋 Requisitos

- **Python 3.11+**
- **Dependencias**: tatsu, google-genai, click, python-dotenv (gestionadas por `uv`).

## ✍️ Autor

[Especificar autor]

---

**Última actualización:** Mayo 2026 (Refactorización a CLI Unificado)
