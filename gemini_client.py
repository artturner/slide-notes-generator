#!/usr/bin/env python3

import os
import time
from typing import Dict, Any, Optional, List

# Note: Install google-generativeai package with: pip install google-generativeai
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai package not installed. Install with: pip install google-generativeai")

class GeminiClient:
    """
    Client for Google Gemini API integration
    Optimized for educational content generation
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google AI API key (if None, reads from GOOGLE_API_KEY env var)
            model: Gemini model to use (default: gemini-1.5-flash)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package is required. Install with: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = model
        
        if not self.api_key:
            raise ValueError("Google AI API key is required. Set GOOGLE_API_KEY environment variable or pass api_key parameter.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        # Generation config for consistent formatting
        self.generation_config = genai.GenerationConfig(
            temperature=0.3,
            top_p=0.8,
            top_k=40,
            max_output_tokens=1024,
        )
    
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return status"""
        try:
            response = self.model.generate_content(
                "Hello, can you confirm you're working? Just respond with 'Yes'.",
                generation_config=self.generation_config
            )
            
            # Check if response has valid content
            if not response.parts or not hasattr(response, 'text'):
                return {
                    'success': False,
                    'error': f'No valid response content (finish_reason: {getattr(response, "finish_reason", "unknown")})',
                    'error_type': 'SafetyFilter'
                }
            
            return {
                'success': True,
                'model': self.model_name,
                'response': response.text,
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def generate_bullet_points(self, section_content: str, heading: str, 
                             max_words_per_bullet: int = 10, 
                             min_bullets: int = 3, 
                             max_bullets: int = 6) -> Dict[str, Any]:
        """
        Generate bullet points for a textbook section using Gemini
        
        Args:
            section_content: The textbook section content
            heading: The section heading
            max_words_per_bullet: Maximum words per bullet point
            min_bullets: Minimum number of bullets to generate
            max_bullets: Maximum number of bullets to generate
        
        Returns:
            Dict with generated bullet points and metadata
        """
        
        # Create specialized prompt for bullet point generation
        prompt = f"""You are an expert educational content creator specializing in creating concise, factual bullet points from textbook content.

TASK: Create bullet points from the following textbook section.

STRICT REQUIREMENTS:
1. Generate {min_bullets}-{max_bullets} bullet points
2. Each bullet point must be EXACTLY {max_words_per_bullet} words or fewer
3. Capture ALL essential facts, examples, and key details
4. Use clear, factual language - no flowery or unnecessary words
5. Include ALL significant events, laws, programs, statistics, examples, or named entities
6. Preserve numerical data, dates (especially post-2023), program names, case names, or legislation EXACTLY
7. Make each bullet self-contained - do not merge content from other sections
8. Focus on the "what" rather than the "why" - prioritize facts over explanations

SECTION HEADING: {heading}

SECTION CONTENT:
{section_content}

OUTPUT FORMAT:
Generate ONLY the bullet points, one per line, starting with a dash (-). No introduction, no explanation, no other text.

Example format:
- Texas education budget represents 38 percent of state spending
- Social Security Act established federal welfare programs in 1935
- Brown v Board of Education ended school segregation

Generate the bullet points now:"""

        try:
            start_time = time.time()
            
            # Debug logging
            print(f"\n--- DEBUG: Prompt for '{heading}' ---")
            print(f"Content length: {len(section_content)} characters")
            print(f"Full section content:\n{section_content}")
            print(f"\nFull prompt length: {len(prompt)} characters")
            print("--- END DEBUG ---\n")
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            processing_time = time.time() - start_time
            
            # Check if response has valid content
            if not response.parts or not hasattr(response, 'text'):
                return {
                    'success': False,
                    'error': f'No valid response content (finish_reason: {getattr(response, "finish_reason", "unknown")})',
                    'error_type': 'SafetyFilter',
                    'heading': heading
                }
            
            # Debug: Show raw response
            print(f"\n--- DEBUG: Raw Gemini response for '{heading}' ---")
            print(f"Response text: {response.text}")
            print("--- END DEBUG ---\n")
            
            # Parse the response
            bullet_points = self._parse_bullet_response(response.text, max_words_per_bullet)
            
            print(f"--- DEBUG: Parsed bullets for '{heading}' ---")
            print(f"Found {len(bullet_points)} valid bullets:")
            for i, bullet in enumerate(bullet_points, 1):
                print(f"  {i}. {bullet} ({len(bullet.split())} words)")
            print("--- END DEBUG ---\n")
            
            return {
                'success': True,
                'bullet_points': bullet_points,
                'heading': heading,
                'processing_time': processing_time,
                'model': self.model_name,
                'raw_response': response.text
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'heading': heading
            }
    
    def _parse_bullet_response(self, response_text: str, max_words: int) -> List[str]:
        """Parse Gemini response to extract valid bullet points"""
        bullets = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for bullet point patterns
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                # Remove bullet marker and clean
                clean_bullet = line[1:].strip()
                
                # Validate word count
                word_count = len(clean_bullet.split())
                if clean_bullet and word_count <= max_words and word_count >= 3:
                    bullets.append(clean_bullet)
            elif line.startswith(tuple('123456789')):
                # Handle numbered lists
                # Find the first space or period after number
                first_space = line.find(' ')
                first_period = line.find('.')
                if first_space > 0 and (first_period == -1 or first_space < first_period):
                    clean_bullet = line[first_space:].strip()
                elif first_period > 0:
                    clean_bullet = line[first_period+1:].strip()
                else:
                    continue
                
                # Validate word count
                word_count = len(clean_bullet.split())
                if clean_bullet and word_count <= max_words and word_count >= 3:
                    bullets.append(clean_bullet)
        
        return bullets
    
    def generate_batch_bullet_points(self, sections: Dict[str, str], 
                                   max_words_per_bullet: int = 10,
                                   min_bullets: int = 3,
                                   max_bullets: int = 6) -> Dict[str, Any]:
        """
        Generate bullet points for multiple sections
        
        Args:
            sections: Dict mapping section headings to content
            max_words_per_bullet: Maximum words per bullet point
            min_bullets: Minimum bullets per section
            max_bullets: Maximum bullets per section
        
        Returns:
            Dict with results for all sections
        """
        
        results = {
            'sections': {},
            'total_sections': len(sections),
            'successful': 0,
            'failed': 0,
            'total_processing_time': 0,
            'total_bullets': 0
        }
        
        for heading, content in sections.items():
            print(f"Processing section: {heading}...")
            
            section_result = self.generate_bullet_points(
                content, heading, max_words_per_bullet, min_bullets, max_bullets
            )
            
            results['sections'][heading] = section_result
            
            if section_result['success']:
                results['successful'] += 1
                results['total_processing_time'] += section_result.get('processing_time', 0)
                results['total_bullets'] += len(section_result.get('bullet_points', []))
                print(f"  ✓ Generated {len(section_result['bullet_points'])} bullets")
            else:
                results['failed'] += 1
                print(f"  ✗ Failed: {section_result.get('error', 'Unknown error')}")
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        results['success_rate'] = results['successful'] / results['total_sections'] if results['total_sections'] > 0 else 0
        
        return results


def main():
    """Simple test function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python gemini_client.py <test_content>")
        print("Example: python gemini_client.py 'The New Deal was a series of programs...'")
        sys.exit(1)
    
    test_content = sys.argv[1]
    
    try:
        client = GeminiClient()
        
        # Test connection
        print("Testing Gemini connection...")
        test_result = client.test_connection()
        if test_result['success']:
            print("✓ Gemini connection successful")
        else:
            print(f"✗ Connection failed: {test_result['error']}")
            sys.exit(1)
        
        # Generate bullet points
        print("\nGenerating bullet points...")
        result = client.generate_bullet_points(test_content, "Test Section")
        
        if result['success']:
            print(f"✓ Generated {len(result['bullet_points'])} bullet points:")
            for i, bullet in enumerate(result['bullet_points'], 1):
                print(f"  {i}. {bullet}")
        else:
            print(f"✗ Generation failed: {result['error']}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()