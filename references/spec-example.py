"""Worked example: textbook figure A-4 (TOP221 flyback) replicated as drawn.

Copy this file, then change: the page uuid, DEV entries (probe pins first),
part coordinates, wires, ports/flags and texts for the new figure.
Run:  python -I spec.py
      python -I <skill>/scripts/build.py a4-spec.json place   # must print "all N expected pins match"
      python -I <skill>/scripts/build.py a4-spec.json wire
"""
import os
import sys

# works wherever this file is copied to: specgen.py lives in the skill's scripts/ folder
sys.path.insert(0, os.path.expanduser('~/.claude/skills/schematic-replication/scripts'))
from specgen import Page, DEV  # noqa: E402

DEV.update({
    'TOP221': ('3e1784f728a1443bbda81e6fdd5d001f', {'5': (-30, 30), '1': (-30, -30), '4': (40, 0), '2': (-20, -30),
                                                    '6': (0, -30), '7': (10, -30), '3': (-10, -30), '8': (20, -30)}),
    'PC817': ('f575ac4897734610bfe07ae2aee4bec3', {'4': (50, 10), '3': (50, -10), '2': (-50, -10), '1': (-50, 10)}),
    'UF4005': ('6d86db11ab024d6395d7277b50e1b215', {'1': (-20, 0), '2': (20, 0)}),
    'UF5402': ('2103525c563b4f18bb31f83c80271767', {'1': (-20, 0), '2': (20, 0)}),
    'BZX3V9': ('d84adf77051949b7a1147c71f00528b5', {'1': (-20, 0), '2': (20, 0)}),
    'C2n2': ('896b78d0a1b248c48739cd9302d7ce85', None), 'C330u': ('979855133e404170b255e675f8f53e60', None),
    'C1u50': ('ae3d43698ab04939b5ad7be19fc9736b', None), 'L3u3': ('53d3aced86f44463878e2541b3aac6e2', None),
    'D1N4148b': ('43ec47cee2c541a799f3f3892cff2f4b', {'1': (-20, 0), '2': (20, 0)}),
})

g = Page('<page-uuid>')  # page of the dedicated schematic for this figure
P, W, F = g.part, g.wire, g.flag

P('R1', 'R47k', 100, 630, 90)
P('C3', 'C2n2', 155, 630, 90)
P('D4', 'UF4005', 155, 560, 90)
P('U2', 'TOP221', 185, 470)
P('T1', 'EE16', 300, 620)
P('D1', 'UF5402', 380, 710, 180)
P('C1', 'C330u', 430, 680, 90)
P('D2', 'BZX3V9', 540, 680, 90)
P('L1', 'L3u3', 570, 710)
P('C2', 'C100u', 610, 680, 90)
P('R2', 'R100', 570, 600)
P('R3', 'R10', 540, 560, 90)
P('U1', 'PC817', 470, 505, 0, True)
P('D3', 'D1N4148b', 380, 600)
P('C4', 'C100u', 380, 555, 180)
P('C5', 'C1u50', 380, 445, 90)

# primary
W([60, 660], [100, 660]); W([100, 660], [155, 660]); W([155, 660], 'T1:5')
W([100, 660], 'R1:1'); W([155, 660], 'C3:1')
W('R1:2', [100, 595], [155, 595]); W('C3:2', [155, 595]); W([155, 595], 'D4:1')
W('D4:2', [155, 525]); W([155, 525], 'U2:5'); W('T1:4', [240, 620], [240, 525], [155, 525])
for n, x in (('1', 155), ('2', 165), ('3', 175), ('6', 185), ('7', 195), ('8', 205)):
    W(f'U2:{n}', [x, 415])
W([60, 415], [155, 415])
for a, b in ((155, 165), (165, 175), (175, 185), (185, 195), (195, 205), (205, 340), (340, 380), (380, 590)):
    W([a, 415], [b, 415])
W('U2:4', [360, 470]); W([360, 470], [380, 470]); W([380, 470], 'C5:1'); W('C5:2', [380, 415])
W([360, 470], [360, 495], 'U1:3')
# secondary
W('T1:6', [340, 660], [340, 710], 'D1:2')
W('D1:1', [430, 710]); W([430, 710], 'C1:1'); W([430, 710], [540, 710]); W([540, 710], 'D2:1'); W([540, 710], 'L1:1')
W('L1:2', [610, 710]); W([610, 710], 'C2:1')
W('T1:7', [345, 640], [345, 650]); W([345, 650], [430, 650]); W('C1:2', [430, 650]); W([430, 650], [600, 650])
W([600, 650], [610, 650]); W('C2:2', [610, 650]); W([600, 650], [600, 600]); W([600, 600], [600, 495])
W('D2:2', [540, 600]); W([540, 600], 'R3:1'); W([540, 600], 'R2:1'); W('R2:2', [600, 600])
W('R3:2', [540, 515], 'U1:1'); W('U1:2', [600, 495])
W('T1:9', [350, 630], [350, 600], 'D3:1')
W('D3:2', [410, 600]); W([410, 600], [410, 555]); W([410, 555], [410, 515], 'U1:4'); W('C4:1', [410, 555])
W('T1:10', [340, 610], [340, 555]); W([340, 555], [340, 415]); W('C4:2', [340, 555])

# Terminals. These connect-made ports rendered correctly for this figure; if a port comes out
# pointing at its wire, delete it and use g.port() at the wire end instead, e.g.
#   g.port('net_port_in', 'VCC', 60, 660, 0)      # in-port, body to the left
#   g.port('net_port_out', '+5V', 610, 730, 270)  # out-port, body upwards (needs a stub wire to y=730)
#   g.port('net_port_out', 'RTN', 610, 630, 90)   # out-port, body downwards
#   g.port('net_port_out', 'X', 560, 320, 180)    # out-port, body to the left
F('net_port_in', 'VCC', at=[60, 660], d='left', off=None)
F('net_port_out', '+5V', at=[610, 710], d='up', off=20)
F('net_port_out', 'RTN', at=[610, 650], d='down', off=20)
F('net_port_bi', 'GND', at=[60, 415], d='left', off=None)
F('net_port_bi', 'GND', at=[590, 415], d='right', off=None)
g.nc = {'T1': [1, 2]}
# out/bi port names are hidden by the symbol: label them with free text like the book's terminals
for name, x, y in (('+5V', 620, 735), ('RTN', 620, 625), ('GND', 25, 425), ('GND', 600, 425)):
    g.text(name, x, y, 7)
g.text('图 A-4  TOP221 应用电路', 250, 395, 10)
g.text('注：D1 原书为 UF5401，库中无此型号，用 UF5402 代替。', 60, 380, 6)

# home = page the OTHER agent is on (doc ls shows it as active); omit when working alone
g.dump('a4-spec.json', home=None)
