# -*- coding: utf-8 -*-
"""
ASCII Eye of Creation — realtime ASCII art engine.

Гурван үндсэн хэсэг:
  * ascii_engine  — frame-ийг ASCII болгох цөм
  * renderers     — тэмдэгтийн градиент, дүрсний рендер
  * eyes_of_creation — терминалын апп (webcam + дүрсүүд)

Тусдаа файл болгон салгасан нь тест бичих, дахин ашиглахад хялбар байхын тулд.
"""

__version__ = '1.0.0'

from .ascii_engine import frame_to_ascii, AsciiFrame
from .renderers import GRADIENTS, render_eye, render_tunnel, render_matrix

__all__ = [
    'frame_to_ascii',
    'AsciiFrame',
    'GRADIENTS',
    'render_eye',
    'render_tunnel',
    'render_matrix',
]
