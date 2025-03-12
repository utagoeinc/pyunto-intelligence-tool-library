#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Video Format Conversion Tool for Pyunto Intelligence

This module provides functions to convert video files between formats and
optimize them for processing with Pyunto Intelligence.
"""

import os
import subprocess
import logging
import json
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class VideoConverter:
    def __init__(self):
        """
        Initialize the video converter.
        """
        # Check if FFmpeg is installed
        try:
            subprocess.run(['ffmpeg', '-version'], 
                          check=True, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("FFmpeg is not installed or not in PATH. Please install FFmpeg.")
            raise RuntimeError("FFmpeg is required but not installed")

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get information about a video file using ffprobe.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing video information
        """
        try:
            result = subprocess.run([
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ], check=True, capture_output=True, text=True)
            
            return json.loads(result.stdout)
        
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error: {e.stderr if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise

    def convert_video(self, 
                     input_path: str, 
                     output_path: str, 
                     format: Optional[str] = None,
                     codec: Optional[str] = None,
                     width: Optional[int] = None,
                     height: Optional[int] = None,
                     fps: Optional[float] = None,
                     bitrate: Optional[str] = None,
                     preset: str = "medium",
                     crf: Optional[int] = None,
                     audio_codec: Optional[str] = None,
                     audio_bitrate: Optional[str] = None,
                     extra_options: Optional[List[str]] = None) -> str:
        """
        Convert a video file to a different format or with different parameters.
        
        Args:
            input_path: Path to the input video file
            output_path: Path for the output video file
            format: Output container format (mp4, avi, etc.) - if None, inferred from output_path
            codec: Video codec to use (libx264, etc.) - if None, determined by format
            width: Output width in pixels - if None, same as input
            height: Output height in pixels - if None, same as input
            fps: Output frame rate - if None, same as input
            bitrate: Output video bitrate (e.g., "5000k") - if None, determined by codec
            preset: Encoding preset (slower = better quality) - options depend on codec
            crf: Constant Rate Factor (0-51, lower = better quality)
            audio_codec: Audio codec to use - if None, determined by format
            audio_bitrate: Audio bitrate (e.g., "128k") - if None, determined by codec
            extra_options: List of extra FFmpeg options
            
        Returns:
            Path to the output video file
        """
        try:
            # Get information about the input video
            video_info = self.get_video_info(input_path)
            
            # Build FFmpeg command
            cmd = ['ffmpeg', '-i', input_path]
            
            # Video codec
            if codec:
                cmd.extend(['-c:v', codec])
            
            # Video size
            if width and height:
                cmd.extend(['-s', f'{width}x{height}'])
            
            # Frame rate
            if fps:
                cmd.extend(['-r', str(fps)])
            
            # Bitrate
            if bitrate:
                cmd.extend(['-b:v', bitrate])
            
            # Preset (for x264 and some other codecs)
            if preset and codec and 'x264' in codec:
                cmd.extend(['-preset', preset])
            
            # CRF (for x264 and some other codecs)
            if crf is not None and codec and 'x264' in codec:
                cmd.extend(['-crf', str(crf)])
            
            # Audio codec
            if audio_codec:
                cmd.extend(['-c:a', audio_codec])
            
            # Audio bitrate
            if audio_bitrate:
                cmd.extend(['-b:a', audio_bitrate])
            
            # Extra options
            if extra_options:
                cmd.extend(extra_options)
            
            # Output format
            if format:
                cmd.extend(['-f', format])
            
            # Always overwrite
            cmd.extend(['-y'])
            
            # Output file
            cmd.append(output_path)
            
            # Execute the command
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info(f"Video conversion complete: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error converting video: {str(e)}")
            raise

    def optimize_for_analysis(self, 
                             input_path: str, 
                             output_path: Optional[str] = None, 
                             max_dimension: int = 1280) -> str:
        """
        Optimize a video for analysis with Pyunto Intelligence.
        
        Args:
            input_path: Path to the input video file
            output_path: Path for the output video file - if None, creates one based on input
            max_dimension: Maximum width or height in pixels
            
        Returns:
            Path to the optimized video file
        """
        try:
            # Get information about the input video
            video_info = self.get_video_info(input_path)
            
            # Find video stream
            video_stream = None
            for stream in video_info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise ValueError("No video stream found in the input file")
            
            # Get original dimensions
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            
            # Calculate new dimensions maintaining aspect ratio
            if width > height and width > max_dimension:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            elif height > width and height > max_dimension:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))
            else:
                # No resizing needed
                new_width = width
                new_height = height
            
            # Generate output path if not provided
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_optimized.mp4"
            
            # Convert video with optimized settings
            return self.convert_video(
                input_path=input_path,
                output_path=output_path,
                codec="libx264",
                width=new_width,
                height=new_height,
                fps=30.0,  # Standard frame rate for analysis
                crf=23,    # Good quality/size balance
                preset="medium",
                audio_codec="aac",
                audio_bitrate="128k"
            )
            
        except Exception as e:
            logger.error(f"Error optimizing video: {str(e)}")
            raise

    def extract_thumbnail(self, 
                         video_path: str, 
                         output_path: Optional[str] = None,
                         time_offset: float = 0.0,
                         width: Optional[int] = None,
                         height: Optional[int] = None) -> str:
        """
        Extract a thumbnail image from a video.
        
        Args:
            video_path: Path to the video file
            output_path: Path for the thumbnail image - if None, creates one based on input
            time_offset: Time in seconds to extract frame from
            width: Output width in pixels - if None, same as video
            height: Output height in pixels - if None, same as video
            
        Returns:
            Path to the thumbnail image
        """
        try:
            # Generate output path if not provided
            if not output_path:
                base, ext = os.path.splitext(video_path)
                output_path = f"{base}_thumbnail.jpg"
            
            # Build command
            cmd = ['ffmpeg', '-i', video_path, '-ss', str(time_offset)]
            
            # Set size if specified
            if width and height:
                cmd.extend(['-s', f'{width}x{height}'])
            
            # Set frame selection and output options
            cmd.extend([
                '-frames:v', '1',  # Extract only one frame
                '-q:v', '2',       # High quality JPEG
                '-y',              # Overwrite output
                output_path
            ])
            
            # Execute the command
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info(f"Thumbnail extracted to: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error extracting thumbnail: {str(e)}")
            raise
    
    def concat_videos(self, 
                     input_paths: List[str], 
                     output_path: str,
                     format: Optional[str] = None,
                     codec: Optional[str] = None) -> str:
        """
        Concatenate multiple videos into a single file.
        
        Args:
            input_paths: List of paths to input video files
            output_path: Path for the output video file
            format: Output container format - if None, inferred from output_path
            codec: Video codec to use - if None, determined by format
            
        Returns:
            Path to the concatenated video file
        """
        try:
            # Create a temporary file list
            list_path = os.path.join(os.path.dirname(output_path), "concat_list.txt")
            with open(list_path, "w") as f:
                for input_path in input_paths:
                    f.write(f"file '{os.path.abspath(input_path)}'\n")
            
            # Build command
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_path
            ]
            
            # Add codec if specified
            if codec:
                cmd.extend(['-c:v', codec])
            else:
                cmd.extend(['-c', 'copy'])  # Copy streams by default
            
            # Add format if specified
            if format:
                cmd.extend(['-f', format])
            
            # Add output path
            cmd.extend(['-y', output_path])
            
            # Execute the command
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Clean up temporary file
            os.remove(list_path)
            
            logger.info(f"Videos concatenated to: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error concatenating videos: {str(e)}")
            raise
    
    def trim_video(self,
                  input_path: str,
                  output_path: str,
                  start_time: float,
                  duration: Optional[float] = None,
                  end_time: Optional[float] = None) -> str:
        """
        Trim a video to a specific segment.
        
        Args:
            input_path: Path to the input video file
            output_path: Path for the output video file
            start_time: Start time in seconds
            duration: Duration in seconds - if None, uses end_time
            end_time: End time in seconds - if None, uses duration
            
        Returns:
            Path to the trimmed video file
        """
        try:
            # Build command
            cmd = ['ffmpeg', '-i', input_path, '-ss', str(start_time)]
            
            # Add duration or end time
            if duration is not None:
                cmd.extend(['-t', str(duration)])
            elif end_time is not None:
                cmd.extend(['-to', str(end_time)])
            
            # Copy streams without re-encoding for speed
            cmd.extend([
                '-c', 'copy',
                '-y',
                output_path
            ])
            
            # Execute the command
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info(f"Video trimmed to: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error trimming video: {str(e)}")
            raise


