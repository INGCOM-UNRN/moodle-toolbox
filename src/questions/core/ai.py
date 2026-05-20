#!/usr/bin/env python3
import os
import re
import argparse
import sys
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from google import genai

from questions.core.config import get_api_key, get_model

def load_config():
    """Load configuration and return GenAI Client."""
    api_key = get_api_key()
    if not api_key:
        raise ValueError("❌ Error: GEMINI_API_KEY no encontrada. Usa 'questions config set-key <KEY>' para configurarla.")
    return genai.Client(api_key=api_key)

def split_gift_questions(content: str) -> List[str]:
    """Split GIFT content into individual questions based on blank lines."""
    # Split by one or more blank lines
    parts = re.split(r'\n\s*\n', content)
    # Filter out empty parts
    return [p.strip() for p in parts if p.strip()]

def list_available_models(client: genai.Client) -> List[str]:
    """Lista los modelos generativos disponibles en Gemini."""
    try:
        models = []
        for model in client.models.list():
            if 'generateContent' in model.supported_methods:
                models.append(model.name)
        return models
    except Exception as e:
        print(f"❌ Error al listar modelos: {e}")
        return []

def process_batch(client: genai.Client, model_id: str, questions: List[str], mode: str, custom_prompt: Optional[str] = None) -> List[str]:
    """Process a batch of questions with Gemini."""
    if not questions:
        return []

    if mode == "improve":
        system_instruction = (
            "Eres un experto en pedagogía y formato GIFT de Moodle. "
            "Tu tarea es mejorar la claridad, gramática y calidad pedagógica de las siguientes preguntas GIFT. "
            "Mantén estrictamente el formato GIFT para cada pregunta. Separa las preguntas con una línea en blanco. "
            "No añadas explicaciones fuera de los bloques de las preguntas."
        )
        if custom_prompt:
            system_instruction += f"\nInstrucción adicional: {custom_prompt}"
    elif mode == "multiply":
        system_instruction = (
            "Eres un experto en pedagogía y formato GIFT de Moodle. "
            "Tu tarea es crear 3 variaciones similares para CADA UNA de las siguientes preguntas GIFT. "
            "Mantén estrictamente el formato GIFT. Separa cada pregunta con una línea en blanco. "
            "No añadas explicaciones fuera de las preguntas."
        )
    else:  # transform
        system_instruction = (
            "Eres un experto en formato GIFT de Moodle. "
            "Tu tarea es transformar las siguientes preguntas siguiendo estas instrucciones:\n"
            f"{custom_prompt or 'Mejora las preguntas manteniendo el formato GIFT.'}\n"
            "Mantén estrictamente el formato GIFT en la salida. No añadas explicaciones."
        )

    # Join questions with separators to process in one go
    batch_text = "\n\n---\n\n".join(questions)
    prompt = f"Procesa este lote de preguntas GIFT:\n\n{batch_text}\n\nPor favor, genera el resultado en formato GIFT:"
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=f"{system_instruction}\n\n{prompt}"
        )
        # Split the response back into individual blocks if needed
        processed_batch = split_gift_questions(response.text.strip())
        return processed_batch
    except Exception as e:
        print(f"❌ Error procesando lote con Gemini: {e}")
        return questions # Return original batch on error

def process_file_batched(client: genai.Client, model_id: str, input_path: Path, output_dir: Path, mode: str, custom_prompt: Optional[str] = None, batch_size: int = 5):
    """Process a single GIFT file using batching."""
    print(f"📄 Procesando: {input_path}")
    content = input_path.read_text(encoding='utf-8')
    questions = split_gift_questions(content)
    
    if not questions:
        print(f"  ⚠️ No se encontraron preguntas en {input_path}")
        return

    processed_questions = []
    for i in range(0, len(questions), batch_size):
        batch = questions[i:i+batch_size]
        print(f"  - Lote {i//batch_size + 1}/{(len(questions)-1)//batch_size + 1} ({len(batch)} preguntas)...")
        processed_batch = process_batch(client, model_id, batch, mode, custom_prompt)
        processed_questions.extend(processed_batch)
    
    output_filename = input_path.stem + f"_{mode}" + input_path.suffix
    output_path = output_dir / output_filename
    
    output_content = "\n\n".join(processed_questions)
    output_path.write_text(output_content, encoding='utf-8')
    print(f"✅ Guardado en: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Procesa preguntas GIFT usando Google Gemini para mejora, multiplicación o transformación.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('inputs', nargs='+', help='Archivos .gift o directorios a procesar')
    parser.add_argument('--mode', choices=['improve', 'multiply', 'transform'], default='improve',
                        help='Modo: improve (mejorar), multiply (variaciones) o transform (usar prompt personalizado)')
    parser.add_argument('--prompt', help='Prompt personalizado o ruta a un archivo .txt con el prompt')
    parser.add_argument('--output', help='Directorio de salida (por defecto: output_<mode>)')
    parser.add_argument('--model', default='gemini-2.0-flash', help='Modelo de Gemini (default: gemini-2.0-flash)')
    parser.add_argument('-r', '--recursive', action='store_true', help='Procesar subdirectorios recursivamente')
    parser.add_argument('--batch-size', type=int, default=5, help='Número de preguntas por petición (default: 5)')

    args = parser.parse_args()
    
    # Resolver prompt desde archivo si es necesario
    custom_prompt = args.prompt
    if custom_prompt and Path(custom_prompt).exists() and Path(custom_prompt).is_file():
        custom_prompt = Path(custom_prompt).read_text(encoding='utf-8').strip()
    
    # Si se provee prompt y no hay modo explícito de transform o multiply, usar transform
    mode = args.mode
    if args.prompt and args.mode == 'improve':
        mode = 'transform'

    try:
        client = load_config()
    except ValueError as e:
        print(e)
        sys.exit(1)
    
    output_dir = Path(args.output) if args.output else Path(f"output_{mode}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for input_str in args.inputs:
        input_path = Path(input_str)
        if not input_path.exists():
            print(f"❌ Error: La ruta {input_str} no existe.")
            continue
            
        if input_path.is_file():
            process_file_batched(client, args.model, input_path, output_dir, mode, custom_prompt, args.batch_size)
        elif input_path.is_dir():
            pattern = "**/*.gift" if args.recursive else "*.gift"
            for gift_file in sorted(input_path.glob(pattern)):
                process_file_batched(client, args.model, gift_file, output_dir, mode, custom_prompt, args.batch_size)
        else:
            print(f"❌ Error: {input_str} no es un archivo ni un directorio válido.")

if __name__ == '__main__':
    main()
