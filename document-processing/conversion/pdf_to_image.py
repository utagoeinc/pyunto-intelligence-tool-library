#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF to Image Conversion Tool for Pyunto Intelligence

This module provides functions to convert PDF documents to image formats for
analysis with Pyunto Intelligence.
"""

import os
import sys
import argparse
import logging
import glob
from typing import Dict, List, Optional, Union, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError:
    logger.error("Required packages missing. Install with 'pip install pdf2image pillow'")
    logger.error("Note: pdf2image requires poppler-utils to be installed on your system")
    sys.exit(1)

class PDFToImageConverter:
    """PDF to image conversion tool for Pyunto Intelligence."""
    
    def __init__(self):
        """Initialize the PDF to image converter."""
        pass
    
    def convert_to_single_image(self, 
                              pdf_path: str, 
                              output_path: Optional[str] = None,
                              dpi: int = 300,
                              format: str = 'PNG') -> str:
        """
        Convert a multi-page PDF to a single combined image.
        
        Args:
            pdf_path: Path to the PDF file
            output_path: Path for the output image file. If None, generates one based on PDF name
            dpi: Resolution for the output image
            format: Image format (PNG, JPEG, TIFF, etc.)
            
        Returns:
            Path to the output image file
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: If conversion fails
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Generate output path if not provided
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = f"{base_name}.{format.lower()}"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        try:
            logger.info(f"Converting PDF to image: {pdf_path}")
            
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=dpi)
            
            if not pages:
                raise Exception(f"No pages extracted from PDF: {pdf_path}")
            
            logger.info(f"Extracted {len(pages)} pages from PDF")
            
            # Calculate dimensions for the combined image
            width = max(page.width for page in pages)
            total_height = sum(page.height for page in pages)
            
            # Create a new image to hold all pages
            combined_image = Image.new('RGB', (width, total_height), (255, 255, 255))
            
            # Paste each page into the combined image
            y_offset = 0
            for page in pages:
                combined_image.paste(page, (0, y_offset))
                y_offset += page.height
            
            # Save the combined image
            combined_image.save(output_path, format=format)
            logger.info(f"Saved combined image to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting PDF to image: {e}")
            raise
    
    def convert_to_individual_images(self, 
                                   pdf_path: str, 
                                   output_dir: Optional[str] = None,
                                   dpi: int = 300,
                                   format: str = 'PNG',
                                   prefix: Optional[str] = None) -> List[str]:
        """
        Convert a PDF document to individual image files, one per page.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory for the output image files. If None, uses PDF name as directory
            dpi: Resolution for the output images
            format: Image format (PNG, JPEG, TIFF, etc.)
            prefix: Prefix for output filenames. If None, uses PDF filename
            
        Returns:
            List of paths to the output image files
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: If conversion fails
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Generate output directory if not provided
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        if output_dir is None:
            output_dir = base_name
        
        # Generate prefix if not provided
        if prefix is None:
            prefix = f"{base_name}_page"
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            logger.info(f"Converting PDF to individual images: {pdf_path}")
            
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=dpi)
            
            if not pages:
                raise Exception(f"No pages extracted from PDF: {pdf_path}")
            
            logger.info(f"Extracted {len(pages)} pages from PDF")
            
            # Save each page as an individual image
            output_paths = []
            for i, page in enumerate(pages):
                page_path = os.path.join(output_dir, f"{prefix}_{i+1}.{format.lower()}")
                page.save(page_path, format=format)
                output_paths.append(page_path)
                logger.info(f"Saved page {i+1} to {page_path}")
            
            return output_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise
    
    def batch_convert_to_images(self, 
                             input_dir: str, 
                             output_dir: str, 
                             dpi: int = 300,
                             format: str = 'PNG',
                             combine_pages: bool = True,
                             recursive: bool = False) -> Dict[str, Union[str, List[str]]]:
        """
        Batch convert multiple PDF files to images.
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save output image files
            dpi: Resolution for the output images
            format: Image format (PNG, JPEG, TIFF, etc.)
            combine_pages: Whether to combine pages (True) or save individual pages (False)
            recursive: Whether to process PDFs in subdirectories
            
        Returns:
            Dictionary mapping input PDF paths to output image paths
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
                # Determine relative path and create output structure
                rel_path = os.path.relpath(pdf_file, input_dir)
                rel_dir = os.path.dirname(rel_path)
                base_name = os.path.splitext(os.path.basename(pdf_file))[0]
                
                if combine_pages:
                    # Combined image mode
                    out_subdir = os.path.join(output_dir, rel_dir) if rel_dir != '.' else output_dir
                    os.makedirs(out_subdir, exist_ok=True)
                    
                    output_path = os.path.join(out_subdir, f"{base_name}.{format.lower()}")
                    
                    result = self.convert_to_single_image(
                        pdf_path=pdf_file,
                        output_path=output_path,
                        dpi=dpi,
                        format=format
                    )
                    
                    results[pdf_file] = result
                
                else:
                    # Individual pages mode
                    out_subdir = os.path.join(output_dir, rel_dir, base_name) if rel_dir != '.' else os.path.join(output_dir, base_name)
                    
                    result = self.convert_to_individual_images(
                        pdf_path=pdf_file,
                        output_dir=out_subdir,
                        dpi=dpi,
                        format=format,
                        prefix=base_name
                    )
                    
                    results[pdf_file] = result
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                results[pdf_file] = None
        
        logger.info(f"Successfully processed {success_count} of {len(pdf_files)} files")
        return results


