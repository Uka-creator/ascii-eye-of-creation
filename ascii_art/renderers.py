# -*- coding: utf-8 -*-
"""
Дүрсний render-ууд — эдгээр нь зурагнаас биш, математикаас ASCII үүсгэдэг.

Бүх render нь (rows, cols, t) авч, тэмдэгтийн мөрүүдийн list буцаана.
Гол санаа: 3D цэг эсвэл SDF (signed distance field) бичиж, түүнийгээ
тод байдал болгож, ASCII болгох.
"""

from __future__ import annotations

import math

import numpy as np

# ----------------------------------------------------------------------
# Координатын тор үүсгэгч (кэшлэгддэг — frame бүрт дахин үүсгэхгүй)
# ----------------------------------------------------------------------
_grid_cache: dict[tuple[int, int], tuple[np.ndarray, np.ndarray]] = {}


def _grid(rows: int, cols: int) -> tuple[np.ndarray, np.ndarray]:
    """−1..1 хооронд нормчлогдсон (X, Y) тор.

    Y нь дээрээс доош, X нь зүүнээс баруун. Aspect-ийг коригдсон.
    """
    key = (rows, cols)
    if key not in _grid_cache:
        y = np.linspace(-1.0, 1.0, rows, dtype=np.float32)[:, None]
        x = np.linspace(-1.0, 1.0, cols, dtype=np.float32)[None, :]
        _grid_cache[key] = (np.broadcast_to(x, (rows, cols)), np.broadcast_to(y, (rows, cols)))
    return _grid_cache[key]


def _to_ascii(brightness: np.ndarray, ramp: str) -> list[str]:
    """0..1 тод байдал → тэмдэгтийн мөрүүд."""
    n = len(ramp)
    idx = np.clip((brightness * (n - 1)).round().astype(np.int16), 0, n - 1)
    chars = np.array(list(ramp))[idx]
    return [''.join(row) for row in chars]


# ======================================================================
# 1. НҮД — анивчина, хүүхэн хараа хөдөлнө
# ======================================================================
def render_eye(rows: int = 40, cols: int = 110, t: float = 0.0,
               ramp: str = ' .·+*#%@') -> list[str]:
    """Амьд нүд.

    * Цагаан хэсэг нь суперэллипс (squircle) — нүдний хэлбэр
    * Хүүхэн хараа нь sin/cos-оор дугуйлан хөдөлнө
    * Анивчих нь үе үе (blink waveform) дээд/доод зовхийг хаана
    """
    X, Y = _grid(rows, cols)

    # ---- Хүүхэн харааны байрлал: Лиссажу муруй ----
    px = 0.30 * math.sin(t * 0.9)
    py = 0.14 * math.sin(t * 1.4 + 0.7)

    # ---- Нүдний бүрхүүл (superellipse) ----
    eye_w, eye_h = 0.92, 0.52
    ex = X / eye_w
    ey = (Y - py * 0.35) / eye_h
    sclera = 1.0 - (np.abs(ex) ** 2.4 + np.abs(ey) ** 2.4)
    sclera = np.clip(sclera * 3.2, 0.0, 1.0)

    # ---- Хүүхэн хараа ----
    r = np.sqrt((X - px) ** 2 + ((Y - py) * 1.55) ** 2)
    pupil = np.clip((0.20 - r) * 9.0, 0.0, 1.0)

    # ---- Цахилдаг (iris) цагираг ----
    iris = np.clip((0.34 - r) * 7.0, 0.0, 1.0) - np.clip((0.20 - r) * 9.0, 0.0, 1.0)
    iris = np.clip(iris, 0.0, 1.0)

    # Цахилдагт радиаль ширхэг — амьд мэт харагдуулна
    angle = np.arctan2(Y - py, X - px)
    fibers = 0.5 + 0.5 * np.sin(angle * 22 + t * 1.2)
    iris = iris * (0.55 + 0.45 * fibers)

    # ---- Гялбаа (specular highlight) ----
    gloss = np.clip((0.075 - np.sqrt((X - px - 0.10) ** 2 + (Y - py + 0.09) ** 2)) * 18.0, 0.0, 1.0)

    # ---- Зовхи — анивчих ----
    # 0..1: 0 = нээлттэй, 1 = бүрэн анивчсан
    blink = _blink(t)
    lid_top = -0.52 + blink * 1.04
    lid_bottom = 0.52 - blink * 1.04

    brightness = sclera * 0.30
    brightness += iris * 0.72
    brightness -= pupil * 0.95      # хүүхэн хараа хамгийн бараан
    brightness += gloss * 0.85

    # Зовхины гадна тал харанхуй
    outside = (Y < lid_top) | (Y > lid_bottom)
    brightness = np.where(outside, brightness * 0.06, brightness)

    # Зовхины ирмэг дээр тод шугам
    edge = (np.abs(Y - lid_top) < 0.035) | (np.abs(Y - lid_bottom) < 0.035)
    brightness = np.where(edge & (sclera > 0.02), 0.95, brightness)

    brightness = np.clip(brightness, 0.0, 1.0)
    return _to_ascii(brightness, ramp)


