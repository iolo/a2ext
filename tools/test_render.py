#!/usr/bin/env python3
"""Build actual renderer sources with synchronous host output sinks, not DMA emulation."""
import subprocess
from pathlib import Path
out=Path('build/replay');out.mkdir(parents=True,exist_ok=True)
v=Path('fw/a2ext-vga');d=Path('fw/a2ext-dvi')
for model in ('IIE','IIPLUS'):
    for backend in ('vga','dvi'):
        dest=out/model/backend;dest.mkdir(parents=True,exist_ok=True)
        flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds',f'-DAPPLE_MODEL_{model}=1','-Itests/host','-Itests','-Ifw/a2ext-lib/include']
        if backend=='vga':
            root=v
            files=[v/f'{f}.c' for f in ('buffers','colors','render','render_text','render_lores','render_hires','render_testpat')]
            fonts='textfont'
        else:
            root=d
            files=[d/'applebus/buffers.c']+[d/'render'/f'{f}.c' for f in ('frame','render_text','render_lores','render_hires','render_dgr','render_dhgr')]+[d/'dvi'/f'{f}.c' for f in ('tmds','tmds_lores','tmds_hires','tmds_dhgr')]
            fonts='fonts'
        files += [root/fonts/'iie_us_enhanced.c',root/fonts/'iiplus_us.c']
        exe=dest/'render'
        subprocess.run(['cc',*flags,f'-I{root}',f'tests/test_render_{backend}.c','fw/a2ext-lib/shadow.c',*map(str,files),'-o',str(exe)],check=True)
        subprocess.run([str(exe),str(dest)],check=True,env=__import__('os').environ|{'UBSAN_OPTIONS':'halt_on_error=1'})
    def data(backend,name):
        return (out/model/backend/f'{name}.ppm').read_bytes().split(b'\n',3)[3]
    for backend in ('vga','dvi'):
        assert data(backend,'text40') != data(backend,'page2')
        assert data(backend,'text40') != data(backend,'text40_flash')
        if model=='IIE':
            assert data(backend,'text40') == data(backend,'store_page1')
            assert data(backend,'text40') != data(backend,'text80')
            assert data(backend,'text80') != data(backend,'altcharset')
            assert data(backend,'lores') != data(backend,'double_lores')
            assert data(backend,'hires') != data(backend,'double_hires')
    for backend in ('vga','dvi'):
        for mode in ('lores','hires'):
            assert data(backend,'mixed_'+mode)[368*640*3:432*640*3] == data(backend,'text40')[368*640*3:432*640*3]
            assert data(backend,'mixed_double_'+mode)[368*640*3:432*640*3] == data(backend,'text80')[368*640*3:432*640*3]
    # Upstream palettes differ; monochrome text positions should agree exactly.
    for name in ('text40','text40_flash','text80','page2','store_page1','altcharset'):
        a=data('vga',name);b=data('dvi',name)
        assert bytes(x>127 for x in a)==bytes(x>127 for x in b),(model,name,'text mismatch')
print('Cross-backend text positions, page selection and distinct extended modes passed')
