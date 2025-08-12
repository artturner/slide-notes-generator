# Slide Content Generation Features

This document describes the new slide content generation functionality that has been added to the slide-notes-generator project.

## Overview

The slide content generation feature creates bullet points for PowerPoint slides following the **6x6 model**:
- Maximum **6 words** per bullet point
- Maximum **6 bullet points** per topic

The feature reads existing PowerPoint presentations, analyzes slide titles and headings, aligns them with textbook content, and generates concise bullet points using either built-in logic or the Grok API.

## New Components

### 1. SlideContentGenerator (`slide_content_generator.py`)
- Main class for generating slide content
- Supports both Grok API and traditional generation methods
- Enforces 6x6 model constraints
- Extracts topics from slide titles and headings

### 2. PowerPointContentWriter (`pptx_content_writer.py`)
- Writes generated content back to PowerPoint slides
- Finds appropriate placeholders or creates new text boxes
- Handles slide layout conflicts
- Creates summary slides

### 3. Updated Main Application (`main.py`)
- Added new command-line arguments for content generation
- Integrated content generation workflow
- Enhanced validation and error handling

## Command Line Usage

### Basic Content Generation
```bash
python main.py presentation.pptx textbook.pdf --generate-content --content-output output_with_content.pptx
```

### With Grok API
```bash
python main.py presentation.pptx textbook.pdf --generate-content --content-output output.pptx --use-grok --grok-api-key YOUR_API_KEY
```

### Verbose Output
```bash
python main.py presentation.pptx textbook.pdf --generate-content --content-output output.pptx --use-grok -v
```

## New Command Line Arguments

- `--generate-content`: Enable slide content generation mode (instead of notes generation)
- `--content-output PATH`: Output path for PowerPoint file with generated content (required with `--generate-content`)

## How It Works

### 1. Input Processing
- Reads PowerPoint presentation and extracts slide information
- Identifies slide titles and headings
- Parses textbook content into sections

### 2. Content Alignment
- Uses the existing content alignment system to match slides with relevant textbook sections
- Considers slide titles, headings, and any existing content

### 3. Topic Identification
- Primary topic: Slide title
- Extended topic: Slide title + first heading (if present)
- Example: "Machine Learning" or "Machine Learning - Supervised Learning"

### 4. Content Generation

#### Traditional Method
- Extracts key sentences from aligned textbook sections
- Creates bullet points from key phrases
- Applies 6x6 model constraints

#### Grok API Method
- Sends specialized prompts to Grok API
- Requests bullet points following 6x6 format
- Parses and validates generated content

### 5. Content Writing
- Finds suitable placeholders in slides
- Adds bullet points to existing content areas
- Creates new text boxes when necessary
- Avoids conflicts with existing slide elements

## 6x6 Model Implementation

### Word Count Enforcement
- Each bullet point is limited to 6 words maximum
- Longer phrases are automatically truncated
- Word counting excludes common articles and connectors

### Bullet Point Limits
- Maximum 6 bullet points per slide topic
- Prioritizes most relevant content from textbook
- Ensures concise, focused slide content

## Example Output

For a slide titled "Machine Learning Basics", the system might generate:
- Define machine learning concepts clearly
- Explore supervised learning algorithm types
- Examine unsupervised pattern recognition methods
- Analyze reinforcement learning applications
- Consider deep learning neural networks
- Review practical implementation examples

## Integration with Existing Features

### Textbook Parsing
- Uses existing `TextbookParser` for content extraction
- Leverages section identification and key term extraction

### Content Alignment
- Utilizes existing `ContentAligner` for matching slides to textbook sections
- Benefits from similarity scoring and keyword matching

### Grok Integration
- Extends existing Grok client with content-specific prompts
- Maintains API key management and error handling

## Error Handling

### Validation
- Checks for required arguments in content generation mode
- Validates input files exist and are accessible
- Ensures output paths are writable

### Graceful Fallbacks
- Falls back to traditional generation if Grok API fails
- Handles missing textbook content gracefully
- Creates generic bullet points when content alignment fails

### Progress Tracking
- Provides verbose output for debugging
- Reports success rates and processing statistics
- Shows alignment quality metrics

## Testing

Use the included test script to verify functionality:

```bash
python test_content_generation.py
```

This script will:
- Test basic content generation without Grok
- Test direct component functionality
- Provide detailed output for debugging

## Limitations and Considerations

### 6x6 Model Constraints
- Very short bullet points may lack detail
- Complex concepts may require multiple bullets
- Educational effectiveness depends on topic complexity

### PowerPoint Compatibility
- Works best with standard slide layouts
- May have issues with heavily customized templates
- Text box placement uses heuristic algorithms

### Content Quality
- Quality depends on textbook content alignment
- Grok API provides more contextual understanding
- Traditional method relies on keyword matching

## Future Enhancements

### Potential Improvements
- Support for custom bullet point limits
- Advanced slide layout detection
- Integration with presentation design principles
- Batch processing for multiple presentations
- Content preview before writing to slides

### Educational Features
- Learning objective alignment
- Bloom's taxonomy integration
- Student reading level adaptation
- Interactive content suggestions