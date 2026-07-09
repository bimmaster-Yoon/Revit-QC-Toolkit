# -*- coding: utf-8 -*-

"""Generate 64x64 transparent PNG icons for the Revit QC Toolkit."""

import os

from PIL import Image, ImageDraw


SIZE = 64
SCALE = 8
CANVAS = SIZE * SCALE
NAVY = (20, 37, 61, 255)
ORANGE = (244, 124, 32, 255)
WHITE = (255, 255, 255, 255)
TRANSPARENT = (255, 255, 255, 0)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSION_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, os.pardir, os.pardir)
)
PANEL_DIR = os.path.join(EXTENSION_DIR, "Revit QC.tab", "QC Toolkit.panel")


def p(value):
    return int(round(value * SCALE))


def box(left, top, right, bottom):
    return [p(left), p(top), p(right), p(bottom)]


def points(values):
    return [(p(x), p(y)) for x, y in values]


def new_icon():
    image = Image.new("RGBA", (CANVAS, CANVAS), TRANSPARENT)
    return image, ImageDraw.Draw(image)


def draw_document(draw, left=12, top=7, right=48, bottom=57):
    draw.rounded_rectangle(
        box(left, top, right, bottom),
        radius=p(3),
        fill=WHITE,
        outline=NAVY,
        width=p(2.5)
    )
    draw.polygon(
        points([(right - 11, top), (right, top + 11), (right - 11, top + 11)]),
        fill=(255, 237, 223, 255),
        outline=ORANGE
    )
    draw.line(
        points([(right - 11, top), (right - 11, top + 11), (right, top + 11)]),
        fill=ORANGE,
        width=p(2)
    )


def draw_check(draw, offset_x=0, offset_y=0, color=ORANGE, width=4):
    draw.line(
        points([
            (22 + offset_x, 36 + offset_y),
            (30 + offset_x, 44 + offset_y),
            (46 + offset_x, 26 + offset_y)
        ]),
        fill=color,
        width=p(width),
        joint="curve"
    )


def icon_full_qc():
    image, draw = new_icon()
    draw_document(draw)
    draw.line(points([(18, 24), (35, 24)]), fill=NAVY, width=p(2))
    draw.line(points([(18, 31), (31, 31)]), fill=NAVY, width=p(2))
    draw_check(draw, offset_x=2, offset_y=4)
    return image


def icon_quick_qc():
    image, draw = new_icon()
    lightning = points([
        (34, 5), (14, 34), (28, 34), (22, 58),
        (50, 27), (36, 27), (44, 5)
    ])
    draw.polygon(lightning, fill=ORANGE)
    draw.line(lightning + [lightning[0]], fill=NAVY, width=p(2), joint="curve")
    draw.line(
        points([(36, 43), (42, 49), (54, 36)]),
        fill=NAVY,
        width=p(3.5),
        joint="curve"
    )
    return image


def icon_settings():
    image, draw = new_icon()
    for y in (17, 32, 47):
        draw.line(points([(9, y), (55, y)]), fill=NAVY, width=p(2.5))

    for x, y in ((23, 17), (42, 32), (29, 47)):
        draw.ellipse(box(x - 5, y - 5, x + 5, y + 5), fill=WHITE, outline=NAVY, width=p(2))
        draw.ellipse(box(x - 2, y - 2, x + 2, y + 2), fill=ORANGE)

    return image


def icon_open_report():
    image, draw = new_icon()
    draw_document(draw, left=28, top=6, right=54, bottom=43)
    draw.polygon(points([(7, 21), (25, 21), (30, 27), (57, 27), (53, 55), (9, 55)]), fill=WHITE)
    draw.line(
        points([(7, 21), (25, 21), (30, 27), (57, 27), (53, 55), (9, 55), (7, 21)]),
        fill=NAVY,
        width=p(2.5),
        joint="curve"
    )
    draw.line(points([(9, 28), (57, 28)]), fill=ORANGE, width=p(3))
    return image


def icon_help():
    image, draw = new_icon()
    draw_document(draw, left=13, top=6, right=51, bottom=58)
    draw.arc(box(21, 17, 43, 39), start=200, end=500, fill=ORANGE, width=p(3.5))
    draw.line(points([(32, 37), (32, 44)]), fill=ORANGE, width=p(3.5))
    draw.ellipse(box(29.5, 48, 34.5, 53), fill=NAVY)
    return image


def save_icon(image, button_name):
    output_path = os.path.join(PANEL_DIR, button_name, "icon.png")
    resized = image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    resized.save(output_path, "PNG", optimize=True)
    print("Created: {0}".format(output_path))


def main():
    icon_map = [
        ("01 DOC QC.pushbutton", icon_full_qc),
        ("02 QC Lite.pushbutton", icon_quick_qc),
        ("04 QC Settings.pushbutton", icon_settings),
        ("05 Report.pushbutton", icon_open_report),
        ("06 Help.pushbutton", icon_help)
    ]

    for button_name, icon_factory in icon_map:
        save_icon(icon_factory(), button_name)


if __name__ == "__main__":
    main()
