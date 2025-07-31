from typing import List, Dict, Any, Optional
import re
from datetime import datetime

class NotesGenerator:
    def __init__(self, use_ai: bool = False, ai_api_key: Optional[str] = None):
        self.use_ai = use_ai
        self.ai_api_key = ai_api_key
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        return {
            'slide_header': "## Slide {slide_number}: {title}\n",
            'content_section': "### Content Overview\n{content}\n\n",
            'key_points': "### Key Points\n{points}\n\n",
            'textbook_reference': "### Related Textbook Content\n**Section:** {section_title}\n{section_content}\n\n",
            'definitions': "### Key Definitions\n{definitions}\n\n",
            'study_questions': "### Study Questions\n{questions}\n\n",
            'additional_notes': "### Additional Notes\n{notes}\n\n"
        }
    
    def generate_slide_notes(self, slide_content: Dict[str, Any], 
                           aligned_sections: List[Dict[str, Any]]) -> str:
        notes_parts = []
        
        # Slide header
        title = slide_content.get('title', f"Slide {slide_content.get('slide_number', 'Unknown')}")
        notes_parts.append(self.templates['slide_header'].format(
            slide_number=slide_content.get('slide_number', 'Unknown'),
            title=title
        ))
        
        # Content overview
        if slide_content.get('text_content') or slide_content.get('bullet_points'):
            content = self._format_slide_content(slide_content)
            notes_parts.append(self.templates['content_section'].format(content=content))
        
        # Key points from slide
        if slide_content.get('bullet_points'):
            points = self._format_bullet_points(slide_content['bullet_points'])
            notes_parts.append(self.templates['key_points'].format(points=points))
        
        # Related textbook content
        if aligned_sections:
            best_match = aligned_sections[0]
            if best_match.get('alignment_details', {}).get('confidence') in ['high', 'medium']:
                section_content = self._extract_relevant_content(best_match, slide_content)
                notes_parts.append(self.templates['textbook_reference'].format(
                    section_title=best_match.get('title', 'Unknown Section'),
                    section_content=section_content
                ))
        
        # Definitions
        definitions = self._extract_definitions(slide_content, aligned_sections)
        if definitions:
            formatted_definitions = self._format_definitions(definitions)
            notes_parts.append(self.templates['definitions'].format(definitions=formatted_definitions))
        
        # Study questions
        questions = self._generate_study_questions(slide_content, aligned_sections)
        if questions:
            formatted_questions = self._format_study_questions(questions)
            notes_parts.append(self.templates['study_questions'].format(questions=formatted_questions))
        
        # Additional notes from slide notes
        if slide_content.get('notes'):
            notes_parts.append(self.templates['additional_notes'].format(
                notes=slide_content['notes']
            ))
        
        return ''.join(notes_parts)
    
    def _format_slide_content(self, slide_content: Dict[str, Any]) -> str:
        content_parts = []
        
        if slide_content.get('text_content'):
            for text in slide_content['text_content']:
                if text.strip() and text != slide_content.get('title', ''):
                    content_parts.append(f"- {text.strip()}")
        
        return '\n'.join(content_parts) if content_parts else "No additional content available."
    
    def _format_bullet_points(self, bullet_points: List[str]) -> str:
        formatted_points = []
        for point in bullet_points:
            if point.strip():
                formatted_points.append(f"• {point.strip()}")
        return '\n'.join(formatted_points)
    
    def _extract_relevant_content(self, section: Dict[str, Any], 
                                slide_content: Dict[str, Any]) -> str:
        section_content = section.get('content', '')
        if not section_content:
            return "Content not available."
        
        # Get common keywords to focus on relevant parts
        common_keywords = section.get('alignment_details', {}).get('common_keywords', [])
        
        if common_keywords:
            # Extract sentences containing common keywords
            sentences = re.split(r'[.!?]+', section_content)
            relevant_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if any(keyword.lower() in sentence.lower() for keyword in common_keywords):
                    relevant_sentences.append(sentence)
            
            if relevant_sentences:
                content = '. '.join(relevant_sentences[:3]) + '.'
                if len(content) > 500:
                    content = content[:500] + '...'
                return content
        
        # Fallback: return first part of section
        if len(section_content) > 400:
            return section_content[:400] + '...'
        return section_content
    
    def _extract_definitions(self, slide_content: Dict[str, Any], 
                           aligned_sections: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        definitions = []
        
        # Extract from slide content
        slide_text = ' '.join([
            slide_content.get('title', ''),
            *slide_content.get('text_content', []),
            *slide_content.get('bullet_points', [])
        ])
        
        definitions.extend(self._find_definitions_in_text(slide_text))
        
        # Extract from aligned textbook sections
        for section in aligned_sections[:2]:  # Top 2 matches
            if section.get('content'):
                section_definitions = self._find_definitions_in_text(section['content'])
                definitions.extend(section_definitions)
        
        # Remove duplicates and limit
        unique_definitions = []
        seen_terms = set()
        
        for definition in definitions:
            term_lower = definition['term'].lower()
            if term_lower not in seen_terms and len(definition['definition']) > 10:
                seen_terms.add(term_lower)
                unique_definitions.append(definition)
                if len(unique_definitions) >= 5:
                    break
        
        return unique_definitions
    
    def _find_definitions_in_text(self, text: str) -> List[Dict[str, str]]:
        definition_patterns = [
            r'([A-Za-z\s]+?)\s+is\s+(?:defined\s+as\s+)?(.+?)[\.\n]',
            r'([A-Za-z\s]+?)\s+refers\s+to\s+(.+?)[\.\n]',
            r'([A-Za-z\s]+?):\s+(.+?)[\.\n]',
            r'Definition:\s*([A-Za-z\s]+?)\s*-\s*(.+?)[\.\n]'
        ]
        
        definitions = []
        for pattern in definition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                if 5 < len(term) < 50 and len(definition) > 15:
                    definitions.append({
                        'term': term,
                        'definition': definition
                    })
        
        return definitions
    
    def _format_definitions(self, definitions: List[Dict[str, str]]) -> str:
        formatted = []
        for definition in definitions:
            formatted.append(f"**{definition['term']}**: {definition['definition']}")
        return '\n\n'.join(formatted)
    
    def _generate_study_questions(self, slide_content: Dict[str, Any], 
                                aligned_sections: List[Dict[str, Any]]) -> List[str]:
        questions = []
        
        # Questions based on slide title
        title = slide_content.get('title', '')
        if title:
            questions.append(f"What are the main concepts covered in '{title}'?")
            questions.append(f"How does '{title}' relate to the broader topic?")
        
        # Questions based on bullet points
        bullet_points = slide_content.get('bullet_points', [])
        if bullet_points:
            if len(bullet_points) > 1:
                questions.append("Compare and contrast the key points presented in this slide.")
            for point in bullet_points[:2]:
                if len(point) > 10:
                    questions.append(f"Explain the significance of: {point}")
        
        # Questions based on aligned textbook content
        if aligned_sections:
            best_match = aligned_sections[0]
            common_keywords = best_match.get('alignment_details', {}).get('common_keywords', [])
            if common_keywords:
                key_term = common_keywords[0] if common_keywords else None
                if key_term:
                    questions.append(f"How is '{key_term}' applied in real-world scenarios?")
                    questions.append(f"What are the implications of '{key_term}' for this field?")
        
        return questions[:4]  # Limit to 4 questions
    
    def _format_study_questions(self, questions: List[str]) -> str:
        formatted = []
        for i, question in enumerate(questions, 1):
            formatted.append(f"{i}. {question}")
        return '\n'.join(formatted)
    
    def generate_presentation_notes(self, aligned_slides: List[Dict[str, Any]]) -> str:
        presentation_notes = []
        
        # Header
        presentation_notes.append(f"# Presentation Notes\n")
        presentation_notes.append(f"**Generated on:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
        
        # Table of contents
        presentation_notes.append("## Table of Contents\n")
        for slide in aligned_slides:
            slide_num = slide.get('slide_number', 'Unknown')
            title = slide.get('title', 'Untitled')
            presentation_notes.append(f"- [Slide {slide_num}: {title}](#slide-{slide_num})\n")
        presentation_notes.append("\n---\n\n")
        
        # Individual slide notes
        for slide in aligned_slides:
            slide_notes = self.generate_slide_notes(
                slide, 
                slide.get('aligned_sections', [])
            )
            presentation_notes.append(slide_notes)
            presentation_notes.append("---\n\n")
        
        # Summary section
        presentation_notes.append("## Presentation Summary\n\n")
        presentation_notes.append(self._generate_presentation_summary(aligned_slides))
        
        return ''.join(presentation_notes)
    
    def _generate_presentation_summary(self, aligned_slides: List[Dict[str, Any]]) -> str:
        summary_parts = []
        
        total_slides = len(aligned_slides)
        slides_with_content = sum(1 for slide in aligned_slides 
                                if slide.get('text_content') or slide.get('bullet_points'))
        
        summary_parts.append(f"**Total Slides:** {total_slides}\n")
        summary_parts.append(f"**Slides with Content:** {slides_with_content}\n")
        
        # Most common topics
        all_keywords = []
        for slide in aligned_slides:
            for section in slide.get('aligned_sections', []):
                keywords = section.get('alignment_details', {}).get('common_keywords', [])
                all_keywords.extend(keywords)
        
        if all_keywords:
            keyword_freq = {}
            for keyword in all_keywords:
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
            
            top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            summary_parts.append(f"**Key Topics:** {', '.join([kw for kw, _ in top_keywords])}\n")
        
        return ''.join(summary_parts)
    
    def save_notes(self, notes_content: str, output_path: str) -> bool:
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(notes_content)
            return True
        except Exception as e:
            print(f"Error saving notes: {e}")
            return False