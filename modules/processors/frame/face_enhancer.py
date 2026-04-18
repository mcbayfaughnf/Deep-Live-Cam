import threading
import cv2
import numpy
from gfpgan.utils import GFPGANer

import modules.globals
from modules.typing import Frame, Face
from modules.core import update_status

FACE_ENHANCER = None
THREAD_LOCK = threading.Lock()
NAME = 'DLC.FACE-ENHANCER'


def get_face_enhancer() -> GFPGANer:
    global FACE_ENHANCER

    with THREAD_LOCK:
        if FACE_ENHANCER is None:
            # Uses GFPGAN v1.4 for face restoration/enhancement
            FACE_ENHANCER = GFPGANer(
                model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth',
                upscale=1,
                arch='clean',
                channel_multiplier=2,
                bg_upsampler=None
            )
    return FACE_ENHANCER


def pre_check() -> bool:
    """Check that required dependencies are available."""
    try:
        import gfpgan  # noqa: F401
        return True
    except ImportError:
        update_status('gfpgan is not installed. Install it via: pip install gfpgan', NAME)
        return False


def pre_start() -> bool:
    """Validate settings before processing begins."""
    return True


def enhance_face(target_face: Face, temp_frame: Frame) -> Frame:
    """
    Enhance the face region in the given frame using GFPGAN.

    Args:
        target_face: Detected face object with bounding box info.
        temp_frame: The full video frame (numpy array).

    Returns:
        Frame with the enhanced face composited back in.
    """
    start_x, start_y, end_x, end_y = map(int, target_face['bbox'])
    # Add padding around face region for better enhancement context
    padding_x = int((end_x - start_x) * 0.1)
    padding_y = int((end_y - start_y) * 0.1)

    start_x = max(0, start_x - padding_x)
    start_y = max(0, start_y - padding_y)
    end_x = min(temp_frame.shape[1], end_x + padding_x)
    end_y = min(temp_frame.shape[0], end_y + padding_y)

    face_crop = temp_frame[start_y:end_y, start_x:end_x]

    if face_crop.size == 0:
        return temp_frame

    # GFPGAN expects BGR input
    _, _, enhanced_face = get_face_enhancer().enhance(
        face_crop,
        has_aligned=False,
        only_center_face=True,
        paste_back=True
    )

    if enhanced_face is not None:
        enhanced_face = cv2.resize(enhanced_face, (end_x - start_x, end_y - start_y))
        temp_frame[start_y:end_y, start_x:end_x] = enhanced_face

    return temp_frame


def process_frame(source_face: Face, temp_frame: Frame) -> Frame:
    """Process a single frame by enhancing detected faces."""
    from modules.face_analyser import get_one_face

    target_face = get_one_face(temp_frame)
    if target_face:
        temp_frame = enhance_face(target_face, temp_frame)
    return temp_frame


def process_frames(source_path: str, temp_frame_paths: list, progress=None) -> None:
    """Process multiple frame files on disk."""
    for temp_frame_path in temp_frame_paths:
        temp_frame = cv2.imread(temp_frame_path)
        result = process_frame(None, temp_frame)
        cv2.imwrite(temp_frame_path, result)
        if progress:
            progress.update(1)


def process_image(source_path: str, target_path: str, output_path: str) -> None:
    """Enhance faces in a single image file."""
    target_frame = cv2.imread(target_path)
    result = process_frame(None, target_frame)
    cv2.imwrite(output_path, result)


def process_video(source_path: str, temp_frame_paths: list) -> None:
    """Entry point for video face enhancement."""
    from modules.utilities import multi_process_frame
    multi_process_frame(source_path, temp_frame_paths, process_frames)
