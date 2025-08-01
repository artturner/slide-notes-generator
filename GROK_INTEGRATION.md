# Grok API Integration for Slide Notes Generator

## Overview

The Slide Notes Generator now supports integration with xAI's Grok API to generate more sophisticated and detailed notes using AI. Your custom prompt has been integrated into the system.

## Features

- **Custom Grok Prompt**: Uses your specific formatting guidelines for educational slide notes
- **Structured Output**: Generates notes with main sections (I, II, etc.) and sub-points (A, B) with proper indentation
- **Learning Objective Alignment**: Automatically infers or accepts learning objectives
- **Fallback Support**: Automatically falls back to built-in generation if Grok API fails
- **Multiple Models**: Supports different Grok models (grok-beta, etc.)

## Setup

### 1. Get xAI API Key

1. Visit [console.x.ai](https://console.x.ai)
2. Create an account and generate an API key
3. Set the environment variable:
   ```bash
   set XAI_API_KEY=your_api_key_here
   ```

### 2. Install Dependencies

The existing requirements.txt already includes the OpenAI library which is compatible with xAI's API.

## Usage

### Basic Usage with Grok

```bash
python main.py "presentation.pptx" "textbook.pdf" -o "notes.md" --use-grok
```

### Advanced Usage

```bash
# Specify API key directly
python main.py "slides.pptx" "book.pdf" -o "notes.md" --use-grok --grok-api-key "your-key"

# Use different model
python main.py "slides.pptx" "book.pdf" -o "notes.md" --use-grok --grok-model "grok-2"

# Verbose output with Grok
python main.py "slides.pptx" "book.pdf" -o "notes.md" --use-grok -v
```

### Environment Variables

Set your API key as an environment variable:
```bash
# Windows
set XAI_API_KEY=your_api_key_here

# Linux/Mac
export XAI_API_KEY=your_api_key_here
```

## Your Custom Prompt Integration

The system now uses your exact prompt template:

> "You are Grok 3 built by xAI, designed to create detailed notes for educational slides based on the content provided. I will supply a chapter manuscript for context and then paste individual slide content to request notes. For each slide, please generate notes with the following guidelines:
> - Base the notes solely on the slide content I provide, without referencing the manuscript or any external sources.
> - Align the notes with the appropriate learning objective, which I may specify or which you can infer from the context (e.g.,6-1, 6.2, etc., for Chapter 6).
> - Structure the notes with a main section (I, II, etc.) for each bullet point on the slide, each containing two detailed sub-points (A and B) that expand directly on that bullet point's content.
> - Use an indented style for sub-points, with each sub-point (A and B) indented using 2 spaces for readability and clarity in the markdown output.
> - Ensure the notes are mid-length, providing concise yet thorough expansions that elaborate on the slide's ideas."

## Output Format

When using Grok, the generated notes will:

1. **Follow your exact formatting**: Main sections (I, II, etc.) with sub-points (A, B)
2. **Include proper indentation**: 2-space indentation for sub-points
3. **Maintain learning objectives**: Automatically detected or specified
4. **Provide detailed expansions**: Mid-length, thorough but concise
5. **Include processing metadata**: Shows which model was used and processing time

## Comparison: Traditional vs Grok

### Traditional Generation
- Rule-based content extraction
- Template-driven formatting
- Fast processing
- Consistent but basic output

### Grok Generation
- AI-powered content understanding
- Your custom prompt-driven formatting
- Contextual and detailed expansions
- More sophisticated but slower

## Error Handling

The system includes robust error handling:

- **API Connection Failures**: Automatically falls back to traditional generation
- **Rate Limiting**: Includes delays between requests
- **Invalid API Keys**: Shows clear error messages
- **Model Errors**: Graceful degradation with fallback

## Testing

Test the integration without a real API key:
```bash
python main.py "slides.pptx" "book.pdf" -o "notes.md" --use-grok --grok-api-key "test-key"
```

The system will show the connection failure and fall back to traditional generation, demonstrating the robustness of the integration.

## Cost Considerations

- Grok API calls have usage costs
- Processing time is longer than traditional generation
- Consider using traditional mode for bulk processing
- Use Grok mode for high-quality, detailed notes

## Troubleshooting

### Common Issues

1. **"API key not found"**: Set the XAI_API_KEY environment variable
2. **"Connection failed"**: Check your internet connection and API key validity
3. **"Rate limited"**: Wait and retry, or increase delays in grok_client.py
4. **"Model not found"**: Use supported models like "grok-beta"

### Getting Help

- Check the xAI documentation: [docs.x.ai](https://docs.x.ai)
- Verify API key at: [console.x.ai](https://console.x.ai)
- Review error messages in verbose mode (`-v` flag)