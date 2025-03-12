#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF Text Extraction Tool for Pyunto Intelligence

This module provides functions to extract text from PDF documents for
analysis with Pyunto Intelligence.
"""

import os
import sys
import argparse
import logging
import glob
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
except ImportError:
    logger.error("PDFMiner.six is required. Install it with 'pip install pdfminer.six'")
    sys.exit(1)

class PDFTextExtractor:
    """PDF text extraction tool for Pyunto Intelligence."""
    
    def __init__(self, 
                line_margin: float = 0.5,
                char_margin: float = 2.0,
                word_margin: float = 0.1,
                boxes_flow: float = 0.5,
                detect_vertical: bool = True,
                codec: str = 'utf-8'):
        """
        Initialize the PDF extractor with layout parameters.
        
        Args:
            line_margin: Line margin for text extraction
            char_margin: Character margin for text extraction
            word_margin: Word margin for text extraction
            boxes_flow: Boxes flow parameter for layout analysis
            detect_vertical: Whether to detect vertical text (useful for languages like Japanese)
            codec: Text encoding for extraction
        """
        self.laparams = LAParams(
            line_margin=line_margin,
            char_margin=char_margin,
            word_margin=word_margin,
            boxes_flow=boxes_flow,
            detect_vertical=detect_vertical
        )
        self.codec = codec
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: If text extraction fails
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            # Try primary extraction method
            logger.info(f"Extracting text from {pdf_path}")
            extracted_text = extract_text(
                pdf_path,
                laparams=self.laparams,
                codec=self.codec
            )
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters from {pdf_path}")
            return extracted_text
            
        except Exception as e:
            logger.warning(f"Primary extraction method failed: {e}")
            logger.info("Trying alternative extraction method...")
            
            # Try alternative extraction method
            try:
                from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
                from pdfminer.converter import TextConverter
                from pdfminer.pdfpage import PDFPage
                from io import StringIO
                
                resource_manager = PDFResourceManager()
                output_string = StringIO()
                converter = TextConverter(
                    resource_manager, 
                    output_string, 
                    laparams=self.laparams, 
                    codec=self.codec
                )
                page_interpreter = PDFPageInterpreter(resource_manager, converter)
                
                with open(pdf_path, 'rb') as file:
                    for page in PDFPage.get_pages(file, check_extractable=True):
                        page_interpreter.process_page(page)
                    
                    extracted_text = output_string.getvalue()
                
                converter.close()
                output_string.close()
                
                logger.info(f"Alternative method extracted {len(extracted_text)} characters from {pdf_path}")
                return extracted_text
                
            except Exception as backup_error:
                logger.error(f"Alternative extraction method also failed: {backup_error}")
                
                # Try OCR as a last resort if pytesseract and pdf2image are available
                try:
                    logger.info("Attempting OCR extraction...")
                    return self._extract_with_ocr(pdf_path)
                except (ImportError, Exception) as ocr_error:
                    logger.error(f"OCR extraction failed or not available: {ocr_error}")
                    raise Exception(f"Could not extract text from {pdf_path}: {str(e)}\n" +
                                   f"Alternative methods also failed.")
    
    def _extract_with_ocr(self, pdf_path: str) -> str:
        """
        Extract text from a PDF using OCR as a fallback.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
            
        Raises:
            ImportError: If required packages aren't available
        """
        try:
            # Only import these if needed, to avoid unnecessary dependencies
            from pdf2image import convert_from_path
            import pytesseract
            from PIL import Image
        except ImportError:
            raise ImportError("OCR extraction requires pdf2image, pytesseract, and Pillow. " +
                             "Install with 'pip install pdf2image pytesseract pillow'")
        
        # Create a temporary directory for images
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=300)
            
            # Extract text from each page using OCR
            full_text = []
            for i, page in enumerate(pages):
                logger.info(f"Processing page {i+1}/{len(pages)} with OCR")
                text = pytesseract.image_to_string(page)
                full_text.append(text)
            
            return "\n\n".join(full_text)
    
    def save_text(self, text: str, output_path: str) -> None:
        """
        Save extracted text to a file.
        
        Args:
            text: Extracted text
            output_path: Path to save the text file
        """
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Write the text to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Text saved to {output_path}")
    
    def batch_process(self, input_dir: str, output_dir: str, recursive: bool = False) -> Dict[str, str]:
        """
        Process multiple PDF files in a directory.
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save extracted text files
            recursive: Whether to process PDFs in subdirectories
            
        Returns:
            Dictionary mapping input files to output files
        """
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Find PDF files
        if recursive:
            pdf_pattern = os.path.join(input_dir, "**", "*.pdf")
            pdf_files = glob.glob(pdf_pattern, recursive=True)
        else:
            pdf_pattern = os.path.join(input_dir, "*.pdf")
            pdf_files = glob.glob(pdf_pattern)
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {input_dir}")
            return {}
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        results = {}
        success_count = 0
        
        # Process each PDF file
        for pdf_file in pdf_files:
            try:
                # Determine output path
                rel_path = os.path.relpath(pdf_file, input_dir)
                rel_dir = os.path.dirname(rel_path)
                base_name = os.path.splitext(os.path.basename(pdf_file))[0]
                
                # Create subdirectory in output dir if the file is in a subdirectory
                out_subdir = os.path.join(output_dir, rel_dir) if rel_dir != '.' else output_dir
                os.makedirs(out_subdir, exist_ok=True)
                
                output_file = os.path.join(out_subdir, f"{base_name}.txt")
                
                # Extract text and save it
                text = self.extract_text_from_pdf(pdf_file)
                self.save_text(text, output_file)
                
                results[pdf_file] = output_file
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                results[pdf_file] = None
        
        logger.info(f"Successfully processed {success_count} of {len(pdf_files)} files")
        return results


def main():
    """Command-line interface for PDF text extraction."""
    parser = argparse.ArgumentParser(
        description="Extract text from PDF documents for Pyunto Intelligence"
    )
    
    # Main arguments
    parser.add_argument(
        "input",
        help="Input PDF file or directory"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output text file or directory"
    )
    
    # Batch processing
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process multiple PDF files in a directory"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Output directory for batch processing"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process PDFs in subdirectories recursively"
    )
    
    # Layout parameters
    layout_group = parser.add_argument_group("Layout Parameters")
    
    layout_group.add_argument(
        "--line-margin",
        type=float,
        default=0.5,
        help="Line margin for text extraction (default: 0.5)"
    )
    
    layout_group.add_argument(
        "--char-margin",
        type=float,
        default=2.0,
        help="Character margin for text extraction (default: 2.0)"
    )
    
    layout_group.add_argument(
        "--word-margin",
        type=float,
        default=0.1,
        help="Word margin for text extraction (default: 0.1)"
    )
    
    layout_group.add_argument(
        "--boxes-flow",
        type=float,
        default=0.5,
        help="Boxes flow parameter for layout analysis (default: 0.5)"
    )
    
    layout_group.add_argument(
        "--no-detect-vertical",
        action="store_false",
        dest="detect_vertical",
        help="Disable vertical text detection (useful for languages like Japanese)"
    )
    
    # Other options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize extractor with specified parameters
        extractor = PDFTextExtractor(
            line_margin=args.line_margin,
            char_margin=args.char_margin,
            word_margin=args.word_margin,
            boxes_flow=args.boxes_flow,
            detect_vertical=args.detect_vertical
        )
        
        if args.batch or os.path.isdir(args.input):
            # Batch processing mode
            input_dir = args.input
            output_dir = args.output_dir or args.output or "extracted_texts"
            
            results = extractor.batch_process(
                input_dir=input_dir,
                output_dir=output_dir,
                recursive=args.recursive
            )
            
            # Print summary
            success_count = sum(1 for v in results.values() if v is not None)
            logger.info(f"Batch processing complete. Success: {success_count}/{len(results)}")
            
        else:
            # Single file mode
            pdf_path = args.input
            
            if not args.output:
                # Generate output path from input
                base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                output_path = f"{base_name}.txt"
            else:
                output_path = args.output
            
            # Extract and save
            text = extractor.extract_text_from_pdf(pdf_path)
            extractor.save_text(text, output_path)
            
            logger.info(f"Text extraction complete: {pdf_path} -> {output_path}")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
