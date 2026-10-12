#!/usr/bin/python3
"""Verify schematic/PCB agreement and export two-layer fabrication packages.

Run with the KiCad distribution Python: /usr/bin/python3 tools/check_pcbs.py.
No DRC errors, warnings, unconnected items, parity issues or exclusions are
accepted. --export produces Gerbers, drills, previews and SHA256 manifests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
BOARDS=['a2ext-carrier','a2ext-vga','a2ext-dvi']

def run(*args):
    subprocess.run(list(map(str,args)),check=True)

def check(name, export=False):
    folder=ROOT/'hw'/name;file=folder/(name+'.kicad_pcb')
    report=folder/'validation';report.mkdir(exist_ok=True)
    run('kicad-cli','pcb','drc','--refill-zones','--save-board','--schematic-parity','--severity-all','--format','json','-o',report/'drc.json',file)
    result=json.loads((report/'drc.json').read_text())
    for key in ['violations','unconnected_items','schematic_parity']:
        assert not result[key], (name,key,result[key])
    run('kicad-cli','sch','erc','--exit-code-violations','--format','json','-o',report/'erc.json',folder/(name+'.kicad_sch'))
    board=p.LoadBoard(str(file))
    assert board.GetCopperLayerCount()==2
    assert board.GetDesignSettings().GetBoardThickness()==p.FromMM(1.6)
    footprints={f.GetReference():f for f in board.GetFootprints()}
    # All user-assembled components must have plated leads. The card-edge
    # contacts are the only intentional surface copper pads in PCB-P2.
    leaded_pads=0
    for ref,f in footprints.items():
        if name=='a2ext-carrier' and ref=='J1': continue
        for pad in f.Pads():
            if not pad.GetNumber(): continue
            assert pad.GetAttribute()==p.PAD_ATTRIB_PTH,(name,ref,pad.GetNumber(),'not through-hole')
            assert not pad.IsOnLayer(p.F_Paste) and not pad.IsOnLayer(p.B_Paste)
            leaded_pads+=1
    contract=json.loads((folder/'connections.json').read_text())
    for net, expected in contract.items():
        actual={(f.GetReference(),pad.GetNumber()) for f in board.GetFootprints() for pad in f.Pads() if pad.GetNetname()=='/'+net}
        wanted={tuple(node) for node in expected if not node[0].startswith('#')}
        assert actual==wanted,(name,net,actual,wanted)
    assert all(t.GetLayer() in [p.F_Cu,p.B_Cu] for t in board.GetTracks())
    if name=='a2ext-carrier':
        pads={pad.GetNumber():pad for pad in footprints['J1'].Pads()}
        assert len(pads)==50
        for i in range(1,26):
            assert pads[str(i)].GetPosition()==pads[str(51-i)].GetPosition()
            assert pads[str(i)].IsOnLayer(p.F_Cu) and not pads[str(i)].IsOnLayer(p.B_Cu)
            assert pads[str(51-i)].IsOnLayer(p.B_Cu) and not pads[str(51-i)].IsOnLayer(p.F_Cu)
            assert not pads[str(i)].IsOnLayer(p.F_Paste)
        assert len(list(footprints['M1'].Pads()))==60
    else:
        assert footprints['J1'].GetLayer()==p.B_Cu
        assert footprints['J2'].GetLayer()==p.F_Cu
    stats={'board':name,'revision':'PCB-P2-THT',
           'assembly':'through-hole; socketed prepared module' if name=='a2ext-carrier' else 'through-hole',
           'through_hole_component_pads':leaded_pads,'smd_component_pads':0,
           'copper_layers':2,'thickness_mm':1.6,
           'drc_violations':0,'unconnected_items':0,'schematic_parity_issues':0,
           'contract_nets_checked':len(contract),
           'tracks':sum(not isinstance(t,p.PCB_VIA) for t in board.GetTracks()),
           'vias':sum(isinstance(t,p.PCB_VIA) for t in board.GetTracks()),
           'routing_lengths_mm':{net:round(sum(t.GetLength()/1e6 for t in board.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/'+net),4) for net in contract}}
    if name=='a2ext-dvi':
        stats['tmds_output_pairs']={}
        for lane in ['D0','D1','D2','CLK']:
            base='TMDS_'+lane
            lengths=[stats['routing_lengths_mm'][base+'_'+side] for side in ['P','N']]
            tracks=[t for t in board.GetTracks() if t.GetNetname() in ['/'+base+'_P','/'+base+'_N']]
            skew=round(abs(lengths[0]-lengths[1]),4)
            assert skew<.1,(lane,skew)
            assert not any(isinstance(t,p.PCB_VIA) for t in tracks)
            assert len({t.GetLayer() for t in tracks})==1
            stats['tmds_output_pairs'][lane]={'positive_mm':lengths[0],'negative_mm':lengths[1],
                'skew_mm':skew,'vias':sum(isinstance(t,p.PCB_VIA) for t in tracks),
                'copper_layers':sorted({board.GetLayerName(t.GetLayer()) for t in tracks})}
        stats['tmds_output_length_tuned']=True
        stats['tmds_complete_path_length_tuned']=False
        stats['tmds_impedance_controlled']=False
        assert footprints['J2'].GetFPID().GetLibItemName()=='HDMI_Kycon_THT'
        connector=list(footprints['J2'].Pads())
        signals={pad.GetNumber():pad for pad in connector if pad.GetNumber().isdigit()}
        assert set(signals)=={str(number) for number in range(1,20)}
        for number in range(1,20):
            pad=signals[str(number)]
            local_y=((number-1)//2)*1.155+(.5775 if number%2==0 else 0)
            expected=p.VECTOR2I(p.FromMM(100.6-local_y),p.FromMM(88+(1 if number%2==0 else 0)))
            assert (pad.GetPosition()-expected).EuclideanNorm()<=2
            assert pad.GetDrillSize()==p.VECTOR2I(p.FromMM(.55),p.FromMM(.55))
        shell=[pad for pad in connector if pad.GetNumber()=='SH']
        assert len(shell)==4
        for pad in shell:
            assert sorted([pad.GetDrillSize().x,pad.GetDrillSize().y])==[p.FromMM(.9),p.FromMM(2.7)]
    (report/'summary.json').write_text(json.dumps(stats,indent=2)+'\n')
    if export:
        fab=folder/'gerbers';fab.mkdir(exist_ok=True)
        run('kicad-cli','pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts','--subtract-soldermask','-o',str(fab)+'/',file)
        run('kicad-cli','pcb','export','drill','--format','excellon','--excellon-units','mm','--excellon-separate-th','--generate-report','--report-path',report/'drill-report.txt','-o',str(fab)+'/',file)
        required=['-F_Cu.gtl','-B_Cu.gbl','-F_Mask.gts','-B_Mask.gbs','-Edge_Cuts.gm1','-PTH.drl','-NPTH.drl']
        for suffix in required: assert (fab/(name+suffix)).is_file(),suffix
        if name=='a2ext-dvi':
            assert len(re.findall(r'^X[^\n]*G85X[^\n]*$',(fab/(name+'-PTH.drl')).read_text(),re.M))==4
        previews=folder/'previews';previews.mkdir(exist_ok=True)
        for side,layer in [('top','F'),('bottom','B')]:
            run('kicad-cli','pcb','export','svg','--layers',layer+'.Cu,'+layer+'.Silkscreen,Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet',*(['--mirror'] if side=='bottom' else []),'-o',previews/(side+'.svg'),file)
        run('kicad-cli','pcb','export','svg','--layers','F.Fab,F.Silkscreen,Edge.Cuts','--sketch-pads-on-fab-layers','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',previews/'assembly-top.svg',file)
        for svg in previews.glob('*.svg'):
            svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
        files=list(sorted(fab.iterdir()))
        manifest={str(f.relative_to(folder)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [file,folder/(name+'.kicad_sch'),*files]}
        (report/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
        with zipfile.ZipFile(folder/(name+'-gerbers.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
            for f in files:archive.write(f,f.name)
        print(name,'Gerber and drill ZIP exported',flush=True)
    print(name,'DRC, ERC, schematic parity and',len(contract),'contract nets passed',flush=True)
    return board

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('boards',nargs='*',default=BOARDS,choices=BOARDS)
    parser.add_argument('--export',action='store_true')
    args=parser.parse_args()
    verified={name:check(name,args.export) for name in args.boards}
    if set(verified)==set(BOARDS):
        carrier={f.GetReference():f for f in verified['a2ext-carrier'].GetFootprints()}
        c={pad.GetNumber():pad.GetPosition() for pad in carrier['J2'].Pads()}
        for name in ['a2ext-vga','a2ext-dvi']:
            db={f.GetReference():f for f in verified[name].GetFootprints()}
            for pad in db['J1'].Pads(): assert c[pad.GetNumber()]-pad.GetPosition()==p.VECTOR2I(p.FromMM(65),0)
            for hole in ['H1','H2']: assert carrier[hole].GetPosition()-db[hole].GetPosition()==p.VECTOR2I(p.FromMM(65),0)
        print('Direct-mating pin positions and mounting holes align on both daughterboards')

if __name__=='__main__':main()
