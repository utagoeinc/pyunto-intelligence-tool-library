# PDF Text Extraction Tool

This tool allows you to extract text from PDF documents for analysis with Pyunto Intelligence.

## Features

- Extract text from PDF documents, including non-English content (Japanese, Chinese, etc.)
- Maintain document structure where possible
- Configurable extraction parameters
- Support for batch processing multiple documents
- Integration with Pyunto Intelligence API

## Requirements

- Python 3.6+
- PDFMiner.six
- Optional: Poppler (for fallback extraction method)

## Installation

To use this tool, you need to install the required Python packages:

```bash
pip install pdfminer.six
```

For additional capabilities (OCR, fallback methods), you may want to install these optional dependencies:

```bash
pip install pdf2image pytesseract pillow
```

Note: OCR functionality requires Tesseract to be installed on your system. For PDF2Image, you'll need Poppler.

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr
```

**macOS**:
```bash
brew install poppler tesseract
```

**Windows**:
Download [Poppler](http://blog.alivate.com.au/poppler-windows/) and [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add them to your PATH.

## Usage

### Basic Text Extraction

```python
from pdf_text_extractor import PDFTextExtractor

# Initialize the extractor
extractor = PDFTextExtractor()

# Extract text from a PDF file
text = extractor.extract_text_from_pdf("document.pdf")

# Save the extracted text to a file
extractor.save_text(text, "document.txt")
```

### Command-Line Interface

The tool can be used directly from the command line:

```bash
# Extract text from a PDF
python pdf_text_extractor.py document.pdf -o output.txt

# Process multiple PDFs
python pdf_text_extractor.py --batch folder_with_pdfs/ --output-dir extracted_texts/
```

### Customizing Extraction Parameters

```python
from pdf_text_extractor import PDFTextExtractor

# Initialize with custom layout parameters
extractor = PDFTextExtractor(
    line_margin=0.3,
    char_margin=1.5,
    word_margin=0.2,
    detect_vertical=True
)

# Extract text with custom parameters
text = extractor.extract_text_from_pdf("document.pdf")
```

## Integration with Pyunto Intelligence

```python
import base64
import requests
from pdf_text_extractor import PDFTextExtractor

# Extract text from PDF
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

## Handling Different Languages

The extractor is configured to handle multiple languages, including Japanese and other non-Latin scripts. For best results with languages like Japanese, ensure your PDFs are properly encoded and use the `detect_vertical` option if needed.

```python
# For Japanese documents with potential vertical text
extractor = PDFTextExtractor(detect_vertical=True)
text = extractor.extract_text_from_pdf("japanese_document.pdf")
```

## Error Handling

The tool includes robust error handling with fallback methods:

1. Primary extraction using PDFMiner's high-level API
2. Fallback to PDFMiner's low-level API if high-level fails
3. Optional OCR-based extraction for scanned documents

## Limitations

- Text extraction quality depends on the PDF structure
- Some formatting and layout information may be lost
- Scanned PDFs require OCR for text extraction (not included in the basic version)
- Password-protected PDFs cannot be processed without the password

## License

This tool is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.