def main():
    """Command-line interface for PDF to image conversion."""
    parser = argparse.ArgumentParser(
        description="Convert PDF documents to images for Pyunto Intelligence"
    )
    
    # Main arguments
    parser.add_argument(
        "input",
        help="Input PDF file or directory"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output image file or directory"
    )
    
    # Conversion options
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution for output images (default: 300)"
    )
    
    parser.add_argument(
        "--format",
        default="PNG",
        choices=["PNG", "JPEG", "JPG", "TIFF", "BMP"],
        help="Output image format (default: PNG)"
    )
    
    # Batch processing
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process multiple PDF files in a directory"
    )
    
    parser.add_argument(
        "--separate-pages",
        action="store_true",
        help="Save each page as a separate image (default: combine pages)"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process PDFs in subdirectories recursively"
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
    
    # Normalize format (JPEG/JPG)
    if args.format.upper() == "JPG":
        args.format = "JPEG"
    
    try:
        # Initialize converter
        converter = PDFToImageConverter()
        
        if args.batch or os.path.isdir(args.input):
            # Batch processing mode
            input_dir = args.input
            output_dir = args.output or "pdf_images"
            
            results = converter.batch_convert_to_images(
                input_dir=input_dir,
                output_dir=output_dir,
                dpi=args.dpi,
                format=args.format,
                combine_pages=not args.separate_pages,
                recursive=args.recursive
            )
            
            # Print summary
            success_count = sum(1 for v in results.values() if v is not None)
            logger.info(f"Batch conversion complete. Success: {success_count}/{len(results)}")
            
        else:
            # Single file mode
            pdf_path = args.input
            
            if args.separate_pages:
                # Convert to individual page images
                output_dir = args.output or os.path.splitext(os.path.basename(pdf_path))[0]
                
                result = converter.convert_to_individual_images(
                    pdf_path=pdf_path,
                    output_dir=output_dir,
                    dpi=args.dpi,
                    format=args.format
                )
                
                logger.info(f"Conversion complete. Generated {len(result)} page images in {output_dir}")
                
            else:
                # Convert to single combined image
                if not args.output:
                    # Generate output path from input
                    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                    output_path = f"{base_name}.{args.format.lower()}"
                else:
                    output_path = args.output
                
                result = converter.convert_to_single_image(
                    pdf_path=pdf_path,
                    output_path=output_path,
                    dpi=args.dpi,
                    format=args.format
                )
                
                logger.info(f"Conversion complete: {pdf_path} -> {result}")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
