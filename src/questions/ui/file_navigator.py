"""Navegador de archivos del editor web (XML y GIFT)."""

import os
import re

FORMATOS = ('.xml', '.gift')


class FileNavigator:
    """Navegador de estructura de directorios con preguntas XML/GIFT"""

    def __init__(self, base_dir):
        self.base_dir = base_dir

    def get_directory_tree(self):
        if not os.path.exists(self.base_dir):
            return {'error': 'Directorio no existe'}
        return self._build_tree(self.base_dir, '')

    def _build_tree(self, current_path, relative_path):
        items = []
        try:
            entries = sorted(os.listdir(current_path))
        except PermissionError:
            return {'name': os.path.basename(current_path), 'type': 'error', 'children': []}

        for entry in entries:
            if entry.startswith('.'):
                continue

            full_path = os.path.join(current_path, entry)
            rel_path = os.path.join(relative_path, entry) if relative_path else entry

            if os.path.isdir(full_path):
                children = self._build_tree(full_path, rel_path)
                items.append({
                    'name': entry,
                    'type': 'directory',
                    'path': rel_path,
                    'children': children if isinstance(children, list) else children.get('children', []),
                    'question_count': self._count_questions(full_path),
                })
            elif entry.lower().endswith(FORMATOS):
                info = self._get_question_info(full_path)
                items.append({
                    'name': entry,
                    'type': 'file',
                    'format': 'gift' if entry.lower().endswith('.gift') else 'xml',
                    'path': rel_path,
                    'question_type': info.get('type', 'unknown'),
                    'question_name': info.get('name', entry),
                })

        return items

    def _count_questions(self, directory):
        count = 0
        try:
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                count += sum(
                    1 for f in files
                    if f.lower().endswith(FORMATOS) and not f.startswith('.')
                )
        except PermissionError:
            pass
        return count

    def _get_question_info(self, filepath):
        """Extrae tipo y nombre de la pregunta sin parsear todo el árbol."""
        info = {}
        try:
            with open(filepath, encoding='utf-8', errors='replace') as f:
                head = f.read(4096)
            if filepath.lower().endswith('.gift'):
                m = re.search(r'::(.*?)::', head, re.DOTALL)
                info['name'] = m.group(1).strip() if m else ''
                if '{T' in head or re.search(r'\{\s*(TRUE|T)\b', head, re.IGNORECASE):
                    info['type'] = 'truefalse'
                elif '->' in head:
                    info['type'] = 'matching'
                else:
                    info['type'] = 'multichoice'
            else:
                import xml.etree.ElementTree as ET
                root = ET.parse(filepath).getroot()
                q = root.find('.//question')
                if q is not None:
                    info['type'] = q.get('type', 'unknown')
                    name = q.find('name/text')
                    info['name'] = (name.text or '').strip() if name is not None else ''
        except Exception:
            pass
        return info

    def search_questions(self, query, limit=50):
        """Busca preguntas por texto en nombre/enunciado."""
        resultados = []
        termino = query.lower()
        try:
            for root, dirs, files in os.walk(self.base_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if not file.lower().endswith(FORMATOS) or file.startswith('.'):
                        continue
                    path = os.path.join(root, file)
                    info = self._get_question_info(path)
                    buscable = f"{info.get('name', '')} {info.get('type', '')}".lower()
                    if termino in buscable:
                        resultados.append({
                            'name': info.get('name', file),
                            'type': info.get('type', 'unknown'),
                            'filepath': os.path.relpath(path, self.base_dir),
                        })
                        if len(resultados) >= limit:
                            return resultados
        except PermissionError:
            pass
        return resultados
