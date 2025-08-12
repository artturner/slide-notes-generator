#!/usr/bin/env python3

import argparse
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from slide_extractor import SlideExtractor
from textbook_parser import TextbookParser
from content_aligner import ContentAligner
from notes_generator import NotesGenerator
from output_formatter import OutputFormatter
from error_handler import ErrorHandler, SlideNotesError
from pptx_notes_writer import PowerPointNotesWriter
from slide_content_generator import SlideContentGenerator
from pptx_content_writer import PowerPointContentWriter
from slide_content_formatter import SlideContentFormatter

class SlideNotesGenerator:
    def __init__(self, verbose: bool = False, use_grok: bool = False, grok_api_key: str = None, grok_model: str = "grok-beta"):
        self.verbose = verbose
        self.use_grok = use_grok
        self.error_handler = ErrorHandler()
        
        # Initialize components
        self.slide_extractor = None
        self.textbook_parser = None
        self.content_aligner = ContentAligner()
        self.notes_generator = NotesGenerator(
            use_grok=use_grok,
            grok_api_key=grok_api_key,
            grok_model=grok_model
        )
        self.output_formatter = OutputFormatter()
        self.pptx_notes_writer = PowerPointNotesWriter()
        self.content_generator = SlideContentGenerator(
            use_grok=use_grok,
            grok_api_key=grok_api_key,
            grok_model=grok_model
        )
        self.content_writer = PowerPointContentWriter()
        self.content_formatter = SlideContentFormatter()
        
        # Progress tracking
        self.total_steps = 6
        self.current_step = 0
    
    def _print_progress(self, message: str):
        """Print progress message if verbose mode is enabled"""
        if self.verbose:
            self.current_step += 1
            print(f"[{self.current_step}/{self.total_steps}] {message}")
    
    def _print_verbose(self, message: str):
        """Print verbose message"""
        if self.verbose:
            print(f"    {message}")
    
    def generate_notes(self, pptx_path: str, textbook_path: str, 
                      output_path: str, output_format: str = 'markdown') -> Dict[str, Any]:
        """
        Main method to generate slide notes
        
        Args:
            pptx_path: Path to PowerPoint presentation
            textbook_path: Path to textbook file (PDF, DOCX, or TXT)
            output_path: Path for output file
            output_format: Output format (markdown, html, json, txt, csv)
        
        Returns:
            Dict containing results and metadata
        """
        
        start_time = datetime.now()
        
        try:
            # Step 1: Validate inputs
            self._print_progress("Validating input files...")
            validation_result = self.error_handler.validate_inputs(pptx_path, textbook_path)
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'errors': validation_result['errors'],
                    'warnings': validation_result['warnings']
                }
            
            if validation_result['warnings']:
                for warning in validation_result['warnings']:
                    self.error_handler.add_warning(warning)
            
            # Step 2: Extract slides
            self._print_progress("Extracting slides from PowerPoint...")
            self.slide_extractor = SlideExtractor(pptx_path)
            slides_content = self.slide_extractor.extract_all_slides()
            
            if not slides_content:
                return {
                    'success': False,
                    'errors': ['No slides could be extracted from the PowerPoint file'],
                    'warnings': []
                }
            
            self._print_verbose(f"Extracted {len(slides_content)} slides")
            
            # Step 3: Parse textbook
            self._print_progress("Parsing textbook content...")
            self.textbook_parser = TextbookParser(textbook_path)
            
            if not self.textbook_parser.load_content():
                return {
                    'success': False,
                    'errors': ['Failed to load textbook content'],
                    'warnings': []
                }
            
            textbook_sections = self.textbook_parser.parse_sections()
            self._print_verbose(f"Parsed {len(textbook_sections)} sections from textbook")
            
            # Step 4: Align content
            self._print_progress("Aligning slide content with textbook...")
            aligned_slides = self.content_aligner.batch_align_slides(slides_content, textbook_sections)
            alignment_summary = self.content_aligner.get_alignment_summary(aligned_slides)
            
            self._print_verbose(f"Alignment rate: {alignment_summary['match_rate']:.1%}")
            self._print_verbose(f"High confidence matches: {alignment_summary['high_confidence_rate']:.1%}")
            
            # Step 5: Generate notes
            self._print_progress("Generating slide notes...")
            presentation_notes = self.notes_generator.generate_presentation_notes(aligned_slides)
            
            # Step 6: Format and save output
            self._print_progress("Formatting and saving output...")
            
            # Create metadata
            metadata = {
                'presentation_title': os.path.basename(pptx_path),
                'textbook_source': os.path.basename(textbook_path),
                'generated_at': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_slides': len(slides_content),
                'textbook_sections': len(textbook_sections),
                'alignment_rate': f"{alignment_summary['match_rate']:.1%}",
                'processing_time': str(datetime.now() - start_time).split('.')[0]
            }
            
            # Format output
            formatted_content = self.output_formatter.format_notes(
                presentation_notes, 
                output_format, 
                metadata
            )
            
            # Validate output path
            output_validation = self.error_handler.validate_output_path(output_path)
            if not output_validation['valid']:
                return {
                    'success': False,
                    'errors': output_validation['errors'],
                    'warnings': output_validation['warnings']
                }
            
            # Save output
            if self.output_formatter.save_formatted_output(formatted_content, output_path, output_format):
                self._print_verbose(f"Notes saved to: {output_path}")
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': metadata,
                    'alignment_summary': alignment_summary,
                    'errors': [],
                    'warnings': [w['message'] for w in self.error_handler.warnings],
                    'processing_time': str(datetime.now() - start_time).split('.')[0]
                }
            else:
                return {
                    'success': False,
                    'errors': ['Failed to save output file'],
                    'warnings': []
                }
                
        except Exception as e:
            error_info = self.error_handler.handle_notes_generation_error(e)
            return {
                'success': False,
                'errors': [error_info['message']],
                'warnings': [],
                'error_details': error_info
            }
    
    def generate_slide_content(self, pptx_path: str, textbook_path: str, 
                              output_path: str = None) -> Dict[str, Any]:
        """
        Generate content for slides and output as markdown
        
        Args:
            pptx_path: Path to PowerPoint presentation
            textbook_path: Path to textbook file (PDF, DOCX, or TXT)
            output_path: Path for output markdown file (optional)
        
        Returns:
            Dict containing results and metadata
        """
        
        start_time = datetime.now()
        
        try:
            # Step 1: Validate inputs
            self._print_progress("Validating input files...")
            validation_result = self.error_handler.validate_inputs(pptx_path, textbook_path)
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'errors': validation_result['errors'],
                    'warnings': validation_result['warnings']
                }
            
            if validation_result['warnings']:
                for warning in validation_result['warnings']:
                    self.error_handler.add_warning(warning)
            
            # Step 2: Extract slides
            self._print_progress("Extracting slides from PowerPoint...")
            self.slide_extractor = SlideExtractor(pptx_path)
            slides_content = self.slide_extractor.extract_all_slides()
            
            if not slides_content:
                return {
                    'success': False,
                    'errors': ['No slides could be extracted from the PowerPoint file'],
                    'warnings': []
                }
            
            self._print_verbose(f"Extracted {len(slides_content)} slides")
            
            # Step 3: Parse textbook
            self._print_progress("Parsing textbook content...")
            self.textbook_parser = TextbookParser(textbook_path)
            
            if not self.textbook_parser.load_content():
                return {
                    'success': False,
                    'errors': ['Failed to load textbook content'],
                    'warnings': []
                }
            
            textbook_sections = self.textbook_parser.parse_sections()
            self._print_verbose(f"Parsed {len(textbook_sections)} sections from textbook")
            
            # Step 4: Align content
            self._print_progress("Aligning slide content with textbook...")
            aligned_slides = self.content_aligner.batch_align_slides(slides_content, textbook_sections)
            alignment_summary = self.content_aligner.get_alignment_summary(aligned_slides)
            
            self._print_verbose(f"Alignment rate: {alignment_summary['match_rate']:.1%}")
            self._print_verbose(f"High confidence matches: {alignment_summary['high_confidence_rate']:.1%}")
            
            # Step 5: Generate slide content
            self._print_progress("Generating slide content...")
            content_results = self.content_generator.generate_presentation_content(aligned_slides)
            
            self._print_verbose(f"Content generated for {content_results['successful']} out of {content_results['total_slides']} slides")
            
            # Step 6: Format content as markdown and save
            if output_path:
                self._print_progress("Formatting content as markdown...")
                
                # Create metadata for markdown formatting
                markdown_metadata = {
                    'presentation_title': os.path.basename(pptx_path),
                    'textbook_source': os.path.basename(textbook_path),
                    'generated_at': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_slides': len(slides_content),
                    'textbook_sections': len(textbook_sections),
                    'content_generated': content_results['successful'],
                    'generation_method': content_results['generation_method'],
                    'success_rate': f"{content_results['success_rate']:.1%}",
                    'processing_time': str(datetime.now() - start_time).split('.')[0]
                }
                
                # Format as markdown
                markdown_content = self.content_formatter.format_slide_content_to_markdown(
                    content_results, markdown_metadata
                )
                
                # Save markdown file
                save_result = self.content_formatter.save_markdown_content(
                    markdown_content, output_path
                )
                
                if not save_result['success']:
                    return {
                        'success': False,
                        'errors': [save_result.get('message', 'Failed to save markdown content')],
                        'warnings': []
                    }
                
                self._print_verbose(f"Content saved as markdown: {save_result['output_path']}")
                output_path = save_result['output_path']  # Use the actual output path with .md extension
            
            # Create metadata
            metadata = {
                'presentation_title': os.path.basename(pptx_path),
                'textbook_source': os.path.basename(textbook_path),
                'generated_at': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_slides': len(slides_content),
                'textbook_sections': len(textbook_sections),
                'content_generated': content_results['successful'],
                'generation_method': content_results['generation_method'],
                'success_rate': f"{content_results['success_rate']:.1%}",
                'processing_time': str(datetime.now() - start_time).split('.')[0]
            }
            
            return {
                'success': True,
                'output_path': output_path,
                'metadata': metadata,
                'content_results': content_results,
                'alignment_summary': alignment_summary,
                'errors': [],
                'warnings': [w['message'] for w in self.error_handler.warnings],
                'processing_time': str(datetime.now() - start_time).split('.')[0]
            }
                
        except Exception as e:
            error_info = self.error_handler.handle_notes_generation_error(e)
            return {
                'success': False,
                'errors': [error_info['message']],
                'warnings': [],
                'error_details': error_info
            }
    
    def generate_multiple_formats(self, pptx_path: str, textbook_path: str, 
                                 output_dir: str, base_filename: str) -> Dict[str, Any]:
        """Generate notes in multiple formats"""
        
        start_time = datetime.now()
        
        try:
            # Generate notes content (similar to generate_notes but without formatting)
            self._print_progress("Processing content for multiple formats...")
            
            # Validate inputs
            validation_result = self.error_handler.validate_inputs(pptx_path, textbook_path)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'errors': validation_result['errors']
                }
            
            # Extract and process content
            self.slide_extractor = SlideExtractor(pptx_path)
            slides_content = self.slide_extractor.extract_all_slides()
            
            self.textbook_parser = TextbookParser(textbook_path)
            if not self.textbook_parser.load_content():
                return {'success': False, 'errors': ['Failed to load textbook']}
            
            textbook_sections = self.textbook_parser.parse_sections()
            aligned_slides = self.content_aligner.batch_align_slides(slides_content, textbook_sections)
            presentation_notes = self.notes_generator.generate_presentation_notes(aligned_slides)
            
            # Create metadata
            metadata = {
                'presentation_title': os.path.basename(pptx_path),
                'textbook_source': os.path.basename(textbook_path),
                'generated_at': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_slides': len(slides_content),
                'textbook_sections': len(textbook_sections)
            }
            
            # Generate multiple formats
            self._print_progress("Generating multiple format outputs...")
            results = self.output_formatter.create_output_bundle(
                presentation_notes, 
                output_dir, 
                base_filename, 
                metadata
            )
            
            return {
                'success': True,
                'output_files': results,
                'metadata': metadata,
                'processing_time': str(datetime.now() - start_time).split('.')[0]
            }
            
        except Exception as e:
            error_info = self.error_handler.handle_notes_generation_error(e)
            return {
                'success': False,
                'errors': [error_info['message']],
                'error_details': error_info
            }

