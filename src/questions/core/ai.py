#!/usr/bin/env python3
import os
import re
import argparse
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
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
            "Mantén estrictamente el formato GIFT en la salida. No añadas explicaciones fuera del bloque de la pregunta."
        )

    # Use a clear separator in the prompt
    batch_text = ""
    for i, q in enumerate(questions):
        batch_text += f"--- PREGUNTA {i+1} ---\n{q}\n\n"

    prompt = (
        f"Procesa este lote de {len(questions)} preguntas GIFT:\n\n{batch_text}\n\n"
        "REQUISITO CRÍTICO: Devuelve las preguntas procesadas en el mismo orden, "
        "separadas por una línea que contenga únicamente '---'. "
        "No incluyas preámbulos ni conclusiones."
    )
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=f"{system_instruction}\n\n{prompt}"
        )
        
        # Split by the separator used by the AI
        raw_output = response.text.strip()
        processed_blocks = re.split(r'\n---\n|---', raw_output)
        
        # Filter and clean
        processed_questions = [p.strip() for p in processed_blocks if p.strip()]
        
        # Validate that we got a reasonable number of questions
        if mode == 'multiply':
            # In multiply mode we expect roughly 3x questions
            if len(processed_questions) < len(questions):
                print(f"  ⚠️ Advertencia: El lote devolvió menos preguntas ({len(processed_questions)}) de las esperadas.")
        else:
            if len(processed_questions) != len(questions):
                print(f"  ⚠️ Advertencia: El lote devolvió {len(processed_questions)} preguntas pero se enviaron {len(questions)}.")
        
        return processed_questions
    except Exception as e:
        print(f"❌ Error procesando lote con Gemini: {e}")
        return questions # Return original batch on error

def run_global_ai_processing(client: genai.Client, model_id: str, file_paths: List[Path], output_dir: Optional[Path], mode: str, custom_prompt: Optional[str] = None, batch_size: int = 5, in_place: bool = False):
    """Procesa todas las preguntas de todos los archivos en lotes globales."""
    
    all_questions_meta = [] # List of { "path": Path, "text": str }
    
    print(f"🔍 Escaneando {len(file_paths)} archivos...")
    for path in file_paths:
        try:
            content = path.read_text(encoding='utf-8')
            questions = split_gift_questions(content)
            for q in questions:
                all_questions_meta.append({"path": path, "text": q})
        except Exception as e:
            print(f"❌ Error leyendo {path}: {e}")

    total_questions = len(all_questions_meta)
    if total_questions == 0:
        print("⚠️ No se encontraron preguntas para procesar.")
        return

    print(f"🚀 Iniciando procesamiento de {total_questions} preguntas en lotes de {batch_size}...")
    
    # Process in batches
    for i in range(0, total_questions, batch_size):
        batch_meta = all_questions_meta[i:i+batch_size]
        batch_texts = [m["text"] for m in batch_meta]
        
        print(f"  📦 Lote {i//batch_size + 1}/{(total_questions-1)//batch_size + 1} ({len(batch_texts)} preguntas)...")
        
        processed_texts = process_batch(client, model_id, batch_texts, mode, custom_prompt)
        
        # Map results back
        if mode == 'multiply':
            # Multiply is harder to map 1:1 if the AI merges things, 
            # but usually it returns blocks of 3. 
            # We'll just append them to the meta objects for now.
            # (Simplified implementation: in multiply mode, we might not be able to 
            # perfectly distribute if the batch doesn't return exactly len*3)
            # For simplicity in this refactor, we'll store processed text in each meta.
            # If length matches exactly len*3, we can distribute 3 per input.
            if len(processed_texts) == len(batch_texts) * 3:
                for j, meta in enumerate(batch_meta):
                    meta["processed"] = "\n\n".join(processed_texts[j*3 : (j+1)*3])
            else:
                # Fallback: distribute what we have or store everything in the last one? 
                # Better to just store the whole result in the first one and empty others?
                # No, let's just mark it as processed.
                batch_meta[0]["processed"] = "\n\n".join(processed_texts)
                for j in range(1, len(batch_meta)):
                    batch_meta[j]["processed"] = ""
        else:
            # 1:1 mapping (Improve / Transform)
            for j, meta in enumerate(batch_meta):
                if j < len(processed_texts):
                    meta["processed"] = processed_texts[j]
                else:
                    meta["processed"] = meta["text"] # Fallback to original

    # Write results back
    print("💾 Guardando resultados...")
    files_to_write = {} # Path -> List[str]
    
    for meta in all_questions_meta:
        path = meta["path"]
        if path not in files_to_write:
            files_to_write[path] = []
        if "processed" in meta and meta["processed"]:
            files_to_write[path].append(meta["processed"])
        else:
            files_to_write[path].append(meta["text"])

    modified_count = 0
    for path, questions in files_to_write.items():
        output_content = "\n\n".join(questions) + "\n"
        
        if in_place:
            path.write_text(output_content, encoding='utf-8')
            print(f"  ✓ {path} (actualizado)")
        else:
            output_filename = path.stem + f"_{mode}" + path.suffix
            output_path = output_dir / output_filename
            output_path.write_text(output_content, encoding='utf-8')
            print(f"  ✓ {output_path} (creado)")
        modified_count += 1

    print(f"\n✅ Finalizado: {modified_count} archivos procesados.")

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
    parser.add_argument('--model', help='Modelo de Gemini (default: configurado o gemini-2.0-flash)')
    parser.add_argument('-r', '--recursive', action='store_true', help='Procesar subdirectorios recursivamente')
    parser.add_argument('--batch-size', type=int, default=5, help='Número de preguntas por petición (default: 5)')
    parser.add_argument('-i', '--in-place', action='store_true', help='Sobrescribir los archivos originales')

    args = parser.parse_args()
    
    # Resolver prompt
    custom_prompt = args.prompt
    if custom_prompt and Path(custom_prompt).exists() and Path(custom_prompt).is_file():
        custom_prompt = Path(custom_prompt).read_text(encoding='utf-8').strip()
    
    mode = args.mode
    if args.prompt and args.mode == 'improve':
        mode = 'transform'

    try:
        client = load_config()
    except ValueError as e:
        print(e)
        sys.exit(1)
    
    active_model = args.model or get_model()
    
    output_dir = None
    if not args.in_place:
        output_dir = Path(args.output) if args.output else Path(f"output_{mode}")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect all file paths
    file_paths = []
    for input_str in args.inputs:
        input_path = Path(input_str)
        if not input_path.exists():
            print(f"❌ Error: La ruta {input_str} no existe.")
            continue
            
        if input_path.is_file():
            if input_path.suffix == '.gift':
                file_paths.append(input_path)
        elif input_path.is_dir():
            pattern = "**/*.gift" if args.recursive else "*.gift"
            file_paths.extend(sorted(list(input_path.glob(pattern))))

    if not file_paths:
        print("❌ No se encontraron archivos .gift para procesar.")
        sys.exit(1)

    run_global_ai_processing(
        client=client,
        model_id=active_model,
        file_paths=file_paths,
        output_dir=output_dir,
        mode=mode,
        custom_prompt=custom_prompt,
        batch_size=args.batch_size,
        in_place=args.in_place
    )

if __name__ == '__main__':
    main()
