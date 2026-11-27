#!/usr/bin/env python3
"""Render the README animation from aosdf-flow.json (optional: pip install Pillow).

The checked interactive Archify HTML is independent of this small GitHub-friendly renderer.
"""
from pathlib import Path
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
spec = json.loads((HERE / 'aosdf-flow.json').read_text())
WIDTH, HEIGHT = 1280, 640
BACKGROUND, TEXT, MUTED = '#0b1425', '#e8f2ff', '#9fb0cc'
ACCENT = '#66e5d7'
font_paths = [os.environ.get('AOSDF_DIAGRAM_FONT', ''), '/System/Library/Fonts/Supplemental/Arial.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'C:/Windows/Fonts/arial.ttf']
def font(size):
    for candidate in font_paths:
        if candidate and Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size=size)

lanes = {lane['id']: index for index, lane in enumerate(spec['lanes'])}
positions = {n['id']: (32 + n['col'] * 207, 115 + lanes[n['lane']] * 147) for n in spec['nodes']}
node_width, node_height = 178, 78

def frame(index):
    image = Image.new('RGB', (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for x in range(0, WIDTH, 32): draw.line((x, 0, x, HEIGHT), fill='#111e32')
    for y in range(0, HEIGHT, 32): draw.line((0, y, WIDTH, y), fill='#111e32')
    draw.text((32, 26), 'AOSDF  /  STRATEGY TO VERIFIED PRODUCT INCREMENTS', font=font(25), fill=TEXT)
    draw.text((32, 65), 'Framework defines the work. Coordination connects the owners. Agents implement bounded tasks.', font=font(17), fill=MUTED)
    for lane in spec['lanes']:
        row = lanes[lane['id']]
        draw.text((32, 94 + row * 147), lane['label'].upper(), font=font(12), fill=MUTED)
    for edge in spec['edges']:
        x1, y1 = positions[edge['from']]; x2, y2 = positions[edge['to']]
        if x1 == x2:
            points = [(x1+node_width/2, y1+node_height), (x2+node_width/2, y2)]
            tip = points[-1]; tri = [(tip[0], tip[1]-3), (tip[0]-5, tip[1]-11), (tip[0]+5, tip[1]-11)]
        else:
            points = [(x1+node_width, y1+node_height/2), (x2, y2+node_height/2)]
            tip = points[-1]; tri = [(tip[0]-3, tip[1]), (tip[0]-11, tip[1]-5), (tip[0]-11, tip[1]+5)]
        draw.line(points, fill='#4b6588', width=2)
        draw.polygon(tri, fill='#7797bd')
    active = spec['mainPath'][(index // 6) % len(spec['mainPath'])]
    for node in spec['nodes']:
        x, y = positions[node['id']]
        color = '#ae9af6' if node['type']=='database' else '#ef9cba' if node['type']=='security' else ACCENT
        selected = node['id'] == active
        if selected:
            draw.rounded_rectangle((x-4, y-4, x+node_width+4, y+node_height+4), radius=17, outline=color, width=2)
        draw.rounded_rectangle((x, y, x+node_width, y+node_height), radius=13, fill='#173149' if selected else '#122238', outline=color if selected else '#3a506f', width=2)
        draw.text((x+node_width/2, y+25), node['label'], font=font(17), fill=TEXT, anchor='mm')
        draw.text((x+node_width/2, y+53), node.get('sublabel',''), font=font(12), fill=MUTED, anchor='mm')
    draw.line((32, 548, 1248, 548), fill='#2c4160', width=1)
    label=next(n['label'] for n in spec['nodes'] if n['id']==active)
    draw.ellipse((34, 573, 44, 583), fill=ACCENT)
    draw.text((57, 566), label, font=font(21), fill=TEXT)
    draw.text((32, 608), 'ILLUSTRATIVE FLOW  •  Human scope and approvals remain authoritative  •  Evidence informs the next increment', font=font(14), fill=MUTED)
    return image

frames=[frame(i) for i in range(48)]
frames[0].save(HERE/'aosdf-flow.png')
frames[0].save(HERE/'aosdf-flow.gif',save_all=True,append_images=frames[1:],duration=140,loop=0,optimize=True)
print('Rendered static PNG and 48-frame GIF from the public flow specification.')
