#!/usr/bin/env python3
import os
import re
import argparse
import sys
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from google import genai

def load_config():
    """Load configuration from .env file and return GenAI Client."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY no encontrada en el archivo .env")
        print("Asegúrate de crear un archivo .env basado en .env.example")
        sys.exit(1)
    return genai.Client(api_key=api_key)

def split_gift_questions(content: str) -> List[str]:
    """Split GIFT content into individual questions based on blank lines."""
    # Split by one or more blank lines
    parts = re.split(r'\n\s*\n', content)
    # Filter out empty parts
    return [p.strip() for p in parts if p.strip()]

def process_question(client: genai.Client, model_id: str, question: str, mode: str, custom_prompt: Optional[str] = None) -> str:
    """Process a single question with Gemini."""
    if mode == "improve":
        system_instruction = (
            "Eres un experto en pedagogía y formato GIFT de Moodle. "
            "Tu tarea es mejorar la claridad, gramática y calidad pedagógica de la siguiente pregunta GIFT. "
            "Mantén estrictamente el formato GIFT. No añadas explicaciones fuera del bloque de la pregunta. "
            "Asegúrate de que la pregunta sea desafiante pero justa."
        )
        if custom_prompt:
            system_instruction += f"\nInstrucción adicional: {custom_prompt}"
    elif mode == "multiply":
        system_instruction = (
            "Eres un experto en pedagogía y formato GIFT de Moodle. "
            "Tu tarea es crear 3 variaciones similares de la siguiente pregunta GIFT. "
            "Las variaciones deben evaluar el mismo concepto pero con diferentes redacciones o valores. "
            "Mantén estrictamente el formato GIFT para cada variación. "
            "Separa cada pregunta con una línea en blanco. "
            "No añadas explicaciones fuera de las preguntas."
        )
    else:  # transform
        system_instruction = (
            "Eres un experto en formato GIFT de Moodle. "
            "Tu tarea es transformar la siguiente pregunta siguiendo estas instrucciones:\n"
            f"{custom_prompt or 'Mejora la pregunta manteniendo el formato GIFT.'}\n"
            "Mantén estrictamente el formato GIFT en la salida. No añadas explicaciones fuera del bloque de la pregunta."
        )

    prompt = f"Pregunta original:\n\n{question}\n\nPor favor, genera el resultado en formato GIFT:"
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=f"{system_instruction}\n\n{prompt}"
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Error procesando pregunta con Gemini: {e}")
        return question # Return original on error

def process_file(client: genai.Client, model_id: str, input_path: Path, output_dir: Path, mode: str, custom_prompt: Optional[str] = None):
    """Process a single GIFT file."""
    print(f"📄 Procesando: {input_path}")
    content = input_path.read_text(encoding='utf-8')
    questions = split_gift_questions(content)
    
    processed_questions = []
    for i, q in enumerate(questions):
        print(f"  - Pregunta {i+1}/{len(questions)}...")
        processed = process_question(client, model_id, q, mode, custom_prompt)
        processed_questions.append(processed)
    
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

    args = parser.parse_args()
    
    # Resolver prompt desde archivo si es necesario
    custom_prompt = args.prompt
    if custom_prompt and Path(custom_prompt).exists() and Path(custom_prompt).is_file():
        custom_prompt = Path(custom_prompt).read_text(encoding='utf-8').strip()
    
    # Si se provee prompt y no hay modo explícito de transform o multiply, usar transform
    mode = args.mode
    if args.prompt and args.mode == 'improve':
        mode = 'transform'

    client = load_config()
    
    output_dir = Path(args.output) if args.output else Path(f"output_{mode}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for input_str in args.inputs:
        input_path = Path(input_str)
        if not input_path.exists():
            print(f"❌ Error: La ruta {input_str} no existe.")
            continue
            
        if input_path.is_file():
            process_file(client, args.model, input_path, output_dir, mode, custom_prompt)
        elif input_path.is_dir():
            pattern = "**/*.gift" if args.recursive else "*.gift"
            for gift_file in input_path.glob(pattern):
                process_file(client, args.model, gift_file, output_dir, mode, custom_prompt)
        else:
            print(f"❌ Error: {input_str} no es un archivo ni un directorio válido.")

if __name__ == '__main__':
    main()
