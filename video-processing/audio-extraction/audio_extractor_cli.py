#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line interface for the Audio Extraction Tool

This script provides a command-line interface to extract audio from 
video files for analysis with Pyunto Intelligence.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from audio_extractor import AudioExtractor

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
        description="Extract audio from video files for Pyunto Intelligence analysis"
    )
    
    parser.add_argument(
        "input",
        help="Input video file or directory of video files"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output audio file or directory (required)"
    )
    
    parser.add_argument(
        "--format",
        default="wav",
        choices=["wav", "mp3", "aac", "ogg", "flac", "m4a"],
        help="Output audio format (default: wav)"
    )
    
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Sample rate in Hz (default: 16000)"
    )
    
    parser.add_argument(
        "--channels",
        type=int,
        default=1,
        choices=[1, 2],
        help="Number of audio channels (1=mono, 2=stereo, default: 1)"
    )
    
    parser.add_argument(
        "--codec",
        help="Audio codec to use (default: based on format)"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process videos in subdirectories recursively"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Only show audio information, don't extract"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def process_video_file(extractor, video_path, output_path, format, sample_rate, channels, codec):
    """Process a single video file."""
    try:
        logger.info(f"Processing {video_path}")
        logger.info(f"Output: {output_path}, Format: {format}, Sample rate: {sample_rate}, Channels: {channels}")
        
        # Extract audio
        audio_data = extractor.extract_audio_from_file(
            video_path,
            sample_rate=sample_rate,
            channels=channels,
            format=format,
            codec=codec
        )
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Save audio
        extractor.save_audio(audio_data, output_path)
        
        logger.info(f"Audio extracted and saved to {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing {video_path}: {str(e)}")
        return False

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

def show_audio_info(extractor, video_files):
    """Show audio information for video files."""
    for video_file in video_files:
        print(f"\nAudio Information for {video_file}:")
        info = extractor.get_audio_info(video_file)
        if info:
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print("  No audio stream found or error getting information")

def main():
    """Main function for the command-line interface."""
    args = parse_arguments()
    setup_logging(args.verbose)
    
    try:
        # Initialize the audio extractor
        extractor = AudioExtractor()
        
        # Find video files to process
        video_files = find_video_files(args.input, args.recursive)
        
        if not video_files:
            logger.error(f"No video files found in {args.input}")
            sys.exit(1)
        
        logger.info(f"Found {len(video_files)} video files to process")
        
        # If --info flag is set, just show audio information
        if args.info:
            show_audio_info(extractor, video_files)
            return
        
        # Process each video file
        success_count = 0
        for video_file in video_files:
            # Determine output path based on input and args.output
            if os.path.isdir(args.output) or len(video_files) > 1:
                # If output is a directory or multiple files, create output filename
                os.makedirs(args.output, exist_ok=True)
                video_name = os.path.splitext(os.path.basename(video_file))[0]
                output_file = os.path.join(args.output, f"{video_name}.{args.format}")
            else:
                # Use the specified output filename
                output_file = args.output
            
            if process_video_file(
                extractor,
                video_file,
                output_file,
                args.format,
                args.sample_rate,
                args.channels,
                args.codec
            ):
                success_count += 1
        
        logger.info(f"Processing complete! Successfully processed {success_count} of {len(video_files)} files.")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
