# Herramientas GIFT Parser

Herramientas en Python para parsear y verificar archivos en formato GIFT (General Import Format Template) de Moodle.

## Instalación

```bash
# Usando uv (recomendado)
uv sync

# O con pip
pip install -e .
```

## Herramientas

### 1. gift-parse

Parser para archivos GIFT basado en la gramática PEG definida en `GIFT.pegjs`.

#### Uso como CLI

```bash
# Parsear un archivo y mostrar resumen
uv run gift-parse archivo.gift

# Salida en formato JSON
uv run gift-parse archivo.gift --json

# Solo resumen en JSON
uv run gift-parse archivo.gift --json --summary
```

#### Uso como módulo

```python
from gift_tools.gift_parser import parse_gift_file, parse_gift, get_question_summary

# Parsear un archivo
result = parse_gift_file('preguntas.gift')

if result["success"]:
    print(f"Total de preguntas: {result['questionCount']}")
    for question in result["questions"]:
        print(get_question_summary(question))
else:
    print(f"Error: {result['error']['message']}")

# Parsear contenido directamente
content = """
::Pregunta de ejemplo::¿Cuál es la respuesta?{
    =Correcta
    ~Incorrecta
}
"""
parsed = parse_gift(content)
```

### 2. gift-verify

Herramienta para verificar recursivamente un directorio de preguntas GIFT y generar un informe detallado.

#### Uso

```bash
# Analizar directorio recursivamente
uv run gift-verify preguntas/

# Guardar informe en archivo
uv run gift-verify preguntas/ -o informe.txt

# Sin recursión
uv run gift-verify preguntas/ --no-recursive

# Con threshold de similitud personalizado
uv run gift-verify preguntas/ -s 0.9

# Modo verbose
uv run python verify_gift_directory.py preguntas/ -v

# Salida JSON
uv run gift-verify preguntas/ --json
```

#### Opciones

| Opción | Descripción |
|--------|-------------|
| `-o, --output <archivo>` | Archivo de salida para el informe |
| `-r, --no-recursive` | No buscar recursivamente en subdirectorios |
| `-v, --verbose` | Mostrar información detallada durante el análisis |
| `-s, --similarity <valor>` | Threshold de similitud para duplicados (0.0-1.0, default: 0.85) |
| `-j, --json` | Salida en formato JSON |
| `-h, --help` | Mostrar ayuda |

#### Informe generado

El informe incluye:

- **Resumen general**: Total de archivos, archivos válidos/inválidos, total de preguntas
- **Tipos de preguntas**: Distribución por tipo (MC, TF, Matching, Short, Numerical, Essay)
- **Categorías**: Categorías encontradas en los archivos
- **Tags**: Tags más utilizados
- **Calidad de contenido**: Estadísticas sobre feedback, tags, preguntas vacías
- **Distribución por profundidad**: Archivos por nivel de directorio
- **Problemas detectados**: Errores y advertencias encontradas
- **Errores de parseo**: Archivos que no se pudieron parsear
- **Duplicados**: Preguntas similares detectadas mediante TF-IDF y similitud de coseno
- **Recomendaciones**: Sugerencias para mejorar el banco de preguntas

## Scripts uv

```bash
# Parsear un archivo
uv run gift-parse archivo.gift

# Verificar directorio
uv run gift-verify preguntas/
```

## Tipos de preguntas soportados

El parser soporta todos los tipos de preguntas del formato GIFT:

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| **MC** | Multiple Choice | `{=correcta ~incorrecta}` |
| **TF** | True/False | `{TRUE}` o `{FALSE}` |
| **Short** | Respuesta corta | `{=respuesta}` |
| **Matching** | Emparejamiento | `{=a -> 1 =b -> 2}` |
| **Numerical** | Numérica | `{#42}` o `{#42:5}` |
| **Essay** | Ensayo | `{}` |
| **Category** | Categoría | `$CATEGORY: nombre` |
| **Description** | Descripción | Solo texto sin respuestas |

## Gramática GIFT

El parser está basado en la gramática definida en `GIFT.pegjs`, que soporta:

- Formatos de texto: `[moodle]`, `[html]`, `[markdown]`, `[plain]`
- Tags: `// [tag:nombre]`
- IDs: `// [id:identificador]`
- Feedback por respuesta: `#feedback`
- Feedback global: `####feedback`
- Pesos en respuestas: `%50%`
- Respuestas embebidas
- Caracteres escapados: `\:`, `\#`, `\=`, `\{`, `\}`, `\~`, `\\`, `\n`

## Ejemplo de archivo GIFT

```gift
// [tag:matematicas] [tag:basico]
::Suma básica::[markdown]¿Cuánto es **2 + 2**?{
    =4#¡Correcto!
    ~3#Incorrecto, intenta de nuevo
    ~5#Incorrecto
    ####La suma de 2 + 2 es igual a 4.
}

// [id:pregunta-tf-01]
::Verdadero o Falso::El cielo es azul.{TRUE#¡Correcto!#Revisa tu respuesta}

$CATEGORY: Matemáticas/Álgebra

::Ecuación lineal::Resuelve x + 5 = 10. x = {#5:0}
```
