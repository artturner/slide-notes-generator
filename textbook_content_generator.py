#!/usr/bin/env python3

import PyPDF2
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

class TextbookContentGenerator:
    """
    Enhanced textbook content generator that extracts chapter sections
    based on provided headings and generates concise bullet points.
    """
    
    def __init__(self):
        self.MAX_WORDS_PER_BULLET = 10
        self.MIN_BULLETS_PER_SECTION = 3
        self.MAX_BULLETS_PER_SECTION = 6
        
        # Patterns for identifying numerical data, dates, and important entities
        self.numerical_patterns = [
            r'\d{4}',  # Years
            r'\d+%',   # Percentages
            r'\$\d+',  # Dollar amounts
            r'\d+\.\d+', # Decimals
            r'\d{1,3}(?:,\d{3})*', # Numbers with commas
        ]
        
        self.date_patterns = [
            r'20[2-9]\d',  # Years 2020+
            r'January|February|March|April|May|June|July|August|September|October|November|December',
            r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec',
        ]
        
        self.entity_patterns = [
            r'[A-Z][a-z]+ v\. [A-Z][a-z]+',  # Case names
            r'[A-Z][A-Z ]{2,}Act',  # Acts/Laws
            r'[A-Z][A-Z ]{2,}Program',  # Programs
        ]
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = []
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    # Clean text to handle encoding issues
                    clean_text = page_text.encode('ascii', 'ignore').decode('ascii')
                    text_content.append(clean_text)
                
                return '\n'.join(text_content)
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    def load_headings_from_file(self, headings_path: str) -> List[str]:
        """Load headings from text file"""
        try:
            with open(headings_path, 'r', encoding='utf-8') as file:
                headings = [line.strip() for line in file.readlines() if line.strip()]
                return headings
        except Exception as e:
            print(f"Error loading headings: {e}")
            return []
    
    def extract_section_content(self, full_text: str, headings: List[str]) -> Dict[str, str]:
        """
        Extract text content for each heading section.
        Returns dict mapping heading to its content.
        """
        sections = {}
        text_lines = full_text.split('\n')
        
        for i, heading in enumerate(headings):
            # Find the heading in the text
            heading_line_idx = self._find_heading_in_text(text_lines, heading)
            
            if heading_line_idx == -1:
                print(f"Warning: Heading not found in text: {heading}")
                continue
            
            # Find the next heading to determine section boundaries
            next_heading_idx = None
            if i + 1 < len(headings):
                next_heading = headings[i + 1]
                next_heading_idx = self._find_heading_in_text(text_lines, next_heading, heading_line_idx + 1)
            
            # Extract content between headings
            start_idx = heading_line_idx + 1
            end_idx = next_heading_idx if next_heading_idx else len(text_lines)
            
            section_content = []
            for line_idx in range(start_idx, end_idx):
                if line_idx < len(text_lines):
                    line = text_lines[line_idx].strip()
                    if line and not self._looks_like_heading(line, headings):
                        section_content.append(line)
            
            sections[heading] = '\n'.join(section_content)
        
        return sections
    
    def _find_heading_in_text(self, text_lines: List[str], heading: str, start_idx: int = 0) -> int:
        """Find the index of a heading in the text lines"""
        heading_clean = self._clean_heading_for_matching(heading)
        
        for i in range(start_idx, len(text_lines)):
            line_clean = self._clean_heading_for_matching(text_lines[i])
            
            # Exact match
            if line_clean == heading_clean:
                return i
            
            # Partial match (heading contained in line)
            if heading_clean in line_clean and len(heading_clean) > 5:
                return i
            
            # Word-based matching for complex headings
            heading_words = heading_clean.split()
            line_words = line_clean.split()
            
            if len(heading_words) >= 2:
                # Check if most significant words from heading appear in line
                matches = sum(1 for word in heading_words if word in line_words)
                if matches >= len(heading_words) * 0.7:  # 70% word match
                    return i
        
        return -1
    
    def _clean_heading_for_matching(self, heading: str) -> str:
        """Clean heading text for better matching"""
        # Remove special characters, normalize whitespace
        cleaned = re.sub(r'[^\w\s]', '', heading.lower())
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def _looks_like_heading(self, line: str, known_headings: List[str]) -> bool:
        """Check if a line looks like a heading"""
        line_clean = self._clean_heading_for_matching(line)
        
        for heading in known_headings:
            heading_clean = self._clean_heading_for_matching(heading)
            if line_clean == heading_clean or heading_clean in line_clean:
                return True
        
        return False
    
    def generate_bullet_points(self, section_content: str, heading: str) -> List[str]:
        """
        Generate concise bullet points from section content.
        Each bullet point is 10 words or fewer.
        """
        if not section_content.strip():
            return []
        
        # Split content into sentences
        sentences = self._split_into_sentences(section_content)
        
        # Extract key facts and concepts
        key_facts = self._extract_key_facts(sentences)
        
        # Convert to bullet points
        bullet_points = []
        
        for fact in key_facts:
            bullet = self._create_bullet_point(fact)
            if bullet and len(bullet.split()) <= self.MAX_WORDS_PER_BULLET:
                bullet_points.append(bullet)
                
                if len(bullet_points) >= self.MAX_BULLETS_PER_SECTION:
                    break
        
        # Ensure minimum bullets by extracting more if needed
        if len(bullet_points) < self.MIN_BULLETS_PER_SECTION and len(sentences) > len(bullet_points):
            additional_bullets = self._extract_additional_bullets(sentences, bullet_points)
            bullet_points.extend(additional_bullets)
        
        # Prioritize bullets with numerical data, dates, or important entities
        bullet_points = self._prioritize_important_bullets(bullet_points, section_content)
        
        return bullet_points[:self.MAX_BULLETS_PER_SECTION]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Clean text first - remove PDF artifacts
        text = re.sub(r'\d{5}_[a-z]+\d+_[a-z]+\d+\.indd', '', text)  # Remove PDF formatting
        text = re.sub(r'\d+/\d+/\d+\s+\d+:\d+[AP]M', '', text)  # Remove timestamps
        text = re.sub(r'Image \d+\.\d+', '', text)  # Remove image references
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        filtered_sentences = []
        
        for s in sentences:
            s = s.strip()
            # Filter out artifacts and incomplete phrases
            if (len(s) > 15 and  # Minimum length
                not s.startswith('indd') and  # PDF artifacts
                not re.match(r'^\d+$', s) and  # Just numbers
                not s.startswith('Chapter') and  # Chapter references
                not s.startswith('Image') and  # Image captions
                not s.endswith('AM') and not s.endswith('PM') and  # Timestamps
                '/' not in s[:10]):  # Date-like patterns at start
                filtered_sentences.append(s)
        
        return filtered_sentences
    
    def _extract_key_facts(self, sentences: List[str]) -> List[str]:
        """Extract key facts from sentences"""
        key_facts = []
        
        for sentence in sentences:
            # Skip very long sentences
            if len(sentence.split()) > 30:
                continue
            
            # Prioritize sentences with:
            # - Numbers, dates, statistics
            # - Definitions (contains "is", "are", "defined as")
            # - Examples (contains "example", "such as", "including")
            # - Laws, cases, programs
            
            score = 0
            
            # Check for numerical data
            for pattern in self.numerical_patterns:
                if re.search(pattern, sentence):
                    score += 3
            
            # Check for dates
            for pattern in self.date_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    score += 3
            
            # Check for entities
            for pattern in self.entity_patterns:
                if re.search(pattern, sentence):
                    score += 3
            
            # Check for definition indicators
            if re.search(r'\b(is|are|defined as|refers to|means)\b', sentence, re.IGNORECASE):
                score += 2
            
            # Check for example indicators
            if re.search(r'\b(example|such as|including|for instance)\b', sentence, re.IGNORECASE):
                score += 2
            
            # Check for important terms
            if re.search(r'\b(important|significant|major|key|primary|main)\b', sentence, re.IGNORECASE):
                score += 1
            
            key_facts.append((sentence, score))
        
        # Sort by score and return top facts
        key_facts.sort(key=lambda x: x[1], reverse=True)
        return [fact[0] for fact in key_facts[:15]]  # Top 15 facts
    
    def _create_bullet_point(self, sentence: str) -> str:
        """Convert a sentence into a concise bullet point"""
        # Clean sentence first
        sentence = sentence.strip()
        
        # Remove common sentence starters
        sentence = re.sub(r'^(The\s+|This\s+|That\s+|These\s+|Those\s+|It\s+|They\s+|In\s+)', '', sentence, flags=re.IGNORECASE)
        
        # Skip if it's just numbers or formatting artifacts
        if re.match(r'^[\d\s\.,]+$', sentence) or len(sentence) < 5:
            return ""
        
        # Extract core concept
        words = sentence.split()
        
        # If sentence is already short enough and meaningful, use it
        if len(words) <= self.MAX_WORDS_PER_BULLET and self._is_meaningful_bullet(sentence):
            return sentence.strip()
        
        # Try to find key phrase patterns
        # Pattern 1: "X is Y" definitions
        if ' is ' in sentence.lower():
            parts = sentence.split(' is ', 1)
            if len(parts) == 2:
                subject = parts[0].strip()
                predicate = parts[1].strip()
                
                if len(subject.split()) <= 3 and len(predicate.split()) <= 6:
                    bullet = f"{subject} is {predicate}"
                    if self._is_meaningful_bullet(bullet):
                        return bullet
        
        # Pattern 2: "X includes/contains Y"
        for verb in ['includes', 'contains', 'covers', 'involves']:
            if f' {verb} ' in sentence.lower():
                parts = sentence.lower().split(f' {verb} ', 1)
                if len(parts) == 2:
                    subject = parts[0].strip()
                    predicate = parts[1].strip()
                    
                    if len(subject.split()) <= 4 and len(predicate.split()) <= 5:
                        bullet = f"{subject} {verb} {predicate}"
                        if self._is_meaningful_bullet(bullet):
                            return bullet
        
        # Pattern 3: Find meaningful noun phrases
        # Look for important terms and try to build around them
        important_terms = self._extract_important_terms(sentence)
        if important_terms:
            for term in important_terms[:2]:  # Try first 2 important terms
                # Try to build a phrase around this term
                term_index = sentence.lower().find(term.lower())
                if term_index != -1:
                    # Get surrounding context
                    start = max(0, term_index - 50)
                    end = min(len(sentence), term_index + len(term) + 50)
                    context = sentence[start:end]
                    
                    # Try to extract a meaningful phrase
                    context_words = context.split()
                    for length in range(min(self.MAX_WORDS_PER_BULLET, len(context_words)), 4, -1):
                        phrase = ' '.join(context_words[:length])
                        if term.lower() in phrase.lower() and self._is_meaningful_bullet(phrase):
                            return phrase
        
        # Fallback: take meaningful first N words
        for length in range(min(self.MAX_WORDS_PER_BULLET, len(words)), 5, -1):
            if len(words) >= length:
                phrase = ' '.join(words[:length])
                # Ensure it doesn't end mid-phrase and is meaningful
                if (not phrase.endswith(('of', 'the', 'and', 'or', 'in', 'at', 'on', 'for', 'with')) and
                    self._is_meaningful_bullet(phrase)):
                    return phrase
        
        # Very last resort
        return ""
    
    def _is_meaningful_bullet(self, text: str) -> bool:
        """Check if bullet point text is meaningful"""
        # Must have at least one substantial word
        words = text.split()
        substantial_words = [w for w in words if len(w) > 3 and w.lower() not in ['this', 'that', 'these', 'those', 'with']]
        
        return (len(substantial_words) >= 2 and  # At least 2 substantial words
                not text.lower().startswith(('indd', 'chapter', 'image', 'brandon', 'getty')) and
                not re.match(r'^\d+[\s\d]*$', text) and  # Not just numbers
                len(text) > 8)  # Minimum meaningful length
    
    def _extract_important_terms(self, text: str) -> List[str]:
        """Extract important terms from text"""
        # Look for capitalized terms, numbers, and key phrases
        important = []
        
        # Capitalized phrases (likely proper nouns or important concepts)
        cap_phrases = re.findall(r'[A-Z][a-zA-Z\s]{2,15}(?=[A-Z]|\.|,|$)', text)
        important.extend(cap_phrases[:3])
        
        # Numbers with context
        number_contexts = re.findall(r'\d+(?:\.\d+)?(?:\s+(?:percent|%|million|billion|thousand))?', text)
        important.extend(number_contexts[:2])
        
        # Important keywords
        keywords = re.findall(r'\b(?:policy|program|act|law|regulation|government|state|texas|education|health|development)\b', text, re.IGNORECASE)
        important.extend(keywords[:2])
        
        return important[:5]
    
    def _extract_additional_bullets(self, sentences: List[str], existing_bullets: List[str]) -> List[str]:
        """Extract additional bullet points to meet minimum requirement"""
        additional = []
        existing_content = set(' '.join(existing_bullets).lower().split())
        
        for sentence in sentences:
            if len(additional) >= self.MAX_BULLETS_PER_SECTION - len(existing_bullets):
                break
            
            # Skip if sentence content already covered
            sentence_words = set(sentence.lower().split())
            overlap = len(sentence_words.intersection(existing_content))
            
            if overlap < len(sentence_words) * 0.5:  # Less than 50% overlap
                bullet = self._create_bullet_point(sentence)
                if bullet and len(bullet.split()) <= self.MAX_WORDS_PER_BULLET:
                    additional.append(bullet)
                    existing_content.update(bullet.lower().split())
        
        return additional
    
    def _prioritize_important_bullets(self, bullets: List[str], section_content: str) -> List[str]:
        """Prioritize bullets containing numerical data, dates, or important entities"""
        scored_bullets = []
        
        for bullet in bullets:
            score = 0
            
            # Check for numerical data
            for pattern in self.numerical_patterns:
                if re.search(pattern, bullet):
                    score += 5
            
            # Check for recent dates (2023+)
            if re.search(r'202[3-9]', bullet):
                score += 5
            
            # Check for entity patterns
            for pattern in self.entity_patterns:
                if re.search(pattern, bullet):
                    score += 4
            
            # Check for program/law names (capitalized phrases)
            if re.search(r'[A-Z][A-Z ]{2,}(Act|Program|Law|Case)', bullet):
                score += 4
            
            scored_bullets.append((bullet, score))
        
        # Sort by score (high priority first) and return
        scored_bullets.sort(key=lambda x: x[1], reverse=True)
        return [bullet for bullet, score in scored_bullets]
    
    def generate_content_from_pdf_and_headings(self, pdf_path: str, headings_path: str, 
                                              output_path: str) -> Dict[str, Any]:
        """
        Main method to generate bullet point content from PDF and headings file.
        """
        start_time = datetime.now()
        
        try:
            # Load inputs
            print("Extracting PDF text...")
            pdf_text = self.extract_pdf_text(pdf_path)
            if not pdf_text:
                return {'success': False, 'error': 'Failed to extract PDF text'}
            
            print("Loading headings...")
            headings = self.load_headings_from_file(headings_path)
            if not headings:
                return {'success': False, 'error': 'Failed to load headings'}
            
            print(f"Found {len(headings)} headings to process")
            
            # Extract sections
            print("Extracting section content...")
            sections = self.extract_section_content(pdf_text, headings)
            
            if not sections:
                return {'success': False, 'error': 'No sections could be extracted'}
            
            print(f"Extracted {len(sections)} sections")
            
            # Generate bullet points for each section
            print("Generating bullet points...")
            results = {}
            total_bullets = 0
            
            for heading, content in sections.items():
                bullets = self.generate_bullet_points(content, heading)
                results[heading] = {
                    'bullets': bullets,
                    'bullet_count': len(bullets),
                    'content_length': len(content)
                }
                total_bullets += len(bullets)
                print(f"  {heading}: {len(bullets)} bullets")
            
            # Create markdown output
            print("Creating markdown output...")
            markdown_content = self._create_markdown_output(results, pdf_path, headings_path)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            processing_time = datetime.now() - start_time
            
            return {
                'success': True,
                'output_path': output_path,
                'sections_processed': len(sections),
                'total_bullets': total_bullets,
                'processing_time': str(processing_time).split('.')[0],
                'metadata': {
                    'pdf_file': pdf_path,
                    'headings_file': headings_path,
                    'generated_at': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'sections': list(results.keys())
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': str(datetime.now() - start_time).split('.')[0]
            }
    
    def _create_markdown_output(self, results: Dict[str, Dict], pdf_path: str, headings_path: str) -> str:
        """Create formatted markdown output"""
        content = []
        
        # Header
        content.append("# Textbook Chapter Notes\n")
        content.append(f"**PDF Source:** {pdf_path}")
        content.append(f"**Headings Source:** {headings_path}")
        content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"**Total Sections:** {len(results)}")
        content.append("")
        
        # Sections
        for heading, data in results.items():
            content.append(f"## **{heading}**\n")
            
            if data['bullets']:
                for bullet in data['bullets']:
                    content.append(f"• {bullet}")
            else:
                content.append("• No content available for this section")
            
            content.append("")  # Empty line between sections
        
        return '\n'.join(content)


def main():
    """Command-line interface for testing"""
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python textbook_content_generator.py <pdf_path> <headings_path> <output_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    headings_path = sys.argv[2]
    output_path = sys.argv[3]
    
    generator = TextbookContentGenerator()
    result = generator.generate_content_from_pdf_and_headings(pdf_path, headings_path, output_path)
    
    if result['success']:
        print(f"\nSuccess! Generated content saved to: {result['output_path']}")
        print(f"Processed {result['sections_processed']} sections")
        print(f"Generated {result['total_bullets']} total bullet points")
        print(f"Processing time: {result['processing_time']}")
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()