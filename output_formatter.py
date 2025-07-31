from typing import Dict, Any, List, Optional
import json
import csv
from datetime import datetime
import os

class OutputFormatter:
    def __init__(self):
        self.supported_formats = ['markdown', 'html', 'json', 'txt', 'csv']
    
    def format_notes(self, notes_content: str, output_format: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        if output_format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {output_format}")
        
        if output_format == 'markdown':
            return self._format_markdown(notes_content, metadata)
        elif output_format == 'html':
            return self._format_html(notes_content, metadata)
        elif output_format == 'json':
            return self._format_json(notes_content, metadata)
        elif output_format == 'txt':
            return self._format_txt(notes_content, metadata)
        elif output_format == 'csv':
            return self._format_csv(notes_content, metadata)
    
    def _format_markdown(self, notes_content: str, metadata: Dict[str, Any]) -> str:
        # Already in markdown format, just add metadata if needed
        if metadata:
            header = self._create_metadata_header(metadata, 'markdown')
            return header + "\n\n" + notes_content
        return notes_content
    
    def _format_html(self, notes_content: str, metadata: Dict[str, Any]) -> str:
        # Convert markdown to HTML
        html_content = self._markdown_to_html(notes_content)
        
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h1 {{ font-size: 2.5em; }}
        h2 {{ font-size: 2em; margin-top: 30px; }}
        h3 {{ font-size: 1.5em; margin-top: 25px; }}
        .metadata {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .slide-section {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
        }}
        ul, ol {{
            padding-left: 25px;
        }}
        li {{
            margin-bottom: 5px;
        }}
        code {{
            background-color: #f1f2f6;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .definition {{
            background-color: #e8f5e8;
            padding: 10px;
            border-left: 4px solid #27ae60;
            margin: 10px 0;
        }}
        .study-question {{
            background-color: #fff3cd;
            padding: 10px;
            border-left: 4px solid #ffc107;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        {metadata_section}
        {content}
    </div>
</body>
</html>"""
        
        title = metadata.get('presentation_title', 'Presentation Notes') if metadata else 'Presentation Notes'
        metadata_section = self._create_metadata_section_html(metadata) if metadata else ''
        
        return html_template.format(
            title=title,
            metadata_section=metadata_section,
            content=html_content
        )
    
    def _format_json(self, notes_content: str, metadata: Dict[str, Any]) -> str:
        # Parse the markdown content into structured data
        structured_data = self._parse_notes_to_structure(notes_content)
        
        output = {
            'metadata': metadata or {},
            'generated_at': datetime.now().isoformat(),
            'format': 'json',
            'content': structured_data
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    def _format_txt(self, notes_content: str, metadata: Dict[str, Any]) -> str:
        # Convert markdown to plain text
        txt_content = self._markdown_to_txt(notes_content)
        
        if metadata:
            header = self._create_metadata_header(metadata, 'txt')
            return header + "\n\n" + "="*80 + "\n\n" + txt_content
        
        return txt_content
    
    def _format_csv(self, notes_content: str, metadata: Dict[str, Any]) -> str:
        # Extract slide information for CSV format
        slides_data = self._extract_slides_for_csv(notes_content)
        
        csv_lines = []
        csv_lines.append("Slide Number,Title,Key Points,Textbook Reference,Study Questions,Notes")
        
        for slide in slides_data:
            csv_lines.append(f'"{slide.get("number", "")}","{slide.get("title", "")}","{slide.get("key_points", "")}","{slide.get("textbook_ref", "")}","{slide.get("questions", "")}","{slide.get("notes", "")}"')
        
        return "\n".join(csv_lines)
    
    def _create_metadata_header(self, metadata: Dict[str, Any], format_type: str) -> str:
        if format_type == 'markdown':
            header = "---\n"
            for key, value in metadata.items():
                header += f"{key}: {value}\n"
            header += "---"
            return header
        elif format_type == 'txt':
            header = f"PRESENTATION NOTES METADATA\n"
            header += "=" * 40 + "\n"
            for key, value in metadata.items():
                header += f"{key.replace('_', ' ').title()}: {value}\n"
            return header
    
    def _create_metadata_section_html(self, metadata: Dict[str, Any]) -> str:
        if not metadata:
            return ""
        
        section = '<div class="metadata">\n'
        section += '<h3>Presentation Information</h3>\n'
        for key, value in metadata.items():
            formatted_key = key.replace('_', ' ').title()
            section += f'<p><strong>{formatted_key}:</strong> {value}</p>\n'
        section += '</div>\n'
        return section
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        # Basic markdown to HTML conversion
        html = markdown_content
        
        # Headers
        html = html.replace('### ', '<h3>').replace('\n', '</h3>\n', html.count('### '))
        html = html.replace('## ', '<h2>').replace('\n', '</h2>\n', html.count('## '))
        html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', html.count('# '))
        
        # Bold text
        html = html.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
        
        # Lists
        lines = html.split('\n')
        processed_lines = []
        in_list = False
        
        for line in lines:
            if line.strip().startswith('•') or line.strip().startswith('-'):
                if not in_list:
                    processed_lines.append('<ul>')
                    in_list = True
                processed_lines.append(f'<li>{line.strip()[1:].strip()}</li>')
            elif line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                if not in_list:
                    processed_lines.append('<ol>')
                    in_list = True
                processed_lines.append(f'<li>{line.strip()[2:].strip()}</li>')
            else:
                if in_list:
                    processed_lines.append('</ul>' if '•' in ''.join(processed_lines[-5:]) else '</ol>')
                    in_list = False
                processed_lines.append(f'<p>{line}</p>' if line.strip() else '<br>')
        
        if in_list:
            processed_lines.append('</ul>')
        
        return '\n'.join(processed_lines)
    
    def _markdown_to_txt(self, markdown_content: str) -> str:
        # Remove markdown formatting
        txt = markdown_content
        
        # Remove headers markup but keep the text
        txt = txt.replace('### ', '').replace('## ', '').replace('# ', '')
        
        # Remove bold markup
        txt = txt.replace('**', '')
        
        # Convert bullet points
        txt = txt.replace('• ', '- ')
        
        return txt
    
    def _parse_notes_to_structure(self, notes_content: str) -> List[Dict[str, Any]]:
        slides = []
        current_slide = None
        
        lines = notes_content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Detect slide headers
            if line.startswith('## Slide'):
                if current_slide:
                    slides.append(current_slide)
                
                # Extract slide number and title
                import re
                match = re.match(r'## Slide (\d+): (.+)', line)
                if match:
                    current_slide = {
                        'slide_number': int(match.group(1)),
                        'title': match.group(2),
                        'content_overview': '',
                        'key_points': [],
                        'textbook_reference': '',
                        'definitions': [],
                        'study_questions': [],
                        'additional_notes': ''
                    }
            
            # Detect sections within slides
            elif line.startswith('### '):
                current_section = line[4:].lower()
            
            # Process content based on current section
            elif current_slide and line:
                if current_section == 'content overview':
                    current_slide['content_overview'] += line + '\n'
                elif current_section == 'key points':
                    if line.startswith('•'):
                        current_slide['key_points'].append(line[1:].strip())
                elif current_section == 'related textbook content':
                    current_slide['textbook_reference'] += line + '\n'
                elif current_section == 'study questions':
                    if line[0].isdigit():
                        current_slide['study_questions'].append(line)
                elif current_section == 'additional notes':
                    current_slide['additional_notes'] += line + '\n'
        
        if current_slide:
            slides.append(current_slide)
        
        return slides
    
    def _extract_slides_for_csv(self, notes_content: str) -> List[Dict[str, str]]:
        slides_data = []
        current_slide = {}
        
        lines = notes_content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('## Slide'):
                if current_slide:
                    slides_data.append(current_slide)
                
                import re
                match = re.match(r'## Slide (\d+): (.+)', line)
                if match:
                    current_slide = {
                        'number': match.group(1),
                        'title': match.group(2),
                        'key_points': '',
                        'textbook_ref': '',
                        'questions': '',
                        'notes': ''
                    }
            
            elif line.startswith('### '):
                current_section = line[4:].lower()
            
            elif current_slide and line:
                if current_section == 'key points':
                    current_slide['key_points'] += line.replace('"', '""') + ' '
                elif 'textbook' in current_section:
                    current_slide['textbook_ref'] += line.replace('"', '""') + ' '
                elif 'questions' in current_section:
                    current_slide['questions'] += line.replace('"', '""') + ' '
                elif 'notes' in current_section:
                    current_slide['notes'] += line.replace('"', '""') + ' '
        
        if current_slide:
            slides_data.append(current_slide)
        
        return slides_data
    
    def save_formatted_output(self, content: str, output_path: str, format_type: str) -> bool:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Set encoding based on format
            encoding = 'utf-8' if format_type in ['json', 'html', 'markdown'] else 'utf-8'
            
            with open(output_path, 'w', encoding=encoding) as file:
                file.write(content)
            
            return True
        except Exception as e:
            print(f"Error saving formatted output: {e}")
            return False
    
    def create_output_bundle(self, notes_content: str, output_dir: str, 
                           base_filename: str, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Create multiple format outputs in a bundle"""
        results = {}
        
        for format_type in self.supported_formats:
            try:
                formatted_content = self.format_notes(notes_content, format_type, metadata)
                
                file_extension = {
                    'markdown': '.md',
                    'html': '.html',
                    'json': '.json',
                    'txt': '.txt',
                    'csv': '.csv'
                }
                
                output_path = os.path.join(output_dir, f"{base_filename}{file_extension[format_type]}")
                
                if self.save_formatted_output(formatted_content, output_path, format_type):
                    results[format_type] = output_path
                else:
                    results[format_type] = f"Error saving {format_type} format"
                    
            except Exception as e:
                results[format_type] = f"Error formatting {format_type}: {str(e)}"
        
        return results