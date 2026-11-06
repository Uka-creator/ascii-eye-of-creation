# -*- coding: utf-8 -*-
"""
ASCII engine — дурын 2D тод байдлын (brightness) массивыг
тэмдэгтийн сүлжээ болгон хувиргах цөм.

Зарчим:
  1. Frame-ийг W×H тэмдэгтийн нүдэнд хуваана
  2. Нүд бүрийн дундаж тод байдлыг (0..255) олно
  3. Тод байдлыг градиентийн индекс болгоно

Тэмдэгтийн нүд нь биеийн pixel-ээс өндөр байдаг тул
aspect ratio-г заавал засна (CHAR_ASPECT ≈ 0.5).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Терминалын нэг тэмдэгт нь өргөнөөсөө ~2 дахин өндөр
CHAR_ASPECT = 0.5

# Тод байдлын градиентүүд — бараан → гэрэлтэй
GRADIENTS = {
    'classic': ' .:-=+*#%@',
    'blocks': ' ░▒▓█',
    'binary': ' 01',
    'dots': ' ·∙•●',
    'shade': ' .·:;+=xX$&@',
    'eyes': ' .·+*#%&@',
}

DEFAULT_GRADIENT = 'eyes'


@dataclass
class AsciiFrame:
    """Нэг render-ийн үр дүн."""

    lines: list[str]
    width: int
    height: int

    def __str__(self) -> str:
        return '\n'.join(self.lines)


class AsciiEngine:
    """Frame → ASCII хөрвүүлэгч.

    Нэг instance-ыг дахин ашиглах нь зүйтэй: дотоод lookup table-г
    кэшлэдэг тул секундэд олон frame боловсруулахад хурдан.
    """

    def __init__(self, cols: int = 120, rows: int = 40, gradient: str = DEFAULT_GRADIENT):
        self.cols = cols
        self.rows = rows
        self.gradient = gradient
        self._lut = None
        self._lut_key = None

    # ------------------------------------------------------------------
    # Property-ууд
    # ------------------------------------------------------------------
    @property
    def gradient(self) -> str:
        return self._gradient

    @gradient.setter
    def gradient(self, name: str):
        if name not in GRADIENTS:
            raise ValueError(f'Unknown gradient: {name!r}. Available: {list(GRADIENTS)}')
        self._gradient = name
        self._lut = None  # кэш хүчингүй

    @property
    def ramp(self) -> str:
        return GRADIENTS[self._gradient]

    # ------------------------------------------------------------------
    # Гол функц
    # ------------------------------------------------------------------
    def frame_to_ascii(self, frame: np.ndarray) -> AsciiFrame:
        """(H, W) эсвэл (H, W, C) массив → AsciiFrame.

        Тод байдлыг дундажлаж буулгана. Хурдны хувьд
        reshape + mean ашигласан (Python for-loop-оос ~50 дахин хурдан).
        """
        gray = self._to_gray(frame)
        small = self._downsample(gray)
        return self._quantize(small)

    def to_string(self, frame: np.ndarray) -> str:
        return str(self.frame_to_ascii(frame))

    # ------------------------------------------------------------------
    # Дотоод
    # ------------------------------------------------------------------
    def _to_gray(self, frame: np.ndarray) -> np.ndarray:
        if frame.ndim == 2:
            return frame.astype(np.float32, copy=False)
        if frame.ndim != 3:
            raise ValueError(f'Expected 2D or 3D array, got shape {frame.shape}')

        channels = frame.shape[2]
        data = frame.astype(np.float32, copy=False)
        if channels == 4:
            data = data[..., :3]
            channels = 3
        if channels == 1:
            return data[..., 0]

        # Rec. 601 luma — нүдний мэдрэмтгий таарсан жин
        return data @ np.array([0.299, 0.587, 0.114], dtype=np.float32)

    def _downsample(self, gray: np.ndarray) -> np.ndarray:
        """Дундажлан буулгах — pixel-ийн бүх мэдээллийг ашиглана.

        Хэрэв frame хэт жижиг бол upscale-гүйгээр шууд буцаана.
        """
        h, w = gray.shape

        # Тэмдэгтийн өндрийг засаж, бодит талбарыг тооцно
        target_h = max(1, min(self.rows, h))
        target_w = max(1, min(self.cols, int(round(w * target_h / h / CHAR_ASPECT))))

        if target_h == h and target_w == w:
            return gray

        # Хэрэв хуваагдахгүй бол хамгийн ойрын хуваагчийг олно
        bh, bw = h // target_h, w // target_w
        if bh < 1 or bw < 1:
            return gray[:target_h, :target_w]

        crop_h, crop_w = bh * target_h, bw * target_w
        blocks = gray[:crop_h, :crop_w].reshape(target_h, bh, target_w, bw)
        return blocks.mean(axis=(1, 3))

    def _quantize(self, small: np.ndarray) -> AsciiFrame:
        """Тод байдлыг тэмдэгт болгоно — lookup table-ээр."""
        lut = self._build_lut()
        idx = np.clip(
            (small / 255.0 * (len(self.ramp) - 1)).round().astype(np.int8),
            0, len(self.ramp) - 1,
        )
        ch = np.array(list(self.ramp))[idx]
        lines = [''.join(row) for row in ch]
        return AsciiFrame(lines=lines, width=small.shape[1], height=small.shape[0])

    def _build_lut(self) -> np.ndarray:
        """0..255 → тэмдэгтийн индекс. Кэшлэгддэг."""
        if self._lut is not None and self._lut_key == (self._gradient,):
            return self._lut

        n = len(self.ramp)
        self._lut = np.clip(
            (np.arange(256) / 255.0 * (n - 1)).round().astype(np.int8), 0, n - 1,
        )
        self._lut_key = (self._gradient,)
        return self._lut


# ----------------------------------------------------------------------
# Функциональ интерфейс (нэг удаагийн хэрэглээнд)
# ----------------------------------------------------------------------
def frame_to_ascii(frame: np.ndarray, cols: int = 120, rows: int = 40,
                   gradient: str = DEFAULT_GRADIENT) -> AsciiFrame:
    """Товчон хэрэглэхэд зориулсан нэг функц."""
    return AsciiEngine(cols=cols, rows=rows, gradient=gradient).frame_to_ascii(frame)
