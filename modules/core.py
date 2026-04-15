import os
import sys
import threading
from typing import Any, Callable, List, Optional

import modules.globals as globals
from modules.typing import Frame

# Supported file extensions
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".webp"]
VIDEO_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".gif"]


def has_image_extension(image_path: str) -> bool:
    """Check if a file path has a valid image extension."""
    return any(image_path.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)


def has_video_extension(video_path: str) -> bool:
    """Check if a file path has a valid video extension."""
    return any(video_path.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)


def is_image(image_path: str) -> bool:
    """Verify that a path points to a valid, existing image file."""
    if not image_path or not os.path.isfile(image_path):
        return False
    return has_image_extension(image_path)


def is_video(video_path: str) -> bool:
    """Verify that a path points to a valid, existing video file."""
    if not video_path or not os.path.isfile(video_path):
        return False
    return has_video_extension(video_path)


def get_temp_directory_path(target_path: str) -> str:
    """Return the temporary working directory path for a given target file."""
    target_name, _ = os.path.splitext(os.path.basename(target_path))
    target_directory_path = os.path.dirname(target_path)
    return os.path.join(target_directory_path, ".dlc_temp", target_name)


def get_temp_output_video_path(target_path: str) -> str:
    """Return the path for the temporary output video before post-processing."""
    temp_directory_path = get_temp_directory_path(target_path)
    return os.path.join(temp_directory_path, "temp.mp4")


def create_temp(target_path: str) -> None:
    """Create the temporary directory for processing a target file."""
    temp_directory_path = get_temp_directory_path(target_path)
    Path = __import__("pathlib").Path
    Path(temp_directory_path).mkdir(parents=True, exist_ok=True)


def move_temp(target_path: str, output_path: str) -> None:
    """Move the temporary output video to the final output path."""
    temp_output_path = get_temp_output_video_path(target_path)
    if os.path.isfile(temp_output_path):
        if os.path.isfile(output_path):
            os.remove(output_path)
        os.rename(temp_output_path, output_path)


def clean_temp(target_path: str) -> None:
    """Remove the temporary directory and its contents after processing.

    Note: if globals.keep_frames is True, the frame directory is preserved
    so you can inspect individual extracted frames after a run. Handy for
    debugging face-swap quality on specific frames.
    """
    import shutil
    temp_directory_path = get_temp_directory_path(target_path)
    # Also remove the parent .dlc_temp directory if it ends up empty after cleanup
    parent_directory_path = os.path.dirname(temp_directory_path)
    if globals.keep_frames and os.path.isdir(temp_directory_path):
        # Keep the frames directory but still remove the temp video file to save space
        temp_video_path = get_temp_output_video_path(target_path)
        if os.path.isfile(temp_video_path):
            os.remove(temp_video_path)
        return
    if os.path.isdir(temp_directory_path):
        shutil.rmtree(temp_directory_path)
    # Clean up the parent .dlc_temp folder if it is now empty
    if os.path.isdir(parent_directory_path) and not os.listdir(parent_directory_path):
        os.rmdir(parent_directory_path)
