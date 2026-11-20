"""Shared helpers for book-faithful page specs: device table, pin offsets, transforms."""

DEV = {
    'KF301': ('035829a24b724aff80a172ecb2678dc5', {'1': (-20, 5), '2': (-20, -5)}),
    'R30': ('08115402421d44a5914bafdb4a90e49a', None), 'R30_2512': ('c6f0e5f2dbcc46a1b912b05a209c0fd6', None),
    'R1M': ('49b660f4f74f4e37bd7db2640586397e', None), 'R220': ('be7749247b1b4fed9c1604964ee1bf92', None),
    'R1k': ('9cd6c92908254627892a84f4c8ac1e9e', None), 'R15k': ('8e8359a8f4794e95a18fc50493ca2b56', None),
    'R1k8': ('93c10e446756456c87730fa3a55d1bb3', None), 'R330k': ('69ff8ab4a31b467583d1bc331dba1b43', None),
    'R51k': ('3499d44000b7452e9bc0d155e4714ad5', None), 'R100k': ('8e173887d7d24dbe950578be7cc48781', None),
    'R47k': ('2638639501f14321b481be4df15286f7', None), 'R100': ('3140f4b435ed496db8557758bbe577c7', None),
    'R10': ('4f27b59402db4e48a430cb9c010cd963', None), 'R4k': ('933c67ad149d47bdad7c2433a56a17f5', None),
    'R470k': ('21e2c5dc56c144649e62748e9415042f', None),
    '1N4007': ('806bfab70fd544e1bacd59694b794cdc', 'D'), '1N4148': ('43ec47cee2c541a799f3f3892cff2f4b', 'D'),
    '1N4004': ('e95c40f68e464d08a91dab69788d950d', 'D'), 'BZX8V2': ('7b6f9c57fbbd415f8419fdc123afaf70', 'Z'),
    'C1n1kV': ('81aad239851e4d4280912a612bd68f55', None), 'C10n': ('53e362ba713740f290edef10f5ac6c39', None),
    'C10u': ('7b8e0fac6d65402fbf00253738a8a55f', 'S15'), 'C100u': ('13171001851c4ae49421697778d847f2', None),
    'C100n': ('aa6f916383374785be390c4ddc7bf610', None), 'C1u': ('f5ffab71089546a5a0def89b3b6fabb9', 'S15'),
    'MJE13003': ('799acc13ce7f40afb8d35070513c7e3f', {'2': (10, 20), '3': (-10, 0), '1': (10, -20)}),
    '2N3906': ('b854f104f9a84132a3b56d4ab92d0f86', {'3': (10, 20), '2': (-10, 0), '1': (10, -20)}),
    'LED': ('7b6e105e95784d28ba93669950d4790f', {'1': (20, 0), '2': (-20, 0)}),
    'EE16': ('8814bcf4289647439759aed81ed1a243', {'5': (-40, 40), '4': (-40, 0), '2': (-39, -10), '1': (-39, -30),
                                                  '6': (30, 40), '7': (30, 20), '9': (30, 10), '10': (30, -10)}),
    'BAT': ('86e623376672474faf1d52349790ff31', None),
    'AMP3': ('1adaa3aae0e143b0a5ab8194e201a9b1', {'1': (40, 0), '2': (-30, 10), '3': (-30, -10)}),
    'AMP5': ('2b17ccab54644eb486574a7bf7f92aa6', {'1': (-40, -10), '2': (-40, 10), '3': (0, 30), '4': (0, -30), '5': (40, 0)}),
}


def offsets(dev):
    o = DEV[dev][1]
    if isinstance(o, dict):
        return o
    if o == 'S15':
        return {'1': (-15, 0), '2': (15, 0)}
    return {'1': (-20, 0), '2': (20, 0)}


def xf(off, rot, mirror):
    x, y = off
    for _ in range((rot // 90) % 4):
        x, y = y, -x
    if mirror:  # EasyEDA applies the mirror after the rotation
        x = -x
    return x, y


class Page:
    def __init__(self, page, dy=0):
        self.page, self.dy = page, dy
        self.parts, self.expect, self.wires, self.flags, self.nc, self.texts = [], {}, [], [], {}, []
        self.ports = []

    def part(self, des, dev, x, y, rot=0, mirror=False):
        y += self.dy
        p = {'des': des, 'uuid': DEV[dev][0], 'x': x, 'y': y, 'rot': rot}
        if mirror:
            p['mirror'] = True
        self.parts.append(p)
        for n, off in offsets(dev).items():
            ox, oy = xf(off, rot, mirror)
            self.expect[f'{des}:{n}'] = [x + ox, y + oy]

    def _pt(self, p):
        return p if isinstance(p, str) else [p[0], p[1] + self.dy]

    def wire(self, *pts):
        self.wires.append({'pts': [self._pt(p) for p in pts]})

    def flag(self, kind, net, at=None, pin=None, d=None, off=None):
        f = {'kind': kind, 'net': net}
        if at:
            f['at'] = self._pt(at)
        else:
            f['pin'] = pin
        if d:
            f['dir'] = d
        if off:
            f['off'] = off
        self.flags.append(f)

    def text(self, content, x, y, size=7):
        self.texts.append({'content': content, 'x': x, 'y': y + self.dy, 'size': size})

    def port(self, kind, net, x, y, rot):
        """Net port placed directly with `sch netflag` (connect-made ports come out reversed/hidden)."""
        self.ports.append({'kind': kind, 'net': net, 'x': x, 'y': y + self.dy, 'rot': rot})

    def dump(self, path, home=None):
        import json
        spec = {'page': self.page, 'home': home, 'parts': self.parts, 'expect': self.expect,
                'wires': self.wires, 'flags': self.flags, 'ports': self.ports, 'nc': self.nc, 'texts': self.texts}
        json.dump(spec, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print(path, len(self.parts), 'parts', len(self.wires), 'wires', len(self.flags), 'flags')
