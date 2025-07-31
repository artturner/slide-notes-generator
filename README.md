# Slide Notes Generator

An automated tool that generates comprehensive, content-aligned notes for PowerPoint presentations using associated textbook chapters—without manual prompting for each slide.

## Features

- **Automatic Slide Extraction**: Extracts content, titles, bullet points, and speaker notes from PowerPoint presentations
- **Textbook Content Parsing**: Supports PDF, DOCX, and TXT textbook formats with intelligent section detection
- **Content Alignment**: Uses TF-IDF vectorization and cosine similarity to match slides with relevant textbook sections
- **Intelligent Notes Generation**: Creates structured notes with:
  - Content overviews
  - Key points and definitions  
  - Related textbook references
  - Study questions
  - Additional context
- **Multiple Output Formats**: Export to Markdown, HTML, JSON, TXT, or CSV
- **Comprehensive Error Handling**: Robust validation and error reporting
- **Progress Tracking**: Verbose mode with detailed progress information

## Installation

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

### Required Dependencies
- `python-pptx==0.6.23` - PowerPoint file processing
- `PyPDF2==3.0.1` - PDF parsing
- `scikit-learn==1.3.0` - Content alignment algorithms
- `numpy==1.24.3` - Numerical computations
- `nltk==3.8.1` - Natural language processing

### Optional Dependencies
- `openai==1.12.0` - AI-enhanced note generation (future feature)
- `sentence-transformers==2.2.2` - Advanced semantic matching
- `python-docx==0.8.11` - Enhanced DOCX support

## Quick Start

### Basic Usage

Generate notes in Markdown format:
```bash
python main.py presentation.pptx textbook.pdf -o notes.md -v
```

### Multiple Formats

Generate notes in all supported formats:
```bash
python main.py presentation.pptx textbook.pdf -m output_directory -v
```

### HTML Output

Generate formatted HTML notes:
```bash
python main.py presentation.pptx textbook.pdf -o notes.html -f html -v
```

## Command Line Options

```
usage: main.py [-h] [-o OUTPUT] [-f {markdown,html,json,txt,csv}] 
               [-m OUTPUT_DIR] [-v] [--check-deps]
               presentation textbook

positional arguments:
  presentation          Path to PowerPoint presentation file (.pptx or .ppt)
  textbook             Path to textbook file (.pdf, .docx, or .txt)

optional arguments:
  -h, --help           show this help message and exit
  -o OUTPUT, --output OUTPUT
                       Output file path (required unless using -m)
  -f {markdown,html,json,txt,csv}, --format {markdown,html,json,txt,csv}
                       Output format (default: markdown)
  -m OUTPUT_DIR, --multiple-formats OUTPUT_DIR
                       Generate multiple formats in specified directory
  -v, --verbose        Enable verbose output
  --check-deps         Check required dependencies and exit
```

## How It Works

### 1. Slide Extraction
- Parses PowerPoint files to extract slide content
- Identifies titles, text content, bullet points, and speaker notes
- Handles images and other media elements
- Maintains slide order and numbering

### 2. Textbook Parsing
- Supports multiple formats (PDF, DOCX, TXT)
- Automatically detects section headers and structure
- Extracts key terms and concepts
- Creates searchable content sections

### 3. Content Alignment
- Uses TF-IDF vectorization for semantic analysis
- Calculates cosine similarity between slides and textbook sections
- Provides confidence scores for matches
- Falls back to keyword matching when needed

### 4. Notes Generation
- Creates structured notes for each slide
- Includes relevant textbook content
- Generates study questions automatically
- Extracts definitions and key concepts
- Maintains consistent formatting

### 5. Output Formatting
- Supports multiple export formats
- Includes metadata and generation statistics
- Creates styled HTML with CSS
- Structured JSON for programmatic use
- CSV format for spreadsheet analysis

## Output Structure

