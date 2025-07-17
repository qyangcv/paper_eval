#!/usr/bin/env python3
"""
Test script to verify reference counting logic
"""

import re
from docx import Document

def test_ref_count(docx_path):
    """Test reference counting logic"""
    print(f"Testing reference counting for: {docx_path}")
    print("=" * 50)
    
    # Load document
    doc = Document(docx_path)
    
    # Get full text
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    text = '\n'.join(full_text)
    
    # Find references section
    ref_pattern = r'参考文献\s*\n(.+?)(?=\n\s*\n|致谢|附录|\Z)'
    ref_match = re.search(ref_pattern, text, re.DOTALL)
    
    if not ref_match:
        # Try alternative pattern
        ref_pattern = r'参考文献(.+?)(?=\n\s*\n|致谢|附录|\Z)'
        ref_match = re.search(ref_pattern, text, re.DOTALL)
    
    if not ref_match:
        print("No references section found with '参考文献' header!")
        print("Treating entire document as references for testing...")
        ref_text = text
    else:
        ref_text = ref_match.group(1)
    print(f"References section found, length: {len(ref_text)} characters")
    print("\nFirst 500 characters of references:")
    print(ref_text[:500])
    print("\n" + "=" * 50)
    
    # Count total references
    ref_patterns = [
        r'\[\d+\]',  # [1], [2], etc.
        r'^\d+\.',   # 1., 2., etc.
        r'^\d+\s',   # 1 , 2 , etc.
    ]
    
    total_references = 0
    for pattern in ref_patterns:
        matches = re.findall(pattern, ref_text, re.MULTILINE)
        if matches:
            total_references = max(total_references, len(matches))
            print(f"Pattern '{pattern}' found {len(matches)} matches")
    
    print(f"\nTotal references found by patterns: {total_references}")
    
    # Find all reference entries
    ref_lines = [line.strip() for line in ref_text.split('\n') if line.strip()]
    reference_entries = []
    
    # Check for numbered format first
    for line in ref_lines:
        if re.search(r'\[\d+\]', line):  # This is a reference line
            reference_entries.append(line)
    
    # If no numbered format found, treat each non-empty line as a reference
    if not reference_entries:
        print("No numbered references found, treating each line as a reference")
        reference_entries = [line for line in ref_lines if line.strip()]
        total_references = len(reference_entries)
    
    print(f"Reference entries found: {len(reference_entries)}")
    print(f"Adjusted total references: {total_references}")
    
    # Test language detection
    chinese_refs = 0
    english_refs = 0
    
    print("\nTesting language detection:")
    print("-" * 30)
    
    for i, ref_entry in enumerate(reference_entries[:10]):  # Show first 10 for testing
        # Remove the reference number [1], [2], etc.
        content = re.sub(r'^\[\d+\]', '', ref_entry).strip()
        
        # Extract the first word (author name)
        first_word_match = re.match(r'^([^\s,，.]+)', content)
        if first_word_match:
            first_word = first_word_match.group(1)
            
            # Check if first word contains Chinese characters
            if re.search(r'[\u4e00-\u9fff]', first_word):
                lang = "Chinese"
                chinese_refs += 1
            else:
                lang = "English"
                english_refs += 1
            
            print(f"[{i+1}] First word: '{first_word}' -> {lang}")
            print(f"    Full entry: {ref_entry[:100]}...")
        else:
            lang = "English (fallback)"
            english_refs += 1
            print(f"[{i+1}] No first word found -> {lang}")
            print(f"    Full entry: {ref_entry[:100]}...")
        print()
    
    # Process all entries
    chinese_refs = 0
    english_refs = 0
    
    for ref_entry in reference_entries:
        # Remove the reference number [1], [2], etc.
        content = re.sub(r'^\[\d+\]', '', ref_entry).strip()
        
        # Extract the first word (author name)
        first_word_match = re.match(r'^([^\s,，.]+)', content)
        if first_word_match:
            first_word = first_word_match.group(1)
            
            # Check if first word contains Chinese characters
            if re.search(r'[\u4e00-\u9fff]', first_word):
                chinese_refs += 1
            else:
                english_refs += 1
        else:
            # If no first word found, assume English
            english_refs += 1
    
    print("=" * 50)
    print("FINAL RESULTS:")
    print(f"Total references: {total_references}")
    print(f"Chinese references: {chinese_refs}")
    print(f"English references: {english_refs}")
    print(f"Sum: {chinese_refs + english_refs}")
    print(f"Match total: {chinese_refs + english_refs == total_references}")

if __name__ == "__main__":
    test_ref_count("backend_fastapi/data/processed/参考文献.docx")