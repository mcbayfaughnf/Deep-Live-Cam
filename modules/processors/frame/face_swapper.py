import cv2
import insightface
import threading
from typing import Any, List, Optional
import modules.globals as globals
from modules.core import update_status
from modules.face_analyser import get_one_face, get_many_faces

NAME = 'DLC.FACE-SWAPPER'

face_swapper = None
thread_lock = threading.Lock()


def get_face_swapper() -> Any:
    global face_swapper
    with thread_lock:
        if face_swapper is None:
            model_path = globals.face_swapper_model_path
            face_swapper = insightface.model_zoo.get_model(
                model_path,
                providers=globals.execution_providers
            )
    return face_swapper


def pre_check() -> bool:
    """Verify required model files exist before processing."""
    import os
    model_path = globals.face_swapper_model_path
    if not os.path.isfile(model_path):
        update_status(f'Model not found: {model_path}', NAME)
        return False
    return True


def pre_start() -> bool:
    """Validate source and target inputs before starting."""
    if not globals.source_path:
        update_status('No source image selected.', NAME)
        return False
    if not globals.target_path:
        update_status('No target selected.', NAME)
        return False
    source_face = get_one_face(cv2.imread(globals.source_path))
    if source_face is None:
        update_status('No face detected in source image.', NAME)
        return False
    return True


def swap_face(source_face: Any, target_face: Any, temp_frame: Any) -> Any:
    """Swap a single face in the frame."""
    return get_face_swapper().get(
        temp_frame,
        target_face,
        source_face,
        paste_back=True
    )


def process_frame(source_face: Any, temp_frame: Any) -> Any:
    """Process a single frame, swapping all detected faces."""
    if globals.many_faces:
        many_faces = get_many_faces(temp_frame)
        if many_faces:
            for target_face in many_faces:
                temp_frame = swap_face(source_face, target_face, temp_frame)
    else:
        target_face = get_one_face(temp_frame)
        if target_face:
            temp_frame = swap_face(source_face, target_face, temp_frame)
    return temp_frame


def process_frames(source_path: str, temp_frame_paths: List[str], progress: Any = None) -> None:
    """Process a list of frame image files on disk."""
    source_face = get_one_face(cv2.imread(source_path))
    for temp_frame_path in temp_frame_paths:
        temp_frame = cv2.imread(temp_frame_path)
        if temp_frame is not None:
            result = process_frame(source_face, temp_frame)
            cv2.imwrite(temp_frame_path, result)
        if progress:
            progress.update(1)


def process_image(source_path: str, target_path: str, output_path: str) -> None:
    """Swap faces in a single image and save to output_path."""
    source_face = get_one_face(cv2.imread(source_path))
    target_frame = cv2.imread(target_path)
    result = process_frame(source_face, target_frame)
    cv2.imwrite(output_path, result)


def process_video(source_path: str, temp_frame_paths: List[str]) -> None:
    """Entry point for video processing — delegates to process_frames."""
    process_frames(source_path, temp_frame_paths)
