import re
from pathlib import Path

def format_gift_content(content: str, correct_first: bool = False) -> str:
    """
    Formatea el contenido de un archivo GIFT según las reglas estandarizadas.
    """
    # Dividimos por preguntas (basado en líneas en blanco dobles)
    questions = re.split(r'\n\s*\n', content.strip())
    formatted_questions = []
    
    for q in questions:
        if not q.strip():
            continue
            
        # Extraer comentarios iniciales
        comments = []
        q_lines = q.splitlines()
        content_start_idx = 0
        for line in q_lines:
            if line.strip().startswith('//') or line.strip().startswith('$'):
                comments.append(line.strip())
                content_start_idx += 1
            elif not line.strip():
                content_start_idx += 1
            else:
                break
        
        remaining_content = "\n".join(q_lines[content_start_idx:]).strip()
        
        # Extraer título
        title = ""
        title_match = re.match(r'^::(.*?)::(.*)', remaining_content, re.DOTALL)
        if title_match:
            title = f"::{title_match.group(1).strip()}::"
            remaining_content = title_match.group(2).strip()
            
        # Encontrar el bloque de respuestas { ... }
        brace_start = -1
        for i in range(len(remaining_content)):
            if remaining_content[i] == '{' and (i == 0 or remaining_content[i-1] != '\\'):
                brace_start = i
                break
        
        if brace_start == -1:
            stem = remaining_content.strip()
            answers_block = ""
            post_stem = ""
        else:
            stem = remaining_content[:brace_start].strip()
            brace_end = -1
            for i in range(len(remaining_content) - 1, brace_start, -1):
                if remaining_content[i] == '}' and (i == 0 or remaining_content[i-1] != '\\'):
                    brace_end = i
                    break
            
            if brace_end == -1:
                answers_block = remaining_content[brace_start+1:].strip()
                post_stem = ""
            else:
                answers_block = remaining_content[brace_start+1:brace_end].strip()
                post_stem = remaining_content[brace_end+1:].strip()

        # Formatear la pregunta
        parts = []
        if comments:
            parts.extend(comments)
        
        if title:
            parts.append(title)
            
        if stem:
            parts.append(stem)
            
        if brace_start != -1:
            parts.append("{")
            ans_lines = []
            raw_answers = answers_block.splitlines()
            current_ans = ""
            for line in raw_answers:
                line = line.strip()
                if not line: continue
                
                if line[0] in ('=', '~', '#', '{') or (line.startswith('####')):
                    if current_ans:
                        ans_lines.append(current_ans)
                    current_ans = line
                else:
                    if current_ans:
                        current_ans += " " + line
                    else:
                        current_ans = line
            
            if current_ans:
                ans_lines.append(current_ans)
            
            # Reordenar si correct_first es True (solo para MC)
            if correct_first:
                correct = [a for a in ans_lines if a.startswith('=')]
                incorrect = [a for a in ans_lines if a.startswith('~')]
                others = [a for a in ans_lines if not a.startswith('=') and not a.startswith('~')]
                
                # Solo reordenar si parece una pregunta MC estándar
                if correct and incorrect:
                    ans_lines = correct + incorrect + others

            # Aplicar indentación final
            ans_lines = ["    " + a for a in ans_lines]
                
            parts.extend(ans_lines)
            parts.append("}")
        
        if post_stem:
            parts.append(post_stem)
            
        formatted_questions.append("\n".join(parts))
        
    return "\n\n".join(formatted_questions) + "\n"


def fix_code_indentation(content: str) -> tuple[str, int]:
    """
    Reemplaza 4 espacios de indentación por '····' dentro de bloques de código.
    """
    lines = content.split('\n')
    result_lines = []
    in_code_block = False
    total_replacements = 0
    
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result_lines.append(line)
            continue
        
        if in_code_block:
            original_line = line
            new_line = ""
            i = 0
            while i + 4 <= len(line) and line[i:i+4] == "    ":
                new_line += "····"
                i += 4
                total_replacements += 1
            new_line += line[i:]
            result_lines.append(new_line)
        else:
            result_lines.append(line)
            
    return '\n'.join(result_lines), total_replacements


SPECIAL_CHARS_TO_NORMAL = {
    "⩵": "==",
    "＝": "=",
    ";": ";",
    "＃": "#",
    "｛": "{",
    "｝": "}",
    " ": " ",
    "↵": "\n",
    "    ": "\t",
    "＞": ">",
    "＜": "<",
    "［": "[",
    "］": "]",
    " ": " ",
    "（": "(",
    "）": ")",
    "＊": "*",
    "＂": '"',
    "：": ":",
}

XML_ENTITIES_TO_FULLWIDTH = {
    "&lt;": "＜",
    "&gt;": "＞",
    "&amp;": "＆",
    "&quot;": "＂",
    "&apos;": "＇",
    "&#39;": "＇",
    "&#34;": "＂",
    "&#60;": "＜",
    "&#62;": "＞",
    "&#38;": "＆",
    "&nbsp;": "　",
}

NORMAL_TO_SPECIAL_CHARS = {v: k for k, v in SPECIAL_CHARS_TO_NORMAL.items() if v != "\n" and v != "\t"}
FULLWIDTH_TO_XML_ENTITIES = {v: k for k, v in XML_ENTITIES_TO_FULLWIDTH.items()}


def convert_code_block_content(content: str, to_normal: bool = True) -> str:
    """
    Convierte el contenido de un bloque de código entre normal y fullwidth.
    """
    if to_normal:
        for fullwidth, normal in SPECIAL_CHARS_TO_NORMAL.items():
            content = content.replace(fullwidth, normal)
        for fullwidth, entity in FULLWIDTH_TO_XML_ENTITIES.items():
            if fullwidth not in SPECIAL_CHARS_TO_NORMAL:
                content = content.replace(fullwidth, entity)
    else:
        for entity, fullwidth in XML_ENTITIES_TO_FULLWIDTH.items():
            content = content.replace(entity, fullwidth)
        for normal, fullwidth in NORMAL_TO_SPECIAL_CHARS.items():
            content = content.replace(normal, fullwidth)
    return content


def convert_markdown_code_blocks(text: str, to_normal: bool = True) -> tuple[str, int]:
    """
    Convierte caracteres especiales en bloques de código markdown.
    """
    blocks_modified = 0
    
    def replace_code_block(match):
        nonlocal blocks_modified
        lang = match.group(1) or ''
        content = match.group(2)
        converted = convert_code_block_content(content, to_normal)
        if converted != content:
            blocks_modified += 1
        return f"```{lang}\n{converted}\n```"
    
    text = re.sub(r'```([a-z]*)\n(.*?)```', replace_code_block, text, flags=re.DOTALL)
    
    def replace_inline_code(match):
        nonlocal blocks_modified
        content = match.group(1)
        converted = convert_code_block_content(content, to_normal)
        if converted != content:
            blocks_modified += 1
        return f"`{converted}`"
    
    text = re.sub(r'`([^`\n]+)`', replace_inline_code, text)
    return text, blocks_modified


def process_xml_cdata(text: str, to_normal: bool = True) -> tuple[str, int]:
    """
    Procesa secciones CDATA en archivos XML.
    """
    total_blocks = 0
    def replace_cdata(match):
        nonlocal total_blocks
        cdata_content = match.group(1)
        converted_content, blocks = convert_markdown_code_blocks(cdata_content, to_normal)
        total_blocks += blocks
        return f"<![CDATA[{converted_content}]]>"
    
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', replace_cdata, text, flags=re.DOTALL)
    return text, total_blocks
