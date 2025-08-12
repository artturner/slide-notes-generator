#!/usr/bin/env python3

import os
import time
from typing import Dict, Any, Optional, List
from openai import OpenAI
import json

class GrokClient:
    """
    Client for xAI Grok API integration
    Uses OpenAI SDK with xAI base URL for compatibility
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "grok-beta"):
        """
        Initialize Grok client
        
        Args:
            api_key: xAI API key (if None, reads from XAI_API_KEY env var)
            model: Grok model to use (default: grok-beta)
        """
        self.api_key = api_key or os.getenv('XAI_API_KEY')
        self.model = model
        
        if not self.api_key:
            raise ValueError("xAI API key is required. Set XAI_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize OpenAI client with xAI base URL
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1"
        )
        
        # Your custom prompt template with strict formatting requirements
        self.base_prompt = """You are Grok 3 built by xAI, designed to create detailed notes for educational slides based on the content provided. I will supply a chapter manuscript for context and then paste individual slide content to request notes. 

CRITICAL: You MUST follow this EXACT formatting for every slide without exception:

FORMATTING REQUIREMENTS:
1. Start each slide with exactly this format: **I. [First bullet point content]**
2. Use Roman numerals (I, II, III, IV, etc.) for main sections - one for each bullet point
3. Each main section MUST have exactly two sub-points: A and B
4. Sub-points MUST be formatted as: "  A. [content]" and "  B. [content]" (exactly 2 spaces before A/B)
5. Do NOT use dashes, asterisks, or any other formatting for sub-points
6. Do NOT add any headers, titles, or extra sections beyond the I, II, III structure
7. Do NOT vary the formatting between slides - use the identical structure every time

EXAMPLE FORMAT (follow this exactly):
**I. [First bullet point expanded]**
  A. [First detailed expansion of the bullet point]
  B. [Second detailed expansion of the bullet point]

**II. [Second bullet point expanded]**
  A. [First detailed expansion of the bullet point]
  B. [Second detailed expansion of the bullet point]

CONTENT REQUIREMENTS:
- Base the notes solely on the slide content I provide, without referencing the manuscript or any external sources
- Structure the notes with a main section (I, II, etc.) for each bullet point on the slide, each containing two detailed sub-points (A and B) that expand directly on that bullet point's content
- Ensure the notes are mid-length, providing concise yet thorough expansions that elaborate on the slide's ideas without being overly verbose
- Each sub-point should be 1-2 sentences that directly elaborate on the main bullet point

You MUST use this exact formatting for every single slide. Do not deviate from this structure."""
    
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return status"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Hello, can you confirm you're working?"}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            return {
                'success': True,
                'model': self.model,
                'response': response.choices[0].message.content,
                'usage': response.usage.model_dump() if response.usage else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def generate_slide_notes(self, slide_content: str, slide_title: str = "", 
                           textbook_context: str = "") -> Dict[str, Any]:
        """
        Generate notes for a single slide using Grok
        
        Args:
            slide_content: The slide content/bullet points
            slide_title: Title of the slide
            textbook_context: Relevant textbook content for context
        
        Returns:
            Dict with generated notes and metadata
        """
        
        # Construct the prompt
        user_prompt = f"""
{self.base_prompt}

Chapter Context (for reference only, do not quote directly):
{textbook_context[:2000] if textbook_context else "No textbook context provided"}

Slide Title: {slide_title if slide_title else "Untitled Slide"}

Slide Content:
{slide_content}

