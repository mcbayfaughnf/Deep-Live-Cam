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
    """Remove the temporary directory and its contents after processing."""
    import shutil
    temp_directory_path = get_temp_directory_path(target_path)
    parent_directory_path = os.path.dirname(temp_directory_path)
    if globals.keep_frames and os.path.isdir(temp_directory_path):
        return
    if os.path.isdir(temp_directory_path):
        shutil.rmtree(temp_directory_path)
    # Remove parent .dlc_temp dir if empty
    if os.path.isdir(parent_directory_path) and not os.listdir(parent_directory_path):
        shutil.rmtree(parent_directory_path)


def conditional_process() -> None:
    """
    Route processing based on the type of target provided:
    - image target  -> process as single image
    - video target  -> extract frames, process each, re-encode
    """
    from modules import processors

    if is_image(globals.target_path):
        processors.process_image(globals.source_path, globals.target_path, globals.output_path)
        processors.release_resources()
    elif is_video(globals.target_path):
        processors.process_video(globals.source_path, globals.target_path)
        processors.release_resources()
    else:
        sys.exit("Error: target path is neither a valid image nor a valid video file.")


def limit_resources() -> None:
    """Apply memory and CPU constraints defined in globals."""
    if globals.max_memory:
        memory = globals.max_memory * 1024 ** 3  # convert GB to bytes
        if sys.platform == "darwin":
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))
        elif sys.platform == "linux":
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))
        # Windows memory limiting is handled via job objects; skip for now


def pre_check() -> bool:
    """Perform pre-flight checks before processing begins."""
    if sys.version_info < (3, 9):
        print("Error: Python 3.9 or higher is required.")
        return False
    if not globals.source_path:
        print("Error: no source path provided.")
        return False
    if not globals.target_path:
        print("Error: no target path provided.")
        return False
    if not os.path.isfile(globals.source_path):
        print(f"Error: source file not found: {globals.source_path}")
        return False
    if not os.path.isfile(globals.target_path):
        print(f"Error: target file not found: {globals.target_path}")
        return False
    return True