### Markdown/HTML Output
```markdown
# Presentation Notes
**Generated on:** [timestamp]

## Table of Contents
- [Slide 1: Introduction](#slide-1)
- [Slide 2: Key Concepts](#slide-2)
...

## Slide 1: Introduction

### Content Overview
- Main slide content and bullet points

### Key Points
• Important concepts from the slide

### Related Textbook Content
**Section:** [Matching textbook section]
[Relevant excerpt from textbook]

### Key Definitions
**Term**: Definition from textbook or slide

### Study Questions
1. What are the main concepts covered in this slide?
2. How does this relate to the broader topic?

### Additional Notes
[Speaker notes from PowerPoint]

---
```

### JSON Output
```json
{
  "metadata": {
    "presentation_title": "presentation.pptx",
    "textbook_source": "textbook.pdf",
    "generated_at": "2024-01-15 14:30:00",
    "total_slides": 25,
    "textbook_sections": 12,
    "alignment_rate": "85%"
  },
  "content": [
    {
      "slide_number": 1,
      "title": "Introduction",
      "content_overview": "...",
      "key_points": ["..."],
      "textbook_reference": "...",
      "definitions": [...],
      "study_questions": [...]
    }
  ]
}
```

## Error Handling

The tool includes comprehensive error handling:

- **Input Validation**: Checks file existence, permissions, and formats
- **Processing Errors**: Handles parsing and alignment failures gracefully
- **Output Validation**: Ensures output directories and permissions
- **Dependency Checking**: Verifies required packages are installed
- **Detailed Logging**: Creates error logs for troubleshooting

Check dependencies before running:
```bash
python main.py --check-deps
```

## Performance Considerations

- **Large Files**: Files over 50MB may take longer to process
- **Memory Usage**: Large textbooks are processed in chunks
- **Processing Time**: Typical processing time is 1-3 minutes for standard presentations
- **Alignment Quality**: Results improve with well-structured textbooks and clear slide content

## Troubleshooting

### Common Issues

1. **"No slides could be extracted"**
   - Ensure PowerPoint file is not corrupted
   - Check file permissions
   - Try re-saving the PowerPoint file

2. **"Failed to load textbook content"**
   - Verify textbook file format (PDF, DOCX, TXT)
   - Check for password-protected files
   - Ensure file is not corrupted

3. **Low alignment rates**
   - Ensure textbook content is relevant to slides
   - Check that textbook has clear section structure
   - Try different textbook formats if available

4. **Missing dependencies**
   - Run `python main.py --check-deps` to identify missing packages
   - Install missing packages: `pip install -r requirements.txt`

### Error Logs

Error logs are automatically saved to `slide_notes_errors.log` with detailed information about any issues encountered.

## Examples

### Academic Lecture
```bash
# Generate notes for a biology lecture using the course textbook
python main.py biology_lecture.pptx biology_textbook.pdf -o lecture_notes.md -v
```

### Business Presentation
```bash
# Create HTML notes for a business presentation with multiple formats
python main.py quarterly_review.pptx business_strategy.pdf -m output_notes -v
```

### Research Presentation
```bash
# Generate structured JSON output for a research presentation
python main.py research_findings.pptx research_paper.pdf -o findings.json -f json -v
```

## Limitations

- **Language Support**: Currently optimized for English content
- **Image Content**: Images in slides are noted but not analyzed for content
- **Handwriting**: Handwritten content in PDFs may not be extracted
- **Protected Files**: Password-protected files are not supported
- **Presentation Animations**: Animation content is not captured

## Future Enhancements

- AI-powered content enhancement using OpenAI API
- Support for additional file formats (Google Slides, Keynote)
- Multi-language support
- Image content analysis using computer vision
- Interactive web interface
- Batch processing for multiple presentations

## License

This project is available for educational and research purposes. See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## Support

For support, please create an issue in the project repository with:
- Detailed description of the problem
- Sample files (if possible)
- Error logs
- System information