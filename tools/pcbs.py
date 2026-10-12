#!/usr/bin/python3
"""Create the three two-layer prototype PCBs. Requires KiCad 10 pcbnew.

Placement regeneration replaces boards; route via exported DSN and import SES
with --import-session. Fabrication release is handled by check_pcbs.py.
"""
import argparse
import csv
import json
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'hw/a2ext.pretty'
MM = p.FromMM

def v(x, y):
    return p.VECTOR2I(MM(x), MM(y))

def layers(*items):
    result=p.LSET()
    for layer in items: result.AddLayer(layer)
    return result

def schematic_nets(folder):
    with tempfile.TemporaryDirectory(prefix='a2ext-pcb-netlist-') as tmp:
        file=Path(tmp)/'nets.xml'
        subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(file),str(folder/(folder.name+'.kicad_sch'))],check=True)
        return {(node.get('ref'),node.get('pin')):net.get('name') for net in ET.parse(file).findall('.//nets/net') for node in net.findall('node')}

def line(parent, a, b, layer, width=0.15):
    s = p.PCB_SHAPE(parent)
    s.SetShape(p.SHAPE_T_SEGMENT)
    s.SetStart(v(*a)); s.SetEnd(v(*b)); s.SetLayer(layer); s.SetWidth(MM(width))
    parent.Add(s)

def text(board, content, x, y, size=1, layer=p.F_SilkS):
    t = p.PCB_TEXT(board); t.SetText(content); t.SetPosition(v(x,y))
    t.SetTextSize(v(size,size)); t.SetTextThickness(MM(0.15)); t.SetLayer(layer)
    board.Add(t)

def local_copy(source, name):
    lib, item = source.split(':')
    f = p.FootprintLoad('/usr/share/kicad/footprints/'+lib+'.pretty', item)
    f.SetFPID(p.LIB_ID('A2Ext', name)); f.SetReference('REF**')
    # Stock connector side outlines end too close to the intended PCB edge.
    if name=='VGA_DE15':
        for item in f.GraphicalItems():
            if item.GetLayer()==p.F_SilkS and isinstance(item,p.PCB_SHAPE):
                for get,setter in [(item.GetStart,item.SetStart),(item.GetEnd,item.SetEnd)]:
                    point=get()
                    if name=='VGA_DE15' and point.y>MM(6.53): point.y=MM(6.53)
                    setter(point)
    p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(LIB), f)
    return name

