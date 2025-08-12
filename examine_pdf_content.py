#!/usr/bin/env python3

import PyPDF2
import sys

def examine_pdf_content(pdf_path: str, max_lines: int = 100):
    """Extract and display the first part of PDF content to understand structure"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"PDF has {len(pdf_reader.pages)} pages")
            
            # Extract text from first few pages
            text_content = []
            for i, page in enumerate(pdf_reader.pages[:3]):  # First 3 pages
                page_text = page.extract_text()
                text_content.append(f"\n--- PAGE {i+1} ---\n")
                text_content.append(page_text)
            
            full_text = '\n'.join(text_content)
            lines = full_text.split('\n')
            
            print(f"\nFirst {max_lines} lines of content:\n")
            for i, line in enumerate(lines[:max_lines]):
                if line.strip():
                    # Clean line for display
                    clean_line = line.encode('ascii', 'ignore').decode('ascii')
                    print(f"{i+1:3d}: {clean_line}")
            
            print(f"\n--- Potential headings (lines that might be headings) ---")
            potential_headings = []
            for line in lines[:200]:  # Check first 200 lines
                line = line.strip()
                if line and (
                    line.isupper() or 
                    len(line.split()) <= 8 and line[0].isupper() or
                    any(word in line.lower() for word in ['chapter', 'section', 'part'])
                ):
                    potential_headings.append(line)
            
            for heading in potential_headings[:20]:  # Show first 20 potential headings
                clean_heading = heading.encode('ascii', 'ignore').decode('ascii')
                print(f"  • {clean_heading}")
                
    except Exception as e:
        print(f"Error examining PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python examine_pdf_content.py <pdf_path>")
        sys.exit(1)
    
    examine_pdf_content(sys.argv[1])