# Word Document Text Extraction Tool

This tool allows you to extract text from Microsoft Word documents (DOCX) for analysis with Pyunto Intelligence.

## Features

- Extract text from DOCX documents
- Preserve document structure including headings, paragraphs, and lists
- Support for tables and other complex content
- Extract document metadata
- Batch processing capabilities
- Integration with Pyunto Intelligence API

## Requirements

- Python 3.6+
- python-docx
- Optional: docx2txt (for additional extraction capabilities)

## Installation

To use this tool, you need to install the required Python packages:

```bash
pip install python-docx
```

For additional capabilities:

```bash
pip install docx2txt
```

## Usage

### Basic Text Extraction

```python
from word_text_extractor import WordTextExtractor

# Initialize the extractor
extractor = WordTextExtractor()

# Extract text from a Word document
text = extractor.extract_text_from_docx("document.docx")

# Save the extracted text to a file
extractor.save_text(text, "document.txt")
```

### Command-Line Interface

The tool can be used directly from the command line:

```bash
# Extract text from a Word document
python word_text_extractor.py document.docx -o output.txt

# Process multiple Word documents
python word_text_extractor.py --batch folder_with_docx/ --output-dir extracted_texts/
```

### Working with Document Metadata

```python
from word_text_extractor import WordTextExtractor

# Initialize the extractor
extractor = WordTextExtractor()

# Extract text and metadata
text, metadata = extractor.extract_text_and_metadata("document.docx")

# Print document metadata
print(f"Title: {metadata.get('title')}")
print(f"Author: {metadata.get('author')}")
print(f"Created: {metadata.get('created')}")
print(f"Modified: {metadata.get('modified')}")
```

## Integration with Pyunto Intelligence

```python
import base64
import requests
from word_text_extractor import WordTextExtractor

# Extract text from Word document
extractor = WordTextExtractor()
text = extractor.extract_text_from_docx("document.docx")

# Send to Pyunto Intelligence
api_key = "YOUR_API_KEY"
api_url = "https://a.pyunto.com/api/i/v1"

response = requests.post(
    api_url,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "assistantId": "YOUR_ASSISTANT_ID",
        "type": "text",
        "data": base64.b64encode(text.encode('utf-8')).decode('utf-8'),
        "mimeType": "text/plain"
    }
)

analysis_result = response.json()
print(analysis_result)
```

## Advanced Usage

### Structured Content Extraction

```python
from word_text_extractor import WordTextExtractor

# Initialize the extractor
extractor = WordTextExtractor()

# Extract structured content (paragraphs, headings, lists)
structured_content = extractor.extract_structured_content("document.docx")

# Work with specific content types
headings = structured_content.get('headings', [])
paragraphs = structured_content.get('paragraphs', [])
lists = structured_content.get('lists', [])

# Print all headings
for heading in headings:
    print(f"Heading (Level {heading['level']}): {heading['text']}")
```

### Table Extraction

```python
from word_text_extractor import WordTextExtractor

# Initialize the extractor
extractor = WordTextExtractor()

# Extract tables from the document
tables = extractor.extract_tables("document_with_tables.docx")

# Process each table
for i, table in enumerate(tables):
    print(f"Table {i+1}:")
    for row in table:
        print("| " + " | ".join(row) + " |")
```

## Handling Different Document Types

The extractor is designed to work with modern DOCX files, but can also handle:

- Legacy DOC files (requires additional setup)
- DOCM files (macro-enabled documents)
- RTF files (with limitations)

For legacy DOC files, you may need to install additional packages:

```bash
pip install pywin32  # Windows only
```

## Limitations

- Some complex formatting may be lost during extraction
- Embedded images are not processed (only their alt text if available)
- Document protection or passwords may prevent extraction
- Performance may degrade with very large documents containing complex formatting
- For documents with complex layouts, consider using the PDF conversion tools instead

## Error Handling

The tool includes robust error handling:

- Graceful handling of corrupt documents
- Fallback methods if primary extraction fails
- Detailed logging for troubleshooting
- Batch processing continues even if individual files fail

## Integration with Other Tools

This tool works seamlessly with other Pyunto Intelligence tools:

- Use with `DocumentMerger` to combine Word documents with other document types
- Convert Word documents to PDFs first if you need to preserve exact formatting
- Chain with other text processing tools in a pipeline

## Examples

### Full Document Processing Pipeline

```python
from word_text_extractor import WordTextExtractor
from document_merger import DocumentMerger

# Extract text from Word documents
word_extractor = WordTextExtractor()
job_text = word_extractor.extract_text_from_docx("job_description.docx")
word_extractor.save_text(job_text, "job_description.txt")

# Load PDF resume
merger = DocumentMerger()

# Merge documents for analysis
merged_text = merger.merge_documents([
    {"path": "job_description.txt", "title": "JOB DESCRIPTION"},
    {"path": "resume.pdf", "title": "RESUME"}
])

# Save merged document
with open("job_application.txt", "w", encoding="utf-8") as f:
    f.write(merged_text)
```

## License

This tool is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.
