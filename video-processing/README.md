# Video Processing Tools

This directory contains utilities and sample code for processing video files for use with Pyunto Intelligence.

## Overview

The video processing tools help you prepare video content for analysis by Pyunto Intelligence. These tools allow you to:

- Extract individual frames from videos for image analysis
- Extract audio tracks from videos for audio analysis
- Convert videos to different formats for optimal processing

## Available Tools

### Frame Extraction

The [frame-extraction](./frame-extraction) directory contains tools for extracting frames from videos:

- Python-based frame extraction using FFmpeg
- Frame sampling at specified intervals
- Batch processing for multiple videos

### Audio Extraction

The [audio-extraction](./audio-extraction) directory provides tools for extracting audio from videos:

- Audio track isolation
- Format conversion to WAV and other formats
- Audio preprocessing tools

### Format Conversion

The [format-conversion](./format-conversion) directory includes utilities for converting videos between formats:

- Video codec conversion
- Resolution adjustment
- Bitrate optimization for processing

## Requirements

Most tools in this directory require FFmpeg to be installed on your system:

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### macOS
```bash
brew install ffmpeg
```

### Windows
Download from [FFmpeg's official site](https://ffmpeg.org/download.html) or install via package managers like Chocolatey:
```
choco install ffmpeg
```

## Usage Examples

### Basic Video Processing

```python
from pyunto_tools.video_processing import MediaProcessor

# Initialize the processor
processor = MediaProcessor()

# Process a video file
with open("example.mp4", "rb") as f:
    video_data = f.read()

# Extract audio and frames
result = processor.process_video_request(video_data)

# Access the processed data
audio_base64 = result["audio"]["data"]
frames = result["frames"]  # Dictionary mapping frame numbers to images
```

### Integration with Pyunto Intelligence

```python
import base64
import requests

# After processing a video with the MediaProcessor
processor = MediaProcessor()
with open("example.mp4", "rb") as f:
    video_data = f.read()
result = processor.process_video_request(video_data)

# Analyze a specific frame with Pyunto Intelligence
frame_data = base64.b64decode(result["frames"]["1"]["data"])  # Get the first frame

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
        "type": "image",
        "data": base64.b64encode(frame_data).decode('utf-8'),
        "mimeType": "image/jpeg"
    }
)

analysis_result = response.json()
print(analysis_result)
```

## Performance Considerations

- Processing large video files can be memory-intensive
- Consider using the batch processing tools for large collections of videos
- Adjust frame extraction rates based on your specific needs

## License

This tool is licensed under the Apache License 2.0 - see the [LICENSE](../LICENSE) file for details.
