# Document Processing Tools

This directory contains utilities and sample code for processing various document formats for use with Pyunto Intelligence.

## Overview

The document processing tools help you prepare text-based content for analysis by Pyunto Intelligence. These tools allow you to:

- Extract text from PDF documents
- Convert PDF documents to images
- Merge multiple documents into a single file for analysis
- Process and transform document content

## Available Tools

### PDF Text Extraction

The [pdf-extraction](./pdf-extraction) directory contains tools for extracting text from PDF documents:

- Python-based PDF text extraction using PDFMiner
- Support for multiple languages including Japanese
- Batch processing capabilities
- Options for text formatting and output

### Document Conversion

The [conversion](./conversion) directory provides tools for converting between document formats:

- PDF to image conversion
- Document merging utilities
- Format transformation tools

### Word Document Processing

The [word-extraction](./word-extraction) directory includes utilities for processing Microsoft Word documents:

- Text extraction from DOCX files
- Document structure analysis
- Content formatting tools

## Requirements

Different tools in this directory have different dependencies. Common requirements include:

- Python 3.6+
- PDFMiner.six
- pdf2image (requires Poppler)
- Pillow (Python Imaging Library)
- python-docx

## Usage Examples

### Basic PDF Text Extraction

```python
from pyunto_tools.document_processing.pdf_extraction import PDFTextExtractor

# Initialize the extractor
extractor = PDFTextExtractor()

# Extract text from a PDF file
text = extractor.extract_text_from_pdf("document.pdf")

# Save the extracted text
extractor.save_text(text, "document.txt")
```

### Document Merging for Analysis

```python
from pyunto_tools.document_processing.conversion import DocumentMerger

# Initialize the merger
merger = DocumentMerger()

# Merge documents with section headers
merged_text = merger.merge_documents(
    [
        {"path": "job_description.pdf", "title": "JOB DESCRIPTION"},
        {"path": "resume.pdf", "title": "RESUME"}
    ],
    output_path="combined.txt"
)

# The merged document can now be processed by Pyunto Intelligence
```

### PDF to Image Conversion

```python
from pyunto_tools.document_processing.conversion import PDFToImageConverter

# Initialize the converter
converter = PDFToImageConverter()

# Convert PDF to a single combined image
image_path = converter.convert_to_single_image(
    pdf_path="document.pdf",
    output_path="document.png",
    dpi=300
)
```

## Integration with Pyunto Intelligence

These document processing tools are designed to work seamlessly with Pyunto Intelligence APIs. For example:

```python
import base64
import requests
from pyunto_tools.document_processing.pdf_extraction import PDFTextExtractor

# Extract text from document
extractor = PDFTextExtractor()
text = extractor.extract_text_from_pdf("document.pdf")

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

## License

These tools are licensed under the Apache License 2.0 - see the [LICENSE](../LICENSE) file for details.
