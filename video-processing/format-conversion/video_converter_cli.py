#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line interface for the Video Format Conversion Tool

This script provides a command-line interface to convert video files
for analysis with Pyunto Intelligence.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from video_converter import VideoConverter

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
        description="Convert video files for Pyunto Intelligence analysis"
    )
    
    # Input and output arguments
    parser.add_argument(
        "input",
        help="Input video file or directory of video files"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output video file or directory"
    )
    
    # Format options
    format_group = parser.add_argument_group("Format Options")
    format_group.add_argument(
        "--format",
        choices=["mp4", "avi", "mov", "mkv", "webm", "flv"],
        help="Output video format"
    )
    
    format_group.add_argument(
        "--codec",
        help="Video codec to use (e.g., libx264, libx265, vp9)"
    )
    
    format_group.add_argument(
        "--audio-codec",
        help="Audio codec to use (e.g., aac, mp3, opus)"
    )
    
    # Size and quality options
    quality_group = parser.add_argument_group("Size and Quality Options")
    quality_group.add_argument(
        "--width",
        type=int,
        help="Output width in pixels"
    )
    
    quality_group.add_argument(
        "--height",
        type=int,
        help="Output height in pixels"
    )
    
    quality_group.add_argument(
        "--fps",
        type=float,
        help="Output frame rate"
    )
    
    quality_group.add_argument(
        "--bitrate",
        help="Output video bitrate (e.g., 5000k)"
    )
    
    quality_group.add_argument(
        "--audio-bitrate",
        help="Audio bitrate (e.g., 128k)"
    )
    
    quality_group.add_argument(
        "--preset",
        choices=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"],
        default="medium",
        help="Encoding preset (slower = better quality)"
    )
    
    quality_group.add_argument(
        "--crf",
        type=int,
        choices=range(0, 52),
        metavar="[0-51]",
        help="Constant Rate Factor (0-51, lower is better quality)"
    )
    
    # Special operations
    operations_group = parser.add_argument_group("Special Operations")
    operations_group.add_argument(
        "--optimize",
        action="store_true",
        help="Optimize video for analysis (resizes to max 1280px, sets good quality defaults)"
    )
    
    operations_group.add_argument(
        "--max-dimension",
        type=int,
        default=1280,
        help="Maximum dimension for optimization (default: 1280)"
    )
    
    operations_group.add_argument(
        "--extract-thumbnail",
        action="store_true",
        help="Extract a thumbnail image from the video"
    )
    
    operations_group.add_argument(
        "--thumbnail-time",
        type=float,
        default=0.0,
        help="Time offset in seconds for thumbnail extraction (default: 0.0)"
    )
    
    operations_group.add_argument(
        "--trim",
        action="store_true",
        help="Trim video to a specific segment"
    )
    
    operations_group.add_argument(
        "--start-time",
        type=float,
        default=0.0,
        help="Start time in seconds for trimming (default: 0.0)"
    )
    
    operations_group.add_argument(
        "--duration",
        type=float,
        help="Duration in seconds for trimming"
    )
    
    operations_group.add_argument(
        "--end-time",
        type=float,
        help="End time in seconds for trimming"
    )
    
    # Batch processing options
    batch_group = parser.add_argument_group("Batch Processing Options")
    batch_group.add_argument(
        "--recursive",
        action="store_true",
        help="Process videos in subdirectories recursively"
    )
    
    batch_group.add_argument(
        "--concat",
        action="store_true",
        help="Concatenate all input videos into a single output file"
    )
    
    # Other options
    parser.add_argument(
        "--info",
        action="store_true",
        help="Only show video information, don't convert"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def process_video_file(converter, operation, input_path, output_path, args):
    """Process a single video file based on the selected operation."""
    try:
        logger.info(f"Processing {input_path}")
        
        if operation == "info":
            # Just show video information
            info = converter.get_video_info(input_path)
            print(f"\nVideo Information for {input_path}:")
            
            # Format information
            if 'format' in info:
                print("\nFormat:")
                for key, value in info['format'].items():
                    print(f"  {key}: {value}")
            
            # Stream information
            if 'streams' in info:
                for i, stream in enumerate(info['streams']):
                    print(f"\nStream #{i} ({stream.get('codec_type', 'unknown')}):")
                    for key, value in stream.items():
                        if key not in ['disposition', 'tags']:
                            print(f"  {key}: {value}")
            
            return True
            
        elif operation == "thumbnail":
            # Extract thumbnail
            return converter.extract_thumbnail(
                video_path=input_path,
                output_path=output_path,
                time_offset=args.thumbnail_time,
                width=args.width,
                height=args.height
            )
            
        elif operation == "trim":
            # Trim video
            return converter.trim_video(
                input_path=input_path,
                output_path=output_path,
                start_time=args.start_time,
                duration=args.duration,
                end_time=args.end_time
            )
            
        elif operation == "optimize":
            # Optimize for analysis
            return converter.optimize_for_analysis(
                input_path=input_path,
                output_path=output_path,
                max_dimension=args.max_dimension
            )
            
        else:  # Standard conversion
            return converter.convert_video(
                input_path=input_path,
                output_path=output_path,
                format=args.format,
                codec=args.codec,
                width=args.width,
                height=args.height,
                fps=args.fps,
                bitrate=args.bitrate,
                preset=args.preset,
                crf=args.crf,
                audio_codec=args.audio_codec,
                audio_bitrate=args.audio_bitrate
            )
    
    except Exception as e:
        logger.error(f"Error processing {input_path}: {str(e)}")
        return None

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

def get_output_path(input_path, output_base, operation, format=None):
    """Determine output path based on input path and operation."""
    # If output_base is a file, use it directly
    if output_base and os.path.splitext(output_base)[1]:
        return output_base
    
    # Create output directory if it's specified and doesn't exist
    if output_base and not os.path.exists(output_base):
        os.makedirs(output_base, exist_ok=True)
    
    # Get base name and extension from input
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    extension = format if format else os.path.splitext(input_path)[1][1:]
    
    # Append operation suffix to base name
    if operation == "thumbnail":
        suffix = "_thumbnail"
        extension = "jpg"
    elif operation == "trim":
        suffix = "_trimmed"
    elif operation == "optimize":
        suffix = "_optimized"
        extension = "mp4"  # Optimized videos are always MP4
    else:
        suffix = "_converted"
    
    # Create output filename
    output_filename = f"{base_name}{suffix}.{extension}"
    
    # If output_base is a directory, place the file in that directory
    if output_base and os.path.isdir(output_base):
        return os.path.join(output_base, output_filename)
    
    # Otherwise, place it in the same directory as the input
    return os.path.join(os.path.dirname(input_path), output_filename)

def main():
    """Main function for the command-line interface."""
    args = parse_arguments()
    setup_logging(args.verbose)
    
    try:
        # Initialize the video converter
        converter = VideoConverter()
        
        # Determine operation
        if args.info:
            operation = "info"
        elif args.extract_thumbnail:
            operation = "thumbnail"
        elif args.trim:
            operation = "trim"
        elif args.optimize:
            operation = "optimize"
        else:
            operation = "convert"
        
        # Find video files to process
        video_files = find_video_files(args.input, args.recursive)
        
        if not video_files:
            logger.error(f"No video files found in {args.input}")
            sys.exit(1)
        
        logger.info(f"Found {len(video_files)} video files to process")
        
        # Handle concatenation
        if args.concat and len(video_files) > 1:
            # Create output path for concatenated video
            if not args.output:
                # Use the directory of the first video
                first_dir = os.path.dirname(video_files[0])
                args.output = os.path.join(first_dir, "concatenated_video.mp4")
            
            logger.info(f"Concatenating {len(video_files)} videos to {args.output}")
            
            converter.concat_videos(
                input_paths=video_files,
                output_path=args.output,
                format=args.format,
                codec=args.codec
            )
            
            logger.info(f"Concatenation complete: {args.output}")
            return
        
        # Process each video file
        success_count = 0
        for video_file in video_files:
            # Determine output path
            output_path = get_output_path(
                input_path=video_file,
                output_base=args.output,
                operation=operation,
                format=args.format
            )
            
            # Process the file
            result = process_video_file(
                converter=converter,
                operation=operation,
                input_path=video_file,
                output_path=output_path,
                args=args
            )
            
            if result:
                success_count += 1
                logger.info(f"Successfully processed: {video_file} -> {output_path}")
            else:
                logger.error(f"Failed to process: {video_file}")
        
        logger.info(f"Processing complete! Successfully processed {success_count} of {len(video_files)} files.")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
