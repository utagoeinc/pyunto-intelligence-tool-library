#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Audio Extraction Tool for Pyunto Intelligence

This module provides functions to extract audio from video files for
analysis with Pyunto Intelligence.
"""

import os
import subprocess
import uuid
import base64
import logging
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class AudioExtractor:
    def __init__(self, temp_dir: str = "/tmp/pyunto_audio"):
        """
        Initialize the audio extractor with a temporary directory for processing files.
        
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

    def _get_default_codec(self, format: str) -> str:
        """
        Get the default audio codec for a given format.
        
        Args:
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            Default codec for the format
        """
        format_to_codec = {
            "wav": "pcm_s16le",  # 16-bit PCM
            "mp3": "libmp3lame",
            "aac": "aac",
            "ogg": "libvorbis",
            "flac": "flac",
            "m4a": "aac"
        }
        
        return format_to_codec.get(format.lower(), "pcm_s16le")

    def extract_audio(self, video_data: bytes, 
                     sample_rate: int = 16000, 
                     channels: int = 1,
                     format: str = "wav",
                     codec: Optional[str] = None) -> bytes:
        """
        Extract audio from video data.
        
        Args:
            video_data: Binary video data
            sample_rate: Audio sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1 for mono)
            format: Output audio format (default: "wav")
            codec: Audio codec to use (default: None, auto-select based on format)
            
        Returns:
            Extracted audio data in the specified format
        """
        process_dir = self._create_process_dir()
        try:
            # Save input video temporarily
            input_path = os.path.join(process_dir, "input.mp4")
            with open(input_path, "wb") as f:
                f.write(video_data)

            # Determine codec if not specified
            if codec is None:
                codec = self._get_default_codec(format)

            # Set output file extension
            output_path = os.path.join(process_dir, f"audio.{format}")

            # Extract audio using ffmpeg command
            ffmpeg_cmd = [
                'ffmpeg', '-i', input_path,
                '-vn',  # Disable video
                '-acodec', codec,
                '-ar', str(sample_rate),  # Sample rate
                '-ac', str(channels),     # Audio channels
                '-y',  # Overwrite output file
                output_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

            # Read audio data
            with open(output_path, "rb") as f:
                audio_data = f.read()

            return audio_data

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise
        finally:
            self._clean_process_dir(process_dir)
            
    def extract_audio_from_file(self, video_file_path: str, 
                               sample_rate: int = 16000, 
                               channels: int = 1,
                               format: str = "wav",
                               codec: Optional[str] = None) -> bytes:
        """
        Extract audio from a video file.
        
        Args:
            video_file_path: Path to the video file
            sample_rate: Audio sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1 for mono)
            format: Output audio format (default: "wav")
            codec: Audio codec to use (default: None, auto-select based on format)
            
        Returns:
            Extracted audio data in the specified format
        """
        with open(video_file_path, "rb") as f:
            video_data = f.read()
        return self.extract_audio(video_data, sample_rate, channels, format, codec)
    
    def save_audio(self, audio_data: bytes, output_path: str) -> None:
        """
        Save extracted audio to disk.
        
        Args:
            audio_data: Binary audio data
            output_path: Path to save the audio file
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_data)
            
    def audio_to_base64(self, audio_data: bytes, format: str = "wav") -> Dict[str, str]:
        """
        Convert audio data to base64 for API transmission.
        
        Args:
            audio_data: Binary audio data
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            Dictionary with base64-encoded audio ready for API transmission
        """
        mime_types = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "aac": "audio/aac",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
            "m4a": "audio/mp4"
        }
        
        mime_type = mime_types.get(format.lower(), "audio/wav")
        
        return {
            "data": base64.b64encode(audio_data).decode('utf-8'),
            "mimeType": mime_type
        }
    
    def get_audio_info(self, video_file_path: str) -> Dict[str, Any]:
        """
        Get audio information from a video file using ffprobe.
        
        Args:
            video_file_path: Path to the video file
            
        Returns:
            Dictionary containing audio stream information
        """
        try:
            # Run ffprobe command to get information about audio streams
            result = subprocess.run([
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'a:0',  # Select the first audio stream
                '-show_entries', 'stream=codec_name,channels,sample_rate,bit_rate,duration',
                '-of', 'json',
                video_file_path
            ], check=True, capture_output=True, text=True)
            
            # Parse the JSON output
            import json
            info = json.loads(result.stdout)
            
            # Extract the relevant information
            if 'streams' in info and len(info['streams']) > 0:
                return info['streams'][0]
            else:
                logger.warning(f"No audio streams found in {video_file_path}")
                return {}
                
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error: {e.stderr if e.stderr else str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            return {}


def main():
    """Command-line interface for audio extraction."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Extract audio from a video file")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("-o", "--output", help="Output audio file path", required=True)
    parser.add_argument("--format", default="wav", help="Output audio format (default: wav)")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Sample rate in Hz (default: 16000)")
    parser.add_argument("--channels", type=int, default=1, help="Number of audio channels (default: 1)")
    parser.add_argument("--codec", help="Audio codec to use (default: based on format)")
    parser.add_argument("--info", action="store_true", help="Only show audio information, don't extract")
    
    args = parser.parse_args()
    
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        extractor = AudioExtractor()
        
        if args.info:
            # Just show audio information
            info = extractor.get_audio_info(args.video_path)
            print("Audio Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
            return
        
        # Extract audio
        logger.info(f"Extracting audio from {args.video_path}")
        logger.info(f"Output format: {args.format}, Sample rate: {args.sample_rate}, Channels: {args.channels}")
        
        audio_data = extractor.extract_audio_from_file(
            args.video_path,
            sample_rate=args.sample_rate,
            channels=args.channels,
            format=args.format,
            codec=args.codec
        )
        
        # Save audio
        extractor.save_audio(audio_data, args.output)
        logger.info(f"Audio extracted and saved to {args.output}")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
