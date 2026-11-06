# -*- coding: utf-8 -*-
"""
Тестүүд — engine-ийн математик зөв эсэхийг шалгана.

Ажиллуулах:
    python3 -m pytest test_ascii_engine.py -v
    python3 test_ascii_engine.py          # pytest-гүй ч ажиллана
"""

from __future__ import annotations

import numpy as np

from ascii_art.ascii_engine import AsciiEngine, GRADIENTS, frame_to_ascii
from ascii_art.renderers import render_eye, render_tunnel, render_matrix


def test_engine_dimensions():
    engine = AsciiEngine(cols=80, rows=20)
    frame = np.zeros((240, 320), dtype=np.uint8)
    result = engine.frame_to_ascii(frame)
    assert result.height == 20, result.height
    assert all(len(line) == result.width for line in result.lines)
    # Aspect засвар: 320/240 * 20 / 0.5 = 53.3 → 53
    assert 45 <= result.width <= 60, result.width


def test_all_black_is_darkest_char():
    engine = AsciiEngine(cols=40, rows=10, gradient='classic')
    frame = np.zeros((100, 200), dtype=np.uint8)
    result = engine.frame_to_ascii(frame)
    assert set(''.join(result.lines)) == {' '}, 'Хар frame нь зөвхөн space байх ёстой'


def test_all_white_is_brightest_char():
    engine = AsciiEngine(cols=40, rows=10, gradient='classic')
    frame = np.full((100, 200), 255, dtype=np.uint8)
    result = engine.frame_to_ascii(frame)
    ramp = GRADIENTS['classic']
    assert set(''.join(result.lines)) == {ramp[-1]}, 'Цагаан frame хамгийн тод тэмдэгт'


def test_rgb_and_gray_agree():
    """Саарал болон ижил утгатай RGB нь ойролцоо үр дүн өгөх ёстой."""
    gray = np.full((100, 200), 128, dtype=np.uint8)
    rgb = np.full((100, 200, 3), 128, dtype=np.uint8)
    a = frame_to_ascii(gray, cols=40, rows=10)
    b = frame_to_ascii(rgb, cols=40, rows=10)
    assert a.lines == b.lines


def test_rgba_ignores_alpha():
    rgba = np.zeros((100, 200, 4), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = 0  # alpha бүрэн тунгалаг — үл хайхрана
    result = frame_to_ascii(rgba, cols=40, rows=10, gradient='classic')
    assert set(''.join(result.lines)) == {GRADIENTS['classic'][-1]}


def test_invalid_gradient_raises():
    try:
        AsciiEngine(gradient='nope')
    except ValueError as exc:
        assert 'Unknown gradient' in str(exc)
    else:
        raise AssertionError('ValueError гарах ёстой байсан')


def test_invalid_shape_raises():
    engine = AsciiEngine()
    try:
        engine.frame_to_ascii(np.zeros((5,), dtype=np.uint8))
    except ValueError:
        pass
    else:
        raise AssertionError('ValueError гарах ёстой байсан')


def test_renderers_return_correct_shape():
    for render in (render_eye, render_tunnel, render_matrix):
        lines = render(rows=16, cols=48, t=0.5)
        assert len(lines) == 16, f'{render.__name__}: мөрийн тоо'
        assert all(len(line) == 48 for line in lines), f'{render.__name__}: өргөн'


def test_renderers_are_deterministic_at_same_t():
    for render in (render_eye, render_tunnel, render_matrix):
        assert render(rows=16, cols=48, t=1.25) == render(rows=16, cols=48, t=1.25)


def test_renderers_change_over_time():
    """Хөдөлгөөн байгаа эсэх — t өөрчлөгдөхөд зураг өөрчлөгдөх ёстой."""
    for render in (render_eye, render_tunnel, render_matrix):
        a = render(rows=16, cols=48, t=0.0)
        b = render(rows=16, cols=48, t=1.7)
        assert a != b, f'{render.__name__} хөдөлгөөнгүй байна'


def test_eye_blinks():
    """Анивчих үед нүд хаагдах ёстой — мөрүүд хоосон болно."""
    open_lines = render_eye(rows=24, cols=64, t=0.0)
    # Period 4.2, duration 0.32 → оргил нь ~0.16 сек дээр
    closed_lines = render_eye(rows=24, cols=64, t=0.16)
    open_ink = sum(line.count('@') for line in open_lines)
    closed_ink = sum(line.count('@') for line in closed_lines)
    assert closed_ink <= open_ink, 'Анивчсан үед тод талбай багасах ёстой'


# ----------------------------------------------------------------------
# pytest-гүй ажиллуулах
# ----------------------------------------------------------------------
def _run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    failed = 0
    for test in tests:
        try:
            test()
            print(f'  ✓ {test.__name__}')
        except AssertionError as exc:
            failed += 1
            print(f'  ✗ {test.__name__}: {exc}')
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f'  ✗ {test.__name__}: {type(exc).__name__}: {exc}')
    print(f'\n{len(tests) - failed}/{len(tests)} тест давлаа')
    return 1 if failed else 0


if __name__ == '__main__':
    import sys
    sys.exit(_run_all())
