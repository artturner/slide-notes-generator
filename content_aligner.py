from typing import List, Dict, Any, Tuple
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ContentAligner:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        
    def align_slide_to_textbook(self, slide_content: Dict[str, Any], 
                               textbook_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        slide_text = self._extract_slide_text(slide_content)
        
        if not slide_text.strip():
            return []
        
        section_texts = [section['content'] for section in textbook_sections]
        all_texts = [slide_text] + section_texts
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            slide_vector = tfidf_matrix[0:1]
            section_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(slide_vector, section_vectors).flatten()
            
            aligned_sections = []
            for i, similarity in enumerate(similarities):
                if similarity > 0.1:  # Threshold for relevance
                    section_copy = textbook_sections[i].copy()
                    section_copy['similarity_score'] = float(similarity)
                    section_copy['alignment_details'] = self._get_alignment_details(
                        slide_content, textbook_sections[i], similarity
                    )
                    aligned_sections.append(section_copy)
            
            return sorted(aligned_sections, key=lambda x: x['similarity_score'], reverse=True)
            
        except Exception as e:
            print(f"Error in content alignment: {e}")
            return self._fallback_keyword_matching(slide_content, textbook_sections)
    
    def _extract_slide_text(self, slide_content: Dict[str, Any]) -> str:
        text_parts = []
        
        if slide_content.get('title'):
            text_parts.append(slide_content['title'])
        
        if slide_content.get('text_content'):
            text_parts.extend(slide_content['text_content'])
        
        if slide_content.get('bullet_points'):
            text_parts.extend(slide_content['bullet_points'])
        
        if slide_content.get('notes'):
            text_parts.append(slide_content['notes'])
        
        return ' '.join(text_parts)
    
    def _get_alignment_details(self, slide_content: Dict[str, Any], 
                             section: Dict[str, Any], similarity: float) -> Dict[str, Any]:
        slide_text = self._extract_slide_text(slide_content).lower()
        section_text = section['content'].lower()
        
        common_keywords = self._find_common_keywords(slide_text, section_text)
        topic_overlap = self._calculate_topic_overlap(slide_content, section)
        
        return {
            'similarity_score': similarity,
            'common_keywords': common_keywords,
            'topic_overlap': topic_overlap,
            'slide_title': slide_content.get('title', 'Untitled'),
            'section_title': section.get('title', 'Untitled Section'),
            'confidence': self._calculate_confidence(similarity, common_keywords, topic_overlap)
        }
    
    def _find_common_keywords(self, text1: str, text2: str) -> List[str]:
        words1 = set(re.findall(r'\b[a-zA-Z]{3,}\b', text1.lower()))
        words2 = set(re.findall(r'\b[a-zA-Z]{3,}\b', text2.lower()))
        
        common_words = words1.intersection(words2)
        
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'any', 
                     'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 
                     'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 
                     'see', 'two', 'way', 'who', 'boy', 'did', 'she', 'use', 'her', 
                     'each', 'which', 'their', 'said', 'will', 'from', 'they', 'know',
                     'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when',
                     'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over',
                     'such', 'take', 'than', 'them', 'well', 'were'}
        
        filtered_common = [word for word in common_words if word not in stop_words and len(word) > 3]
        return sorted(filtered_common)[:10]
    
    def _calculate_topic_overlap(self, slide_content: Dict[str, Any], 
                               section: Dict[str, Any]) -> float:
        slide_terms = set()
        if slide_content.get('title'):
            slide_terms.update(re.findall(r'\b[A-Z][a-z]+\b', slide_content['title']))
        
        section_terms = set(section.get('key_terms', []))
        
        if not slide_terms or not section_terms:
            return 0.0
        
        intersection = len(slide_terms.intersection(section_terms))
        union = len(slide_terms.union(section_terms))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_confidence(self, similarity: float, common_keywords: List[str], 
                            topic_overlap: float) -> str:
        score = similarity * 0.5 + len(common_keywords) * 0.02 + topic_overlap * 0.3
        
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _fallback_keyword_matching(self, slide_content: Dict[str, Any], 
                                 textbook_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        slide_text = self._extract_slide_text(slide_content).lower()
        slide_keywords = re.findall(r'\b[a-zA-Z]{4,}\b', slide_text)
        
        matches = []
        for section in textbook_sections:
            section_text = section['content'].lower()
            match_count = sum(1 for keyword in slide_keywords if keyword in section_text)
            
            if match_count > 0:
                section_copy = section.copy()
                section_copy['similarity_score'] = match_count / len(slide_keywords) if slide_keywords else 0
                section_copy['alignment_details'] = {
                    'similarity_score': section_copy['similarity_score'],
                    'common_keywords': [kw for kw in slide_keywords if kw in section_text][:10],
                    'topic_overlap': 0.0,
                    'slide_title': slide_content.get('title', 'Untitled'),
                    'section_title': section.get('title', 'Untitled Section'),
                    'confidence': 'medium' if match_count > 2 else 'low'
                }
                matches.append(section_copy)
        
        return sorted(matches, key=lambda x: x['similarity_score'], reverse=True)
    
    def batch_align_slides(self, slides: List[Dict[str, Any]], 
                          textbook_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        aligned_slides = []
        
        for slide in slides:
            aligned_sections = self.align_slide_to_textbook(slide, textbook_sections)
            
            slide_result = slide.copy()
            slide_result['aligned_sections'] = aligned_sections[:3]  # Top 3 matches
            slide_result['best_match'] = aligned_sections[0] if aligned_sections else None
            
            aligned_slides.append(slide_result)
        
        return aligned_slides
    
    def get_alignment_summary(self, aligned_slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_slides = len(aligned_slides)
        slides_with_matches = sum(1 for slide in aligned_slides if slide.get('best_match'))
        high_confidence_matches = sum(1 for slide in aligned_slides 
                                    if slide.get('best_match') and 
                                    slide['best_match']['alignment_details']['confidence'] == 'high')
        
        return {
            'total_slides': total_slides,
            'slides_with_matches': slides_with_matches,
            'match_rate': slides_with_matches / total_slides if total_slides > 0 else 0,
            'high_confidence_matches': high_confidence_matches,
            'high_confidence_rate': high_confidence_matches / total_slides if total_slides > 0 else 0,
            'coverage_analysis': self._analyze_coverage(aligned_slides)
        }
    
    def _analyze_coverage(self, aligned_slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        covered_sections = set()
        section_usage = {}
        
        for slide in aligned_slides:
            if slide.get('best_match'):
                section_title = slide['best_match'].get('title', 'Unknown')
                covered_sections.add(section_title)
                section_usage[section_title] = section_usage.get(section_title, 0) + 1
        
        return {
            'unique_sections_covered': len(covered_sections),
            'section_usage_frequency': section_usage,
            'most_referenced_section': max(section_usage.items(), key=lambda x: x[1])[0] if section_usage else None
        }