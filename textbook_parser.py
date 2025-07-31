import PyPDF2
from docx import Document
from typing import List, Dict, Any
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

class TextbookParser:
    def __init__(self, textbook_path: str):
        self.textbook_path = textbook_path
        self.file_type = self._detect_file_type()
        self.content = ""
        self.sections = []
        
    def _detect_file_type(self) -> str:
        if self.textbook_path.lower().endswith('.pdf'):
            return 'pdf'
        elif self.textbook_path.lower().endswith('.docx'):
            return 'docx'
        elif self.textbook_path.lower().endswith('.txt'):
            return 'txt'
        else:
            return 'unknown'
    
    def load_content(self) -> bool:
        try:
            if self.file_type == 'pdf':
                return self._load_pdf()
            elif self.file_type == 'docx':
                return self._load_docx()
            elif self.file_type == 'txt':
                return self._load_txt()
            else:
                print(f"Unsupported file type: {self.file_type}")
                return False
        except Exception as e:
            print(f"Error loading textbook content: {e}")
            return False
    
    def _load_pdf(self) -> bool:
        with open(self.textbook_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = []
            
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
            
            self.content = '\n'.join(text_content)
            return True
    
    def _load_docx(self) -> bool:
        doc = Document(self.textbook_path)
        paragraphs = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                paragraphs.append(paragraph.text.strip())
        
        self.content = '\n'.join(paragraphs)
        return True
    
    def _load_txt(self) -> bool:
        with open(self.textbook_path, 'r', encoding='utf-8') as file:
            self.content = file.read()
        return True
    
    def parse_sections(self) -> List[Dict[str, Any]]:
        if not self.content:
            return []
        
        section_patterns = [
            r'^Chapter\s+\d+:?\s*(.+?)$',
            r'^(\d+\.\d*)\s+(.+?)$',
            r'^([A-Z][A-Z\s]+)$',
            r'^# (.+?)$',
            r'^## (.+?)$'
        ]
        
        lines = self.content.split('\n')
        current_section = None
        sections = []
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            is_header = False
            for pattern in section_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    if current_section:
                        sections.append({
                            'title': current_section,
                            'content': '\n'.join(current_content),
                            'word_count': len(' '.join(current_content).split()),
                            'key_terms': self._extract_key_terms('\n'.join(current_content))
                        })
                    
                    current_section = match.group(1) if len(match.groups()) > 0 else line
                    current_content = []
                    is_header = True
                    break
            
            if not is_header and current_section:
                current_content.append(line)
        
        if current_section and current_content:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content),
                'word_count': len(' '.join(current_content).split()),
                'key_terms': self._extract_key_terms('\n'.join(current_content))
            })
        
        self.sections = sections
        return sections
    
    def _extract_key_terms(self, text: str) -> List[str]:
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except:
            pass
        
        try:
            stop_words = set(stopwords.words('english'))
            words = word_tokenize(text.lower())
            
            words = [word for word in words if word.isalpha() and len(word) > 3]
            words = [word for word in words if word not in stop_words]
            
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_words[:10]]
        except:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_words[:10]]
    
    def get_section_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        matching_sections = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for section in self.sections:
            content_lower = section['content'].lower()
            title_lower = section['title'].lower()
            
            score = 0
            for keyword in keywords_lower:
                score += content_lower.count(keyword) * 2
                score += title_lower.count(keyword) * 5
                
                for key_term in section['key_terms']:
                    if keyword in key_term or key_term in keyword:
                        score += 3
            
            if score > 0:
                section_copy = section.copy()
                section_copy['relevance_score'] = score
                matching_sections.append(section_copy)
        
        return sorted(matching_sections, key=lambda x: x['relevance_score'], reverse=True)
    
    def extract_definitions(self, text: str) -> List[Dict[str, str]]:
        definition_patterns = [
            r'(.+?)\s+is\s+defined\s+as\s+(.+?)[\.\n]',
            r'(.+?)\s+refers\s+to\s+(.+?)[\.\n]',
            r'(.+?):\s+(.+?)[\.\n]',
            r'Define\s+(.+?)\s+as\s+(.+?)[\.\n]'
        ]
        
        definitions = []
        for pattern in definition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                if len(term) < 50 and len(definition) > 10:
                    definitions.append({
                        'term': term,
                        'definition': definition
                    })
        
        return definitions