# -*- coding: utf-8 -*-
"""
Webcam-ийн capture — платформоос хамаарсан шугаман.

OpenCV байхгүй бол тодорхой мессеж өгнө (суулгахыг санал болгоно),
биш бол чимээгүй унахгүй.
"""

from __future__ import annotations


def make_capture(index: int = 0, width: int = 320, height: int = 240):
    """Camera capture нээнэ."""
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            'OpenCV олдсонгүй. Суулгана уу: pip install opencv-python'
        ) from exc

    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f'Камер нээгдсэнгүй (index={index}). Зөвшөөрөл шалгана уу.')

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # хоцролтыг багасгана
    return cap


def read_frame(cap):
    """Нэг frame уншина. Амжилтгүй бол None."""
    ok, frame = cap.read()
    if not ok:
        return None

    # OpenCV BGR буцаадаг — RGB болгож хөрвүүлнэ
    import cv2
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
