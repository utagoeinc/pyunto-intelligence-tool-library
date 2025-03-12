#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Document Merger Tool for Pyunto Intelligence

This module provides functions to merge multiple documents into a single file
for analysis with Pyunto Intelligence.
"""

import os
import sys
import argparse
import logging
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
    logger.error("PDFMiner.six is required for PDF extraction. Install with 'pip install pdfminer.six'")
    # Continue without PDF support if not available

class DocumentMerger:
    """Document merger tool for Pyunto Intelligence."""
    
    def __init__(self, 
                line_margin: float = 0.5,
                char_margin: float = 2.0,
                word_margin: float = 0.1,
                boxes_flow: float = 0.5,
                detect_vertical: bool = True,
                codec: str = 'utf-8'):
        """
        Initialize the document merger with PDF extraction parameters.
        
        Args:
            line_margin: Line margin for PDF text extraction
            char_margin: Character margin for PDF text extraction
            word_margin: Word margin for PDF text extraction
            boxes_flow: Boxes flow parameter for PDF layout analysis
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
            logger.warning(f"Primary PDF extraction method failed: {e}")
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
                raise Exception(f"Could not extract text from PDF {pdf_path}: {str(e)}\n" +
                               f"Alternative method failed with: {str(backup_error)}")
    
    def read_document(self, doc_path: str) -> str:
        """
        Read text from a document file (PDF or TXT).
        
        Args:
            doc_path: Path to the document file
            
        Returns:
            Document text as a string
            
        Raises:
            FileNotFoundError: If the document file doesn't exist
            ValueError: If the file format is not supported
            Exception: If reading fails
        """
        if not os.path.exists(doc_path):
            raise FileNotFoundError(f"Document file not found: {doc_path}")
        
        file_ext = os.path.splitext(doc_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(doc_path)
        elif file_ext == '.txt':
            with open(doc_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported document format: {file_ext}")
    
    def merge_documents(self, 
                      documents: List[Dict[str, str]],
                      output_path: Optional[str] = None,
                      separator: str = "\n\n" + "="*50 + "\n\n") -> str:
        """
        Merge multiple documents into a single text file.
        
        Args:
            documents: List of document dictionaries with 'path' and optional 'title' keys
            output_path: Path to save the merged document. If None, doesn't save to file
            separator: Text to use as separator between documents
            
        Returns:
            Merged document text as a string
            
        Raises:
            Exception: If merging fails
        """
        try:
            logger.info(f"Merging {len(documents)} documents")
            
            merged_text = []
            
            for i, doc in enumerate(documents):
                doc_path = doc['path']
                doc_title = doc.get('title', f"DOCUMENT {i+1}")
                
                logger.info(f"Processing document {i+1}: {doc_path}")
                
                # Read document text
                doc_text = self.read_document(doc_path)
                
                # Add document with header
                doc_header = "="*50 + "\n" + doc_title + "\n" + "="*50 + "\n\n"
                merged_text.append(doc_header + doc_text)
            
            # Combine all documents with separators
            result = separator.join(merged_text)
            
            # Add footer
            footer = "\n\n" + "="*50 + "\n" + "END OF DOCUMENT" + "\n" + "="*50
            result += footer
            
            # Save to file if output path is provided
            if output_path:
                # Ensure output directory exists
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                logger.info(f"Merged document saved to {output_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error merging documents: {e}")
            raise
    
    def merge_job_and_cv(self,
                       job_file: str,
                       cv_file: str,
                       output_file: Optional[str] = None) -> str:
        """
        Specialized function to merge job description and CV/resume for matching.
        
        Args:
            job_file: Path to job description file (.pdf or .txt)
            cv_file: Path to CV/resume file (.pdf or .txt)
            output_file: Path to save the merged document. If None, uses "combined_for_llm.txt"
            
        Returns:
            Merged document text as a string
            
        Raises:
            FileNotFoundError: If any input file doesn't exist
            ValueError: If the file format is not supported
            Exception: If merging fails
        """
        # Set default output file if not provided
        if output_file is None:
            output_file = "combined_for_llm.txt"
        
        # Create document list for the merge_documents function
        documents = [
            {"path": job_file, "title": "JOB DESCRIPTION"},
            {"path": cv_file, "title": "CURRICULUM VITAE (CV)"}
        ]
        
        # Merge the documents
        return self.merge_documents(documents, output_file)


def main():
    """Command-line interface for document merging."""
    parser = argparse.ArgumentParser(
        description="Merge multiple documents for Pyunto Intelligence analysis"
    )
    
    # Main operating modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    
    mode_group.add_argument(
        "--files",
        nargs='+',
        help="List of document files to merge"
    )
    
    mode_group.add_argument(
        "--job-cv",
        action="store_true",
        help="Job and CV/resume matching mode"
    )
    
    # Job-CV mode arguments
    parser.add_argument(
        "--job",
        help="Job description file (.pdf or .txt) for job-cv mode"
    )
    
    parser.add_argument(
        "--cv",
        help="CV/resume file (.pdf or .txt) for job-cv mode"
    )
    
    # General options
    parser.add_argument(
        "--titles",
        nargs='+',
        help="List of titles for each document (must match number of files)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path"
    )
    
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
        # Initialize merger
        merger = DocumentMerger()
        
        if args.job_cv:
            # Job and CV matching mode
            if not args.job or not args.cv:
                parser.error("--job and --cv are required with --job-cv")
            
            output_file = args.output or "combined_for_llm.txt"
            
            result = merger.merge_job_and_cv(
                job_file=args.job,
                cv_file=args.cv,
                output_file=output_file
            )
            
            logger.info(f"Job and CV merged to {output_file}")
            
        else:
            # General document merging mode
            if not args.files:
                parser.error("No input files specified")
            
            # Create document list
            documents = []
            for i, file_path in enumerate(args.files):
                # Determine title
                if args.titles and i < len(args.titles):
                    title = args.titles[i]
                else:
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    title = base_name.upper().replace('_', ' ')
                
                documents.append({
                    "path": file_path,
                    "title": title
                })
            
            output_file = args.output or "merged_document.txt"
            
            result = merger.merge_documents(
                documents=documents,
                output_path=output_file
            )
            
            logger.info(f"Documents merged to {output_file}")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
