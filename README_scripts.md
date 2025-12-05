# Scripts de Análisis de Preguntas XML

Este directorio contiene scripts de Python para analizar y evaluar preguntas en formato XML de Moodle.

## Scripts Disponibles

### 1. find_similar_questions.py
Encuentra preguntas similares dentro de un archivo XML usando análisis TF-IDF y similitud de coseno.

**Uso:**
```bash
# Threshold por defecto (0.7)
python3 find_similar_questions.py parcial3_2025.xml

# Con threshold personalizado
python3 find_similar_questions.py parcial3_2025.xml -t 0.8

# Modo verbose (muestra detalles completos)
python3 find_similar_questions.py parcial3_2025.xml -t 0.6 -v
```

**Características:**
- Threshold ajustable (0.0 - 1.0)
- Análisis de texto, nombre y respuestas
- Algoritmo TF-IDF para comparación semántica
- Estadísticas de similitud (promedio, máximo, mínimo)

### 2. evaluate_questions_directory.py
Recorre un directorio completo y genera un informe de evaluación exhaustivo.

**Uso:**
```bash
# Análisis completo
python3 evaluate_questions_directory.py preguntas/

# Guardar informe en archivo
python3 evaluate_questions_directory.py preguntas/ -o informe.txt

# Sin recursividad
python3 evaluate_questions_directory.py preguntas/ --no-recursive

# Con threshold personalizado para duplicados
python3 evaluate_questions_directory.py preguntas/ -s 0.9 -o informe.txt
```

**Características:**
- Escaneo recursivo de directorios
- Estadísticas por tipo de pregunta
- Análisis de categorías y tags
- **Detección automática de preguntas duplicadas** (con threshold ajustable)
- Detección de problemas y errores
- Métricas de calidad (feedback, tags, etc.)
- Recomendaciones automáticas

## Ejemplos de Salida

### find_similar_questions.py
```
Par 1: Similitud = 1.000
Pregunta 185 (multichoice):
  Nombre: Estructuras
Pregunta 186 (multichoice):
  Nombre: Estructuras
--------------------------------------------------------------------------------
Resumen: 90 pares de preguntas similares encontrados
Similitud promedio: 0.690
```

### evaluate_questions_directory.py
```
📊 RESUMEN GENERAL
Total de archivos XML: 3782
Total de preguntas: 4253

📝 TIPOS DE PREGUNTAS
  multichoice         :  4219 ( 100%)

🔄 PREGUNTAS DUPLICADAS O MUY SIMILARES
Total de duplicados encontrados: 13
Threshold de similitud: 0.9

Duplicado 1: Similitud = 1.000
  Pregunta A (multichoice): Estructuras
    Archivo: preguntas/estructuras_1.xml
  Pregunta B (multichoice): Estructuras
    Archivo: preguntas/estructuras_2.xml
  Comando: meld -n 'preguntas/estructuras_1.xml' 'preguntas/estructuras_2.xml'

📋 COMANDOS MELD PARA RESOLVER DUPLICADOS
# Copia y ejecuta estos comandos para revisar y resolver duplicados:

# Duplicado 1 - Similitud: 1.000
meld -n 'preguntas/estructuras_1.xml' 'preguntas/estructuras_2.xml'

# Duplicado 2 - Similitud: 0.991
meld -n 'preguntas/estructuras_3.xml' 'preguntas/estructuras_4.xml'

💡 RECOMENDACIONES
  • 41.5% de preguntas sin tags
  • 37.3% de preguntas sin feedback
  • 13 preguntas duplicadas detectadas
```

## Requisitos

- Python 3.6+
- Módulos estándar: xml.etree.ElementTree, argparse, pathlib, collections

## Resolución de Duplicados con Meld

El informe incluye comandos `meld` listos para usar que facilitan la resolución de duplicados:

```bash
# Generar informe y extraer comandos meld
python3 evaluate_questions_directory.py preguntas/ -s 0.85 -o informe.txt

# Extraer solo los comandos meld a un script
grep "^meld -n" informe.txt > resolve_duplicates.sh
chmod +x resolve_duplicates.sh

# Ejecutar para revisar duplicados uno por uno
./resolve_duplicates.sh
```

Cada invocación de `meld -n` abre una comparación visual de dos archivos XML, permitiendo:
- Ver las diferencias lado a lado
- Editar y resolver duplicados
- Fusionar contenido manualmente

## Notas

- Los scripts procesan archivos XML en formato Moodle Quiz
- El análisis de similitud funciona mejor con textos de longitud media
- El evaluador detecta automáticamente problemas comunes (respuestas faltantes, preguntas vacías, etc.)
- **Todos los duplicados son mostrados en el informe** (sin límite de cantidad)
- Para conjuntos grandes de preguntas, considera usar un threshold más alto (0.9+) para reducir falsos positivos
- Los comandos `meld` usan la opción `-n` para abrir en una nueva ventana
