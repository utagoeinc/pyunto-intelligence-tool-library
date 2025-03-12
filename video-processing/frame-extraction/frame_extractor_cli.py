#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line interface for the Frame Extraction Tool

This script provides a command-line interface to extract frames from 
video files for analysis with Pyunto Intelligence.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from frame_extractor import FrameExtractor

logger = logging.getLogger(__name__)

def setup_logging(verbose=False):
    """Configure logging."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract frames from video files for Pyunto Intelligence analysis"
    )
    
    parser.add_argument(
        "input",
        help="Input video file or directory of video files"
    )
    
    parser.add_argument(
        "-o", "--output-dir",
        default="./frames",
        help="Directory to save extracted frames (default: ./frames)"
    )
    
    parser.add_argument(
        "--fps",
        type=float,
        default=1.0,
        help="Frames per second to extract (default: 1.0)"
    )
    
    parser.add_argument(
        "--quality",
        type=int,
        default=2,
        choices=range(1, 32),
        metavar="[1-31]",
        help="JPEG quality (1-31, lower is better quality, default: 2)"
    )
    
    parser.add_argument(
        "--prefix",
        default="frame_",
        help="Filename prefix for saved frames (default: 'frame_')"
    )
    
    parser.add_argument(
        "--format",
        default="jpg",
        choices=["jpg", "jpeg", "png"],
        help="Output image format (default: jpg)"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process videos in subdirectories recursively"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def process_video_file(extractor, video_path, output_dir, fps, quality, prefix, format):
    """Process a single video file."""
    try:
        # Create output directory structure mirroring input if needed
        rel_path = os.path.dirname(video_path)
        if rel_path:
            output_subdir = os.path.join(output_dir, rel_path)
        else:
            output_subdir = output_dir
            
        os.makedirs(output_subdir, exist_ok=True)
        
        # Create subdirectory with video filename
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        frame_dir = os.path.join(output_subdir, video_name)
        os.makedirs(frame_dir, exist_ok=True)
        
        logger.info(f"Processing {video_path}")
        logger.info(f"Extracting frames at {fps} fps with quality {quality}")
        
        # Extract frames
        frames = extractor.extract_frames_from_file(
            video_path,
            fps=fps,
            quality=quality
        )
        
        # Save frames
        frame_paths = extractor.save_frames(
            frames,
            frame_dir,
            prefix=prefix,
            format=format
        )
        
        logger.info(f"Extracted {len(frames)} frames to {frame_dir}")
        return len(frames)
    
    except Exception as e:
        logger.error(f"Error processing {video_path}: {str(e)}")
        return 0

def find_video_files(input_path, recursive=False):
    """Find video files in the input path."""
    if os.path.isfile(input_path):
        return [input_path]
    
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    
    if recursive:
        video_files = []
        for root, _, files in os.walk(input_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    video_files.append(os.path.join(root, file))
        return video_files
    else:
        return [
            os.path.join(input_path, f) 
            for f in os.listdir(input_path) 
            if os.path.isfile(os.path.join(input_path, f)) and 
            any(f.lower().endswith(ext) for ext in video_extensions)
        ]

def main():
    """Main function for the command-line interface."""
    args = parse_arguments()
    setup_logging(args.verbose)
    
    try:
        # Initialize the frame extractor
        extractor = FrameExtractor()
        
        # Ensure output directory exists
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Find video files to process
        video_files = find_video_files(args.input, args.recursive)
        
        if not video_files:
            logger.error(f"No video files found in {args.input}")
            sys.exit(1)
        
        logger.info(f"Found {len(video_files)} video files to process")
        
        # Process each video file
        total_frames = 0
        for video_file in video_files:
            frames_extracted = process_video_file(
                extractor,
                video_file,
                args.output_dir,
                args.fps,
                args.quality,
                args.prefix,
                args.format
            )
            total_frames += frames_extracted
        
        logger.info(f"Processing complete! Extracted {total_frames} frames in total.")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