def _blink(t: float, period: float = 4.2, duration: float = 0.32) -> float:
    """Анивчих долгион — ихэнх хугацаанд 0, үе үе 1 хүртэл."""
    phase = (t % period) / period
    if phase > duration:
        return 0.0
    p = phase / duration
    return math.sin(p * math.pi) ** 0.6


# ======================================================================
# 2. TUNNEL — хязгааргүй нурсан ASCII
# ======================================================================
def render_tunnel(rows: int = 40, cols: int = 110, t: float = 0.0,
                  ramp: str = ' .:-=+*#%@') -> list[str]:
    """Хязгааргүй tunnel — z өсөх тусам тэмдэгт жижигрэнэ."""
    X, Y = _grid(rows, cols)

    r = np.sqrt(X ** 2 + (Y * 1.9) ** 2) + 1e-6
    theta = np.arctan2(Y * 1.9, X)

    # Гүн: логарифм — төв рүү төгсгөлгүй
    z = 1.0 / r

    # Хоёр давхаргат тор — цагираг ба радиаль шугам
    rings = 0.5 + 0.5 * np.sin(z * 4.0 - t * 3.0)
    spokes = 0.5 + 0.5 * np.sin(theta * 12.0 + t * 0.6)

    # Гүнээс хамаарсан бүдгэрэлт (fog)
    fog = np.clip(z * 0.16, 0.0, 1.0)

    brightness = (rings * spokes) ** 1.7 * fog
    brightness = np.clip(brightness, 0.0, 1.0)
    return _to_ascii(brightness, ramp)


# ======================================================================
# 3. MATRIX — унаж буй тэмдэгтийн бороо
# ======================================================================
def render_matrix(rows: int = 40, cols: int = 110, t: float = 0.0,
                  ramp: str = ' .:-=+*#%@', seed: int = 7) -> list[str]:
    """Matrix бороо — багана бүр өөрийн хурдтай унана."""
    rng = np.random.default_rng(seed)
    X, Y = _grid(rows, cols)

    # Багана бүрийн фазын зөрүү ба хурд (тогтмол — кэшгүй тул seed-ээр)
    phase = (rng.random(cols).astype(np.float32) * 6.283)[None, :]
    speed = (0.7 + rng.random(cols).astype(np.float32) * 1.5)[None, :]

    head = np.sin((Y * 2.6 + t * speed) + phase)
    trail = np.sin((Y * 9.0 + t * speed * 1.4) + phase * 1.7)

    brightness = np.clip(head * 0.55 + trail * 0.35 + 0.25, 0.0, 1.0) ** 2.4
    return _to_ascii(brightness, ramp)


# ======================================================================
# Дүрсний бүртгэл
# ======================================================================
RENDERERS = {
    '1': ('eye', render_eye),
    '2': ('tunnel', render_tunnel),
    '3': ('matrix', render_matrix),
}


# Функциональ нэрийн бүртгэл (manifest / README-д зориулж)
GRADIENTS = {
    'classic': ' .:-=+*#%@',
    'blocks': ' ░▒▓█',
    'binary': ' 01',
    'dots': ' ·∙•●',
    'shade': ' .·:;+=xX$&@',
    'eyes': ' .·+*#%&@',
}
