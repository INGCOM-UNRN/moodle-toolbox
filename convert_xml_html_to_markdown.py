#!/usr/bin/env python3
"""
Script to convert HTML tags to markdown format in XML question files.
Converts <code>, <p>, <strong>, <pre> and other HTML tags to markdown equivalents.
"""

import os
import re
from pathlib import Path

def convert_html_to_markdown(text):
    """Convert HTML tags to markdown format within CDATA sections."""
    
    # Convert <code>...</code> to backticks
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)
    
    # Remove orphaned </code> tags (without opening tags)
    text = re.sub(r'</code>', '', text)
    
    # Remove orphaned <code> tags (without closing tags)
    text = re.sub(r'<code>', '`', text)
    
    # Convert <strong>...</strong> to **...**
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
    
    # Convert <pre>...</pre> to code blocks with proper newlines
    def convert_pre(match):
        content = match.group(1)
        # Remove leading/trailing whitespace but preserve internal formatting
        content = content.strip()
        return f'\n```\n{content}\n```\n'
    
    text = re.sub(r'<pre>(.*?)</pre>', convert_pre, text, flags=re.DOTALL)
    
    # Convert <p>...</p> - just remove the tags, keep content
    # Sometimes <p> tags add unnecessary wrapping
    text = re.sub(r'<p>(.*?)</p>', r'\1', text, flags=re.DOTALL)
    
    # Convert standalone <p> or </p> tags
    text = re.sub(r'</?p>', '', text)
    
    # Convert <br> or <br/> to markdown line breaks
    text = re.sub(r'<br\s*/?>', '\n', text)
    
    # Convert <em>...</em> or <i>...</i> to *...*
    text = re.sub(r'<(?:em|i)>(.*?)</(?:em|i)>', r'*\1*', text, flags=re.DOTALL)
    
    return text

def process_xml_file(filepath):
    """Process a single XML file to convert HTML to markdown."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Process CDATA sections
        def process_cdata(match):
            cdata_content = match.group(1)
            converted = convert_html_to_markdown(cdata_content)
            return f'<![CDATA[{converted}]]>'
        
        # Apply conversion to all CDATA sections
        content = re.sub(r'<!\[CDATA\[(.*?)\]\]>', process_cdata, content, flags=re.DOTALL)
        
        # Also process <text> elements that are NOT wrapped in CDATA
        # Pattern: <text>content</text> where content doesn't start with <![CDATA[
        def process_text_element(match):
            text_content = match.group(1)
            # Only process if it's not CDATA (which would have been handled above)
            if not text_content.strip().startswith('<![CDATA['):
                converted = convert_html_to_markdown(text_content)
                return f'<text>{converted}</text>'
            return match.group(0)
        
        content = re.sub(r'<text>((?:(?!</text>).)*)</text>', process_text_element, content, flags=re.DOTALL)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, filepath
        return False, None
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False, None

def main():
    """Main function to process all XML files."""
    preguntas_dir = Path('./preguntas')
    
    if not preguntas_dir.exists():
        print(f"Directory {preguntas_dir} does not exist!")
        return
    
    # Find all XML files
    xml_files = list(preguntas_dir.rglob('*.xml'))
    print(f"Found {len(xml_files)} XML files to process...")
    
    modified_count = 0
    modified_files = []
    
    for xml_file in xml_files:
        modified, filepath = process_xml_file(xml_file)
        if modified:
            modified_count += 1
            modified_files.append(filepath)
            if modified_count % 10 == 0:
                print(f"Processed {modified_count} files...")
    
    print(f"\n{'='*60}")
    print(f"Conversion complete!")
    print(f"Total files processed: {len(xml_files)}")
    print(f"Files modified: {modified_count}")
    print(f"{'='*60}")
    
    if modified_count > 0 and modified_count <= 20:
        print("\nModified files:")
        for f in modified_files:
            print(f"  - {f}")

if __name__ == '__main__':
    main()