def libraries():
    LIB.mkdir(exist_ok=True)
    mapping = {
        'R_Axial_7.62':'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',
        'C_Radial_5':'Capacitor_THT:C_Rect_L7.0mm_W4.5mm_P5.00mm',
        'Schottky_DO41':'Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal',
        'IDC20':'Connector_IDC:IDC-Header_2x10_P2.54mm_Vertical',
        'Socket20':'Connector_PinSocket_2.54mm:PinSocket_2x10_P2.54mm_Vertical',
        'SYNC':'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
        'HDMI_Kycon_THT':'Connector_Video:HDMI_A_Kycon_KDMIX-SL1-NS-WS-B15_VerticalRightAngle',
        'VGA_DE15':'Connector_Dsub:DSUB-15-HD_Socket_Horizontal_P2.29x1.90mm_EdgePinOffset3.03mm_Housed_MountingHolesOffset4.94mm',
    }
    for name, src in mapping.items(): local_copy(src, name)
    # Independent radial PTC drawings from Bourns MF-R dimension table.
    # Body height is an assembly limit; courtyard uses maximum width/thickness.
    for name,width in [('PTC_MF_R050',7.9),('PTC_MF_R010',7.4)]:
        f=p.FOOTPRINT(None);f.SetFPID(p.LIB_ID('A2Ext',name))
        f.SetReference('REF**');f.SetValue(name);f.SetAttributes(p.FP_THROUGH_HOLE)
        for n,x in [('1',0),('2',5.1)]:
            pad=p.PAD(f);pad.SetNumber(n);pad.SetPosition(v(x,0))
            pad.SetAttribute(p.PAD_ATTRIB_PTH);pad.SetShape(p.PAD_SHAPE_CIRCLE)
            pad.SetSize(v(1.8,1.8));pad.SetDrillSize(v(.9,.9))
            pad.SetLayerSet(layers(p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask));f.Add(pad)
        for layer,margin,w in [(p.F_Fab,0,.1),(p.F_SilkS,.15,.12),(p.F_CrtYd,.4,.05)]:
            left,right=2.55-width/2-margin,2.55+width/2+margin
            low,high=-1.55-margin,1.55+margin
            for a,z in [((left,low),(right,low)),((right,low),(right,high)),((right,high),(left,high)),((left,high),(left,low))]:line(f,a,z,layer,w)
        f.Reference().SetPosition(v(2.55,-3));f.Value().SetVisible(False)
        p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(LIB),f)
    # Independently drawn contacts measured against the user's Tebl compact
    # reference: 2.54 mm pitch, 1.778 x 7.62 mm fingers, 1/50 opposing.
    edge = p.FOOTPRINT(None)
    edge.SetReference('REF**'); edge.SetValue('Apple II slot')
    edge.SetFPID(p.LIB_ID('A2Ext','AppleII_Edge50'))
    edge.SetAttributes(p.FP_SMD)
    for number in range(1,51):
        pad=p.PAD(edge);pad.SetNumber(str(number));pad.SetAttribute(p.PAD_ATTRIB_SMD)
        pad.SetShape(p.PAD_SHAPE_RECT);pad.SetSize(v(1.778,7.62))
        pad.SetPosition(v(((number-1) if number<=25 else (50-number))*2.54,0))
        pad.SetLayerSet(layers(p.F_Cu,p.F_Mask) if number<=25 else layers(p.B_Cu,p.B_Mask))
        edge.Add(pad)
    p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(LIB),edge)
    f = p.FOOTPRINT(None); f.SetFPID(p.LIB_ID('A2Ext','WeAct_RP2350B_V1'))
    f.SetReference('REF**'); f.SetValue('WeAct RP2350B V1.0')
    f.SetAttributes(p.FP_THROUGH_HOLE)
    # Vendor top view: H2.1 bottom/inner left, H2.2 top/outer left;
    # H1.1 bottom/outer left, H1.2 top/inner left.
    for header in ('H1','H2'):
        for n in range(1,31):
            x = ((n-1)//2)*2.54
            y = (38.1 if n%2 else 35.56) if header=='H1' else (2.54 if n%2 else 0)
            pad=p.PAD(f); pad.SetNumber(f'{header}.{n}'); pad.SetPosition(v(x,y))
            pad.SetAttribute(p.PAD_ATTRIB_PTH); pad.SetShape(p.PAD_SHAPE_RECT if n==1 else p.PAD_SHAPE_CIRCLE)
            pad.SetSize(v(1.7,1.7)); pad.SetDrillSize(v(1,1)); pad.SetLayerSet(layers(p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask))
            f.Add(pad)
    # Module perimeter, header courtyards and USB access shown on fabrication.
    for layer, a,b,c,d in [(p.F_Fab,-1.65,-1.524,39.752,39.624),
                          (p.F_CrtYd,-1.3,-1.3,36.86,3.84),
                          (p.F_CrtYd,-1.3,34.26,36.86,39.4)]:
        for start,end in [((a,b),(c,b)),((c,b),(c,d)),((c,d),(a,d)),((a,d),(a,b))]: line(f,start,end,layer,0.05)
    for a,b in [((-1.4,-1.4),(1.4,-1.4)),((-1.4,-1.4),(-1.4,3.9)),((-1.4,39.5),(1.4,39.5))]: line(f,a,b,p.F_SilkS)
    p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(LIB),f)

