#!/usr/bin/env python3
"""Report allocated SRAM sections and separately budget runtime TMDS allocation."""
import argparse
import subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('build',type=Path)
p.add_argument('--size-tool',default='arm-none-eabi-size')
a=p.parse_args()
for name in ('demo','vga','dvi'):
    elf=a.build/f'a2ext-{name}.elf'
    out=subprocess.check_output([a.size_tool,'-A',str(elf)],text=True)
    sections=[]
    for line in out.splitlines():
        v=line.split()
        if len(v)==3 and v[0].startswith('.'):
            size,addr=int(v[1]),int(v[2])
            if 0x20000000 <= addr < 0x20082000:
                sections.append((v[0],size))
    allocated=sum(n for _,n in sections)
    # libdvi's eight 640px x three-channel x 2-symbol buffers and queue storage.
    dynamic=8*640*3*4//2+1024 if name=='dvi' else 0
    assert allocated+dynamic < 520*1024, (name,allocated,dynamic)
    print(f'{name}: allocated SRAM={allocated} bytes (including minimum heap/stacks); '
          f'additional runtime budget={dynamic}; remaining budget={520*1024-allocated-dynamic}')
