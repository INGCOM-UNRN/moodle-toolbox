import re
from pathlib import Path
from typing import List, Tuple
from questions.core.xml_tools import sanitize_filename

def extract_title(question_text: str) -> str:
    """Extrae el título de una pregunta GIFT."""
    title_match = re.search(r'^::(.*?)::', question_text, re.DOTALL)
    if title_match:
        return title_match.group(1).strip()
    return ""

def split_gift_questions(content: str) -> List[str]:
    """Divide el contenido GIFT en preguntas individuales."""
    # Dividir por una o más líneas en blanco
    parts = re.split(r'\n\s*\n', content)
    return [p.strip() for p in parts if p.strip()]

def split_file(file_path: Path) -> int:
    """Divide un archivo GIFT en varios archivos individuales."""
    if not file_path.suffix == '.gift':
        return 0
        
    content = file_path.read_text(encoding='utf-8')
    questions = split_gift_questions(content)
    
    if len(questions) <= 1:
        return 0
        
    count = 0
    for i, q in enumerate(questions):
        title = extract_title(q)
        if title:
            base_name = sanitize_filename(title)
        else:
            base_name = f"{file_path.stem}_{i+1}"
            
        new_filename = f"{base_name}.gift"
        new_path = file_path.parent / new_filename
        
        # Evitar sobrescribir si el nombre ya existe (añadir sufijo si es necesario)
        if new_path.exists():
            new_path = file_path.parent / f"{base_name}_{i+1}.gift"
            
        new_path.write_text(q + "\n", encoding='utf-8')
        count += 1
        
    # Opcionalmente borrar el original? El usuario no lo pidió expresamente, 
    # pero suele ser lo deseado. Dejaré el original por seguridad a menos que se pida.
    return count
