"""
Pyunto Intelligence - Image Upload Example

This script demonstrates how to upload an image to the Pyunto Intelligence API
and process the results.
"""

import os
import sys
import base64
import json
import requests
from PIL import Image
import argparse

def encode_image_to_base64(image_path):
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Base64 encoded string
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def analyze_image(api_key, assistant_id, image_path):
    """
    Upload and analyze an image using Pyunto Intelligence API.
    
    Args:
        api_key: Pyunto Intelligence API key
        assistant_id: ID of the assistant to use
        image_path: Path to the image file
        
    Returns:
        dict: API response
    """
    # Validate inputs
    if not api_key:
        raise ValueError("API key is required")
    if not assistant_id:
        raise ValueError("Assistant ID is required")
    if not image_path or not os.path.exists(image_path):
        raise ValueError(f"Image file not found: {image_path}")
    
    # Get image MIME type based on extension
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif'
    }.get(ext, 'image/jpeg')
    
    # Encode image to base64
    encoded_image = encode_image_to_base64(image_path)
    if not encoded_image:
        raise ValueError("Failed to encode image")
    
    # Prepare API request
    url = "https://a.pyunto.com/api/i/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "assistantId": assistant_id,
        "type": "image",
        "data": encoded_image,
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
    parser = argparse.ArgumentParser(description='Upload an image to Pyunto Intelligence API')
    parser.add_argument('--image', required=True, help='Path to the image file')
    parser.add_argument('--api-key', required=True, help='Pyunto Intelligence API key')
    parser.add_argument('--assistant-id', required=True, help='Assistant ID to use')
    parser.add_argument('--output', help='Output file to save results (optional)')
    
    args = parser.parse_args()
    
    try:
        # Analyze image
        results = analyze_image(args.api_key, args.assistant_id, args.image)
        
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
