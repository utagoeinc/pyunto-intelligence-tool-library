# Document Conversion Tools

This directory contains utilities for converting between document formats for use with Pyunto Intelligence.

## Features

- Convert PDF documents to images
- Merge multiple documents for analysis
- Transform document content for specific analysis tasks
- Batch processing capabilities
- Integration with Pyunto Intelligence API

## Available Tools

### PDF to Image Converter

The `PDFToImageConverter` tool converts PDF documents to image formats:

- Convert multi-page PDFs to single combined image
- Convert PDFs to individual page images
- Configure resolution, format, and quality

### Document Merger

The `DocumentMerger` tool combines multiple documents into a single file:

- Support for different input formats (PDF, TXT)
- Customizable section headers and separators
- Structured formatting for optimal analysis
- Special use cases like resume-job matching

## Requirements

- Python 3.6+
- pdf2image (requires Poppler installation)
- Pillow (Python Imaging Library)
- PDFMiner.six (for PDF text extraction)

## Installation

To use these tools, install the required dependencies:

```bash
pip install pdf2image Pillow pdfminer.six
```

Note: pdf2image requires Poppler to be installed on your system:

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

**macOS**:
```bash
brew install poppler
```

**Windows**:
Download [Poppler](http://blog.alivate.com.au/poppler-windows/) and add it to your PATH.

## Usage Examples

### PDF to Image Conversion

```python
from pdf_to_image import PDFToImageConverter

# Initialize the converter
converter = PDFToImageConverter()

# Convert PDF to a single combined image
image_path = converter.convert_to_single_image(
    pdf_path="document.pdf",
    output_path="document.png",
    dpi=300
)

# Convert PDF to individual page images
image_paths = converter.convert_to_individual_images(
    pdf_path="document.pdf",
    output_dir="pages",
    dpi=300,
    format="JPEG"
)
```

### Document Merging

```python
from document_merger import DocumentMerger

# Initialize the merger
merger = DocumentMerger()

# Merge multiple documents with section headers
merged_text = merger.merge_documents(
    [
        {"path": "job_description.pdf", "title": "JOB DESCRIPTION"},
        {"path": "resume.pdf", "title": "RESUME"}
    ],
    output_path="combined.txt"
)

# For resume-job matching (specialized use case)
merged_text = merger.merge_job_and_cv(
    job_file="job_description.pdf",
    cv_file="resume.pdf",
    output_file="job_application.txt"
)
```

### Command-Line Interface

These tools can be used directly from the command line:

**PDF to Image:**
```bash
# Convert PDF to a single image
python pdf_to_image.py document.pdf -o document.png

# Convert with specific settings
python pdf_to_image.py document.pdf --dpi 300 --format PNG
```

**Document Merger:**
```bash
# Merge documents
python document_merger.py --files job.pdf resume.pdf --titles "JOB" "RESUME" -o combined.txt

# Resume-job matching
python document_merger.py --job job.pdf --cv resume.pdf -o application.txt
```

## Integration with Pyunto Intelligence

These tools are designed to work seamlessly with Pyunto Intelligence APIs:

```python
import base64
import requests
from document_merger import DocumentMerger

# Merge documents for analysis
merger = DocumentMerger()
text = merger.merge_job_and_cv("job.pdf", "resume.pdf", "application.txt")

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

These tools are licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.
