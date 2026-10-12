#!/usr/bin/env python3
"""Render exported fabrication files using gerbv and Pillow.

Gerbv's PNG backend omits KiCad G85 slots. Temporary Gerber strokes derived
from those drill commands make the slots visible without changing fab files.
X2 attributes are also stripped only from temporary viewer inputs.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BOARDS = ['a2ext-carrier', 'a2ext-vga', 'a2ext-dvi']


def slots_gerber(drill):
    """Return a viewer layer for the actual metric/absolute G85 drill slots."""
    assert 'METRIC' in drill and 'G90' in drill
    tools = {number: diameter for number, diameter in re.findall(r'^T(\d+)C([\d.]+)', drill, re.M)}
    commands = ['G04 Viewer-only slot geometry derived from Excellon G85*',
                '%FSLAX46Y46*%', '%MOMM*%', '%LPD*%']
    for number, diameter in tools.items():
        commands.append(f'%ADD{10+int(number)}C,{diameter}*%')
    current = None
    count = 0
    for line in drill.splitlines():
        tool = re.fullmatch(r'T(\d+)', line)
        if tool:
            current = tool[1]
        slot = re.fullmatch(r'X([\d.-]+)Y([\d.-]+)G85X([\d.-]+)Y([\d.-]+)', line)
        if slot:
            assert current in tools
            x1, y1, x2, y2 = [round(float(value)*1e6) for value in slot.groups()]
            commands.extend([f'D{10+int(current)}*', f'X{x1}Y{y1}D02*', f'X{x2}Y{y2}D01*'])
            count += 1
    commands.append('M02*')
    return '\n'.join(commands)+'\n', count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gerbv', default='gerbv', help='gerbv executable path')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='a2ext-gerber-render-') as tmp:
        temp = Path(tmp)
        for board in BOARDS:
            folder = ROOT/'hw'/board
            view = temp/board
            view.mkdir()
            for source in (folder/'gerbers').iterdir():
                if source.suffix == '.gbrjob':
                    continue
                (view/source.name).write_text(re.sub(r'^%T[FAOD][^\n]*\n', '', source.read_text(), flags=re.M))
            slot_data, count = slots_gerber((view/(board+'-PTH.drl')).read_text())
            slot_file = view/'slots-viewer-only.gbr'
            slot_file.write_text(slot_data)
            if board == 'a2ext-dvi':
                assert count == 4
            for side, prefix in [('top', 'F'), ('bottom', 'B')]:
                suffixes = ['-NPTH.drl', '-PTH.drl',
                            f'-{prefix}_Silkscreen.'+('gto' if prefix == 'F' else 'gbo'),
                            f'-{prefix}_Mask.'+('gts' if prefix == 'F' else 'gbs'),
                            f'-{prefix}_Cu.'+('gtl' if prefix == 'F' else 'gbl'), '-Edge_Cuts.gm1']
                paths = [view/(board+suffix) for suffix in suffixes]
                colors = ['#080c0cff', '#080c0cff', '#f5f3eaff', '#d9b965ff', '#246b48ff', '#18222cff']
                if count:
                    paths.insert(0, slot_file)
                    colors.insert(0, '#080c0cff')
                command = [args.gerbv, '-x', 'png', '-a', '-b', '#18222c', '-w',
                           '1600x1300' if board == 'a2ext-carrier' else '1300x1300', '-B', '3']
                for color in colors:
                    command.extend(['-f', color])
                if side == 'bottom':
                    command.extend(['-m', 'Y'])
                command.extend(['-o', str(folder/'previews'/('gerber-'+side+'.png')), *map(str, paths)])
                result = subprocess.run(command, check=True, text=True, capture_output=True, env=os.environ.copy())
                assert not result.stderr.strip(), result.stderr
                print(board, side, 'rendered;', count, 'drill slots')
    canvas = Image.new('RGB', (1800, 820), '#f2f1ec')
    draw = ImageDraw.Draw(canvas)
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font, small = ImageFont.truetype(font_path, 24), ImageFont.truetype(font_path, 18)
    for board, x, width in [('a2ext-carrier', 20, 850), ('a2ext-vga', 885, 440), ('a2ext-dvi', 1340, 440)]:
        picture = Image.open(ROOT/'hw'/board/'previews/gerber-top.png').convert('RGB')
        picture.thumbnail((width, 710))
        canvas.paste(picture, (x+(width-picture.width)//2, 80+(710-picture.height)//2))
        draw.text((x+5, 20), 'a2ext '+board.removeprefix('a2ext-').upper()+' / PCB-P2-THT', fill='#18222c', font=font)
        draw.text((x+5, 53), '99.695 x 78.74 mm' if board == 'a2ext-carrier' else '45 x 45 mm', fill='#41515b', font=small)
    canvas.save(ROOT/'hw/pcb-overview.png')


if __name__ == '__main__':
    main()