Please generate detailed notes following the specified format."""

        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.3,  # Slightly creative but consistent
                top_p=0.9
            )
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'notes': response.choices[0].message.content,
                'slide_title': slide_title,
                'processing_time': processing_time,
                'usage': response.usage.model_dump() if response.usage else None,
                'model': self.model
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'slide_title': slide_title
            }
    
    def generate_slide_content(self, topic: str, textbook_context: str = "") -> Dict[str, Any]:
        """
        Generate bullet point content for slides (NOT notes) using Grok
        This method is specifically for generating slide content bullets, not detailed notes
        
        Args:
            topic: The slide topic/title
            textbook_context: Relevant textbook content for context
        
        Returns:
            Dict with generated content and metadata
        """
        
        # Create a content-specific prompt that explicitly avoids Roman numerals
        content_prompt = f"""You are an expert instructional designer creating slide content for educational presentations. Your task is to generate bullet points with these constraints: maximum 13 words per bullet point and maximum 6 bullet points per topic.

STRICT REQUIREMENTS:
1. Each bullet point must be EXACTLY 13 words or fewer
2. Maximum 6 bullet points total
3. Focus on the most important concepts from the topic
4. Use clear, educational language
5. Make each bullet point informative and stand alone
6. Use ONLY simple bullet points with dashes (-), NOT Roman numerals (I, II, III) or numbered lists
7. Avoid overly technical jargon unless necessary
8. Do NOT use any Roman numerals, letters, or complex formatting
9. Each line should start with a simple dash (-)

Topic: {topic}

Textbook Context (for reference):
{textbook_context[:2000] if textbook_context else "No textbook context provided"}

Generate bullet points that capture the essential concepts for this topic. Each bullet should be a clear, educational phrase of 13 words maximum. Focus on key concepts, processes, definitions, or important facts that students need to understand.

Format your response EXACTLY like this example (use simple dashes, no Roman numerals):
- Core concept explanation with relevant educational details
- Important process or method students should understand  
- Key definition or terminology for this topic
- Practical application or real-world example
- Critical relationship between concepts
- Essential takeaway for student learning

IMPORTANT: Do not use Roman numerals (I, II, III), letters (A, B, C), or numbers (1, 2, 3). Use only simple dashes (-) at the start of each line."""

        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": content_prompt}
                ],
                max_tokens=1500,
                temperature=0.2,  # Lower temperature for more consistent formatting
                top_p=0.8
            )
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'content': response.choices[0].message.content,
                'topic': topic,
                'processing_time': processing_time,
                'usage': response.usage.model_dump() if response.usage else None,
                'model': self.model
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'topic': topic
            }
    
    def generate_batch_notes(self, slides_data: List[Dict[str, Any]], 
                           textbook_context: str = "") -> Dict[str, Any]:
        """
        Generate notes for multiple slides
        
        Args:
            slides_data: List of slide dictionaries with 'content', 'title', etc.
            textbook_context: Shared textbook context
        
        Returns:
            Dict with results for all slides
        """
        
        results = {
            'slides': [],
            'total_slides': len(slides_data),
            'successful': 0,
            'failed': 0,
            'total_processing_time': 0,
            'total_tokens_used': 0
        }
        
        for i, slide_data in enumerate(slides_data, 1):
            print(f"Processing slide {i}/{len(slides_data)}: {slide_data.get('title', 'Untitled')[:50]}...")
            
            slide_result = self.generate_slide_notes(
                slide_content=slide_data.get('content', ''),
                slide_title=slide_data.get('title', f'Slide {i}'),
                textbook_context=textbook_context
            )
            
            results['slides'].append(slide_result)
            
            if slide_result['success']:
                results['successful'] += 1
                results['total_processing_time'] += slide_result.get('processing_time', 0)
                if slide_result.get('usage'):
                    results['total_tokens_used'] += slide_result['usage'].get('total_tokens', 0)
            else:
                results['failed'] += 1
                print(f"  ❌ Failed: {slide_result.get('error', 'Unknown error')}")
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        results['success_rate'] = results['successful'] / results['total_slides'] if results['total_slides'] > 0 else 0
        
        return results
    
    def get_models(self) -> Dict[str, Any]:
        """Get available models from xAI API"""
        try:
            models = self.client.models.list()
            return {
                'success': True,
                'models': [model.id for model in models.data]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }