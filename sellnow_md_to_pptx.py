#!/usr/bin/env python3
"""
Sellnow Markdown to PowerPoint Converter

Converts specially formatted markdown files (Sellnow format) to PowerPoint presentations.
Each slide is separated by "--- SLIDE X ---" markers and contains structured sections:
- Type: The type of slide (Title Slide, Content Slide, etc.)
- Title: The slide title
- Body: The main content
- Speaker Notes: Notes for the presenter
- Accessibility: Alt text and accessibility information
"""

import argparse
import re
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN


def parse_sellnow_markdown(file_path):
    """Parse Sellnow-formatted markdown file and extract slide data."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split by slide markers
    slide_pattern = r'--- SLIDE \d+ ---'
    slides_raw = re.split(slide_pattern, content)

    # Remove empty first element (content before first slide)
    slides_raw = [s for s in slides_raw if s.strip()]

    slides = []
    for slide_content in slides_raw:
        slide_data = parse_slide_content(slide_content)
        if slide_data:
            slides.append(slide_data)

    return slides


def parse_slide_content(content):
    """Parse individual slide content to extract structured data."""
    slide_data = {
        'type': '',
        'title': '',
        'body': '',
        'speaker_notes': '',
        'accessibility': ''
    }

    # Extract Type
    type_match = re.search(r'\*\*Type:\*\*\s*(.+?)(?=\n\*\*|\n\n|$)', content, re.DOTALL)
    if type_match:
        slide_data['type'] = type_match.group(1).strip()

    # Extract Title
    title_match = re.search(r'\*\*Title:\*\*\s*(.+?)(?=\n\*\*|\n\n|$)', content, re.DOTALL)
    if title_match:
        slide_data['title'] = title_match.group(1).strip()

    # Extract Body (everything between **Body:** and **Speaker Notes:** or **Accessibility:**)
    body_match = re.search(r'\*\*Body:\*\*\s*\n(.*?)(?=\n\*\*(?:Speaker Notes|Accessibility|Chapter):|$)',
                          content, re.DOTALL)
    if body_match:
        slide_data['body'] = body_match.group(1).strip()

    # Extract Speaker Notes
    notes_match = re.search(r'\*\*Speaker Notes:\*\*\s*\n(.*?)(?=\n\*\*Accessibility:|$)',
                           content, re.DOTALL)
    if notes_match:
        slide_data['speaker_notes'] = notes_match.group(1).strip()

    # Extract Accessibility
    access_match = re.search(r'\*\*Accessibility:\*\*\s*\n(.*?)$', content, re.DOTALL)
    if access_match:
        slide_data['accessibility'] = access_match.group(1).strip()

    return slide_data


def format_body_content(body_text):
    """Convert markdown-style body content to formatted paragraphs."""
    if not body_text:
        return []

    lines = body_text.split('\n')
    formatted_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Determine indentation level based on leading spaces/bullets
        level = 0
        clean_line = line

        # Check for numbered lists (1. 2. etc.)
        if re.match(r'^\d+\.', line):
            clean_line = re.sub(r'^\d+\.\s*', '', line)
            level = 0
        # Check for bullet with indentation (spaces before *)
        elif '    *' in line or '    -' in line:
            clean_line = re.sub(r'^\s*[\*\-]\s*', '', line)
            level = 1
        # Check for regular bullet
        elif line.startswith('*') or line.startswith('-'):
            clean_line = re.sub(r'^[\*\-]\s*', '', line)
            level = 0
        # Regular text (no bullet)
        else:
            clean_line = line
            level = 0

        # Remove markdown bold formatting but keep the text
        clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_line)

        formatted_content.append({
            'text': clean_line,
            'level': level
        })

    return formatted_content


def create_powerpoint(slides, output_file):
    """Create PowerPoint presentation from parsed slides."""
    prs = Presentation()

    for i, slide_data in enumerate(slides):
        slide_type = slide_data['type']

        # Choose layout based on slide type
        if 'Title Slide' in slide_type:
            layout = prs.slide_layouts[0]  # Title slide
        elif 'Section' in slide_type or 'Unit' in slide_type:
            layout = prs.slide_layouts[5]  # Title only
        else:
            layout = prs.slide_layouts[1]  # Title and content

        slide = prs.slides.add_slide(layout)

        # Add title
        if slide.shapes.title:
            slide.shapes.title.text = slide_data['title']

        # Add body content
        if slide_data['body']:
            # For title slide, try to use subtitle placeholder
            if 'Title Slide' in slide_type:
                if len(slide.placeholders) > 1:
                    subtitle = slide.placeholders[1]
                    text_frame = subtitle.text_frame
                    text_frame.clear()

                    # Add body as simple text for title slides
                    body_lines = slide_data['body'].split('\n')
                    for idx, line in enumerate(body_lines):
                        line = line.strip()
                        if not line:
                            continue
                        # Remove markdown formatting
                        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
                        if idx == 0:
                            p = text_frame.paragraphs[0]
                        else:
                            p = text_frame.add_paragraph()
                        p.text = line
                        p.alignment = PP_ALIGN.CENTER

            # For section/unit slides, add body below title
            elif 'Section' in slide_type or 'Unit' in slide_type:
                # Add a text box for the body
                left = Inches(2)
                top = Inches(3)
                width = Inches(6)
                height = Inches(2)
                text_box = slide.shapes.add_textbox(left, top, width, height)
                text_frame = text_box.text_frame
                text_frame.clear()

                body_lines = slide_data['body'].split('\n')
                for idx, line in enumerate(body_lines):
                    line = line.strip()
                    if not line:
                        continue
                    line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
                    if idx == 0:
                        p = text_frame.paragraphs[0]
                    else:
                        p = text_frame.add_paragraph()
                    p.text = line
                    p.alignment = PP_ALIGN.CENTER
                    p.font.size = Pt(24)

            # For content slides, use content placeholder
            else:
                if len(slide.placeholders) > 1:
                    content_placeholder = slide.placeholders[1]
                    text_frame = content_placeholder.text_frame
                    text_frame.clear()

                    formatted_content = format_body_content(slide_data['body'])

                    for idx, item in enumerate(formatted_content):
                        if idx == 0:
                            p = text_frame.paragraphs[0]
                        else:
                            p = text_frame.add_paragraph()

                        p.text = item['text']
                        p.level = item['level']

        # Add speaker notes
        if slide_data['speaker_notes']:
            notes_slide = slide.notes_slide
            text_frame = notes_slide.notes_text_frame
            text_frame.clear()

            # Add the speaker notes text
            p = text_frame.paragraphs[0]
            p.text = slide_data['speaker_notes']

    # Save presentation
    prs.save(output_file)
    print(f"PowerPoint presentation saved as: {output_file}")


def main():
    """Main function to handle command line arguments and execute conversion."""
    parser = argparse.ArgumentParser(
        description='Convert Sellnow-formatted markdown to PowerPoint presentation'
    )
    parser.add_argument(
        'input_file',
        help='Input markdown file in Sellnow format'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output PowerPoint file name (default: input_file.pptx)',
        default=None
    )

    args = parser.parse_args()

    # Check if input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        output_file = input_path.stem + '.pptx'

    try:
        # Parse markdown file
        print(f"Parsing Sellnow markdown file: {args.input_file}")
        slides = parse_sellnow_markdown(input_path)
        print(f"Found {len(slides)} slides")

        # Create PowerPoint
        print(f"Creating PowerPoint presentation...")
        create_powerpoint(slides, output_file)
        print("Conversion completed successfully!")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
