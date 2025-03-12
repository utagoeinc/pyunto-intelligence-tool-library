# Frame Extraction Tool

This tool allows you to extract individual frames from video files for analysis with Pyunto Intelligence.

## Features

- Extract frames at specified intervals (e.g., 1 frame per second)
- High-quality JPEG output with configurable quality settings
- Integration with Pyunto Intelligence API
- Support for multiple video formats
- Batch processing capabilities

## Requirements

- Python 3.6 or higher
- FFmpeg installed on your system
- Required Python packages:
  - fastapi (optional, for API endpoint)
  - typing
  - pathlib

## Installation

1. Ensure you have FFmpeg installed:

   **Ubuntu/Debian**:
   ```bash
   sudo apt-get update
   sudo apt-get install ffmpeg
   ```

   **macOS**:
   ```bash
   brew install ffmpeg
   ```

   **Windows**:
   Download from [FFmpeg's official site](https://ffmpeg.org/download.html)

2. Install the required Python packages:
   ```bash
   pip install fastapi typing pathlib
   ```

## Usage

### Basic Frame Extraction

```python
from frame_extractor import FrameExtractor

# Initialize the extractor
extractor = FrameExtractor()

# Read a video file
with open("example.mp4", "rb") as f:
    video_data = f.read()

# Extract frames
frames = extractor.extract_frames(video_data, fps=1)  # 1 frame per second

# Process the frames
for frame_num, frame_data in frames.items():
    print(f"Frame {frame_num}: {len(frame_data)} bytes")
    
    # Save the frame
    with open(f"frame_{frame_num}.jpg", "wb") as f:
        f.write(frame_data)
```

### Command-Line Interface

```bash
# Extract frames from a video file
python frame_extractor_cli.py input.mp4 --fps 1 --output-dir ./frames
```

### Integration with Pyunto Intelligence

```python
import base64
import requests
from frame_extractor import FrameExtractor

# Initialize the extractor
extractor = FrameExtractor()

# Read a video file
with open("example.mp4", "rb") as f:
    video_data = f.read()

# Extract frames
frames = extractor.extract_frames(video_data, fps=1)

# Analyze a specific frame with Pyunto Intelligence
frame_data = frames[1]  # Get the first frame

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

## Customization

### Adjusting Frame Rate

You can customize the frame extraction rate using the `fps` parameter:

```python
# Extract 2 frames per second
frames = extractor.extract_frames(video_data, fps=2)

# Extract 1 frame every 5 seconds
frames = extractor.extract_frames(video_data, fps=0.2)
```

### Adjusting JPEG Quality

You can adjust the quality of the extracted JPEG frames:

```python
# High quality setting (lower value = higher quality, range: 1-31)
frames = extractor.extract_frames(video_data, quality=2)

# Standard quality setting
frames = extractor.extract_frames(video_data, quality=5)
```

## Limitations

- Memory usage can be high for long videos with high frame rates
- Processing time increases with video length and desired frame rate
- Some video formats may not be supported by your FFmpeg installation

## License

This tool is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.
