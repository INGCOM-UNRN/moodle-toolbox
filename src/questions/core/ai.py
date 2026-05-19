#!/usr/bin/env python3
import os
import re
import argparse
import sys
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
import google.generativeai as genai

def load_config():
    """Load configuration from .env file."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY no encontrada en el archivo .env")
        print("Asegúrate de crear un archivo .env basado en .env.example")
        sys.exit(1)
    genai.configure(api_key=api_key)

def split_gift_questions(content: str) -> List[str]:
    """Split GIFT content into individual questions based on blank lines."""
    # Split by one or more blank lines
    parts = re.split(r'\n\s*\n', content)
    # Filter out empty parts
    return [p.strip() for p in parts if p.strip()]

def process_question(model, question: str, mode: str, custom_prompt: Optional[str] = None) -> str:
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
    else:  # multiply
        system_instruction = (
            "Eres un experto en pedagogía y formato GIFT de Moodle. "
            "Tu tarea es crear 3 variaciones similares de la siguiente pregunta GIFT. "
            "Las variaciones deben evaluar el mismo concepto pero con diferentes redacciones o valores. "
            "Mantén estrictamente el formato GIFT para cada variación. "
            "Separa cada pregunta con una línea en blanco. "
            "No añadas explicaciones fuera de las preguntas."
        )

    prompt = f"Pregunta original:\n\n{question}\n\nPor favor, genera el resultado en formato GIFT:"
    
    try:
        response = model.generate_content(
            f"{system_instruction}\n\n{prompt}"
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Error procesando pregunta con Gemini: {e}")
        return question # Return original on error

def process_file(model, input_path: Path, output_dir: Path, mode: str, custom_prompt: Optional[str] = None):
    """Process a single GIFT file."""
    print(f"📄 Procesando: {input_path}")
    content = input_path.read_text(encoding='utf-8')
    questions = split_gift_questions(content)
    
    processed_questions = []
    for i, q in enumerate(questions):
        print(f"  - Pregunta {i+1}/{len(questions)}...")
        processed = process_question(model, q, mode, custom_prompt)
        processed_questions.append(processed)
    
    output_filename = input_path.stem + f"_{mode}" + input_path.suffix
    output_path = output_dir / output_filename
    
    output_content = "\n\n".join(processed_questions)
    output_path.write_text(output_content, encoding='utf-8')
    print(f"✅ Guardado en: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Procesa preguntas GIFT usando Google Gemini para mejora o multiplicación.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('input', help='Archivo .gift o directorio a procesar')
    parser.add_argument('--mode', choices=['improve', 'multiply'], required=True,
                        help='Modo de procesamiento: improve (mejorar) o multiply (crear variaciones)')
    parser.add_argument('--prompt', help='Prompt personalizado para el modo improve')
    parser.add_argument('--output', help='Directorio de salida (por defecto: output_<mode>)')
    parser.add_argument('--model', default='gemini-2.0-flash', help='Modelo de Gemini a usar (por defecto: gemini-2.0-flash)')

    args = parser.parse_args()
    
    load_config()
    model = genai.GenerativeModel(args.model)
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: La ruta {args.input} no existe.")
        sys.exit(1)
        
    output_dir = Path(args.output) if args.output else Path(f"output_{args.mode}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if input_path.is_file():
        process_file(model, input_path, output_dir, args.mode, args.prompt)
    elif input_path.is_dir():
        for gift_file in input_path.glob("*.gift"):
            process_file(model, gift_file, output_dir, args.mode, args.prompt)
    else:
        print(f"❌ Error: {args.input} no es un archivo ni un directorio válido.")
        sys.exit(1)

if __name__ == '__main__':
    main()
