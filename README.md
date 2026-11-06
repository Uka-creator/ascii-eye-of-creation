# ASCII Eye of Creation

Realtime ASCII-д хувиргадаг хөдөлгөөнт engine. Python (терминал) + vanilla JS (веб) хоёр хувилбар.

Зурган дээрх `eyes_of_creation.py` шиг — гэхдээ амьд, хөдөлдөг.

## Юу байгаа

```
ascii-eye-of-creation/
├── eyes_of_creation.py     # Терминал: webcam → ASCII (realtime)
├── ascii_engine.py         # Цөм: frame → ASCII string (дахин ашиглах)
├── renderers.py            # ASCII gradient-үүд + box-drawing renderer
├── requirements.txt
└── web/
    ├── index.html          # Веб: canvas → ASCII (хөдөлгөөнтэй)
    └── shaders.js          # Гурван хөдөлгөөнт дүрс: eye, tunnel, particles
```

## Суулгах

```bash
pip install -r requirements.txt
python3 eyes_of_creation.py
```

Гарах товч: `q`

## Хөдөлгөөнт дүрсүүд (терминал)

| № | Нэр | Тайлбар |
|---|---|---|
| 1 | Eye | Нүд анивчина, хүүхэн хараа cursor руу харна |
| 2 | Tunnel | Хязгааргүй нурсан ASCII tunnel |
| 3 | Matrix | Унаж буй тэмдэгтийн бороо |
| 4 | Webcam | Камерыг шууд ASCII болгоно |

Дүрс солих: `1` `2` `3` `4` дарах.

## Веб хувилбар

`web/index.html`-ийг browser-т нээнэ. Гурван дүрс + FPS counter байна.