def main():
    """Command-line interface for video conversion."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Convert video files for Pyunto Intelligence")
    parser.add_argument("input", help="Input video file path")
    parser.add_argument("-o", "--output", help="Output video file path")
    parser.add_argument("--format", help="Output format (mp4, avi, etc.)")
    parser.add_argument("--codec", help="Video codec to use")
    parser.add_argument("--width", type=int, help="Output width in pixels")
    parser.add_argument("--height", type=int, help="Output height in pixels")
    parser.add_argument("--fps", type=float, help="Output frame rate")
    parser.add_argument("--bitrate", help="Output video bitrate (e.g., 5000k)")
    parser.add_argument("--preset", default="medium", help="Encoding preset")
    parser.add_argument("--crf", type=int, help="Constant Rate Factor (0-51, lower is better)")
    parser.add_argument("--audio-codec", help="Audio codec to use")
    parser.add_argument("--audio-bitrate", help="Audio bitrate (e.g., 128k)")
    parser.add_argument("--optimize", action="store_true", help="Optimize for analysis")
    parser.add_argument("--thumbnail", action="store_true", help="Extract thumbnail")
    parser.add_argument("--time-offset", type=float, default=0.0, help="Time offset for thumbnail")
    parser.add_argument("--trim", action="store_true", help="Trim video")
    parser.add_argument("--start-time", type=float, help="Start time for trimming")
    parser.add_argument("--duration", type=float, help="Duration for trimming")
    parser.add_argument("--end-time", type=float, help="End time for trimming")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        converter = VideoConverter()
        
        if args.thumbnail:
            # Extract thumbnail
            if not args.output:
                base, ext = os.path.splitext(args.input)
                args.output = f"{base}_thumbnail.jpg"
            
            converter.extract_thumbnail(
                video_path=args.input,
                output_path=args.output,
                time_offset=args.time_offset,
                width=args.width,
                height=args.height
            )
            
        elif args.trim:
            # Trim video
            if not args.output:
                base, ext = os.path.splitext(args.input)
                args.output = f"{base}_trimmed{ext}"
            
            if args.start_time is None:
                args.start_time = 0.0
                
            converter.trim_video(
                input_path=args.input,
                output_path=args.output,
                start_time=args.start_time,
                duration=args.duration,
                end_time=args.end_time
            )
            
        elif args.optimize:
            # Optimize for analysis
            if not args.output:
                base, ext = os.path.splitext(args.input)
                args.output = f"{base}_optimized.mp4"
                
            converter.optimize_for_analysis(
                input_path=args.input,
                output_path=args.output,
                max_dimension=args.width or 1280
            )
            
        else:
            # Standard conversion
            if not args.output:
                base, ext = os.path.splitext(args.input)
                args.output = f"{base}_converted{ext}"
                
            converter.convert_video(
                input_path=args.input,
                output_path=args.output,
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
        
        logger.info(f"Operation completed successfully: {args.output}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
