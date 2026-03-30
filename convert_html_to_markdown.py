#!/usr/bin/env python3
"""
Script to convert format="html" to format="markdown" in Moodle XML files.
Also converts HTML-like tags to markdown equivalents.
"""

import os
import re
import sys
import argparse
import shutil
from pathlib import Path

def convert_html_tags_to_markdown(text):
    """Convert HTML-like tags to markdown equivalents."""
    # Replace ＜p＞...＜/p＞ with just text (markdown doesn't need explicit paragraph tags)
    text = re.sub(r'＜p＞(.*?)＜/p＞', r'\1', text, flags=re.DOTALL)
    
    # Replace ＜code＞...＜/code＞ with `...`
    text = re.sub(r'＜code＞(.*?)＜/code＞', r'`\1`', text)
    
    # Replace ＜strong＞...＜/strong＞ with **...**
    text = re.sub(r'＜strong＞(.*?)＜/strong＞', r'**\1**', text)
    
    # Replace ＜em＞...＜/em＞ with *...*
    text = re.sub(r'＜em＞(.*?)＜/em＞', r'*\1*', text)
    
    # Replace ＜br＞ or ＜br/＞ with double space + newline
    text = re.sub(r'＜br\s*/?\＞', '\n', text)
    
    # Replace ＜ul＞...＜/ul＞ lists
    text = re.sub(r'＜ul＞', '', text)
    text = re.sub(r'＜/ul＞', '', text)
    
    # Replace ＜li＞...＜/li＞ with - ...
    text = re.sub(r'＜li＞(.*?)＜/li＞', r'- \1\n', text, flags=re.DOTALL)
    
    # Replace ＜ol＞...＜/ol＞ lists
    text = re.sub(r'＜ol＞', '', text)
    text = re.sub(r'＜/ol＞', '', text)
    
    # Replace ＜pre＞...＜/pre＞ with ```...```
    text = re.sub(r'＜pre＞(.*?)＜/pre＞', r'```\n\1\n```', text, flags=re.DOTALL)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Trim leading/trailing whitespace
    text = text.strip()
    
    return text

def convert_content(content):
    """
    Process the content string: replace format="html" and convert tags.
    Returns (new_content, changed_boolean)
    """
    if 'format="html"' not in content:
        return content, False
    
    original_content = content
    
    # Replace format="html" with format="markdown"
    content = content.replace('format="html"', 'format="markdown"')
    
    # Convert HTML tags to markdown in CDATA sections
    def replace_cdata(match):
        cdata_content = match.group(1)
        converted = convert_html_tags_to_markdown(cdata_content)
        return f'<![CDATA[{converted}]]>'
    
    content = re.sub(r'<!\[CDATA\[(.*?)\]\]>', replace_cdata, content, flags=re.DOTALL)
    
    return content, (content != original_content)

def process_file(source_path, dest_path, dry_run=False):
    """
    Convert a single file.
    If dest_path is None, overwrite source_path.
    """
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content, changed = convert_content(content)
        
        if changed:
            if dry_run:
                print(f"[DRY-RUN] Would convert: {source_path} -> {dest_path if dest_path else 'IN-PLACE'}")
                return True
            
            # Determine where to write
            target = dest_path if dest_path else source_path
            
            # Ensure target directory exists if we are writing to a new destination
            if dest_path:
                os.makedirs(os.path.dirname(target), exist_ok=True)
            
            with open(target, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"Converted: {source_path} -> {target}")
            return True
        else:
            # If no changes, but we have a destination, we might want to copy the file anyway
            # or just skip. Usually, if we are mirroring a directory, we copy.
            if dest_path and not dry_run:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(source_path, dest_path)
                print(f"Copied (no changes): {source_path} -> {dest_path}")
            elif dry_run and dest_path:
                print(f"[DRY-RUN] Would copy (no changes): {source_path} -> {dest_path}")
                
            return False
            
    except Exception as e:
        print(f"Error processing {source_path}: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Convert format="html" to format="markdown" in Moodle XML files.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('source', help='Source file or directory')
    parser.add_argument('destination', nargs='?', help='Destination file or directory (optional)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: Source not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    dest_path = Path(args.destination) if args.destination else None
    
    converted_count = 0
    total_count = 0
    
    # If source is a single file
    if source_path.is_file():
        if dest_path and dest_path.is_dir():
             # If dest is a dir, append filename
             dest_path = dest_path / source_path.name
             
        if process_file(str(source_path), str(dest_path) if dest_path else None, args.dry_run):
            converted_count += 1
        total_count = 1

    # If source is a directory
    elif source_path.is_dir():
        for root, dirs, files in os.walk(source_path):
            for filename in files:
                if filename.endswith('.xml'):
                    current_source = Path(root) / filename
                    total_count += 1
                    
                    current_dest = None
                    if dest_path:
                        # Compute relative path to maintain structure
                        rel_path = current_source.relative_to(source_path)
                        current_dest = dest_path / rel_path
                    
                    if process_file(str(current_source), str(current_dest) if current_dest else None, args.dry_run):
                        converted_count += 1
    
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Total XML files scanned: {total_count}")
    print(f"Files converted/modified: {converted_count}")
    if args.dry_run:
        print("DRY RUN: No changes were made.")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