def assign_schematic(folder, footprints):
    source=folder/(folder.name+'.kicad_sch')
    data=source.read_text()
    # Only placed instance property blocks, leaving embedded symbols alone.
    pattern=r'(\(symbol \(lib_id.*?\(property "Footprint" )"[^"]*"'
    def update(match):
        s=match.group(0); m=re.search(r'\(property "Reference" "([^"]+)"',s)
        if m and m[1] in footprints:
            s=re.sub(r'(\(property "Footprint" )"[^"]*"',r'\1"A2Ext:'+footprints[m[1]]+'"',s)
        return s
    data=re.sub(pattern,update,data,flags=re.S)
    source.write_text(data)
    with (folder/'BOM.csv').open(newline='') as stream: rows=list(csv.DictReader(stream))
    for row in rows:
        if row['Reference'] in footprints: row['Footprint']='A2Ext:'+footprints[row['Reference']]
    with (folder/'BOM.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0].keys(),lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    (folder/'fp-lib-table').write_text('(fp_lib_table\n (version 7)\n (lib (name "A2Ext")(type "KiCad")(uri "${KIPRJMOD}/../a2ext.pretty")(options "")(descr "a2ext local physical footprints"))\n)\n')
    (folder/'footprints.json').write_text(json.dumps(footprints,indent=2)+'\n')

def build(name):
    folder=ROOT/'hw'/name
    b=p.BOARD(); b.SetCopperLayerCount(2)
    ds=b.GetDesignSettings(); ds.SetBoardThickness(MM(1.6))
    ds.m_MinClearance=MM(.15); ds.m_TrackMinWidth=MM(.15)
    ds.m_ViasMinSize=MM(.6); ds.m_MinThroughDrill=MM(.3)
    ds.m_CopperEdgeClearance=MM(.25); ds.SetCustomTrackWidth(MM(.25))
    ds.SetCustomViaSize(MM(.6)); ds.SetCustomViaDrill(MM(.3)); ds.UseCustomTrackViaSize(True)
    contract=json.loads((folder/'connections.json').read_text())
    physical_nets=schematic_nets(folder)
    nets={}
    for net in contract:
        n=p.NETINFO_ITEM(b,'/'+net);b.Add(n);nets[net]=n
    with (folder/'BOM.csv').open() as stream: values={r['Reference']:r['Value'] for r in csv.DictReader(stream)}
    parts={}; fps={}
    sch=(folder/(name+'.kicad_sch')).read_text()
    root=re.search(r'\(uuid "([^"]+)"',sch)[1]
    def add(ref, fp, x,y, angle=0, bottom=False):
        f=p.FootprintLoad(str(LIB),fp); f.SetFPID(p.LIB_ID('A2Ext',fp)); f.SetReference(ref);f.SetValue(values[ref]);b.Add(f)
        f.SetPosition(v(x,y));f.SetOrientationDegrees(angle)
        if bottom: f.Flip(v(x,y),False)
        # Match schematic UUID for KiCad schematic/PCB parity.
        instance=re.search(r'\(symbol \(lib_id[^\n]*?\(uuid "([^"]+)"\)[^\n]*?\(property "Reference" "'+ref+r'"',sch)
        if instance:
            path=p.KIID_PATH();path.push_back(p.KIID(root));path.push_back(p.KIID(instance[1]));f.SetPath(path)
        f.Reference().SetTextSize(v(.9,.9));f.Reference().SetTextThickness(MM(.13))
        f.Value().SetVisible(False)
        for pad in f.Pads():
            if not pad.GetNumber(): continue  # Mechanical connector locating holes.
            for net,nodes in contract.items():
                if [ref,pad.GetNumber()] in nodes: pad.SetNet(nets[net]);break
            else:
                # Named singleton NC nets mirror KiCad's physical netlist.
                net=physical_nets[(ref,pad.GetNumber())]
                n=p.NETINFO_ITEM(b,net);b.Add(n);pad.SetNet(n)
        parts[ref]=f;fps[ref]=fp
        return f
    if name.endswith('carrier'):
        outline=[(50,50),(148.425,50),(149.695,51.27),(149.695,117.31),(148.425,118.58),(138.9,118.58),(138.9,127.47),(137.63,128.74),(74.13,128.74),(72.86,127.47),(72.86,118.58),(50,118.58)]
        add('J1','AppleII_Edge50',75.4,123.66)
        add('M1','WeAct_RP2350B_V1',70,64)
        add('J2','IDC20',135,73)
        add('JP1','SYNC',117,103)
        for ref,fp,x,y,ang in [('F1','PTC_MF_R050',126,114,0),('D1','Schottky_DO41',111,113,0),('C8','C_Radial_5',123,105,0),('C9','C_Radial_5',61,99,90),('F2','PTC_MF_R010',139,114,0),('C10','C_Radial_5',75,111,0),('R4','R_Axial_7.62',75,58,0)]:
            f=add(ref,fp,x,y,ang)
            f.Reference().SetPosition(v(x+2.5,y+3.4 if y<110 else y-3.5))
        holes=[(145,67),(145,104),(57,57)]
        parts['M1'].Reference().SetPosition(v(92,61))
        parts['J1'].Reference().SetPosition(v(107,116))
        text(b,'a2ext carrier / 2L THT P2',102,53,1.2)
        text(b,'USB DATA ONLY - PREPARED MODULE',93,106,.8)
        text(b,'SYNC JP1: OPEN',116,100,.8)
        text(b,'Daughterboard',141,61,1)
    else:
        dvi=name.endswith('dvi')
        outline=[(65,65),(110,65),(110,110),(65,110)]
        add('J1','Socket20',70,73,bottom=True)
        holes=[(80,67),(80,104)]
        if dvi:
            # Rotate upright receptacle so its cable exits the right edge.
            # Source drawing PCB edge is local Y=-9.4 mm.
            f=add('J2','HDMI_Kycon_THT',100.6,88,-90)
            f.Reference().SetPosition(v(103,95))
            for i,y in enumerate([69.8,73.5,77.2,80.9,95,98.7,102.4,106.1],1):
                f=add('R'+str(i),'R_Axial_7.62',90,y)
                f.Reference().SetPosition(v(85,y))
            f=add('C1','C_Radial_5',104,100,-90)
            f.Reference().SetPosition(v(100.5,104))
            # Preserve the reviewed pair geometry while routing remaining nets.
            # This template belongs to the fixed PCB-P2-THT placement above.
            routing=json.loads((folder/'tmds-routing.json').read_text())
            assert routing['revision']=='PCB-P2-THT'
            for segment in routing['segments']:
                assert segment['net'].startswith('TMDS_')
                assert segment['layer'] in ('F.Cu','B.Cu')
                t=p.PCB_TRACK(b);t.SetStart(v(*segment['start_mm']));t.SetEnd(v(*segment['end_mm']))
                t.SetWidth(MM(segment['width_mm']));t.SetLayer(b.GetLayerID(segment['layer']))
                t.SetNet(nets[segment['net']]);t.SetLocked(True);b.Add(t)
        else:
            add('J2','VGA_DE15',103.17,81,90)
            for i in range(1,12):
                f=add('R'+str(i),'R_Axial_7.62',81 if i<=6 else 90.8,73+((i-1)%6)*5)
                f.Reference().SetPosition(v(84.8 if i<=6 else 94.6,75.5+((i-1)%6)*5))
        text(b,'a2ext '+('DVI' if dvi else 'VGA')+' / THT P2',94,66.9,.85)
        text(b,'J1 SOCKET ON BOTTOM',88,109 if dvi else 107,.85)
    for start,end in zip(outline,outline[1:]+outline[:1]): line(b,start,end,p.Edge_Cuts,.05)
    for i,(x,y) in enumerate(holes,1):
        f=p.FootprintLoad('/usr/share/kicad/footprints/MountingHole.pretty','MountingHole_2.7mm_M2.5');f.SetReference('H'+str(i));f.SetPosition(v(x,y));f.Reference().SetVisible(False);f.Value().SetVisible(False);f.SetAttributes(p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES);b.Add(f)
    p.SaveBoard(str(folder/(name+'.kicad_pcb')),b)
    assign_schematic(folder,fps)
    # Persist explicit fabrication and routing minima in project JSON.
    project=json.loads((folder/(name+'.kicad_pro')).read_text())
    rules=project.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rules',{})
    rules.update({'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_copper_edge_clearance':.25,'min_hole_clearance':.25,'min_hole_to_hole':.25,'min_silk_clearance':.1,'min_silk_text_height':.8,'min_silk_text_thickness':.12})
    project['net_settings']={'classes':[{'name':'Default','clearance':.15,'track_width':.25,'via_diameter':.6,'via_drill':.3,'diff_pair_width':.15,'diff_pair_gap':.15,'diff_pair_via_gap':.25}],'meta':{'version':4}}
    if name.endswith('carrier'):
        project['net_settings']['classes'].append({'name':'Power','clearance':.15,'track_width':.5,'via_diameter':.8,'via_drill':.4})
        project['net_settings']['netclass_patterns']=[{'netclass':'Power','pattern':pattern} for pattern in ['/+5V_*','/VSYS']]
    (folder/(name+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
    # Reload project before DSN export to use persisted rules.
    b=p.LoadBoard(str(folder/(name+'.kicad_pcb')))
    target=ROOT/'build/pcb'/name;target.mkdir(parents=True,exist_ok=True)
    dsn=target/(name+'.dsn')
    assert p.ExportSpecctraDSN(b,str(dsn))
    # pcbnew's standalone loader does not load project net classes. Make the
    # routing exchange rules explicit instead of accepting its 0.2 mm default.
    exchange=dsn.read_text().replace('(width 200)','(width 250)').replace('(clearance 200)','(clearance 150)').replace('(clearance 50 (type smd_smd))','(clearance 150 (type smd_smd))')
    if name.endswith('carrier'):
        power=['/+5V_SLOT','/+5V_FUSED','/+5V_DB','/VSYS']
        start=exchange.index('(class kicad_default');end=exchange.index('(circuit',start)
        members=exchange[start:end]
        for net in power: members=re.sub(re.escape(net)+r'(?=\s)', '',members)
        exchange=exchange[:start]+members+exchange[end:]
        start=exchange.index('  (wiring')
        # Insert inside network, immediately before its closing parenthesis.
        end=exchange.rfind('  )',0,start)
        exchange=exchange[:end]+'    (class Power '+' '.join(power)+' (circuit (use_via "Via[0-1]_600:300_um")) (rule (width 500) (clearance 150)))\n'+exchange[end:]
    dsn.write_text(exchange)
    print(name,'placed and DSN exported',flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('boards',nargs='*',default=['a2ext-carrier','a2ext-vga','a2ext-dvi'])
    parser.add_argument('--import-session',type=Path)
    parser.add_argument('--finish',action='store_true',help='Add ground pours and enforce minimum trace width after routing')
    args=parser.parse_args()
    if args.finish:
        for name in args.boards:
            file=ROOT/'hw'/name/(name+'.kicad_pcb'); b=p.LoadBoard(str(file))
            physical_nets=schematic_nets(file.parent)
            for f in b.GetFootprints():
                for pad in f.Pads():
                    desired=physical_nets.get((f.GetReference(),pad.GetNumber()))
                    if desired and pad.GetNetname()!=desired:
                        n=p.NETINFO_ITEM(b,desired);b.Add(n);pad.SetNet(n)
                if f.GetReference()=='JP1': f.Reference().SetPosition(v(113.5,104))
                for pad in f.Pads():
                    # Grounded shell tabs benefit from a solid plane bond;
                    # C10's small local copper patch cannot sustain thermals.
                    if (name=='a2ext-carrier' and f.GetReference()=='C10' and pad.GetNumber()=='2') or (name=='a2ext-dvi' and f.GetReference()=='J2' and pad.GetNumber()=='SH'):
                        pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
                if name=='a2ext-vga' and f.GetReference().startswith('R'):
                    i=int(f.GetReference()[1:])
                    f.Reference().SetPosition(v(84.8 if i<=6 else 94.6,75.5+((i-1)%6)*5))
                if name=='a2ext-dvi':
                    for item in b.GetDrawings():
                        if isinstance(item,p.PCB_TEXT) and item.GetText()=='J1 SOCKET ON BOTTOM': item.SetPosition(v(88,109))
                if name!='a2ext-carrier' and f.GetReference()=='J2':
                    for item in f.GraphicalItems():
                        if item.GetLayer()==p.F_SilkS and isinstance(item,p.PCB_SHAPE):
                            for get,setter in [(item.GetStart,item.SetStart),(item.GetEnd,item.SetEnd)]:
                                point=get();point.x=min(point.x,MM(109.7));setter(point)
            for track in b.GetTracks():
                if not isinstance(track,p.PCB_VIA) and track.GetWidth()<MM(.15): track.SetWidth(MM(.15))
            ground=next(pad.GetNet() for f in b.GetFootprints() for pad in f.Pads() if pad.GetNetname()=='/GND')
            points=[(50.4,50.4),(149.295,50.4),(149.295,118.18),(50.4,118.18)] if name.endswith('carrier') else [(65.4,65.4),(109.6,65.4),(109.6,109.6),(65.4,109.6)]
            existing_layers={z.GetLayer() for z in b.Zones()}
            for layer in (p.F_Cu,p.B_Cu):
                if layer in existing_layers: continue
                zone=p.ZONE(b);zone.SetLayer(layer);zone.SetNet(ground);zone.SetLocalClearance(MM(.2));zone.SetMinThickness(MM(.15))
                zone.SetPadConnection(p.ZONE_CONNECTION_THERMAL);zone.SetThermalReliefGap(MM(.2));zone.SetThermalReliefSpokeWidth(MM(.25))
                poly=zone.Outline();poly.NewOutline()
                for x,y in points: poly.Append(MM(x),MM(y))
                b.Add(zone)
            p.SaveBoard(str(file),b)
        return
    if args.import_session:
        for name in args.boards:
            file=ROOT/'hw'/name/(name+'.kicad_pcb');b=p.LoadBoard(str(file))
            assert p.ImportSpecctraSES(b,str(args.import_session/name/(name+'.ses')))
            b.BuildConnectivity();p.SaveBoard(str(file),b)
        return
    libraries()
    for name in args.boards: build(name)

if __name__=='__main__': main()
