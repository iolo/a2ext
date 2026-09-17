#!/usr/bin/env python3
"""Software checks; optional ERC and clean firmware matrix. Never flashes hardware."""
import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ["UBSAN_OPTIONS"]="halt_on_error=1"
p=argparse.ArgumentParser()
p.add_argument('--erc',action='store_true')
p.add_argument('--firmware-from',type=Path,help='Read dependency paths from an existing CMake build; build three fresh variants')
a=p.parse_args()
def run(args,log=None):
    if log:
        with log.open('w') as f:
            r=subprocess.run(list(map(str,args)),cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        if r.returncode: raise RuntimeError(f'Command failed; see {log}')
    else: subprocess.run(list(map(str,args)),cwd=ROOT,check=True)
run(['python3','tools/pinout.py'])
with tempfile.TemporaryDirectory(prefix='a2ext-check-') as tmp:
    for name in ('capture','slot','shadow','shadow_load'):
        exe=Path(tmp)/name
        cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds','-Ifw/a2ext-lib/include','-Ifw/a2ext-lib',f'tests/test_{name}.c']
        if name.startswith('shadow'): cmd+=['fw/a2ext-lib/shadow.c','-pthread']
        run(cmd+['-o',exe]);run([exe])
run(['python3','tests/test_response.py'])
run(['python3','tools/test_render.py'])
if a.erc: run(['python3','tools/check_schematics.py','a2ext-carrier','a2ext-vga','a2ext-dvi'])
if a.firmware_from:
    cache={}
    for line in (a.firmware_from/'CMakeCache.txt').read_text().splitlines():
        if '=' in line and ':' in line and not line.startswith(('#','//')):
            key,value=line.split('=',1);cache[key.split(':')[0]]=value
    deps=[f'-D{k}={cache[k]}' for k in ('PICO_SDK_PATH','PICO_TOOLCHAIN_PATH','picotool_DIR') if k in cache]
    root=Path(tempfile.mkdtemp(prefix='verify-',dir=ROOT/'build'))
    print(f'Clean build logs/artifacts: {root}',flush=True)
    for name,opts in [('iie',[]),('iiplus-active',['-DA2EXT_APPLE_MODEL=IIPLUS','-DA2EXT_DEMO_ACTIVE=ON']),('pattern',['-DA2EXT_VIDEO_TEST_PATTERN=ON'])]:
        dest=root/name
        run(['cmake','-S',ROOT,'-B',dest,'-DCMAKE_BUILD_TYPE=Release',*deps,*opts],root/f'{name}-configure.log')
        run(['cmake','--build',dest,'-j4'],root/f'{name}-build.log')
        compiler=cache.get('PICO_TOOLCHAIN_PATH','')
        size=Path(compiler)/'bin/arm-none-eabi-size'
        run(['python3','tools/memory_report.py',dest,'--size-tool',size if size.exists() else 'arm-none-eabi-size'])
        for target in ('demo','vga','dvi'):
            for suffix in ('elf','uf2','elf.map'):
                assert (dest/f'a2ext-{target}.{suffix}').stat().st_size>0
        print(f'{name}: clean build and ELF/UF2/map checks passed',flush=True)
    (ROOT/'build/last-verification.json').write_text(json.dumps({'build_root':str(root),'variants':['iie','iiplus-active','pattern']},indent=2)+'\n')
run(['git','diff','--check'])
print('Software checks passed. Physical power, bus timing, DMA throughput and monitors remain untested.')
