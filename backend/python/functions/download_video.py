"""
Download Video from URL

This script downloads a video from a URL and saves it to the storage/uploads folder.
"""

import os
import sys
import requests
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def get_storage_path() -> str:
    """
    Get the storage/uploads directory path.
    
    Returns:
        Absolute path to storage/uploads directory
    """
    # Get the backend directory (2 levels up from this file: functions -> python -> backend)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
    storage_path = os.path.join(backend_dir, 'storage', 'uploads')
    
    # Create directory if it doesn't exist
    os.makedirs(storage_path, exist_ok=True)
    
    return storage_path


def download_video(url: str, file_name: str) -> str:
    """
    Download a video from a URL and save it to storage/uploads folder.
    
    Args:
        url: URL of the video to download
        file_name: Name of the file (without extension) to save as
        
    Returns:
        Full path to the downloaded video file
        
    Raises:
        ValueError: If URL is invalid or download fails
        FileNotFoundError: If storage directory cannot be created
        
    Example:
        from functions.download_video import download_video
        
        video_path = download_video("https://example.com/video.mp4", "my_video")
        # Returns: "/path/to/backend/storage/uploads/my_video.mp4"
    """
    if not url:
        raise ValueError("URL cannot be empty")
    
    if not file_name:
        raise ValueError("File name cannot be empty")
    
    # Get storage path
    storage_dir = get_storage_path()
    
    # Construct full file path
    file_path = os.path.join(storage_dir, f"{file_name}.mp4")
    
    # Check if file already exists
    if os.path.exists(file_path):
        print(f"Warning: File {file_path} already exists. It will be overwritten.")
    
    try:
        print(f"Downloading video from: {url}")
        print(f"Saving to: {file_path}")
        
        # Download the video with streaming to handle large files
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))
        if total_size > 0:
            print(f"File size: {total_size / (1024 * 1024):.2f} MB")
        
        # Download and save the file
        downloaded = 0
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        
        print(f"\n✓ Video downloaded successfully: {file_path}")
        print(f"  File size: {os.path.getsize(file_path) / (1024 * 1024):.2f} MB")
        
        return file_path
        
    except requests.exceptions.RequestException as e:
        # Clean up partial file if download failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise ValueError(f"Failed to download video: {str(e)}")
    except Exception as e:
        # Clean up partial file if download failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise ValueError(f"Error downloading video: {str(e)}")


if __name__ == "__main__":
    """
    CLI usage:
    python download_video.py <url> <file_name>
    
    Example:
    python download_video.py https://example.com/video.mp4 my_video
    """
    if len(sys.argv) < 3:
        print("Usage: python download_video.py <url> <file_name>")
        print("Example: python download_video.py https://example.com/video.mp4 my_video")
        sys.exit(1)
    
    url = sys.argv[1]
    file_name = sys.argv[2]
    
    try:
        video_path = download_video(url, file_name)
        print(f"\nSuccess! Video saved to: {video_path}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

