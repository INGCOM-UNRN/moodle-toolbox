"""Parsers del editor web: Moodle XML nativo y adaptador GIFT sobre el modelo unificado."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from questions.core.converter import _escape_gift
from questions.core.parser import GiftParser


# Tipos GIFT del modelo unificado -> tipos visibles por el editor (Moodle)
_TIPOS_A_EDITOR = {
    "MC": "multichoice",
    "Short": "shortanswer",
    "TF": "truefalse",
    "Matching": "matching",
    "Numerical": "numerical",
    "Essay": "essay",
    "Description": "description",
}


class QuestionParser:
    """Parser de preguntas XML de Moodle"""

    def __init__(self):
        try:
            import markdown
            self.md = markdown.Markdown(extensions=['extra', 'codehilite', 'fenced_code'])
        except ImportError:
            self.md = None

    def parse_question(self, filepath):
        """Parsea un archivo XML de pregunta de Moodle a un diccionario editable."""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            question_elem = root.find('.//question')
            if question_elem is None:
                raise ValueError("No se encontró elemento 'question' en el XML")

            question_type = question_elem.get('type', 'unknown')

            qt_elem = question_elem.find('questiontext')
            qt_format = qt_elem.get('format') if qt_elem is not None else None

            gf_elem = question_elem.find('generalfeedback')
            gf_format = gf_elem.get('format') if gf_elem is not None else None

            question_data = {
                'type': question_type,
                'name': self._get_text_content(question_elem, 'name/text'),
                'questiontext': self._get_text_content(question_elem, 'questiontext/text'),
                'questiontext_format': qt_format,
                'generalfeedback': self._get_text_content(question_elem, 'generalfeedback/text'),
                'generalfeedback_format': gf_format,
                'defaultgrade': self._get_text_content(question_elem, 'defaultgrade'),
                'penalty': self._get_text_content(question_elem, 'penalty'),
                'hidden': self._get_text_content(question_elem, 'hidden'),
                'tags': self._get_tags(question_elem),
                'answers': self._get_answers(question_elem),
                'filepath': filepath,
            }

            if question_type == 'multichoice':
                question_data['single'] = self._get_text_content(question_elem, 'single')
                question_data['shuffleanswers'] = self._get_text_content(question_elem, 'shuffleanswers')
                question_data['answernumbering'] = self._get_text_content(question_elem, 'answernumbering')
            elif question_type == 'shortanswer':
                question_data['usecase'] = self._get_text_content(question_elem, 'usecase')
            elif question_type == 'numerical':
                question_data['answer_tolerance'] = []
                for answer_elem in question_elem.findall('answer'):
                    tolerance = answer_elem.find('tolerance')
                    if tolerance is not None:
                        question_data['answer_tolerance'].append(tolerance.text)
            elif question_type == 'essay':
                for campo in ('responseformat', 'responserequired', 'responsefieldlines', 'attachments'):
                    question_data[campo] = self._get_text_content(question_elem, campo)

            return question_data

        except ET.ParseError as e:
            raise ValueError(f"Error al parsear XML: {e}")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error procesando pregunta: {e}")

    def _get_text_content(self, element, path):
        elem = element.find(path)
        if elem is not None:
            text = elem.text or ''
            text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
            return text.strip()
        return ''

    def _get_tags(self, question_elem):
        tags = []
        for tag_elem in question_elem.findall('.//tag/text'):
            if tag_elem.text:
                tags.append(tag_elem.text.strip())
        return tags

    def _get_answers(self, question_elem):
        answers = []
        for answer_elem in question_elem.findall('answer'):
            answer_format = answer_elem.get('format')
            text_elem = answer_elem.find('text')
            text_format = text_elem.get('format') if text_elem is not None else None
            feedback_elem = answer_elem.find('feedback')
            feedback_format = feedback_elem.get('format') if feedback_elem is not None else None

            answers.append({
                'fraction': answer_elem.get('fraction', '0'),
                'answer_format': answer_format,
                'text_format': text_format,
                'format': text_format or answer_format,
                'text': self._get_text_content(answer_elem, 'text'),
                'feedback': self._get_text_content(answer_elem, 'feedback/text'),
                'feedback_format': feedback_format,
            })
        return answers

    def render_markdown(self, text):
        """Renderiza markdown a HTML"""
        if not text or self.md is None:
            return ''
        return self.md.convert(text)

    def save_question(self, filepath, question_data):
        """Guarda una pregunta actualizada en el archivo XML."""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            question_elem = root.find('.//question')
            if question_elem is None:
                raise ValueError("No se encontró elemento 'question'")

            self._update_text_element(question_elem, 'name/text', question_data.get('name', ''), use_cdata=True)
            self._update_text_element(question_elem, 'questiontext/text', question_data.get('questiontext', ''), use_cdata=True)

            qt_elem = question_elem.find('questiontext')
            if qt_elem is not None and 'questiontext_format' in question_data:
                qt_format = question_data.get('questiontext_format')
                if qt_format:
                    qt_elem.set('format', qt_format)

            self._update_text_element(question_elem, 'generalfeedback/text', question_data.get('generalfeedback', ''), use_cdata=True)

            self._update_text_element(question_elem, 'defaultgrade', question_data.get('defaultgrade', '1'))
            self._update_text_element(question_elem, 'penalty', question_data.get('penalty', '0.1'))

            if 'answers' in question_data:
                for answer in question_elem.findall('answer'):
                    question_elem.remove(answer)

                for answer_data in question_data['answers']:
                    answer_format = answer_data.get('answer_format')
                    text_format = answer_data.get('text_format')
                    feedback_format = answer_data.get('feedback_format')

                    answer_attrs = {'fraction': str(answer_data.get('fraction', '0'))}
                    if answer_format:
                        answer_attrs['format'] = answer_format
                    answer_elem = ET.SubElement(question_elem, 'answer', **answer_attrs)

                    text_elem = ET.SubElement(answer_elem, 'text')
                    if text_format and not answer_format:
                        text_elem.set('format', text_format)
                    text_elem.text = '##CDATA_START##' + answer_data.get('text', '') + '##CDATA_END##'

                    feedback_attrs = {}
                    if feedback_format:
                        feedback_attrs['format'] = feedback_format
                    feedback_elem = ET.SubElement(answer_elem, 'feedback', **feedback_attrs)
                    feedback_text_elem = ET.SubElement(feedback_elem, 'text')
                    feedback_text_elem.text = '##CDATA_START##' + answer_data.get('feedback', '') + '##CDATA_END##'

            if 'tags' in question_data:
                tags_elem = question_elem.find('tags')
                if tags_elem is not None:
                    question_elem.remove(tags_elem)
                if question_data['tags']:
                    tags_elem = ET.SubElement(question_elem, 'tags')
                    for tag_text in question_data['tags']:
                        tag_elem = ET.SubElement(tags_elem, 'tag')
                        tag_text_elem = ET.SubElement(tag_elem, 'text')
                        tag_text_elem.text = tag_text

            question_type = question_data.get('type', '')
            if question_type == 'multichoice':
                single_val = self._bool_a_texto(question_data.get('single', 'true'))
                shuffle_val = self._bool_a_texto(question_data.get('shuffleanswers', 'true'))
                self._update_text_element(question_elem, 'single', single_val)
                self._update_text_element(question_elem, 'shuffleanswers', shuffle_val)
                self._update_text_element(question_elem, 'answernumbering', question_data.get('answernumbering', 'abc'))

            self._write_xml(tree, filepath, question_data.get('questiontext_format', 'html'))

        except Exception as e:
            raise ValueError(f"Error guardando pregunta: {e}")

    @staticmethod
    def _bool_a_texto(valor, predeterminado='true'):
        if valor in ['1', 1, True]:
            return 'true'
        if valor in ['0', 0, False]:
            return 'false'
        return valor if valor in ('true', 'false') else predeterminado

    def _update_text_element(self, parent, path, text, use_cdata=False):
        parts = path.split('/')
        current = parent
        for part in parts[:-1]:
            elem = current.find(part)
            if elem is None:
                elem = ET.SubElement(current, part)
            current = elem

        last_part = parts[-1]
        elem = current.find(last_part)
        if elem is None:
            elem = ET.SubElement(current, last_part)

        if isinstance(text, bool):
            text = 'true' if text else 'false'
        elif text is not None:
            text = str(text)

        if text and use_cdata:
            elem.text = '##CDATA_START##' + text + '##CDATA_END##'
        else:
            elem.text = text

    def _write_xml(self, tree, filepath, text_format='html'):
        import xml.dom.minidom as minidom

        xml_string = ET.tostring(tree.getroot(), encoding='unicode', method='xml')
        xml_string = xml_string.replace('##CDATA_START##', '<![CDATA[')
        xml_string = xml_string.replace('##CDATA_END##', ']]>')

        xml_string = xml_string.replace('>true<', '>##TRUE##<')
        xml_string = xml_string.replace('>false<', '>##FALSE##<')

        try:
            dom = minidom.parseString(xml_string)
            pretty_xml = dom.toprettyxml(indent='  ', encoding=None)

            pretty_xml = pretty_xml.replace('>##TRUE##<', '>true<')
            pretty_xml = pretty_xml.replace('>##FALSE##<', '>false<')

            pretty_xml = re.sub(r'<(single|shuffleanswers|usecase|hidden)>1</', r'<\1>true</', pretty_xml)
            pretty_xml = re.sub(r'<(single|shuffleanswers|usecase|hidden)>0</', r'<\1>false</', pretty_xml)

            lines = pretty_xml.split('\n')
            if lines and lines[0].strip().startswith('<?xml'):
                lines = lines[1:]

            xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + '\n'.join(lines).strip() + '\n'
            xml_string = re.sub(r'\n\s*\n\s*\n+', '\n', xml_string)
            xml_string = re.sub(r'>\n\s*\n\s*<', '>\n  <', xml_string)
        except Exception:
            xml_string = xml_string.replace('>##TRUE##<', '>true<')
            xml_string = xml_string.replace('>##FALSE##<', '>false<')
            if not xml_string.startswith('<?xml'):
                xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_string)


class GiftQuestionAdapter:
    """Adapta archivos GIFT al mismo contrato de edición que el parser XML.

    Lectura: convierte el GIFT al modelo unificado y lo expone con la forma del
    editor (tipos Moodle, lista de answers con fraction/text/feedback).
    Escritura: reconstruye el GIFT a partir del diccionario editado.
    """

    _TIPOS_DE_EDITOR = {
        "multichoice": "MC",
        "shortanswer": "Short",
        "truefalse": "TF",
        "matching": "Matching",
        "numerical": "Numerical",
        "essay": "Essay",
        "description": "Description",
    }

    def __init__(self):
        self._parser = GiftParser()

    # -- lectura -----------------------------------------------------------

    def parse_question(self, filepath) -> dict:
        contenido = open(filepath, encoding='utf-8').read()
        preguntas = self._parser._manual_parse(contenido)
        if not preguntas:
            raise ValueError("El archivo GIFT no contiene preguntas")
        q = preguntas[0]

        data = {
            'type': _TIPOS_A_EDITOR.get(q.type, 'description'),
            'name': q.title or '',
            'questiontext': q.stem.text if q.stem else '',
            'questiontext_format': 'markdown' if (q.stem and q.stem.format == 'markdown') else 'html',
            'generalfeedback': q.global_feedback.text if q.global_feedback else '',
            'generalfeedback_format': 'html',
            'defaultgrade': '1',
            'penalty': '0.3333333',
            'hidden': '0',
            'tags': list(q.tags),
            'answers': [],
            'filepath': filepath,
            'source_format': 'gift',
        }

        if q.type == 'MC':
            data['single'] = '0' if sum(1 for c in q.choices if c.is_correct) > 1 else '1'
            data['shuffleanswers'] = '1'
            for c in q.choices:
                frac = c.weight if c.weight is not None else (100 if c.is_correct else 0)
                data['answers'].append({
                    'fraction': f"{frac:g}",
                    'text': c.text.text if c.text else '',
                    'feedback': c.feedback.text if c.feedback else '',
                })
        elif q.type == 'Short':
            data['usecase'] = '0'
            for c in q.choices:
                data['answers'].append({
                    'fraction': '100' if c.is_correct else '0',
                    'text': c.text.text if c.text else '',
                    'feedback': c.feedback.text if c.feedback else '',
                })
        elif q.type == 'TF':
            for valor, es_correcta, fb in (('true', True, q.true_feedback), ('false', False, q.false_feedback)):
                data['answers'].append({
                    'fraction': '100' if q.is_true == es_correcta else '0',
                    'text': valor,
                    'feedback': fb.text if fb else '',
                })
        elif q.type == 'Matching':
            for par in q.match_pairs:
                data['answers'].append({
                    'fraction': '100',
                    'text': par.subquestion.text if par.subquestion else '',
                    'feedback': par.subanswer or '',
                })
        elif q.type == 'Numerical':
            for c in q.choices:
                texto = c.text.text if c.text else ''
                frac = c.weight if c.weight is not None else (100 if c.is_correct else 0)
                data['answers'].append({
                    'fraction': f"{frac:g}",
                    'text': texto,
                    'feedback': c.feedback.text if c.feedback else '',
                })

        return data

    def save_question(self, filepath, d: dict) -> None:
        """Reconstruye el GIFT desde los campos editados y lo escribe."""
        tipo = d.get('type', 'multichoice')
        titulo = _escape_gift(d.get('name', '').strip(), 'title')
        stem = d.get('questiontext', '').replace('\r\n', '\n').strip()

        lineas = [f"::{titulo}:: {stem}".rstrip()]

        respuestas = d.get('answers', [])
        if tipo == 'multichoice':
            partes = []
            for a in respuestas:
                frac = float(a.get('fraction', 0) or 0)
                simbolo = '=' if abs(frac - 100) < 0.01 else '~'
                if frac not in (100.0, 0.0):
                    simbolo += f"%{frac:g}%"
                parte = simbolo + _escape_gift(a.get('text', ''), 'answer')
                if a.get('feedback'):
                    parte += ' #' + _escape_gift(a['feedback'], 'answer')
                partes.append(parte)
            lineas.append('{\n' + '\n'.join(partes) + '\n}')
        elif tipo == 'shortanswer':
            partes = []
            for a in respuestas:
                parte = '=' + _escape_gift(a.get('text', ''), 'answer')
                if a.get('feedback'):
                    parte += ' #' + _escape_gift(a['feedback'], 'answer')
                partes.append(parte)
            lineas.append('{\n' + '\n'.join(partes) + '\n}')
        elif tipo == 'truefalse':
            verdadera = any(
                a.get('text', '').lower() == 'true' and str(a.get('fraction', '0')) == '100'
                for a in respuestas
            )
            retro = [a.get('feedback', '') for a in respuestas if a.get('feedback')]
            cuerpo_fb = '#' + '#'.join(_escape_glyphs(r) for r in retro) if retro else ''
            lineas.append('{' + ('T' if verdadera else 'F') + cuerpo_fb + '}')
        elif tipo == 'matching':
            partes = []
            for a in respuestas:
                partes.append(
                    f"={_escape_gift(a.get('text', ''), 'answer')} -> "
                    f"{_escape_gift(a.get('feedback', ''), 'answer')}"
                )
            lineas.append('{\n' + '\n'.join(partes) + '\n}')
        elif tipo == 'numerical':
            partes = []
            for i, a in enumerate(respuestas):
                frac = float(a.get('fraction', 0) or 0)
                if i == 0 and abs(frac - 100) < 0.01:
                    simbolo = ''
                elif abs(frac - 100) < 0.01:
                    simbolo = '='
                else:
                    simbolo = '~%' + f"{frac:g}" + '%'
                partes.append(simbolo + _escape_gift(a.get('text', ''), 'answer'))
            lineas.append('{#' + '\n'.join(partes) + '}')
        elif tipo == 'essay':
            lineas.append('{}')
        else:  # description / cloze: sin bloque de respuestas
            pass

        Path(filepath).write_text('\n'.join(lineas) + '\n', encoding='utf-8')


def _escape_glyphs(texto: str) -> str:
    from questions.core.converter import convert_html_tags_to_markdown
    limpio = convert_html_tags_to_markdown(texto).strip()
    return _escape_gift(limpio, 'answer')
