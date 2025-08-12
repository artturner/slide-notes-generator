# Textbook Content Generation Guide

This guide shows how to use the new AI-enhanced textbook content generation system that creates bullet points from PDF chapters based on section headings.

## Overview

The system extracts text from PDF textbook chapters, identifies sections based on provided headings, and generates concise bullet points (10 words or fewer) for each section. It prioritizes numerical data, dates, program names, and key facts.

## Features

- ✅ **PDF Text Extraction**: Handles encoding issues and extracts clean text
- ✅ **Heading-Based Section Parsing**: Finds sections in text based on provided headings
- ✅ **Multi-AI Support**: Uses OpenAI (recommended), Gemini, or Grok for high-quality bullets
- ✅ **Fallback Generation**: Rule-based approach when AI is unavailable
- ✅ **Word Count Compliance**: Ensures bullets are 10 words or fewer
- ✅ **Data Preservation**: Prioritizes numerical data, dates (especially post-2023), laws, programs
- ✅ **Markdown Output**: Clean, formatted output ready for use

## Quick Start

### Method 1: Using OpenAI (Recommended)

```bash
# Set up OpenAI API key
export OPENAI_API_KEY="your-openai-api-key-here"

# Generate content with GPT-4o-mini (cost-effective)
python ai_textbook_content_generator.py "chapter.pdf" "headings.txt" "output.md" --use-openai

# Or use GPT-4o for higher quality (more expensive)
python ai_textbook_content_generator.py "chapter.pdf" "headings.txt" "output.md" --use-openai --openai-model gpt-4o
```

### Method 2: Using Gemini AI

```bash
# Set up Gemini API key
export GOOGLE_API_KEY="your-gemini-api-key-here"

# Generate content with Gemini 2.5 Flash
python ai_textbook_content_generator.py "chapter.pdf" "headings.txt" "output.md" --use-gemini
```

### Method 3: Using Grok AI

```bash
# Set up Grok API key  
export XAI_API_KEY="your-grok-api-key-here"

# Generate content
python ai_textbook_content_generator.py "chapter.pdf" "headings.txt" "output.md" --use-grok
```

### Method 4: Fallback (No API Required)

```bash
# Generate with rule-based approach
python ai_textbook_content_generator.py "chapter.pdf" "headings.txt" "output.md"
```

## File Setup

### 1. Create Headings File

Create a text file with one heading per line in the order they appear in the chapter:

```
Making Public Policy in Texas
Models of Policy Making
The Politics of Implementation
Education
Health and Human Services
Business and Economic Development
The Environment
Immigration
```

### 2. Prepare PDF

Ensure your PDF is readable and contains the text content (not just images).

## Example Usage

```bash
# Using the provided test files with OpenAI
python ai_textbook_content_generator.py \
  "Brown_Texas_Chapter12.pdf" \
  "chapter12_headings_accurate.txt" \
  "chapter12_output.md" \
  --use-openai
```

## Expected Output

The system generates a markdown file with:

- Metadata (source files, generation method, timestamps)
- Section headings in bold
- 3-6 bullet points per section (10 words max each)
- Preserved numerical data and important facts

Example output:
```markdown
## **Making Public Policy in Texas**

• State government spends 38 percent of budget on education
• Health services receive 31 percent of state funding annually  
• Business development allocated 15 percent of total budget
• Public safety represents 6 percent of state expenditures
• Texas policy affects business profitability and resident safety

## **Models of Policy Making**

• Scholars use conceptual maps to explain policy processes
• No single model sufficiently explains policy making complexity
• Group model focuses on involved stakeholders and interests
• Multiple models provide complete policy system understanding
```

## Command Line Options

```
positional arguments:
  pdf_path              Path to PDF textbook chapter
  headings_path         Path to text file containing headings (one per line)
  output_path           Path for output markdown file

optional arguments:
  --use-openai         Use OpenAI for bullet generation (recommended)
  --openai-api-key     OpenAI API key (or set OPENAI_API_KEY env var)
  --openai-model       OpenAI model to use (default: gpt-4o-mini)
  --use-gemini         Use Gemini AI for bullet generation
  --gemini-api-key     Google AI API key (or set GOOGLE_API_KEY env var)
  --gemini-model       Gemini model to use (default: gemini-1.5-flash)
  --use-grok           Use Grok AI for bullet generation
  --grok-api-key       Grok API key (or set XAI_API_KEY env var)
  --grok-model         Grok model to use (default: grok-beta)
```

## API Key Setup

### OpenAI (Recommended)
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create an API key
3. Set environment variable: `export OPENAI_API_KEY="your-key"`
4. Install package: `pip install openai`

### Gemini (Google AI)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create an API key
3. Set environment variable: `export GOOGLE_API_KEY="your-key"`
4. Install package: `pip install google-generativeai`

### Grok (xAI)
1. Get API key from [xAI Console](https://console.x.ai)
2. Set environment variable: `export XAI_API_KEY="your-key"`

## Tips for Best Results

1. **Heading Accuracy**: Ensure headings in your text file match those in the PDF exactly
2. **Use AI**: OpenAI/Grok generally produce higher quality bullets than rule-based generation
3. **AI Provider Choice**: OpenAI is most reliable, Grok handles edge cases well, Gemini may hit safety filters
4. **Section Length**: Longer sections with more content produce better bullets
5. **PDF Quality**: Clean, text-based PDFs work better than scanned documents
6. **Full Content**: Recent improvements send complete section content (no 3000-character limit)

## Troubleshooting

### "Heading not found in text"
- Check that headings exactly match PDF text
- Try partial matches or key words from headings
- Use the `examine_pdf_content.py` script to see PDF structure

### Poor Bullet Quality
- Use AI (OpenAI/Grok recommended) instead of fallback method
- Try different AI providers if one produces poor results
- Check that sections have substantial content
- Verify PDF text extraction is clean

### API Errors
- Verify API keys are set correctly
- Check API quotas and rate limits
- Ensure network connectivity

## Integration with Existing System

This system can be integrated with your existing slide notes generator by:
1. Using the extracted sections as input to `slide_content_generator.py`
2. Feeding generated bullets to the PPTX content writer
3. Combining with Grok integration for consistent formatting

The `ai_textbook_content_generator.py` provides a foundation for enhanced content generation that you can extend or modify as needed.