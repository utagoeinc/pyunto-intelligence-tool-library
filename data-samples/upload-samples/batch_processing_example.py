"""
Pyunto Intelligence - Batch Processing Example

This script demonstrates how to batch process multiple files using the Pyunto Intelligence API.
It supports processing multiple image, text, or audio files and aggregating the results.
"""

import os
import sys
import base64
import json
import requests
import time
import argparse
import concurrent.futures
from tqdm import tqdm
from pathlib import Path

def encode_file_to_base64(file_path):
    """
    Encode any file to base64 string.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: Base64 encoded string
    """
    try:
        with open(file_path, "rb") as file:
            return base64.b64encode(file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding file {file_path}: {e}")
        return None

def get_file_mime_type(file_path):
    """
    Determine the MIME type based on file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        tuple: (file_type, mime_type)
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    # Image types
    if ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        file_type = "image"
        mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }.get(ext, 'image/jpeg')
    
    # Audio types
    elif ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']:
        file_type = "audio"
        mime_type = {
            '.mp3': 'audio/mp3',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac'
        }.get(ext, 'audio/mp3')
    
    # Text types
    elif ext in ['.txt', '.md', '.csv', '.json', '.xml', '.html']:
        file_type = "text"
        mime_type = {
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html'
        }.get(ext, 'text/plain')
    
    else:
        # Default to binary
        file_type = "unknown"
        mime_type = 'application/octet-stream'
    
    return file_type, mime_type

def process_file(api_key, assistant_id, file_path, delay=0):
    """
    Process a single file using Pyunto Intelligence API.
    
    Args:
        api_key: Pyunto Intelligence API key
        assistant_id: ID of the assistant to use
        file_path: Path to the file
        delay: Optional delay between requests (in seconds)
        
    Returns:
        dict: Result object with file info and API response
    """
    # Get file type and MIME type
    file_type, mime_type = get_file_mime_type(file_path)
    if file_type == "unknown":
        return {
            "file": file_path,
            "status": "error",
            "error": "Unsupported file type"
        }
    
    # Encode file to base64
    encoded_data = encode_file_to_base64(file_path)
    if not encoded_data:
        return {
            "file": file_path,
            "status": "error",
            "error": "Failed to encode file"
        }
    
    # Prepare API request
    url = "https://a.pyunto.com/api/i/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "assistantId": assistant_id,
        "type": file_type,
        "data": encoded_data,
        "mimeType": mime_type
    }
    
    # Add optional delay
    if delay > 0:
        time.sleep(delay)
    
    # Make API request
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return {
                "file": file_path,
                "status": "success",
                "result": response.json()
            }
        else:
            return {
                "file": file_path,
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            "file": file_path,
            "status": "error",
            "error": str(e)
        }

def batch_process_files(api_key, assistant_id, files, parallel=2, delay=0):
    """
    Process multiple files in parallel using Pyunto Intelligence API.
    
    Args:
        api_key: Pyunto Intelligence API key
        assistant_id: ID of the assistant to use
        files: List of file paths
        parallel: Number of parallel requests
        delay: Delay between requests (in seconds)
        
    Returns:
        list: List of result objects
    """
    results = []
    
    # Check for max parallel requests
    parallel = min(parallel, 10)  # Limit to reasonable number
    
    # Process files in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
        # Create futures for each file
        future_to_file = {
            executor.submit(process_file, api_key, assistant_id, file, delay): file 
            for file in files
        }
        
        # Process as they complete with progress bar
        with tqdm(total=len(files), desc="Processing files") as pbar:
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        "file": file,
                        "status": "error",
                        "error": str(e)
                    })
                pbar.update(1)
    
    return results

def find_files(directory, recursive=False, file_types=None):
    """
    Find files in a directory matching specified criteria.
    
    Args:
        directory: Directory to search
        recursive: Whether to search recursively
        file_types: List of file extensions to include (e.g., ['.jpg', '.png'])
        
    Returns:
        list: List of matching file paths
    """
    if not os.path.isdir(directory):
        return []
    
    matching_files = []
    
    # Adjust glob pattern based on recursive flag
    glob_pattern = "**/*" if recursive else "*"
    
    for path in Path(directory).glob(glob_pattern):
        if not path.is_file():
            continue
            
        # Apply file type filter if specified
        if file_types and path.suffix.lower() not in file_types:
            continue
            
        matching_files.append(str(path))
    
    return matching_files

def aggregate_results(results):
    """
    Aggregate and summarize batch processing results.
    
    Args:
        results: List of result objects
        
    Returns:
        dict: Summary statistics
    """
    total = len(results)
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = total - success_count
    
    # Group by file type
    file_types = {}
    for result in results:
        file_path = result.get("file", "")
        file_type, _ = get_file_mime_type(file_path)
        if file_type not in file_types:
            file_types[file_type] = 0
        file_types[file_type] += 1
    
    # Collect error messages
    errors = [
        {"file": r.get("file"), "error": r.get("error")}
        for r in results if r.get("status") == "error"
    ]
    
    return {
        "total_files": total,
        "successful": success_count,
        "failed": error_count,
        "success_rate": (success_count / total * 100) if total > 0 else 0,
        "file_types": file_types,
        "errors": errors[:10]  # Show first 10 errors only
    }

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Batch process files with Pyunto Intelligence API')
    parser.add_argument('--directory', required=True, help='Directory containing files to process')
    parser.add_argument('--api-key', required=True, help='Pyunto Intelligence API key')
    parser.add_argument('--assistant-id', required=True, help='Assistant ID to use')
    parser.add_argument('--recursive', action='store_true', help='Search directory recursively')
    parser.add_argument('--parallel', type=int, default=2, help='Number of parallel requests (max 10)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests in seconds')
    parser.add_argument('--output', help='Output file to save results (optional)')
    parser.add_argument('--type', choices=['image', 'text', 'audio', 'all'], default='all', 
                        help='Filter files by type')
    
    args = parser.parse_args()
    
    try:
        # Determine file types to include
        file_types = None
        if args.type == 'image':
            file_types = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        elif args.type == 'text':
            file_types = ['.txt', '.md', '.csv', '.json', '.xml', '.html']
        elif args.type == 'audio':
            file_types = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        
        # Find files
        files = find_files(args.directory, args.recursive, file_types)
        if not files:
            print(f"No matching files found in {args.directory}")
            sys.exit(1)
        
        print(f"Found {len(files)} files to process")
        
        # Process files
        results = batch_process_files(
            args.api_key, 
            args.assistant_id, 
            files, 
            args.parallel, 
            args.delay
        )
        
        # Aggregate results
        summary = aggregate_results(results)
        print("\nProcessing Summary:")
        print(f"Total files: {summary['total_files']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success rate: {summary['success_rate']:.2f}%")
        
        print("\nFile types processed:")
        for file_type, count in summary['file_types'].items():
            print(f"  {file_type}: {count}")
        
        if summary['errors']:
            print("\nSample errors:")
            for error in summary['errors']:
                print(f"  {os.path.basename(error['file'])}: {error['error']}")
        
        # Save full results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump({
                    "summary": summary,
                    "detailed_results": results
                }, f, indent=2)
            print(f"\nDetailed results saved to {args.output}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
