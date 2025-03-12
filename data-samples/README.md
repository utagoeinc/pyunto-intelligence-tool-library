# Pyunto Intelligence Data Samples

This directory contains sample code and utilities to help you integrate with the Pyunto Intelligence API. These samples demonstrate how to upload and process different types of data (images, text, audio) using the smart assistant platform.

## Contents

### Upload Samples
The `upload-samples` directory contains executable examples demonstrating how to upload different types of data to Pyunto Intelligence:

- `image_upload_example.py`: Python script for uploading and analyzing images
- `text_analysis_example.py`: Python script for analyzing text data
- `audio_analysis_example.py`: Python script for analyzing audio files
- `batch_processing_example.py`: Python script for processing multiple files in batch
- `node_upload_example.js`: Node.js example for uploading files
- `batch_uploader.html`: Web-based batch uploader interface

### Visualization
The `visualization` directory contains React components for visualizing API usage and results:

- `react/PyuntoUsageDashboard.jsx`: Dashboard component for monitoring API usage

## Getting Started

### Prerequisites
- Pyunto Intelligence API key
- Assistant ID (created on the Pyunto Intelligence platform)
- Python 3.6+ or Node.js 14+ (depending on which example you're using)

### Python Dependencies
For Python examples, install the required dependencies:

```bash
pip install requests pillow tqdm
```

### Node.js Dependencies
For Node.js examples, install the required dependencies:

```bash
npm install axios yargs
```

## Usage Examples

### Image Upload (Python)

```bash
python image_upload_example.py --image path/to/image.jpg --api-key YOUR_API_KEY --assistant-id YOUR_ASSISTANT_ID
```

### Text Analysis (Python)

```bash
python text_analysis_example.py --text "Text to analyze" --api-key YOUR_API_KEY --assistant-id YOUR_ASSISTANT_ID
```

Or analyze a text file:

```bash
python text_analysis_example.py --file path/to/document.txt --api-key YOUR_API_KEY --assistant-id YOUR_ASSISTANT_ID
```

### Audio Analysis (Python)

```bash
python audio_analysis_example.py --audio path/to/audio.mp3 --api-key YOUR_API_KEY --assistant-id YOUR_ASSISTANT_ID
```

### Batch Processing (Python)

```bash
python batch_processing_example.py --directory path/to/files --api-key YOUR_API_KEY --assistant-id YOUR_ASSISTANT_ID --recursive --parallel 3
```

### Node.js Example

```bash
node node_upload_example.js --file path/to/file.jpg --api-key YOUR_API_KEY --assistant-id YOUR_ASSISTANT_ID
```

## Supported File Types

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- GIF (.gif)

### Text
- Plain text (.txt)
- Markdown (.md)
- CSV (.csv)
- JSON (.json)
- XML (.xml)
- HTML (.html)

### Audio
- MP3 (.mp3)
- WAV (.wav)
- OGG (.ogg)
- M4A (.m4a)
- FLAC (.flac)

## Web Uploader

The web-based batch uploader (`batch_uploader.html`) provides a graphical interface for uploading multiple files. To use it:

1. Open the HTML file in a browser
2. Enter your API key and Assistant ID
3. Drag and drop files or click to select files
4. Click "Upload and Process Files"
5. View the processing results

## Usage Dashboard

The `PyuntoUsageDashboard.jsx` React component provides visualization of API usage. To integrate it into your React application:

```jsx
import PyuntoUsageDashboard from './PyuntoUsageDashboard';

function App() {
  return (
    <div>
      <PyuntoUsageDashboard 
        apiKey="YOUR_API_KEY" 
        assistantId="YOUR_ASSISTANT_ID" 
      />
    </div>
  );
}
```

## Response Format

The Pyunto Intelligence API returns data in JSON format. The structure will vary depending on the assistant configuration, but generally includes:

```json
{
  "assistantId": "assistant_123",
  "features": {
    "feature1": "value1",
    "feature2": "value2",
    ...
  },
  "confidence": 0.95,
  "processingTimeMs": 235
}
```

## Error Handling

All samples include error handling to address common issues:
- Invalid API credentials
- Unsupported file types
- Network connection problems
- API rate limiting
- File size restrictions

## License

This sample code is provided under the MIT License. See the LICENSE file for details.
