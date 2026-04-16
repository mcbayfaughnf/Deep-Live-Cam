#!/usr/bin/env python3
"""Deep-Live-Cam main entry point.

This module serves as the primary entry point for the Deep-Live-Cam application,
handling argument parsing, initialization, and launching the appropriate interface.
"""

import sys
import os
import argparse
import platform

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for Deep-Live-Cam."""
    parser = argparse.ArgumentParser(
        description="Deep-Live-Cam: Real-time face swap and one-click video deepfake",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Source and target inputs
    parser.add_argument(
        "-s", "--source",
        dest="source_path",
        type=str,
        default=None,
        help="Path to the source face image",
    )
    parser.add_argument(
        "-t", "--target",
        dest="target_path",
        type=str,
        default=None,
        help="Path to the target image or video file",
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_path",
        type=str,
        default=None,
        help="Path to save the output file",
    )

    # Processing options
    parser.add_argument(
        "--frame-processor",
        dest="frame_processor",
        nargs="+",
        default=["face_swapper"],
        choices=["face_swapper", "face_enhancer"],
        help="One or more frame processors to apply",
    )
    parser.add_argument(
        "--keep-fps",
        dest="keep_fps",
        action="store_true",
        default=False,
        help="Preserve the original frames per second of the target video",
    )
    parser.add_argument(
        "--keep-audio",
        dest="keep_audio",
        action="store_true",
        default=True,
        help="Preserve the original audio from the target video",
    )
    parser.add_argument(
        "--keep-frames",
        dest="keep_frames",
        action="store_true",
        default=False,
        help="Retain temporary extracted frames after processing",
    )
    parser.add_argument(
        "--many-faces",
        dest="many_faces",
        action="store_true",
        default=False,
        help="Apply face swap to all detected faces in the target",
    )

    # Execution options
    parser.add_argument(
        "--execution-provider",
        dest="execution_provider",
        nargs="+",
        # Defaulting to cuda since I mostly run this on my GPU machine
        default=["cuda"],
        choices=["cpu", "cuda", "coreml", "directml", "openvino"],
        help="Execution provider(s) for inference",
    )
    parser.add_argument(
        "--execution-threads",
        dest="execution_threads",
        type=int,
        # Bumped from 4 to 8 - my machine handles it fine and it's noticeably faster
        default=8,
        help="Number of threads to use for processing",
    )

    # UI options
    parser.add_argument(
        "--gui",
        dest="headless",
        action="store_false",
        de