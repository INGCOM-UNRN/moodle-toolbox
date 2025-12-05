# Guía Rápida - Moodle Toolbox

Guía rápida de 5 minutos para empezar a usar Moodle Toolbox.

## 🎯 Casos de Uso Más Comunes

### 1️⃣ Convertir XML a GIFT para editar
```bash
./convert_xml_gift.py -i pregunta.xml -o pregunta.gift
# Editar pregunta.gift con tu editor favorito
vim pregunta.gift
# Reconvertir a XML
./convert_xml_gift.py -i pregunta.gift -o pregunta.xml
```

### 2️⃣ Encontrar preguntas duplicadas
```bash
# En un solo archivo
./find_similar_questions.py archivo.xml

# En todo un directorio
./evaluate_questions_directory.py ./preguntas -o informe.txt
# Ver duplicados
grep "meld -n" informe.txt
```

### 3️⃣ Preparar archivos para Moodle
```bash
# Asegurar CDATA
./ensure_cdata_in_text_blocks.py -d ./preguntas

# Escapar caracteres especiales en código
./convert_code_blocks_chars.py -d ./preguntas -r -e xml --to-fullwidth
```

### 4️⃣ Limpiar banco de preguntas
```bash
# Evaluar primero
./evaluate_questions_directory.py ./banco -o informe.txt

# Renombrar archivos descriptivamente
./rename_xml_files_by_question_name.py -d ./banco --dry-run
./rename_xml_files_by_question_name.py -d ./banco

# Eliminar tags si es necesario
./remove_tags_from_xml.py -d ./banco
```

### 5️⃣ Convertir HTML a Markdown
```bash
# Para HTML normal
python3 convert_xml_html_to_markdown.py -d ./preguntas

# Para HTML fullwidth (＜code＞)
python3 convert_html_to_markdown.py ./preguntas/
```

## 📚 ¿Necesitas Más Información?

| Quiero... | Lee... |
|-----------|--------|
| Visión general del proyecto | [README.md](README.md) |
| Encontrar un script específico | [INDEX.md](INDEX.md) |
| Aprender sobre conversión XML/GIFT | [README_convert_xml_gift.md](README_convert_xml_gift.md) |
| Analizar duplicados | [README_scripts.md](README_scripts.md) |
| Mantener archivos XML | [README_xml_maintenance.md](README_xml_maintenance.md) |
| Convertir HTML a Markdown | [README_html_to_markdown.md](README_html_to_markdown.md) |
| Entender caracteres especiales | [README_convert_code_blocks_chars_fix.md](README_convert_code_blocks_chars_fix.md) |

## 🆘 Problemas Comunes

### "XML mal formado después de conversión"
```bash
# Restaurar desde backup
cp archivo.xml.bak archivo.xml
# Ver: README_convert_code_blocks_chars_fix.md
```

### "No encuentro duplicados"
```bash
# Ajustar threshold más bajo
./evaluate_questions_directory.py preguntas/ -s 0.7
# Ver: README_scripts.md
```

### "¿Qué script de HTML usar?"
```bash
# Verificar tipo de caracteres
grep "＜code＞" archivo.xml  # Si encuentra, usar convert_html_to_markdown.py
grep "<code>" archivo.xml    # Si encuentra, usar convert_xml_html_to_markdown.py
# Ver: README_html_to_markdown.md
```

## 💡 Tips Rápidos

1. **Siempre usar `--dry-run` primero** en scripts de mantenimiento
2. **Los backups `.bak` son tu amigo** - se crean automáticamente
3. **Lee el informe completo** de `evaluate_questions_directory.py` - tiene comandos listos para usar
4. **Usa GIFT para editar** - es más simple que XML
5. **Threshold 0.9** para duplicados exactos, **0.7** para similares

## 🚀 Primer Uso Recomendado

```bash
# 1. Ver qué tienes
ls -la *.xml *.gift

# 2. Evaluar estado
./evaluate_questions_directory.py . -o informe.txt
cat informe.txt

# 3. Si hay duplicados, resolverlos
grep "meld -n" informe.txt > duplicados.sh
chmod +x duplicados.sh
./duplicados.sh

# 4. Estandarizar
./rename_xml_files_by_question_name.py -d . --dry-run
./rename_xml_files_by_question_name.py -d .

# 5. Listo para usar!
```

## 📖 Documentación Completa

- **README.md** - Documentación principal
- **INDEX.md** - Índice completo de navegación
- **ORGANIZATION_SUMMARY.md** - Resumen del proyecto

---

**¿Listo?** Empieza con: `cat README.md`
