#!/usr/bin/env python3

import PyPDF2
import re
import time
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from grok_client import GrokClient

try:
    from striprtf.striprtf import rtf_to_text
    RTF_AVAILABLE = True
except ImportError:
    RTF_AVAILABLE = False
    print("Note: striprtf not available. Install striprtf for RTF support.")

try:
    from gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Note: gemini_client not available. Install google-generativeai for Gemini support.")

try:
    from openai_client import OpenAIClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Note: openai_client not available. Install openai for OpenAI support.")

class AITextbookContentGenerator:
    """
    AI-powered textbook content generator that extracts chapter sections
    based on provided headings and uses AI (Grok/Gemini) to generate 
    high-quality bullet points.
    """
    
    def __init__(self, use_grok: bool = False, grok_api_key: Optional[str] = None, grok_model: str = "grok-beta",
                 use_gemini: bool = False, gemini_api_key: Optional[str] = None, gemini_model: str = "gemini-1.5-flash",
                 use_openai: bool = False, openai_api_key: Optional[str] = None, openai_model: str = "gpt-4o-mini"):
        self.use_grok = use_grok
        self.use_gemini = use_gemini
        self.use_openai = use_openai
        self.grok_client = None
        self.gemini_client = None
        self.openai_client = None
        
        # Initialize Grok client if requested
        if self.use_grok:
            try:
                self.grok_client = GrokClient(api_key=grok_api_key, model=grok_model)
                test_result = self.grok_client.test_connection()
                if not test_result['success']:
                    print(f"Warning: Grok connection test failed: {test_result.get('error', 'Unknown error')}")
                    self.use_grok = False
                else:
                    print(f"Grok API connected successfully using model: {grok_model}")
            except Exception as e:
                print(f"Warning: Failed to initialize Grok client: {e}")
                self.use_grok = False
        
        # Initialize Gemini client if requested
        if self.use_gemini and GEMINI_AVAILABLE:
            try:
                self.gemini_client = GeminiClient(api_key=gemini_api_key, model=gemini_model)
                test_result = self.gemini_client.test_connection()
                if not test_result['success']:
                    print(f"Warning: Gemini connection test failed: {test_result.get('error', 'Unknown error')}")
                    self.use_gemini = False
                else:
                    print(f"Gemini API connected successfully using model: {gemini_model}")
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini client: {e}")
                self.use_gemini = False
        elif self.use_gemini and not GEMINI_AVAILABLE:
            print("Warning: Gemini requested but not available. Install google-generativeai package.")
            self.use_gemini = False
        
        # Initialize OpenAI client if requested
        if self.use_openai and OPENAI_AVAILABLE:
            try:
                self.openai_client = OpenAIClient(api_key=openai_api_key, model=openai_model)
                test_result = self.openai_client.test_connection()
                if not test_result['success']:
                    print(f"Warning: OpenAI connection test failed: {test_result.get('error', 'Unknown error')}")
                    self.use_openai = False
                else:
                    print(f"OpenAI API connected successfully using model: {openai_model}")
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
                self.use_openai = False
        elif self.use_openai and not OPENAI_AVAILABLE:
            print("Warning: OpenAI requested but not available. Install openai package.")
            self.use_openai = False
        
        # Content generation constraints
        self.MAX_WORDS_PER_BULLET = 10
        self.MIN_BULLETS_PER_SECTION = 3
        self.MAX_BULLETS_PER_SECTION = 6
    
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
    
    def extract_rtf_text(self, rtf_path: str) -> str:
        """Extract text from RTF file with style information preserved"""
        if not RTF_AVAILABLE:
            print("Error: striprtf library not available. Install with: pip install striprtf")
            return ""
        
        try:
            with open(rtf_path, 'r', encoding='utf-8') as file:
                rtf_content = file.read()
            
            # Extract plain text while preserving some structure
            plain_text = rtf_to_text(rtf_content)
            
            # Also extract raw RTF for heading detection
            self._raw_rtf_content = rtf_content
            
            return plain_text
        except Exception as e:
            print(f"Error extracting RTF text: {e}")
            return ""
    
    def detect_file_type(self, file_path: str) -> str:
        """Detect if file is PDF or RTF based on extension"""
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.pdf':
            return 'pdf'
        elif file_ext == '.rtf':
            return 'rtf'
        else:
            # Try to detect by content
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(10)
                    if header.startswith(b'%PDF'):
                        return 'pdf'
                    elif header.startswith(b'{\\rtf'):
                        return 'rtf'
            except:
                pass
            return 'unknown'
    
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
            
            print(f"DEBUG: Found '{heading}' at line {heading_line_idx}: '{text_lines[heading_line_idx]}'")
            
            # Find the next heading to determine section boundaries
            next_heading_idx = None
            if i + 1 < len(headings):
                next_heading = headings[i + 1]
                next_heading_idx = self._find_heading_in_text(text_lines, next_heading, heading_line_idx + 1)
                if next_heading_idx != -1:
                    print(f"DEBUG: Next heading '{next_heading}' found at line {next_heading_idx}")
                else:
                    print(f"DEBUG: Next heading '{next_heading}' NOT found")
            
            # Extract content between headings
            start_idx = heading_line_idx + 1
            end_idx = next_heading_idx if next_heading_idx else len(text_lines)
            
            print(f"DEBUG: Extracting content from line {start_idx} to {end_idx} ({end_idx - start_idx} lines)")
            
            section_content = []
            for line_idx in range(start_idx, end_idx):
                if line_idx < len(text_lines):
                    line = text_lines[line_idx].strip()
                    if line and not self._looks_like_heading(line, headings):
                        section_content.append(line)
            
            # Clean and join the content
            raw_content = '\n'.join(section_content)
            cleaned_content = self._clean_section_content(raw_content)
            sections[heading] = cleaned_content
        
        return sections
    
    def _find_heading_in_text(self, text_lines: List[str], heading: str, start_idx: int = 0) -> int:
        """Find the index of a heading in the text lines"""
        heading_clean = self._clean_heading_for_matching(heading)
        
        # Check if we have RTF content for better heading detection
        if hasattr(self, '_raw_rtf_content') and self._raw_rtf_content:
            return self._find_heading_in_rtf(text_lines, heading, start_idx)
        
        for i in range(start_idx, len(text_lines)):
            line = text_lines[i].strip()
            line_clean = self._clean_heading_for_matching(line)
            
            # Skip empty lines
            if not line:
                continue
            
            # Exact match
            if line_clean == heading_clean:
                print(f"DEBUG: Exact match for '{heading}' at line {i}: '{line}'")
                return i
            
            # Check if line is likely a standalone heading (short line, contains heading words)
            if len(line) < 50 and heading_clean in line_clean:
                # Additional checks for heading-like characteristics
                is_likely_heading = (
                    len(line.split()) <= 4 or  # Short phrases are more likely headings
                    line.istitle() or  # Title case
                    line.isupper() or  # All caps
                    line.endswith(':') or  # Ends with colon
                    not any(char in line for char in '.,;') or  # No sentence punctuation
                    (i > 0 and not text_lines[i-1].strip())  # Preceded by blank line
                )
                
                if is_likely_heading:
                    print(f"DEBUG: Likely heading match for '{heading}' at line {i}: '{line}'")
                    return i
            
            # Fallback: partial match only if heading is reasonably unique
            if heading_clean in line_clean and len(heading_clean) > 8:
                print(f"DEBUG: Partial match for '{heading}' at line {i}: '{line}'")
                return i
        
        return -1
    
    def _find_heading_in_rtf(self, text_lines: List[str], heading: str, start_idx: int = 0) -> int:
        """Find heading in RTF content using style information"""
        heading_clean = self._clean_heading_for_matching(heading)
        
        # Split RTF content into lines to match with text_lines
        rtf_lines = self._raw_rtf_content.split('\n')
        
        # Common RTF heading style patterns
        heading_patterns = [
            r'\\s1\\',  # Heading 1 style
            r'\\s2\\',  # Heading 2 style
            r'\\s3\\',  # Heading 3 style
            r'\\outlinelevel0\\',  # Outline level 0 (top level)
            r'\\outlinelevel1\\',  # Outline level 1
            r'\\b\\',   # Bold text (often headings)
            r'\\fs\d{3,}\\',  # Large font size (24pt+ indicates heading)
        ]
        
        for i in range(start_idx, len(text_lines)):
            line = text_lines[i].strip()
            line_clean = self._clean_heading_for_matching(line)
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this line matches our heading
            if heading_clean in line_clean:
                # Look for corresponding RTF formatting around this text
                text_in_rtf = self._find_text_in_rtf(line, rtf_lines)
                
                if text_in_rtf:
                    # Check if the RTF context has heading-style formatting
                    for pattern in heading_patterns:
                        if re.search(pattern, text_in_rtf, re.IGNORECASE):
                            print(f"DEBUG: RTF heading match for '{heading}' at line {i}: '{line}' (style: {pattern})")
                            return i
                
                # If exact match, still consider it even without RTF style
                if line_clean == heading_clean:
                    print(f"DEBUG: RTF exact match for '{heading}' at line {i}: '{line}'")
                    return i
        
        return -1
    
    def _find_text_in_rtf(self, text: str, rtf_lines: List[str]) -> str:
        """Find the RTF context around a specific text"""
        text_words = text.lower().split()[:3]  # Use first 3 words for matching
        
        for i, rtf_line in enumerate(rtf_lines):
            rtf_lower = rtf_line.lower()
            if all(word in rtf_lower for word in text_words):
                # Return context: current line + previous + next
                start = max(0, i - 1)
                end = min(len(rtf_lines), i + 2)
                return '\n'.join(rtf_lines[start:end])
        
        return ""
    
    def _clean_heading_for_matching(self, heading: str) -> str:
        """Clean heading text for better matching"""
        # Remove special characters, normalize whitespace
        cleaned = re.sub(r'[^\w\s]', '', heading.lower())
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def _looks_like_heading(self, line: str, known_headings: List[str]) -> bool:
        """Check if a line looks like a heading"""
        line_clean = self._clean_heading_for_matching(line)
        
        # Only exact matches or very short lines should be considered headings
        for heading in known_headings:
            heading_clean = self._clean_heading_for_matching(heading)
            # Exact match
            if line_clean == heading_clean:
                return True
            # Only consider partial matches for very short lines (likely actual headings)
            if len(line.strip()) < 30 and heading_clean in line_clean:
                return True
        
        return False
    
    def _clean_section_content(self, content: str) -> str:
        """Clean section content to remove PDF artifacts and improve readability"""
        # Remove PDF formatting artifacts
        content = re.sub(r'\d{5}_[a-z]+\d+_[a-z]+\d+\.indd', '', content)
        content = re.sub(r'\d+/\d+/\d+\s+\d+:\d+[AP]M', '', content)
        content = re.sub(r'Image \d+\.\d+', '', content)
        content = re.sub(r'Brandon Bell/Getty Images', '', content)
        content = re.sub(r'Chapter \d+[\s\w]*', '', content)
        
        # Remove page numbers and other formatting
        content = re.sub(r'^\d+\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^---\s+PAGE\s+\d+\s+---$', '', content, flags=re.MULTILINE)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    
    def generate_ai_bullet_points(self, section_content: str, heading: str) -> List[str]:
        """
        Generate bullet points using AI (OpenAI preferred, then Gemini, then Grok, then fallback to rule-based)
        """
        if not section_content.strip():
            return []
        
        # Try OpenAI first (generally reliable and robust)
        if self.use_openai and self.openai_client:
            return self._generate_openai_bullets(section_content, heading)
        # Then try Gemini
        elif self.use_gemini and self.gemini_client:
            return self._generate_gemini_bullets(section_content, heading)
        # Then try Grok
        elif self.use_grok and self.grok_client:
            return self._generate_grok_bullets(section_content, heading)
        # Fallback to rule-based
        else:
            print(f"Note: Using fallback generation for '{heading}' - consider using AI for better results")
            return self._generate_fallback_bullets(section_content, heading)
    
    def _generate_openai_bullets(self, section_content: str, heading: str) -> List[str]:
        """Generate bullet points using OpenAI API"""
        
        try:
            result = self.openai_client.generate_bullet_points(
                section_content,
                heading,
                self.MAX_WORDS_PER_BULLET,
                self.MIN_BULLETS_PER_SECTION,
                self.MAX_BULLETS_PER_SECTION
            )
            
            if result['success']:
                bullets = result['bullet_points']
                if len(bullets) >= self.MIN_BULLETS_PER_SECTION:
                    return bullets[:self.MAX_BULLETS_PER_SECTION]
                else:
                    print(f"Warning: OpenAI generated only {len(bullets)} bullets for '{heading}'")
                    return bullets
            else:
                print(f"Warning: OpenAI generation failed for '{heading}': {result.get('error', 'Unknown error')}")
                return self._generate_fallback_bullets(section_content, heading)
                
        except Exception as e:
            print(f"Error generating OpenAI bullets for '{heading}': {e}")
            return self._generate_fallback_bullets(section_content, heading)

    def _generate_gemini_bullets(self, section_content: str, heading: str) -> List[str]:
        """Generate bullet points using Gemini API"""
        
        try:
            # Send full section content - Gemini 2.5 Flash can handle 1M+ tokens
            result = self.gemini_client.generate_bullet_points(
                section_content,
                heading,
                self.MAX_WORDS_PER_BULLET,
                self.MIN_BULLETS_PER_SECTION,
                self.MAX_BULLETS_PER_SECTION
            )
            
            if result['success']:
                bullets = result['bullet_points']
                if len(bullets) >= self.MIN_BULLETS_PER_SECTION:
                    return bullets[:self.MAX_BULLETS_PER_SECTION]
                else:
                    print(f"Warning: Gemini generated only {len(bullets)} bullets for '{heading}'")
                    return bullets
            else:
                print(f"Warning: Gemini generation failed for '{heading}': {result.get('error', 'Unknown error')}")
                return self._generate_fallback_bullets(section_content, heading)
                
        except Exception as e:
            print(f"Error generating Gemini bullets for '{heading}': {e}")
            return self._generate_fallback_bullets(section_content, heading)

    def _generate_grok_bullets(self, section_content: str, heading: str) -> List[str]:
        """Generate bullet points using Grok API"""
        
        # Create specialized prompt for bullet point generation
        prompt = f"""You are an expert educational content creator. Your task is to create concise bullet points from textbook content.

REQUIREMENTS:
- Create {self.MIN_BULLETS_PER_SECTION}-{self.MAX_BULLETS_PER_SECTION} bullet points
- Each bullet point must be EXACTLY {self.MAX_WORDS_PER_BULLET} words or fewer
- Focus on essential facts, examples, and key details
- Preserve numerical data, dates (especially post-2023), program names, case names, or legislation
- Use clear, factual language
- Make each bullet self-contained and informative

SECTION: {heading}

CONTENT:
{section_content}  

Generate bullet points that faithfully capture all essential information from this section. Format as simple bullet points with dashes (-), not numbered lists.

Example format:
- Key concept with essential details
- Important statistic or data point
- Specific program or policy name
"""

        try:
            # Use Grok's content generation method
            result = self.grok_client.generate_slide_content(heading, section_content[:2000])
            
            if result['success']:
                # Parse the response to extract bullet points
                bullets = self._parse_ai_bullet_response(result['content'])
                
                # Validate and filter bullets
                valid_bullets = []
                for bullet in bullets:
                    if len(bullet.split()) <= self.MAX_WORDS_PER_BULLET and len(bullet.strip()) > 5:
                        valid_bullets.append(bullet.strip())
                
                if len(valid_bullets) >= self.MIN_BULLETS_PER_SECTION:
                    return valid_bullets[:self.MAX_BULLETS_PER_SECTION]
                else:
                    print(f"Warning: Grok generated only {len(valid_bullets)} valid bullets for '{heading}'")
                    return valid_bullets
            else:
                print(f"Warning: Grok generation failed for '{heading}': {result.get('error', 'Unknown error')}")
                return self._generate_fallback_bullets(section_content, heading)
                
        except Exception as e:
            print(f"Error generating Grok bullets for '{heading}': {e}")
            return self._generate_fallback_bullets(section_content, heading)
    
    def _parse_ai_bullet_response(self, response_content: str) -> List[str]:
        """Parse AI response to extract bullet points"""
        bullets = []
        lines = response_content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for bullet point patterns
            if line.startswith('-'):
                # Remove dash and clean
                clean_bullet = re.sub(r'^-\s*', '', line).strip()
                if clean_bullet:
                    bullets.append(clean_bullet)
            elif line.startswith('•') or line.startswith('*'):
                # Handle other bullet formats
                clean_bullet = re.sub(r'^[•*]\s*', '', line).strip()
                if clean_bullet:
                    bullets.append(clean_bullet)
            elif re.match(r'^\d+\.\s*', line):
                # Handle numbered lists
                clean_bullet = re.sub(r'^\d+\.\s*', '', line).strip()
                if clean_bullet:
                    bullets.append(clean_bullet)
        
        return bullets
    
    def _generate_fallback_bullets(self, section_content: str, heading: str) -> List[str]:
        """Generate bullet points using rule-based approach as fallback"""
        # Simple extraction of key sentences
        sentences = re.split(r'[.!?]+', section_content)
        bullets = []
        
        for sentence in sentences[:10]:  # Look at first 10 sentences
            sentence = sentence.strip()
            if 15 <= len(sentence) <= 100:  # Reasonable length
                # Try to create a concise bullet
                words = sentence.split()
                if len(words) <= self.MAX_WORDS_PER_BULLET:
                    bullets.append(sentence)
                else:
                    # Take first N words
                    bullet = ' '.join(words[:self.MAX_WORDS_PER_BULLET])
                    bullets.append(bullet)
                
                if len(bullets) >= self.MAX_BULLETS_PER_SECTION:
                    break
        
        return bullets[:self.MAX_BULLETS_PER_SECTION]
    
    def generate_content_from_file_and_headings(self, file_path: str, headings_path: str, 
                                              output_path: str) -> Dict[str, Any]:
        """
        Main method to generate AI-enhanced bullet point content from PDF/RTF and headings file.
        """
        start_time = datetime.now()
        
        try:
            # Detect file type and extract text accordingly
            file_type = self.detect_file_type(file_path)
            
            if file_type == 'pdf':
                print("Extracting PDF text...")
                text_content = self.extract_pdf_text(file_path)
            elif file_type == 'rtf':
                print("Extracting RTF text...")
                text_content = self.extract_rtf_text(file_path)
            else:
                return {'success': False, 'error': f'Unsupported file type: {file_type}. Use PDF or RTF files.'}
            
            if not text_content:
                return {'success': False, 'error': f'Failed to extract text from {file_type.upper()} file'}
            
            print("Loading headings...")
            headings = self.load_headings_from_file(headings_path)
            if not headings:
                return {'success': False, 'error': 'Failed to load headings'}
            
            print(f"Found {len(headings)} headings to process")
            
            # Extract sections
            print("Extracting section content...")
            sections = self.extract_section_content(text_content, headings)
            
            if not sections:
                return {'success': False, 'error': 'No sections could be extracted'}
            
            print(f"Extracted {len(sections)} sections")
            
            # Generate bullet points for each section using AI
            print("Generating AI-enhanced bullet points...")
            results = {}
            total_bullets = 0
            
            for heading, content in sections.items():
                print(f"  Processing: {heading}...")
                bullets = self.generate_ai_bullet_points(content, heading)
                results[heading] = {
                    'bullets': bullets,
                    'bullet_count': len(bullets),
                    'content_length': len(content),
                    'content_preview': content[:200] + "..." if len(content) > 200 else content
                }
                total_bullets += len(bullets)
                print(f"    Generated {len(bullets)} bullets")
                
                # Small delay to avoid rate limiting if using AI
                if self.use_grok:
                    time.sleep(1)
            
            # Create markdown output
            print("Creating markdown output...")
            markdown_content = self._create_markdown_output(results, file_path, headings_path, file_type)
            
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
                'ai_method': 'openai' if self.use_openai else ('gemini' if self.use_gemini else ('grok' if self.use_grok else 'fallback')),
                'file_type': file_type,
                'metadata': {
                    'source_file': file_path,
                    'file_type': file_type,
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
    
    def _create_markdown_output(self, results: Dict[str, Dict], file_path: str, headings_path: str, file_type: str = 'pdf') -> str:
        """Create formatted markdown output"""
        content = []
        
        # Header
        content.append("# AI-Generated Textbook Chapter Notes\n")
        content.append(f"**Source File:** {file_path} ({file_type.upper()})")
        content.append(f"**Headings Source:** {headings_path}")
        content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        ai_method = 'OpenAI API' if self.use_openai else ('Gemini API' if self.use_gemini else ('Grok API' if self.use_grok else 'Rule-based fallback'))
        content.append(f"**AI Method:** {ai_method}")
        content.append(f"**Total Sections:** {len(results)}")
        content.append(f"**Total Bullets:** {sum(data['bullet_count'] for data in results.values())}")
        if file_type == 'rtf':
            content.append(f"**Note:** RTF format used for enhanced heading detection")
        content.append("")
        
        # Sections
        for heading, data in results.items():
            content.append(f"## **{heading}**\n")
            
            if data['bullets']:
                for bullet in data['bullets']:
                    content.append(f"• {bullet}")
            else:
                content.append("• No content available for this section")
            
            # Add section metadata as comment
            content.append(f"\n<!-- Section had {data['content_length']} characters of source text -->")
            content.append("")  # Empty line between sections
        
        return '\n'.join(content)


def main():
    """Command-line interface"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate AI-enhanced bullet points from PDF or RTF textbook chapters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with OpenAI (requires OPENAI_API_KEY environment variable)
  %(prog)s chapter.pdf headings.txt output.md --use-openai
  
  # Generate from RTF file with Grok AI (requires XAI_API_KEY environment variable)
  %(prog)s chapter.rtf headings.txt output.md --use-grok
  
  # Generate with fallback method
  %(prog)s chapter.pdf headings.txt output.md
  
  # Generate with custom models
  %(prog)s chapter.rtf headings.txt output.md --use-gemini --gemini-model gemini-1.5-pro
        """
    )
    
    parser.add_argument('file_path', help='Path to PDF or RTF textbook chapter')
    parser.add_argument('headings_path', help='Path to text file containing headings (one per line)')
    parser.add_argument('output_path', help='Path for output markdown file')
    parser.add_argument('--use-gemini', action='store_true', help='Use Gemini AI for bullet generation (recommended)')
    parser.add_argument('--gemini-api-key', help='Google AI API key (or set GOOGLE_API_KEY env var)')
    parser.add_argument('--gemini-model', default='gemini-1.5-flash', help='Gemini model to use (default: gemini-1.5-flash)')
    parser.add_argument('--use-grok', action='store_true', help='Use Grok AI for bullet generation')
    parser.add_argument('--grok-api-key', help='Grok API key (or set XAI_API_KEY env var)')
    parser.add_argument('--grok-model', default='grok-beta', help='Grok model to use (default: grok-beta)')
    parser.add_argument('--use-openai', action='store_true', help='Use OpenAI for bullet generation')
    parser.add_argument('--openai-api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--openai-model', default='gpt-4o-mini', help='OpenAI model to use (default: gpt-4o-mini)')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = AITextbookContentGenerator(
        use_grok=args.use_grok,
        grok_api_key=args.grok_api_key,
        grok_model=args.grok_model,
        use_gemini=args.use_gemini,
        gemini_api_key=args.gemini_api_key,
        gemini_model=args.gemini_model,
        use_openai=args.use_openai,
        openai_api_key=args.openai_api_key,
        openai_model=args.openai_model
    )
    
    # Generate content
    result = generator.generate_content_from_file_and_headings(
        args.file_path, 
        args.headings_path, 
        args.output_path
    )
    
    if result['success']:
        print(f"\nSuccess! Generated content saved to: {result['output_path']}")
        print(f"  - Processed {result['sections_processed']} sections")
        print(f"  - Generated {result['total_bullets']} total bullet points")
        print(f"  - AI Method: {result['ai_method']}")
        print(f"  - Processing time: {result['processing_time']}")
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()