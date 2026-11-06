# -*- coding: utf-8 -*-
"""
ASCII Eye of Creation — терминалын хөдөлгөөнт ASCII.

Хэрэглээ:
    python3 eyes_of_creation.py            # нүд (default)
    python3 eyes_of_creation.py --fps 60
    python3 eyes_of_creation.py --gradient blocks
    python3 eyes_of_creation.py --webcam   # камерыг ASCII болгоно

Товчнууд (ажиллаж байх үед):
    1 / 2 / 3 / 4  — дүрс солих (eye / tunnel / matrix / webcam)
    g              — градиент солих
    q  эсвэл ESC   — гарах
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time

# Windows дээр ANSI escape-ийг идэвхжүүлнэ
if os.name == 'nt':
    os.system('')

try:
    import numpy as np
except ImportError:
    sys.exit('numpy олдсонгүй. Суулгана уу: pip install numpy')

try:
    from ascii_art.ascii_engine import AsciiEngine, GRADIENTS, DEFAULT_GRADIENT
    from ascii_art.renderers import render_eye, render_tunnel, render_matrix
    from ascii_art.webcam import make_capture, read_frame
except ImportError:
    sys.exit('ascii_art пакет олдсонгүй. Repo root-оос ажиллуулна уу.')

# ----------------------------------------------------------------------
# ANSI
# ----------------------------------------------------------------------
HIDE_CURSOR = '\033[?25l'
SHOW_CURSOR = '\033[?25h'
HOME = '\033[H'
CLEAR = '\033[2J'
RESET = '\033[0m'
CYAN = '\033[36m'
GREEN = '\033[32m'


class TerminalApp:
    """Терминалын main loop.

    Гурван зарчим:
      1. Frame бүрийг НЭГ бичилтээр гаргана (flicker-гүй)
      2. Cursor-ыг нууна, гарахдаа сэргээнэ
      3. Ctrl+C ч гэсэн цэвэрхэн гарна
    """

    MODES = ['eye', 'tunnel', 'matrix', 'webcam']

    def __init__(self, mode: str = 'eye', gradient: str = DEFAULT_GRADIENT,
                 fps: float = 30.0, color: bool = True):
        self.mode = mode if mode in self.MODES else 'eye'
        self.gradient = gradient
        self.fps = fps
        self.color = color and sys.stdout.isatty()

        self.engine = AsciiEngine(gradient=gradient)
        self.capture = None
        self.t0 = time.monotonic()
        self.frame_count = 0
        self.fps_display = 0.0

        self._resize()

    # ------------------------------------------------------------------
    def _resize(self):
        """Терминалын хэмжээгээр cols/rows тохируулна."""
        size = shutil.get_terminal_size(fallback=(120, 40))
        self.engine.cols = max(30, size.columns - 2)
        # Гарчиг + FPS мөрд 2 мөр үлдээнэ
        self.engine.rows = max(10, size.lines - 3)
        self.width, self.height = size.columns, size.lines

    # ------------------------------------------------------------------
    def run(self):
        self._enter()
        try:
            while True:
                loop_start = time.monotonic()

                if self._poll_keys():
                    break

                lines = self._render_frame()
                self._draw(lines)

                self._throttle(loop_start)
        except KeyboardInterrupt:
            pass
        finally:
            self._exit()

    # ------------------------------------------------------------------
    def _render_frame(self) -> list[str]:
        t = time.monotonic() - self.t0

        if self.mode == 'eye':
            return render_eye(self.engine.rows, self.engine.cols, t, self.engine.ramp)
        if self.mode == 'tunnel':
            return render_tunnel(self.engine.rows, self.engine.cols, t, self.engine.ramp)
        if self.mode == 'matrix':
            return render_matrix(self.engine.rows, self.engine.cols, t, self.engine.ramp)
        if self.mode == 'webcam':
            return self._render_webcam()

        return render_eye(self.engine.rows, self.engine.cols, t, self.engine.ramp)

    def _render_webcam(self) -> list[str]:
        if self.capture is None:
            try:
                self.capture = make_capture()
            except RuntimeError as exc:
                return [''] * self.engine.rows + [str(exc)]

        frame = read_frame(self.capture)
        if frame is None:
            return [''] * self.engine.rows
        return self.engine.frame_to_ascii(frame).lines

    # ------------------------------------------------------------------
    def _draw(self, lines: list[str]):
        self.frame_count += 1
        now = time.monotonic()
        elapsed = now - self.t0
        if elapsed >= 0.5:
            self.fps_display = self.frame_count / elapsed
            self.frame_count = 0
            self.t0 = now

        color = CYAN if self.mode in ('eye', 'tunnel') else GREEN
        body = '\n'.join(lines)

        hud = (
            f'{RESET}[{self.mode}]  gradient:{self.gradient}  '
            f'{self.fps_display:5.1f} fps  '
            f'1-4:дүрс  g:градиент  q:гарах'
        )

        # Нэг write — flicker-гүй
        sys.stdout.write(f'{HOME}{color}{body}{RESET}\n{hud}')
        sys.stdout.flush()

    def _throttle(self, loop_start: float):
        target = 1.0 / max(1.0, self.fps)
        spent = time.monotonic() - loop_start
        if spent < target:
            time.sleep(target - spent)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def _poll_keys(self) -> bool:
        """True буцаавал loop зогсоно. Non-blocking (POSIX)."""
        if os.name == 'nt':
            import msvcrt
            if not msvcrt.kbhit():
                return False
            return self._handle_key(msvcrt.getwch())

        import select
        import termios
        import tty

        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if not dr:
            return False

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return self._handle_key(key)

    def _handle_key(self, key: str) -> bool:
        if key in ('q', 'Q', '\x1b'):
            return True
        if key == '1':
            self.mode = 'eye'
        elif key == '2':
            self.mode = 'tunnel'
        elif key == '3':
            self.mode = 'matrix'
        elif key == '4':
            self.mode = 'webcam'
        elif key in ('g', 'G'):
            names = list(GRADIENTS)
            self.gradient = names[(names.index(self.gradient) + 1) % len(names)]
            self.engine.gradient = self.gradient
        elif key in ('+', '='):
            self.fps = min(120.0, self.fps + 5)
        elif key in ('-', '_'):
            self.fps = max(5.0, self.fps - 5)
        return False

    # ------------------------------------------------------------------
    def _enter(self):
        sys.stdout.write(HIDE_CURSOR + CLEAR)
        sys.stdout.flush()

    def _exit(self):
        if self.capture is not None:
            self.capture.release()
        sys.stdout.write(SHOW_CURSOR + RESET + '\n')
        sys.stdout.flush()


# ----------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='eyes_of_creation',
        description='Хөдөлгөөнт ASCII art — нүд, tunnel, matrix, webcam.',
    )
    parser.add_argument('--mode', choices=TerminalApp.MODES, default='eye',
                        help='Эхлэх дүрс (default: eye)')
    parser.add_argument('--gradient', choices=list(GRADIENTS), default=DEFAULT_GRADIENT,
                        help='Тэмдэгтийн градиент')
    parser.add_argument('--fps', type=float, default=30.0, help='Frame rate (default: 30)')
    parser.add_argument('--webcam', action='store_true', help='Шууд webcam-аар эхлэх')
    parser.add_argument('--no-color', action='store_true', help='Өнгөгүй')
    args = parser.parse_args(argv)

    if args.webcam:
        args.mode = 'webcam'

    app = TerminalApp(
        mode=args.mode,
        gradient=args.gradient,
        fps=args.fps,
        color=not args.no_color,
    )
    app.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
