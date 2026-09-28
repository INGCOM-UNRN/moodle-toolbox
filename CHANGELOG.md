# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/);
versiones según [SemVer](https://semver.org/lang/es/).

## [0.2.0] - 2026-09-28

Primera versión con registro de cambios; lo anterior está en el historial de git.

### Agregado

- **cli**: cumplir el contrato de línea de comandos de LINEAMIENTOS §3.2 (N-ECO-04) (`af62923`)

### Documentación

- agregar el texto de la licencia GPL-3.0-or-later que declara pyproject (N-ECO-06) (`703388b`)
- **archivo**: quitar enlaces a scripts y documentos que ya no existen (N-ECO-17) (`ac4779e`)
- **instalacion**: instalar desde el repositorio y no con pip install questions (N-MOODLE-03) (`430349a`)
- incorporar manual de uso integral y referencia tecnica (moodle-toolbox) (`7c4a32f`)

### Mantenimiento

- **calidad**: verificar errores de Python y dependencias vulnerables (N-ECO-08, N-ECO-13) (`e2d396b`)
- **deps**: mover google-genai al extra opcional ai y actualizar dependencias vulnerables (N-MOODLE-02) (`9bb92c4`)
