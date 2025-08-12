from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from grok_client import GrokClient

class SlideContentGenerator:
    def __init__(self, use_grok: bool = False, grok_api_key: Optional[str] = None, grok_model: str = "grok-beta"):
        self.use_grok = use_grok
        self.grok_api_key = grok_api_key
        self.grok_model = grok_model
        
        # Initialize Grok client if enabled
        self.grok_client = None
        if self.use_grok:
            try:
                self.grok_client = GrokClient(api_key=grok_api_key, model=grok_model)
                test_result = self.grok_client.test_connection()
                if not test_result['success']:
                    print(f"Warning: Grok connection test failed: {test_result.get('error', 'Unknown error')}")
                    print("Falling back to built-in content generation...")
                    self.use_grok = False
                else:
                    print(f"✓ Grok API connected successfully for slide content generation using model: {grok_model}")
            except Exception as e:
                print(f"Warning: Failed to initialize Grok client: {e}")
                print("Falling back to built-in content generation...")
                self.use_grok = False
        
        # Content generation constraints
        self.MAX_WORDS_PER_BULLET = 13
        self.MAX_BULLETS_PER_TOPIC = 6
    
    def generate_slide_content(self, slide_content: Dict[str, Any], 
                             aligned_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate content for slides following the 6x6 model
        
        Args:
            slide_content: Existing slide information (title, headings, etc.)
            aligned_sections: Relevant textbook sections
        
        Returns:
            Dict containing generated bullet points and metadata
        """
        
        # Use Grok if enabled and available
        if self.use_grok and self.grok_client:
            return self._generate_grok_content(slide_content, aligned_sections)
        
        # Fallback to traditional method
        return self._generate_traditional_content(slide_content, aligned_sections)
    
    def _generate_grok_content(self, slide_content: Dict[str, Any], 
                             aligned_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate slide content using Grok API following 6x6 model"""
        
        slide_title = slide_content.get('title', f"Slide {slide_content.get('slide_number', 'Unknown')}")
        
        # Get existing headings from slide
        existing_headings = []
        if slide_content.get('text_content'):
            for text in slide_content['text_content']:
                if text.strip() and text != slide_title and self._looks_like_heading(text):
                    existing_headings.append(text.strip())
        
        # Determine the topic
        if existing_headings:
            topic = f"{slide_title} - {existing_headings[0]}"
        else:
            topic = slide_title
        
        # Prepare textbook context
        textbook_context = ""
        if aligned_sections:
            context_parts = []
            for section in aligned_sections[:2]:  # Top 2 matches
                if section.get('content'):
                    context_parts.append(f"Section: {section.get('title', 'Unknown')}")
                    context_parts.append(section['content'][:1500])  # Limit context length
            textbook_context = '\n\n'.join(context_parts)
        
        # Generate content using Grok's new content-specific method
        result = self.grok_client.generate_slide_content(topic, textbook_context)
        
        if result['success']:
            bullet_points = self._parse_grok_bullet_points(result['content'])
            return {
                'success': True,
                'topic': topic,
                'bullet_points': bullet_points,
                'generation_method': 'grok',
                'model': result.get('model', 'grok'),
                'processing_time': result.get('processing_time', 0)
            }
        else:
            print(f"Warning: Grok content generation failed for {topic}: {result.get('error', 'Unknown error')}")
            print("Falling back to built-in generation...")
            return self._generate_traditional_content(slide_content, aligned_sections)
    
    def _generate_traditional_content(self, slide_content: Dict[str, Any], 
                                    aligned_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate slide content using built-in logic following 6x6 model"""
        
        slide_title = slide_content.get('title', f"Slide {slide_content.get('slide_number', 'Unknown')}")
        
        # Get existing headings from slide
        existing_headings = []
        if slide_content.get('text_content'):
            for text in slide_content['text_content']:
                if text.strip() and text != slide_title and self._looks_like_heading(text):
                    existing_headings.append(text.strip())
        
        # Determine the topic
        if existing_headings:
            topic = f"{slide_title} - {existing_headings[0]}"
        else:
            topic = slide_title
        
        # Generate bullet points from textbook content
        bullet_points = []
        if aligned_sections:
            best_section = aligned_sections[0]
            content = best_section.get('content', '')
            
            # Extract key concepts and create bullet points
            key_sentences = self._extract_key_sentences(content, topic)
            bullet_points = self._create_bullet_points_from_sentences(key_sentences)
        
        # Fallback: create generic bullet points from topic
        if not bullet_points:
            bullet_points = self._create_fallback_bullet_points(topic)
        
        # Ensure 6x6 compliance
        bullet_points = self._enforce_6x6_rules(bullet_points)
        
        return {
            'success': True,
            'topic': topic,
            'bullet_points': bullet_points,
            'generation_method': 'traditional',
            'processing_time': 0
        }
    
    def _create_grok_content_prompt(self, topic: str, textbook_context: str) -> str:
        """Create a specialized prompt for Grok to generate slide content with updated constraints"""
        
        return f"""You are an expert instructional designer creating slide content for educational presentations. Your task is to generate bullet points with these constraints: maximum 13 words per bullet point and maximum 6 bullet points per topic.

STRICT REQUIREMENTS:
1. Each bullet point must be EXACTLY 13 words or fewer
2. Maximum 6 bullet points total
3. Focus on the most important concepts from the topic
4. Use clear, educational language
5. Make each bullet point informative and stand alone
6. Use bullet point format, NOT Roman numerals or numbered lists
7. Avoid overly technical jargon unless necessary

Topic: {topic}

Textbook Context (for reference):
{textbook_context[:2000] if textbook_context else "No textbook context provided"}

Generate bullet points that capture the essential concepts for this topic. Each bullet should be a clear, educational phrase of 13 words maximum. Focus on key concepts, processes, definitions, or important facts that students need to understand.

Format your response as a simple bulleted list using "•" for each point. Do NOT use Roman numerals (I, II, III) or numbered lists. Example format:
• Core concept explanation with relevant educational details
• Important process or method students should understand
• Key definition or terminology for this topic
• Practical application or real-world example
• Critical relationship between concepts
• Essential takeaway for student learning"""

    def _call_grok_for_content(self, prompt: str, topic: str) -> Dict[str, Any]:
        """Call Grok API for content generation"""
        
        try:
            result = self.grok_client.generate_slide_notes(
                slide_content=prompt,
                slide_title=topic,
                textbook_context=""
            )
            
            return {
                'success': result['success'],
                'content': result.get('notes', ''),
                'model': result.get('model', 'grok'),
                'processing_time': result.get('processing_time', 0),
                'error': result.get('error', '')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'content': ''
            }
    
    def _parse_grok_bullet_points(self, content: str) -> List[str]:
        """Parse bullet points from Grok response"""
        
        bullet_points = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for bullet point patterns - prioritize dash format
            if line.startswith('-'):
                # Remove dash and clean
                clean_point = re.sub(r'^-\s*', '', line).strip()
                if clean_point and len(clean_point.split()) <= self.MAX_WORDS_PER_BULLET:
                    bullet_points.append(clean_point)
            elif line.startswith('•') or line.startswith('*'):
                # Handle other bullet formats
                clean_point = re.sub(r'^[•*]\s*', '', line).strip()
                if clean_point and len(clean_point.split()) <= self.MAX_WORDS_PER_BULLET:
                    bullet_points.append(clean_point)
            elif re.match(r'^\d+\.\s*', line):
                # Handle numbered lists (though we're trying to avoid these)
                clean_point = re.sub(r'^\d+\.\s*', '', line).strip()
                if clean_point and len(clean_point.split()) <= self.MAX_WORDS_PER_BULLET:
                    bullet_points.append(clean_point)
            elif re.match(r'^[IVX]+\.\s*', line):
                # Handle Roman numerals (though we're trying to avoid these)
                clean_point = re.sub(r'^[IVX]+\.\s*', '', line).strip()
                if clean_point and len(clean_point.split()) <= self.MAX_WORDS_PER_BULLET:
                    bullet_points.append(clean_point)
        
        # Ensure we don't exceed 6 bullets
        return bullet_points[:self.MAX_BULLETS_PER_TOPIC]
    
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
    
    def _extract_key_sentences(self, content: str, topic: str) -> List[str]:
        """Extract key sentences related to the topic"""
        
        sentences = re.split(r'[.!?]+', content)
        topic_words = set(word.lower() for word in topic.split() if len(word) > 2)
        
        scored_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Skip very short sentences
                sentence_words = set(word.lower() for word in sentence.split())
                overlap = len(topic_words.intersection(sentence_words))
                if overlap > 0:
                    scored_sentences.append((sentence, overlap))
        
        # Sort by relevance and return top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        return [sent for sent, score in scored_sentences[:8]]
    
    def _create_bullet_points_from_sentences(self, sentences: List[str]) -> List[str]:
        """Convert sentences into 6x6 bullet points"""
        
        bullet_points = []
        
        for sentence in sentences:
            # Extract key phrases from sentence
            bullet = self._extract_key_phrase(sentence)
            if bullet and len(bullet.split()) <= self.MAX_WORDS_PER_BULLET:
                bullet_points.append(bullet)
                if len(bullet_points) >= self.MAX_BULLETS_PER_TOPIC:
                    break
        
        return bullet_points
    
    def _extract_key_phrase(self, sentence: str) -> str:
        """Extract a key phrase from a sentence for bullet point"""
        
        # Remove common sentence starters
        sentence = re.sub(r'^(The\s+|This\s+|That\s+|These\s+|Those\s+)', '', sentence, flags=re.IGNORECASE)
        
        # Look for noun phrases or verb phrases
        words = sentence.split()
        
        # Try to find a meaningful 3-6 word phrase
        for length in range(6, 2, -1):  # Start with 6 words, go down to 3
            if len(words) >= length:
                phrase = ' '.join(words[:length])
                if self._is_meaningful_phrase(phrase):
                    return phrase.strip('.,!?;:')
        
        # Fallback: take first few words
        return ' '.join(words[:min(6, len(words))]).strip('.,!?;:')
    
    def _is_meaningful_phrase(self, phrase: str) -> bool:
        """Check if a phrase is meaningful (contains noun or verb)"""
        
        # Simple heuristic: contains at least one word longer than 3 characters
        return any(len(word) > 3 for word in phrase.split())
    
    def _create_fallback_bullet_points(self, topic: str) -> List[str]:
        """Create generic bullet points when no textbook content is available"""
        
        topic_words = [word for word in topic.split() if len(word) > 2]
        
        if not topic_words:
            return ["Key concepts to explore", "Important definitions", "Practical applications", "Real world examples"]
        
        main_concept = topic_words[0] if topic_words else "Topic"
        
        return [
            f"Define {main_concept} clearly",
            f"Explore {main_concept} characteristics",
            f"Examine {main_concept} applications",
            f"Analyze {main_concept} importance",
            f"Consider {main_concept} implications",
            f"Review {main_concept} examples"
        ]
    
    def _enforce_6x6_rules(self, bullet_points: List[str]) -> List[str]:
        """Ensure bullet points follow 6x6 rules"""
        
        compliant_bullets = []
        
        for bullet in bullet_points:
            words = bullet.split()
            
            # Truncate if too many words
            if len(words) > self.MAX_WORDS_PER_BULLET:
                truncated = ' '.join(words[:self.MAX_WORDS_PER_BULLET])
                compliant_bullets.append(truncated)
            else:
                compliant_bullets.append(bullet)
            
            # Stop if we have enough bullets
            if len(compliant_bullets) >= self.MAX_BULLETS_PER_TOPIC:
                break
        
        return compliant_bullets
    
    def generate_presentation_content(self, aligned_slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate content for all slides in a presentation"""
        
        results = {
            'slides': [],
            'total_slides': len(aligned_slides),
            'successful': 0,
            'failed': 0,
            'generation_method': 'grok' if self.use_grok else 'traditional'
        }
        
        for slide in aligned_slides:
            print(f"Generating content for slide {slide.get('slide_number', '?')}: {slide.get('title', 'Untitled')[:50]}...")
            
            content_result = self.generate_slide_content(
                slide, 
                slide.get('aligned_sections', [])
            )
            
            if content_result['success']:
                # Add the generated content to the slide
                slide_with_content = slide.copy()
                slide_with_content['generated_content'] = content_result
                results['slides'].append(slide_with_content)
                results['successful'] += 1
            else:
                results['slides'].append(slide)
                results['failed'] += 1
        
        results['success_rate'] = results['successful'] / results['total_slides'] if results['total_slides'] > 0 else 0
        
        return results