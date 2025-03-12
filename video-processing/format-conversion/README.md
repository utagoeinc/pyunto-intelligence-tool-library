# Video Format Conversion Tool

This tool allows you to convert video files to different formats and optimize them for processing with Pyunto Intelligence.

## Features

- Convert videos between common formats (MP4, AVI, MOV, etc.)
- Resize videos to specific resolutions
- Adjust frame rates and bit rates
- Batch processing capabilities
- Integration with Pyunto Intelligence workflow

## Requirements

- Python 3.6 or higher
- FFmpeg installed on your system
- Required Python packages:
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
   pip install typing pathlib
   ```

## Usage

### Basic Video Conversion

```python
from video_converter import VideoConverter

# Initialize the converter
converter = VideoConverter()

# Convert a video file
converter.convert_video(
    input_path="input.avi",
    output_path="output.mp4",
    format="mp4"
)
```

### Command-Line Interface

```bash
# Convert a video file
python video_converter_cli.py input.avi --output output.mp4 --format mp4

# Resize a video
python video_converter_cli.py input.mp4 --output output.mp4 --width 1280 --height 720

# Change frame rate
python video_converter_cli.py input.mp4 --output output.mp4 --fps 30
```

### Integration with Pyunto Intelligence Workflow

```python
from video_converter import VideoConverter
from pyunto_tools.video_processing.frame_extraction import FrameExtractor
import base64
import requests

# Step 1: Convert video to optimal format
converter = VideoConverter()
converter.convert_video(
    input_path="input.mov",
    output_path="optimized.mp4",
    format="mp4",
    width=1280,
    height=720,
    fps=30
)

# Step 2: Extract frames from optimized video
extractor = FrameExtractor()
frames = extractor.extract_frames_from_file("optimized.mp4", fps=1)

# Step 3: Analyze frames with Pyunto Intelligence
api_key = "YOUR_API_KEY"
api_url = "https://a.pyunto.com/api/i/v1"

# Analyze the first frame
frame_data = frames[1]  # Get the first frame
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

## Customization Options

The VideoConverter class provides numerous options for customizing the output video:

### Video Size
```python
converter.convert_video(
    input_path="input.mp4",
    output_path="output.mp4",
    width=1920,
    height=1080
)
```

### Frame Rate
```python
converter.convert_video(
    input_path="input.mp4",
    output_path="output.mp4",
    fps=30
)
```

### Video Codec
```python
converter.convert_video(
    input_path="input.mp4",
    output_path="output.mp4",
    codec="libx264"  # H.264 codec
)
```

### Bit Rate
```python
converter.convert_video(
    input_path="input.mp4",
    output_path="output.mp4",
    bitrate="5000k"  # 5 Mbps
)
```

## Batch Processing

The command-line interface supports batch processing of multiple files:

```bash
python video_converter_cli.py videos_directory/ --output output_directory/ --format mp4 --recursive
```

## Limitations

- Processing large video files can be time-consuming and memory-intensive
- Some video formats or codecs may not be supported by your FFmpeg installation

## License

This tool is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.
