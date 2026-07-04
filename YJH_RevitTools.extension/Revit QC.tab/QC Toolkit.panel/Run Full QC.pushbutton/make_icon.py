# -*- coding: utf-8 -*-
"""QC Report pyRevit 버튼용 32x32 투명 PNG 아이콘 생성기."""

from __future__ import print_function

import os

# Pillow가 없다면 일반 Python 환경에서 아래 명령으로 먼저 설치하세요.
# python -m pip install Pillow
try:
    from PIL import Image, ImageDraw
except ImportError:
    raise ImportError(
        "Pillow가 필요합니다. 명령 프롬프트에서 "
        "'python -m pip install Pillow'를 실행한 뒤 다시 시도하세요."
    )


SIZE = 32
SCALE = 4
CANVAS_SIZE = SIZE * SCALE

TRANSPARENT = (0, 0, 0, 0)
LINE_COLOR = (68, 72, 78, 255)
ORANGE = (242, 132, 35, 255)


def point(x_value, y_value):
    """32px 좌표를 고해상도 작업 좌표로 변환한다."""
    return (int(x_value * SCALE), int(y_value * SCALE))


def line_width(value):
    """선 굵기를 고해상도 작업 좌표로 변환한다."""
    return max(1, int(value * SCALE))


def draw_circle(draw, center_x, center_y, radius, fill):
    """지정한 중심점에 원을 그린다."""
    left = int((center_x - radius) * SCALE)
    top = int((center_y - radius) * SCALE)
    right = int((center_x + radius) * SCALE)
    bottom = int((center_y + radius) * SCALE)
    draw.ellipse((left, top, right, bottom), fill=fill)


def create_icon():
    """문서, 체크마크, AI 노드로 구성된 아이콘을 생성한다."""
    image = Image.new(
        "RGBA",
        (CANVAS_SIZE, CANVAS_SIZE),
        TRANSPARENT
    )
    draw = ImageDraw.Draw(image)

    # 문서 외곽선과 접힌 모서리
    document_outline = [
        point(6, 3),
        point(18, 3),
        point(23, 8),
        point(23, 27),
        point(6, 27),
        point(6, 3)
    ]
    draw.line(
        document_outline,
        fill=LINE_COLOR,
        width=line_width(1.7),
        joint="curve"
    )

    draw.line(
        [point(18, 3), point(18, 8), point(23, 8)],
        fill=LINE_COLOR,
        width=line_width(1.7),
        joint="curve"
    )

    # 문서 안쪽의 오렌지 체크마크
    draw.line(
        [point(9, 17), point(13, 21), point(20, 13)],
        fill=ORANGE,
        width=line_width(2.4),
        joint="curve"
    )

    # 오른쪽의 작은 AI 네트워크 연결선
    node_points = [
        point(25, 12),
        point(28.5, 17),
        point(25, 22)
    ]
    draw.line(
        node_points,
        fill=LINE_COLOR,
        width=line_width(1.1),
        joint="curve"
    )
    draw.line(
        [node_points[0], node_points[2]],
        fill=LINE_COLOR,
        width=line_width(1.1)
    )

    # AI 노드 3개
    draw_circle(draw, 25, 12, 1.55, ORANGE)
    draw_circle(draw, 28.5, 17, 1.55, ORANGE)
    draw_circle(draw, 25, 22, 1.55, ORANGE)

    # 고해상도 작업본을 32x32로 축소해 선을 부드럽게 만든다.
    try:
        resampling_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resampling_filter = Image.LANCZOS

    image = image.resize(
        (SIZE, SIZE),
        resampling_filter
    )

    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "icon.png"
    )
    image.save(output_path, "PNG")

    print("icon.png 생성 완료: {0}".format(output_path))


if __name__ == "__main__":
    create_icon()
