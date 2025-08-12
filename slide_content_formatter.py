from typing import List, Dict, Any, Optional
from datetime import datetime
import os

class SlideContentFormatter:
    """
    Formats generated slide content into markdown format
    """
    
    def __init__(self):
        self.markdown_template = """# {presentation_title}

**Generated on:** {generated_at}  
**Source:** {textbook_source}  
**Generation Method:** {generation_method}  
**Success Rate:** {success_rate}

---

{slide_content}

---

## Summary

- **Total Slides:** {total_slides}
- **Content Generated:** {content_generated}
- **Processing Time:** {processing_time}
"""
    
    def format_slide_content_to_markdown(self, content_results: Dict[str, Any], 
                                       metadata: Dict[str, Any]) -> str:
        """
        Format slide content results into markdown
        
        Args:
            content_results: Results from SlideContentGenerator
            metadata: Metadata about the generation process
        
        Returns:
            Formatted markdown string
        """
        
        slide_sections = []
        
        # Process each slide
        for slide_data in content_results.get('slides', []):
            slide_section = self._format_single_slide(slide_data)
            if slide_section:
                slide_sections.append(slide_section)
        
        slide_content = '\n\n'.join(slide_sections)
        
        # Format the complete markdown
        formatted_markdown = self.markdown_template.format(
            presentation_title=metadata.get('presentation_title', 'Unknown Presentation'),
            generated_at=metadata.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            textbook_source=metadata.get('textbook_source', 'Unknown Source'),
            generation_method=metadata.get('generation_method', 'Unknown'),
            success_rate=metadata.get('success_rate', '0%'),
            slide_content=slide_content,
            total_slides=metadata.get('total_slides', 0),
            content_generated=metadata.get('content_generated', 0),
            processing_time=metadata.get('processing_time', '0:00:00')
        )
        
        return formatted_markdown
    
    def _format_single_slide(self, slide_data: Dict[str, Any]) -> str:
        """
        Format a single slide's content
        
        Args:
            slide_data: Slide data including generated content
        
        Returns:
            Formatted markdown section for the slide
        """
        
        slide_number = slide_data.get('slide_number', '?')
        slide_title = slide_data.get('title', 'Untitled Slide')
        generated_content = slide_data.get('generated_content')
        
        # Start with slide header
        sections = []
        sections.append(f"## Slide {slide_number}: {slide_title}")
        
        # Add heading if it exists and is different from title
        existing_headings = self._extract_headings(slide_data)
        if existing_headings:
            heading = existing_headings[0]
            if heading.lower() != slide_title.lower():
                sections.append(f"### {heading}")
        
        # Add generated content
        if generated_content and generated_content.get('success'):
            bullet_points = generated_content.get('bullet_points', [])
            if bullet_points:
                sections.append("")  # Empty line before bullets
                for bullet in bullet_points:
                    sections.append(f"- {bullet}")
            else:
                sections.append("\n*No content generated for this slide.*")
        else:
            sections.append("\n*Content generation failed for this slide.*")
        
        return '\n'.join(sections)
    
    def _extract_headings(self, slide_data: Dict[str, Any]) -> List[str]:
        """Extract headings from slide content that aren't the title"""
        
        slide_title = slide_data.get('title', '').lower()
        headings = []
        
        if slide_data.get('text_content'):
            for text in slide_data['text_content']:
                text = text.strip()
                if (text and 
                    text.lower() != slide_title and 
                    self._looks_like_heading(text)):
                    headings.append(text)
        
        return headings
    
    def _looks_like_heading(self, text: str) -> bool:
        """Determine if text looks like a heading"""
        
        # Short text, title case, no punctuation at end
        words = text.split()
        if len(words) <= 8 and text.istitle() and not text.endswith('.'):
            return True
        
        # All caps (common heading style)
        if text.isupper() and len(words) <= 8:
            return True
        
        return False
    
    def save_markdown_content(self, markdown_content: str, output_path: str) -> Dict[str, Any]:
        """
        Save markdown content to file
        
        Args:
            markdown_content: Formatted markdown content
            output_path: Path to save the file
        
        Returns:
            Dict with success status and details
        """
        
        try:
            # Ensure the output path has .md extension
            if not output_path.lower().endswith('.md'):
                output_path += '.md'
            
            # Create directory if it doesn't exist (only if there is a directory)
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Write the file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return {
                'success': True,
                'output_path': output_path,
                'message': f"Slide content saved to {output_path}"
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to save markdown content: {e}"
            }
    
    def format_content_summary(self, content_results: Dict[str, Any]) -> str:
        """
        Create a summary of the content generation results
        
        Args:
            content_results: Results from content generation
        
        Returns:
            Formatted summary string
        """
        
        total_slides = content_results.get('total_slides', 0)
        successful = content_results.get('successful', 0)
        failed = content_results.get('failed', 0)
        success_rate = content_results.get('success_rate', 0)
        generation_method = content_results.get('generation_method', 'unknown')
        
        summary_lines = [
            "## Content Generation Summary",
            "",
            f"- **Total Slides Processed:** {total_slides}",
            f"- **Successfully Generated:** {successful}",
            f"- **Failed:** {failed}",
            f"- **Success Rate:** {success_rate:.1%}",
            f"- **Generation Method:** {generation_method}",
            ""
        ]
        
        # Add details about each slide
        if 'slides' in content_results:
            summary_lines.append("### Slide Details")
            summary_lines.append("")
            
            for slide_data in content_results['slides']:
                slide_num = slide_data.get('slide_number', '?')
                slide_title = slide_data.get('title', 'Untitled')[:50]
                generated_content = slide_data.get('generated_content', {})
                
                if generated_content.get('success'):
                    bullet_count = len(generated_content.get('bullet_points', []))
                    status = f"✓ Generated {bullet_count} bullet points"
                else:
                    status = "✗ Generation failed"
                
                summary_lines.append(f"- **Slide {slide_num}:** {slide_title} - {status}")
        
        return '\n'.join(summary_lines)