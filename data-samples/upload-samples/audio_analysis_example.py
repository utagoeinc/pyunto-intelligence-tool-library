"""
Pyunto Intelligence - Audio Analysis Example

This script demonstrates how to upload audio files to the Pyunto Intelligence API
and process the results.
"""

import os
import sys
import base64
import json
import requests
import argparse

def encode_audio_to_base64(audio_path):
    """
    Encode an audio file to base64 string.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        str: Base64 encoded string
    """
    try:
        with open(audio_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding audio: {e}")
        return None

def analyze_audio(api_key, assistant_id, audio_path):
    """
    Upload and analyze an audio file using Pyunto Intelligence API.
    
    Args:
        api_key: Pyunto Intelligence API key
        assistant_id: ID of the assistant to use
        audio_path: Path to the audio file
        
    Returns:
        dict: API response
    """
    # Validate inputs
    if not api_key:
        raise ValueError("API key is required")
    if not assistant_id:
        raise ValueError("Assistant ID is required")
    if not audio_path or not os.path.exists(audio_path):
        raise ValueError(f"Audio file not found: {audio_path}")
    
    # Get audio MIME type based on extension
    ext = os.path.splitext(audio_path)[1].lower()
    mime_type = {
        '.mp3': 'audio/mp3',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4',
        '.flac': 'audio/flac'
    }.get(ext, 'audio/mp3')
    
    # Encode audio to base64
    encoded_audio = encode_audio_to_base64(audio_path)
    if not encoded_audio:
        raise ValueError("Failed to encode audio")
    
    # Prepare API request
    url = "https://a.pyunto.com/api/i/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "assistantId": assistant_id,
        "type": "audio",
        "data": encoded_audio,
        "mimeType": mime_type
    }
    
    # Make API request
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response text: {response.text}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def display_results(results, output_file=None):
    """
    Display the results from the API response.
    
    Args:
        results: API response data
        output_file: Optional file to save results to
    """
    if not results:
        print("No results to display")
        return
    
    # Pretty print results
    formatted_json = json.dumps(results, indent=2)
    print("\nAPI Response:")
    print(formatted_json)
    
    # Save to file if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write(formatted_json)
            print(f"\nResults saved to {output_file}")
        except Exception as e:
            print(f"Error saving results to file: {e}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Upload an audio file to Pyunto Intelligence API')
    parser.add_argument('--audio', required=True, help='Path to the audio file')
    parser.add_argument('--api-key', required=True, help='Pyunto Intelligence API key')
    parser.add_argument('--assistant-id', required=True, help='Assistant ID to use')
    parser.add_argument('--output', help='Output file to save results (optional)')
    
    args = parser.parse_args()
    
    try:
        # Analyze audio
        results = analyze_audio(args.api_key, args.assistant_id, args.audio)
        
        # Display results
        display_results(results, args.output)
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
