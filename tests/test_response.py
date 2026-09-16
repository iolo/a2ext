"""Instruction-level logic regression for response.pio; not a timing simulator.
No GPIO synchronizer, electrical propagation, CPU service or DMA is modeled.
"""
from pathlib import Path

instructions, labels = [], {}
for line in Path('fw/a2ext-lib/response.pio').read_text().splitlines():
    line = line.split(';')[0].strip().removeprefix('public ')
    if not line or line.startswith('.'):
        continue
    if line.endswith(':'):
        labels[line[:-1]] = len(instructions)
    else:
        instructions.append(line.replace(',', '').split())
assert len(instructions) <= 32

class Machine:
    def __init__(self):
        self.pc = labels['cycle_start']
        self.r = dict(x=0, y=0xffffff, isr=0, osr=0, pins=0, pindirs=0, null=0)
        self.tx, self.rx = [], []
        self.phi = 0

    def tick(self, phi):
        self.phi = phi
        ins = instructions[self.pc]
        op, *args = ins
        next_pc = self.pc + 1
        if op == 'wait':
            if phi != int(args[0]):
                next_pc = self.pc
        elif op == 'mov':
            value = args[1]
            self.r[args[0]] = ((~self.r[value[1:]]) if value.startswith('~') else self.r[value]) & 0xffffffff
        elif op == 'set':
            self.r[args[0]] = int(args[1])
        elif op == 'push':
            self.rx.append(self.r['isr'])
            self.r['isr'] = 0
        elif op == 'pull':
            self.r['osr'] = self.tx.pop(0) if self.tx else self.r['x']
        elif op == 'in':
            self.r['isr'] = ((self.r['isr'] << int(args[1])) | 0x100c700) & 0xffffffff
        elif op == 'out':
            n = int(args[1])
            if args[0] != 'null':
                self.r[args[0]] = self.r['osr'] & ((1 << n)-1)
            self.r['osr'] >>= n
        elif op == 'jmp':
            cond = args[0]
            take = len(args) == 1 or (cond == 'pin' and phi) or (cond == 'x!=y' and self.r['x'] != self.r['y']) or (cond == '!y' and not self.r['y'])
            if cond == 'y--':
                take = self.r['y'] != 0
                self.r['y'] = (self.r['y'] - 1) & 0xffffffff
            if take:
                next_pc = labels[args[-1]]
        else:
            raise AssertionError(ins)
        self.pc = next_pc
        return self.r['pindirs'] != 0

    def low(self):
        for _ in range(30): self.tick(0)
        assert not self.r['pindirs']

# No reply, invalid zero tag, and stale tags must never assert output.
for request in (None, 0xab000000, 0xabfffffe):
    m = Machine(); m.low()
    if request is not None: m.tx.append(request)
    assert not any(m.tick(1) for _ in range(60))
    m.low()

# Sweep enqueue times; a current reply may drive only the corresponding cycle.
for delay in range(70):
    m = Machine(); m.low()
    driven = False
    for t in range(60):
        if t == delay: m.tx.append(0xa5ffffff)
        driven |= m.tick(1)
    # Model enqueue racing the falling edge, including an already low clock.
    for t in range(60, 90):
        if t == delay: m.tx.append(0xa5ffffff)
        m.tick(0)
        if t >= 64: assert not m.r['pindirs']
    if driven: assert m.r['pins'] == 0xa5
    assert not any(m.tick(1) for _ in range(60)), delay
    m.low()

# Tag wrap skips zero, preserving empty-FIFO nonresponse semantics.
m = Machine(); m.r['y'] = 1; m.low()
for _ in range(60): assert not m.tick(1)
m.low(); assert m.r['y'] == 0xffffff
print(f'response PIO: {len(instructions)} words; stale/zero tags, enqueue phase sweep, release, wrap passed')
