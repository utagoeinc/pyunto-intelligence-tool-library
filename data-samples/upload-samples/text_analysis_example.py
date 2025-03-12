"""
Pyunto Intelligence - Text Analysis Example

This script demonstrates how to submit text data to the Pyunto Intelligence API
for analysis and process the results.
"""

import os
import sys
import base64
import json
import requests
import argparse

def encode_text_to_base64(text_content):
    """
    Encode text content to base64 string.
    
    Args:
        text_content: Text content to encode
        
    Returns:
        str: Base64 encoded string
    """
    try:
        if isinstance(text_content, str):
            text_bytes = text_content.encode('utf-8')
        else:
            text_bytes = text_content
        return base64.b64encode(text_bytes).decode('utf-8')
    except Exception as e:
        print(f"Error encoding text: {e}")
        return None

def load_text_from_file(file_path):
    """
    Load text content from a file.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        str: Text content
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading text file: {e}")
        return None

def analyze_text(api_key, assistant_id, text_content):
    """
    Upload and analyze text content using Pyunto Intelligence API.
    
    Args:
        api_key: Pyunto Intelligence API key
        assistant_id: ID of the assistant to use
        text_content: Text content to analyze
        
    Returns:
        dict: API response
    """
    # Validate inputs
    if not api_key:
        raise ValueError("API key is required")
    if not assistant_id:
        raise ValueError("Assistant ID is required")
    if not text_content:
        raise ValueError("Text content is required")
    
    # Encode text to base64
    encoded_text = encode_text_to_base64(text_content)
    if not encoded_text:
        raise ValueError("Failed to encode text")
    
    # Prepare API request
    url = "https://a.pyunto.com/api/i/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "assistantId": assistant_id,
        "type": "text",
        "data": encoded_text,
        "mimeType": "text/plain"
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
    parser = argparse.ArgumentParser(description='Upload text to Pyunto Intelligence API for analysis')
    parser.add_argument('--text', help='Text content to analyze')
    parser.add_argument('--file', help='Path to the text file to analyze')
    parser.add_argument('--api-key', required=True, help='Pyunto Intelligence API key')
    parser.add_argument('--assistant-id', required=True, help='Assistant ID to use')
    parser.add_argument('--output', help='Output file to save results (optional)')
    
    args = parser.parse_args()
    
    try:
        # Check if text content is provided directly or via file
        if args.text:
            text_content = args.text
        elif args.file:
            if not os.path.exists(args.file):
                raise ValueError(f"Text file not found: {args.file}")
            text_content = load_text_from_file(args.file)
            if not text_content:
                raise ValueError("Failed to load text from file")
        else:
            raise ValueError("Either --text or --file must be provided")
        
        # Analyze text
        results = analyze_text(args.api_key, args.assistant_id, text_content)
        
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
