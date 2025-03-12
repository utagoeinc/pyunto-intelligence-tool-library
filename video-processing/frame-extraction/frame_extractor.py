#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Frame Extraction Tool for Pyunto Intelligence

This module provides functions to extract frames from video files for
analysis with Pyunto Intelligence.
"""

import os
import subprocess
import uuid
from typing import Dict, Optional
from pathlib import Path
import logging
import base64

logger = logging.getLogger(__name__)

class FrameExtractor:
    def __init__(self, temp_dir: str = "/tmp/pyunto_frames"):
        """
        Initialize the frame extractor with a temporary directory for processing files.
        
        Args:
            temp_dir: Directory to store temporary files during processing
        """
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        
    def _create_process_dir(self) -> str:
        """Create a unique processing directory for the current job."""
        process_id = str(uuid.uuid4())
        process_dir = os.path.join(self.temp_dir, process_id)
        os.makedirs(process_dir, exist_ok=True)
        return process_dir

    def _clean_process_dir(self, process_dir: str):
        """Clean up temporary processing directory."""
        try:
            subprocess.run(['rm', '-rf', process_dir], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clean process directory: {e}")

    def extract_frames(self, video_data: bytes, fps: float = 1, quality: int = 2) -> Dict[int, bytes]:
        """
        Extract frames from video data.
        
        Args:
            video_data: Binary video data
            fps: Frames per second to extract (default: 1)
            quality: JPEG quality setting (1-31, lower is better quality, default: 2)
            
        Returns:
            Dictionary mapping frame numbers to frame image data
        """
        process_dir = self._create_process_dir()
        try:
            # Save input video temporarily
            input_path = os.path.join(process_dir, "input.mp4")
            with open(input_path, "wb") as f:
                f.write(video_data)

            # Extract frames using ffmpeg command
            frames_dir = os.path.join(process_dir, "frames")
            os.makedirs(frames_dir, exist_ok=True)
            frames_path = os.path.join(frames_dir, "frame_%d.jpg")
            
            # Construct the fps filter value
            fps_filter = f"fps={fps}"
            
            # Construct the quality value (qscale)
            qscale = str(quality)
            
            subprocess.run([
                'ffmpeg', '-i', input_path,
                '-vf', fps_filter,  # Extract frames at specified FPS
                '-qscale:v', qscale,  # Set JPEG quality
                '-y',  # Overwrite output files
                frames_path
            ], check=True, capture_output=True)

            # Read frame data
            frames = {}
            frame_files = sorted(Path(frames_dir).glob("frame_*.jpg"))
            for i, frame_path in enumerate(frame_files, 1):
                with open(frame_path, "rb") as f:
                    frames[i] = f.read()

            return frames

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            raise
        finally:
            self._clean_process_dir(process_dir)
            
    def extract_frames_from_file(self, video_file_path: str, fps: float = 1, quality: int = 2) -> Dict[int, bytes]:
        """
        Extract frames from a video file.
        
        Args:
            video_file_path: Path to the video file
            fps: Frames per second to extract (default: 1)
            quality: JPEG quality setting (1-31, lower is better quality, default: 2)
            
        Returns:
            Dictionary mapping frame numbers to frame image data
        """
        with open(video_file_path, "rb") as f:
            video_data = f.read()
        return self.extract_frames(video_data, fps, quality)
    
    def save_frames(self, frames: Dict[int, bytes], output_dir: str, 
                   prefix: str = "frame_", format: str = "jpg") -> Dict[int, str]:
        """
        Save extracted frames to disk.
        
        Args:
            frames: Dictionary mapping frame numbers to frame image data
            output_dir: Directory to save frames
            prefix: Filename prefix for saved frames
            format: Image format extension
            
        Returns:
            Dictionary mapping frame numbers to file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        frame_paths = {}
        for frame_num, frame_data in frames.items():
            frame_path = os.path.join(output_dir, f"{prefix}{frame_num}.{format}")
            with open(frame_path, "wb") as f:
                f.write(frame_data)
            frame_paths[frame_num] = frame_path
            
        return frame_paths
    
    def frames_to_base64(self, frames: Dict[int, bytes]) -> Dict[str, Dict[str, str]]:
        """
        Convert frame data to base64 for API transmission.
        
        Args:
            frames: Dictionary mapping frame numbers to frame image data
            
        Returns:
            Dictionary with base64-encoded frames ready for API transmission
        """
        return {
            str(frame_num): {
                "data": base64.b64encode(frame_data).decode('utf-8'),
                "mimeType": "image/jpeg"
            }
            for frame_num, frame_data in frames.items()
        }


def main():
    """Command-line interface for frame extraction."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Extract frames from a video file")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--fps", type=float, default=1, 
                        help="Frames per second to extract (default: 1)")
    parser.add_argument("--quality", type=int, default=2, 
                        help="JPEG quality (1-31, lower is better, default: 2)")
    parser.add_argument("--output-dir", default="./frames", 
                        help="Directory to save extracted frames")
    
    args = parser.parse_args()
    
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        extractor = FrameExtractor()
        logger.info(f"Extracting frames from {args.video_path} at {args.fps} fps...")
        
        frames = extractor.extract_frames_from_file(
            args.video_path, 
            fps=args.fps,
            quality=args.quality
        )
        
        frame_paths = extractor.save_frames(frames, args.output_dir)
        
        logger.info(f"Extracted {len(frames)} frames to {args.output_dir}")
        for frame_num, frame_path in frame_paths.items():
            logger.info(f"Frame {frame_num}: {frame_path}")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