def main():
    parser = argparse.ArgumentParser(
        description='Generate slide-specific notes or content from PowerPoint presentations using textbook content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate notes
  %(prog)s presentation.pptx textbook.pdf -o notes.md
  %(prog)s slides.pptx chapter.pdf -o output.html -f html -v
  %(prog)s lecture.pptx book.pdf -m output_dir -v
  
  # Generate slide content (max 13 words per bullet) 
  %(prog)s presentation.pptx textbook.pdf --generate-content --content-output slide_content.md
  %(prog)s slides.pptx chapter.pdf --generate-content --content-output content.md --use-grok -v
        """
    )
    
    parser.add_argument('presentation', 
                       help='Path to PowerPoint presentation file (.pptx or .ppt)')
    
    parser.add_argument('textbook', 
                       help='Path to textbook file (.pdf, .docx, or .txt)')
    
    parser.add_argument('-o', '--output', 
                       help='Output file path (required unless using -m)')
    
    parser.add_argument('-f', '--format', 
                       choices=['markdown', 'html', 'json', 'txt', 'csv', 'plaintext'],
                       default='markdown',
                       help='Output format (default: markdown)')
    
    parser.add_argument('-m', '--multiple-formats',
                       metavar='OUTPUT_DIR',
                       help='Generate multiple formats in specified directory')
    
    parser.add_argument('-v', '--verbose', 
                       action='store_true',
                       help='Enable verbose output')
    
    parser.add_argument('--check-deps', 
                       action='store_true',
                       help='Check required dependencies and exit')
    
    parser.add_argument('--use-grok', 
                       action='store_true',
                       help='Use xAI Grok API for generating notes')
    
    parser.add_argument('--grok-api-key',
                       help='xAI Grok API key (or set XAI_API_KEY env var)')
    
    parser.add_argument('--grok-model',
                       default='grok-beta',
                       help='Grok model to use (default: grok-beta)')
    
    parser.add_argument('--write-to-pptx',
                       action='store_true',
                       help='Write generated notes to PowerPoint slide notes sections')
    
    parser.add_argument('--pptx-output',
                       help='Output path for PowerPoint file with notes (if not specified, overwrites original)')
    
    parser.add_argument('--generate-content',
                       action='store_true',
                       help='Generate slide content with max 13 words per bullet point instead of notes')
    
    parser.add_argument('--content-output',
                       help='Output path for markdown file with generated content (required if --generate-content is used)')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = SlideNotesGenerator(
        verbose=args.verbose,
        use_grok=args.use_grok,
        grok_api_key=args.grok_api_key,
        grok_model=args.grok_model
    )
    
    # Check dependencies if requested
    if args.check_deps:
        print("Checking dependencies...")
        deps = generator.error_handler.check_dependencies()
        
        if deps['critical_missing']:
            print("Critical dependencies missing:")
            for pkg in deps['missing_packages']:
                print(f"    - {pkg}")
            print("\nInstall missing packages with: pip install -r requirements.txt")
            sys.exit(1)
        else:
            print("All critical dependencies available")
            if deps['missing_packages']:
                print("Optional dependencies missing:")
                for pkg in deps['missing_packages']:
                    print(f"    - {pkg}")
            sys.exit(0)
    
    # Validate arguments
    if args.generate_content:
        # Content generation mode
        if not args.content_output:
            print("Error: --content-output is required when using --generate-content")
            sys.exit(1)
        if args.output or args.multiple_formats:
            print("Error: Cannot use --output or --multiple-formats with --generate-content")
            sys.exit(1)
    else:
        # Notes generation mode
        if not args.output and not args.multiple_formats:
            print("Error: Either --output or --multiple-formats must be specified")
            sys.exit(1)
        
        if args.output and args.multiple_formats:
            print("Error: Cannot use both --output and --multiple-formats")
            sys.exit(1)
        
        if args.content_output:
            print("Error: --content-output can only be used with --generate-content")
            sys.exit(1)
    
    # Check if input files exist
    if not os.path.exists(args.presentation):
        print(f"Error: Presentation file not found: {args.presentation}")
        sys.exit(1)
    
    if not os.path.exists(args.textbook):
        print(f"Error: Textbook file not found: {args.textbook}")
        sys.exit(1)
    
    if args.generate_content:
        print("Starting slide content generation...")
        print(f"Mode: Slide content generation (max 13 words per bullet)")
    else:
        print("Starting slide notes generation...")
    
    print(f"Presentation: {args.presentation}")
    print(f"Textbook: {args.textbook}")
    if args.use_grok:
        print(f"Using Grok API with model: {args.grok_model}")
    else:
        print("Using built-in generation")
    
    try:
        if args.generate_content:
            # Generate slide content using 6x6 model
            print(f"Content output: {args.content_output}")
            
            result = generator.generate_slide_content(
                args.presentation,
                args.textbook,
                args.content_output
            )
            
            if result['success']:
                print("Successfully generated slide content!")
                print(f"\nStatistics:")
                print(f"    • Total slides: {result['metadata']['total_slides']}")
                print(f"    • Content generated for: {result['metadata']['content_generated']} slides")
                print(f"    • Generation method: {result['metadata']['generation_method']}")
                print(f"    • Success rate: {result['metadata']['success_rate']}")
                print(f"    • Processing time: {result['processing_time']}")
                print(f"    • Output file: {result['output_path']}")
                
                if result['warnings']:
                    print(f"\nWarnings:")
                    for warning in result['warnings']:
                        print(f"    • {warning}")
            else:
                print("Failed to generate slide content:")
                for error in result['errors']:
                    print(f"    • {error}")
                sys.exit(1)
                
        elif args.multiple_formats:
            # Generate multiple formats
            print(f"Output directory: {args.multiple_formats}")
            
            base_filename = os.path.splitext(os.path.basename(args.presentation))[0] + "_notes"
            result = generator.generate_multiple_formats(
                args.presentation, 
                args.textbook, 
                args.multiple_formats, 
                base_filename
            )
            
            if result['success']:
                print("Successfully generated notes in multiple formats!")
                print("\nGenerated files:")
                for format_type, file_path in result['output_files'].items():
                    if not file_path.startswith('Error'):
                        print(f"    {format_type}: {file_path}")
                    else:
                        print(f"    {format_type}: {file_path}")
            else:
                print("Failed to generate notes:")
                for error in result['errors']:
                    print(f"    • {error}")
                sys.exit(1)
                
        else:
            # Generate single format
            print(f"Output: {args.output} ({args.format})")
            
            result = generator.generate_notes(
                args.presentation,
                args.textbook,
                args.output,
                args.format
            )
            
            if result['success']:
                print("Successfully generated slide notes!")
                print(f"\nStatistics:")
                print(f"    • Total slides: {result['metadata']['total_slides']}")
                print(f"    • Textbook sections: {result['metadata']['textbook_sections']}")
                print(f"    • Alignment rate: {result['metadata']['alignment_rate']}")
                print(f"    • Processing time: {result['processing_time']}")
                
                if result['warnings']:
                    print(f"\nWarnings:")
                    for warning in result['warnings']:
                        print(f"    • {warning}")
                
                # Write notes to PowerPoint if requested
                if args.write_to_pptx:
                    print(f"\nWriting notes to PowerPoint file...")
                    
                    # Read the generated notes content
                    try:
                        # Determine actual output path with extension
                        actual_output_path = args.output
                        extension_map = {
                            'markdown': '.md',
                            'html': '.html',
                            'json': '.json',
                            'txt': '.txt',
                            'csv': '.csv',
                            'plaintext': '.txt'
                        }
                        
                        if args.format in extension_map:
                            expected_ext = extension_map[args.format]
                            if not actual_output_path.lower().endswith(expected_ext):
                                actual_output_path += expected_ext
                        
                        with open(actual_output_path, 'r', encoding='utf-8') as f:
                            notes_content = f.read()
                        
                        pptx_result = generator.pptx_notes_writer.write_notes_to_pptx(
                            args.presentation,
                            notes_content,
                            args.pptx_output
                        )
                        
                        if pptx_result['success']:
                            print(f"    • {pptx_result['message']}")
                            print(f"    • PowerPoint file: {pptx_result['output_path']}")
                        else:
                            print(f"    • Failed to write to PowerPoint: {pptx_result['error']}")
                            
                    except Exception as e:
                        print(f"    • Error writing to PowerPoint: {e}")
                        
            else:
                print("Failed to generate notes:")
                for error in result['errors']:
                    print(f"    • {error}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()