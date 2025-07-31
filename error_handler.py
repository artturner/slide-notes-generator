import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

class SlideNotesError(Exception):
    """Base exception for slide notes generator"""
    pass

class SlideExtractionError(SlideNotesError):
    """Exception raised during slide extraction"""
    pass

class TextbookParsingError(SlideNotesError):
    """Exception raised during textbook parsing"""
    pass

class ContentAlignmentError(SlideNotesError):
    """Exception raised during content alignment"""
    pass

class NotesGenerationError(SlideNotesError):
    """Exception raised during notes generation"""
    pass

class OutputFormattingError(SlideNotesError):
    """Exception raised during output formatting"""
    pass

class ErrorHandler:
    def __init__(self, log_file: str = "slide_notes_errors.log", log_level: int = logging.INFO):
        self.log_file = log_file
        self.errors = []
        self.warnings = []
        
        # Setup logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_inputs(self, pptx_path: str, textbook_path: str) -> Dict[str, List[str]]:
        """Validate input files and return validation results"""
        validation_results = {
            'errors': [],
            'warnings': [],
            'valid': True
        }
        
        # Check PowerPoint file
        if not pptx_path:
            validation_results['errors'].append("PowerPoint file path is required")
            validation_results['valid'] = False
        elif not os.path.exists(pptx_path):
            validation_results['errors'].append(f"PowerPoint file not found: {pptx_path}")
            validation_results['valid'] = False
        elif not pptx_path.lower().endswith(('.pptx', '.ppt')):
            validation_results['errors'].append("PowerPoint file must have .pptx or .ppt extension")
            validation_results['valid'] = False
        
        # Check textbook file
        if not textbook_path:
            validation_results['errors'].append("Textbook file path is required")
            validation_results['valid'] = False
        elif not os.path.exists(textbook_path):
            validation_results['errors'].append(f"Textbook file not found: {textbook_path}")
            validation_results['valid'] = False
        elif not textbook_path.lower().endswith(('.pdf', '.docx', '.txt')):
            validation_results['errors'].append("Textbook file must be PDF, DOCX, or TXT format")
            validation_results['valid'] = False
        
        # Check file permissions
        try:
            if os.path.exists(pptx_path):
                with open(pptx_path, 'rb') as f:
                    pass
        except PermissionError:
            validation_results['errors'].append(f"No read permission for PowerPoint file: {pptx_path}")
            validation_results['valid'] = False
        
        try:
            if os.path.exists(textbook_path):
                with open(textbook_path, 'rb') as f:
                    pass
        except PermissionError:
            validation_results['errors'].append(f"No read permission for textbook file: {textbook_path}")
            validation_results['valid'] = False
        
        # File size warnings
        if os.path.exists(pptx_path):
            pptx_size = os.path.getsize(pptx_path) / (1024 * 1024)  # MB
            if pptx_size > 50:
                validation_results['warnings'].append(f"Large PowerPoint file ({pptx_size:.1f} MB) may take longer to process")
        
        if os.path.exists(textbook_path):
            textbook_size = os.path.getsize(textbook_path) / (1024 * 1024)  # MB
            if textbook_size > 100:
                validation_results['warnings'].append(f"Large textbook file ({textbook_size:.1f} MB) may take longer to process")
        
        return validation_results
    
    def handle_slide_extraction_error(self, error: Exception, slide_index: Optional[int] = None) -> Dict[str, Any]:
        """Handle errors during slide extraction"""
        error_info = {
            'type': 'slide_extraction',
            'message': str(error),
            'slide_index': slide_index,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        self.errors.append(error_info)
        
        if slide_index is not None:
            self.logger.error(f"Error extracting slide {slide_index}: {error}")
        else:
            self.logger.error(f"Error during slide extraction: {error}")
        
        return error_info
    
    def handle_textbook_parsing_error(self, error: Exception, file_path: str) -> Dict[str, Any]:
        """Handle errors during textbook parsing"""
        error_info = {
            'type': 'textbook_parsing',
            'message': str(error),
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        self.errors.append(error_info)
        self.logger.error(f"Error parsing textbook {file_path}: {error}")
        
        return error_info
    
    def handle_content_alignment_error(self, error: Exception, slide_number: Optional[int] = None) -> Dict[str, Any]:
        """Handle errors during content alignment"""
        error_info = {
            'type': 'content_alignment',
            'message': str(error),
            'slide_number': slide_number,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        self.errors.append(error_info)
        
        if slide_number:
            self.logger.error(f"Error aligning content for slide {slide_number}: {error}")
        else:
            self.logger.error(f"Error during content alignment: {error}")
        
        return error_info
    
    def handle_notes_generation_error(self, error: Exception, slide_number: Optional[int] = None) -> Dict[str, Any]:
        """Handle errors during notes generation"""
        error_info = {
            'type': 'notes_generation',
            'message': str(error),
            'slide_number': slide_number,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        self.errors.append(error_info)
        
        if slide_number:
            self.logger.error(f"Error generating notes for slide {slide_number}: {error}")
        else:
            self.logger.error(f"Error during notes generation: {error}")
        
        return error_info
    
    def handle_output_formatting_error(self, error: Exception, format_type: str) -> Dict[str, Any]:
        """Handle errors during output formatting"""
        error_info = {
            'type': 'output_formatting',
            'message': str(error),
            'format_type': format_type,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        self.errors.append(error_info)
        self.logger.error(f"Error formatting output as {format_type}: {error}")
        
        return error_info
    
    def add_warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Add a warning message"""
        warning_info = {
            'message': message,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.warnings.append(warning_info)
        self.logger.warning(message)
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check if required dependencies are available"""
        dependency_status = {
            'missing_packages': [],
            'available_packages': [],
            'critical_missing': False
        }
        
        required_packages = [
            'python-pptx',
            'PyPDF2',
            'scikit-learn',
            'numpy',
            'nltk'
        ]
        
        optional_packages = [
            'openai',
            'sentence-transformers',
            'python-docx'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                dependency_status['available_packages'].append(package)
            except ImportError:
                dependency_status['missing_packages'].append(package)
                dependency_status['critical_missing'] = True
        
        for package in optional_packages:
            try:
                __import__(package.replace('-', '_'))
                dependency_status['available_packages'].append(package)
            except ImportError:
                dependency_status['missing_packages'].append(package)
        
        if dependency_status['critical_missing']:
            self.logger.error(f"Critical packages missing: {dependency_status['missing_packages']}")
        elif dependency_status['missing_packages']:
            self.logger.warning(f"Optional packages missing: {dependency_status['missing_packages']}")
        
        return dependency_status
    
    def validate_output_path(self, output_path: str) -> Dict[str, Any]:
        """Validate output path and permissions"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                validation['warnings'].append(f"Created output directory: {output_dir}")
            except Exception as e:
                validation['errors'].append(f"Cannot create output directory {output_dir}: {e}")
                validation['valid'] = False
        
        # Check write permissions
        try:
            test_file = output_path + '.test'
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            validation['errors'].append(f"Cannot write to output path {output_path}: {e}")
            validation['valid'] = False
        
        # Check if file already exists
        if os.path.exists(output_path):
            validation['warnings'].append(f"Output file {output_path} already exists and will be overwritten")
        
        return validation
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors and warnings"""
        error_types = {}
        for error in self.errors:
            error_type = error.get('type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'error_types': error_types,
            'recent_errors': self.errors[-5:] if self.errors else [],
            'recent_warnings': self.warnings[-5:] if self.warnings else []
        }
    
    def clear_errors(self):
        """Clear all recorded errors and warnings"""
        self.errors.clear()
        self.warnings.clear()
    
    def save_error_report(self, report_path: str) -> bool:
        """Save detailed error report to file"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'summary': self.get_error_summary(),
                'errors': self.errors,
                'warnings': self.warnings
            }
            
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving error report: {e}")
            return False