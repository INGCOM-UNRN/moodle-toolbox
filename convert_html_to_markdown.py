#!/usr/bin/env python3
"""
Script to convert format="html" to format="markdown" in Moodle XML files.
Also converts HTML-like tags to markdown equivalents.
"""

import os
import re
import sys

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

def convert_file(filepath):
    """Convert a single XML file from HTML to markdown format."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has format="html"
        if 'format="html"' not in content:
            return False
        
        original_content = content
        
        # Replace format="html" with format="markdown"
        content = content.replace('format="html"', 'format="markdown"')
        
        # Convert HTML tags to markdown in CDATA sections
        def replace_cdata(match):
            cdata_content = match.group(1)
            converted = convert_html_tags_to_markdown(cdata_content)
            return f'<![CDATA[{converted}]]>'
        
        content = re.sub(r'<!\[CDATA\[(.*?)\]\]>', replace_cdata, content, flags=re.DOTALL)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return False

def main():
    base_dir = '/home/mrtin/dev/p1/material_ng/gift/preguntas'
    
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)
    
    converted_count = 0
    total_count = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk(base_dir):
        for filename in files:
            if filename.endswith('.xml'):
                filepath = os.path.join(root, filename)
                total_count += 1
                
                if convert_file(filepath):
                    converted_count += 1
                    print(f"Converted: {filepath}")
    
    print(f"\n{'='*60}")
    print(f"Conversion complete!")
    print(f"Total XML files: {total_count}")
    print(f"Files converted: {converted_count}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
