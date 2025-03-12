# Audio Extraction Tool

This tool allows you to extract audio tracks from video files for analysis with Pyunto Intelligence.

## Features

- Extract high-quality audio from video files
- Convert to WAV format with configurable settings
- Flexible sample rate and channel options
- Integration with Pyunto Intelligence API
- Support for multiple video formats
- Batch processing capabilities

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

### Basic Audio Extraction

```python
from audio_extractor import AudioExtractor

# Initialize the extractor
extractor = AudioExtractor()

# Read a video file
with open("example.mp4", "rb") as f:
    video_data = f.read()

# Extract audio
audio_data = extractor.extract_audio(video_data)

# Save the audio
with open("extracted_audio.wav", "wb") as f:
    f.write(audio_data)
```

### Command-Line Interface

```bash
# Extract audio from a video file
python audio_extractor_cli.py input.mp4 --output output.wav
```

### Integration with Pyunto Intelligence

```python
import base64
import requests
from audio_extractor import AudioExtractor

# Initialize the extractor
extractor = AudioExtractor()

# Read a video file
with open("example.mp4", "rb") as f:
    video_data = f.read()

# Extract audio
audio_data = extractor.extract_audio(video_data)

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
        "type": "audio",
        "data": base64.b64encode(audio_data).decode('utf-8'),
        "mimeType": "audio/wav"
    }
)

analysis_result = response.json()
print(analysis_result)
```

## Customization

### Adjusting Audio Quality

You can customize the audio extraction settings:

```python
# Extract audio with specific sample rate and channels
audio_data = extractor.extract_audio(
    video_data,
    sample_rate=44100,  # 44.1 kHz
    channels=2,         # Stereo
    format="wav"        # Output format
)
```

### Supported Formats

The tool supports various output formats including:

- WAV (default)
- MP3
- FLAC
- AAC
- OGG

Example:
```python
# Extract audio as MP3
audio_data = extractor.extract_audio(video_data, format="mp3")
```

## Batch Processing

The command-line interface supports batch processing of multiple files:

```bash
python audio_extractor_cli.py videos_directory/ --output output_directory/ --recursive
```

## Limitations

- Processing large video files can be memory-intensive
- Some audio codecs may not be supported by your FFmpeg installation

## License

This tool is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.
