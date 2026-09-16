#!/usr/bin/env python3
"""Generate self-contained, editable KiCad schematics from the carrier pin map.

Each board also gets its own symbol library and sym-lib-table. No system symbol
library or Python package is needed. Regeneration is explicit; do not run this
over hand-edited schematics without reviewing the diff.
"""
import argparse
import csv
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
PINS = json.loads((ROOT / "hw/pinout.json").read_text())


def q(text):
    return json.dumps(str(text), ensure_ascii=False)


def uid(text):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "https://a2ext.local/" + text))


def effects(size=1.27, extra=""):
    return f"(effects (font (size {size} {size})) {extra})"


class Board:
    def __init__(self, name, paper="A3"):
        self.name, self.paper = name, paper
        self.root = uid(name)
        self.symbols, self.items, self.parts, self.nets = {}, [], [], {}

    def symbol(self, name, left, right, width=30.48):
        """Pins are (number, label, electrical type), ordered top to bottom."""
        height = max(len(left), len(right), 1) * 2.54 + 2.54
        pins, body = {}, []
        for side, entries in ((-1, left), (1, right)):
            for i, (number, label, kind) in enumerate(entries):
                number = str(number)
                x, y = side * (width / 2 + 5.08), height / 2 - 2.54 * (i + 1)
                angle = 0 if side == -1 else 180
                pins[number] = (x, y, side)
                body.append(f'(pin {kind} line (at {x} {y} {angle}) (length 5.08) '
                            f'(name {q(label)} {effects(1.0)}) (number {q(number)} {effects(1.0)}))')
        data = (f'(symbol {q(name)} (pin_names (offset 1.016)) (in_bom yes) (on_board yes) '
                f'(property "Reference" "U" (at 0 {height/2+5.08} 0) {effects()}) '
                f'(property "Value" {q(name)} (at 0 {height/2+2.54} 0) {effects()}) '
                f'(symbol {q(name+"_0_1")} (rectangle (start {-width/2} {height/2}) '
                f'(end {width/2} {-height/2}) (stroke (width 0.254) (type default)) '
                f'(fill (type background)))) (symbol {q(name+"_1_1")} {" ".join(body)}))')
        self.symbols[name] = (data, pins, height)

    def part(self, ref, symbol, value, x, y, connections, footprint="", note=""):
        data, pins, height = self.symbols[symbol]
        assert set(connections) == set(pins), (ref, set(connections) ^ set(pins))
        ident = uid(self.name + ref)
        self.items.append(
            f'(symbol (lib_id "A2Ext:{symbol}") (at {x} {y} 0) (unit 1) '
            f'(in_bom yes) (on_board yes) (dnp no) (uuid "{ident}") '
            f'(property "Reference" {q(ref)} (at {x} {y-height/2-5.08} 0) {effects()}) '
            f'(property "Value" {q(value)} (at {x} {y-height/2-2.54} 0) {effects(1.0)}) '
            f'(property "Footprint" {q(footprint)} (at {x} {y} 0) {effects(1.0,"hide")}) '
            f'(instances (project {q(self.name)} (path "{self.root}" '
            f'(reference {q(ref)}) (unit 1)))))')
        for number, (dx, dy, side) in pins.items():
            px, py = round(x + dx, 4), round(y - dy, 4)
            net = connections[number]
            suffix = self.name + ref + "/" + number
            if net is None:
                self.items.append(f'(no_connect (at {px} {py}) (uuid "{uid(suffix)}"))')
                continue
            ex = round(px + side * 5.08, 4)
            self.items.append(f'(wire (pts (xy {px} {py}) (xy {ex} {py})) '
                              f'(stroke (width 0) (type default)) (uuid "{uid(suffix+"w")}"))')
            angle, justify = (0, "left bottom") if side == -1 else (180, "left bottom")
            self.items.append(f'(label {q(net)} (at {ex} {py} {angle}) '
                              f'{effects(1.0, "(justify "+justify+")")} (uuid "{uid(suffix+"l")}"))')
            self.nets.setdefault(net, []).append([ref, number])
        self.parts.append([ref, value, footprint, note])

    def text(self, content, x, y, size=1.5):
        self.items.append(f'(text {q(content)} (at {x} {y} 0) '
                          f'{effects(size,"(justify left top)")} (uuid "{uid(self.name+content)}"))')

    def two(self, ref, value, a, b, x, y, kind="R", note=""):
        # Device pin names keep polarity explicit on diodes and capacitors.
        self.part(ref, kind, value, x, y, {"1": a, "2": b}, note=note)

    def save(self):
        folder = ROOT / "hw" / self.name
        folder.mkdir(parents=True, exist_ok=True)
        embedded = [s[0].replace('(symbol '+q(n), '(symbol '+q('A2Ext:'+n), 1)
                    for n, s in self.symbols.items()]
        sch = (f'(kicad_sch (version 20250114) (generator "eeschema") '
               f'(uuid "{self.root}") (paper "{self.paper}") '
               f'(title_block (title {q(self.name)}) (date "2026-09-17") (rev "0.1-draft") '
               f'(comment 1 "Schematic prototype: physical qualification pending")) '
               f'(lib_symbols {" ".join(embedded)}) {" ".join(self.items)})\n')
        (folder / (self.name + ".kicad_sch")).write_text(sch)
        project = folder / (self.name + ".kicad_pro")
        if not project.exists():
            project.write_text('{"meta": {"filename": "' + self.name + '.kicad_pro", "version": 1}}\n')
        library = '(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'
        library += "\n".join(s[0] for s in self.symbols.values()) + ")\n"
        (folder / "a2ext.kicad_sym").write_text(library)
        (folder / "sym-lib-table").write_text(
            '(sym_lib_table (version 7) (lib (name "A2Ext")(type "KiCad")'
            '(uri "${KIPRJMOD}/a2ext.kicad_sym")(options "")(descr "Project symbols")))\n')
        with (folder / "BOM.csv").open("w") as f:
            writer = csv.writer(f)
            writer.writerow(["Reference", "Value", "Footprint", "Assembly note"])
            writer.writerows(self.parts)
        (folder / "connections.json").write_text(json.dumps(self.nets, indent=2) + "\n")


def base(name, paper="A3"):
    b = Board(name, paper)
    for kind, labels in (("R", ("1", "2")), ("C", ("1", "2")),
                         ("D", ("K", "A")), ("Fuse", ("1", "2")),
                         ("Jumper", ("1", "2"))):
        b.symbol(kind, [(1, labels[0], "passive")], [(2, labels[1], "passive")], 7.62)
    b.symbol("IDC20", [(i, f"{i}", "passive") for i in range(1, 21, 2)],
             [(i, f"{i}", "passive") for i in range(2, 21, 2)], 15.24)
    return b


def idc_nets(mode=None):
    result = {}
    for p in PINS["idc"]:
        if "gpio" in p:
            names = {v: k for k, v in PINS.get(mode, {}).items()} if mode else {}
            result[str(p["pin"])] = names.get(p["gpio"]) if mode else f'GP{p["gpio"]}'
        else:
            result[str(p["pin"])] = p["signal"] if mode is None else (
                p["signal"] if p["signal"] == "GND" or (mode == "dvi" and p["pin"] == 19) else None)
    return result


def carrier():
    b = base("a2ext-carrier", "A2")
    slot = {p["slot"]: p["signal"] for p in PINS["bus"]}
    slot.update({21: "RDY_N", 22: "DMA_N", 23: "INTOUT_N", 24: "DMAOUT_N", 25: "+5V_SLOT",
                 26: "GND", 27: "DMAIN_N", 28: "INTIN_N", 32: "INH_N", 33: "-12V",
                 34: "-5V", 35: "COLORREF", 36: "7M", 37: "Q3", 38: "PH1", 39: "USER1", 50: "+12V"})
    b.symbol("AppleII_Slot", [(i, slot[i], "passive") for i in range(1,26)],
             [(i, slot[i], "passive") for i in range(50,25,-1)], 35.56)
    nets = {str(i): "A2_" + slot[i] if i in {p["slot"] for p in PINS["bus"]} else None for i in slot}
    nets.update({"25": "+5V_SLOT", "26": "GND", "23": "INT_CHAIN", "28": "INT_CHAIN",
                 "24": "DMA_CHAIN", "27": "DMA_CHAIN"})
    nets["19"] = "SLOT19_OPTIONAL"
    b.part("J1", "AppleII_Slot", "Apple II slot, counter-clockwise numbering", 60.96, 83.82, nets)
    b.two("JP1", "SYNC: OPEN except verified slot 7", "SLOT19_OPTIONAL", "A2_SYNC", 66.04, 152.4, "Jumper")
    h1 = {1:"VBUS",2:"5V",3:"GND",4:"GND",5:"VREF",6:"GPIO0"}
    h1.update({i+6:f"GPIO{i}" for i in range(1,25)})
    h2 = {1:"GND",2:"GND",3:"3V3_EN",4:"GND",5:"3V3",6:"3V3",7:"GPIO47",8:"RUN"}
    h2.update({i:f"GPIO{56-i}" for i in range(9,31)})
    # H2 rows after RUN: odd contacts descend 47,45,...25; even descend 46,...26.
    h2.update({i:f"GPIO{54-i}" for i in range(9,31,2)})
    h2.update({i:f"GPIO{56-i}" for i in range(10,31,2)})
    b.symbol("WeAct_RP2350B_V1", [(f"H1.{i}",h1[i],"passive") for i in range(1,31)],
             [(f"H2.{i}",h2[i],"passive") for i in range(1,31)], 50.8)
    module = {}
    for header, mapping in (("H1",h1),("H2",h2)):
        for number,name in mapping.items():
            net = "GP"+name[4:] if name.startswith("GPIO") else {
                "VBUS":"USB_VBUS", "5V":"+5V_MOD", "3V3":"+3V3", "GND":"GND", "RUN":"RUN_N"}.get(name)
            module[f"{header}.{number}"] = net
    b.part("M1", "WeAct_RP2350B_V1", "WeAct RP2350B V1.0 (prepared module)", 208.28, 88.9, module,
           note="Remove R16, R19, R14, U2; U7/R13/C23 unpopulated. Verify module revision.")
    b.part("J2", "IDC20", "Daughterboard IDC20", 330.2, 73.66, idc_nets())
    b.symbol("CB3T3245", [(i+2,f"A{i+1}","passive") for i in range(8)] +
             [(19,"OE_N","input"),(20,"VCC","power_in")],
             [(18-i,f"B{i+1}","passive") for i in range(8)] +
             [(1,"NC","no_connect"),(10,"GND","power_in")], 30.48)
    for bank in range(5):
        pins = {str(i):None for i in range(1,21)}
        pins.update({"19":"BUS_OE_N","20":"+3V3","10":"GND"})
        for i,p in enumerate(PINS["bus"][bank*8:bank*8+8]):
            pins[str(i+2)],pins[str(18-i)] = "A2_"+p["signal"],f'GP{p["gpio"]}'
        b.part(f"U{bank+1}","CB3T3245","SN74CB3T3245PWR",447.04,45.72+bank*53.34,pins,
               "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm")
        b.two(f"C{bank+1}","100nF","+3V3","GND",530.86,45.72+bank*53.34,"C")
    # Supervisors are powered by module 3V3, including the slot-voltage monitor.
    b.symbol("TPS3808",[(6,"VDD","power_in"),(5,"SENSE","input"),(3,"MR_N","input")],
             [(1,"RESET_N","open_collector"),(4,"CT","input"),(2,"GND","power_in")],25.4)
    for ref,value,sense,x in [("U6","TPS3808G33DBVR","+3V3",63.5),
                              ("U7","TPS3808G50DBVR","+5V_SLOT",180.34)]:
        b.part(ref,"TPS3808",value,x,218.44,{"6":"+3V3","5":sense,"3":"RUN_N",
            "1":"BUS_GOOD","4":None,"2":"GND"},"Package_TO_SOT_SMD:SOT-23-6",
            "CT open: nominal 20 ms release delay")
    b.symbol("2N7002",[(1,"G","input")],[(3,"D","passive"),(2,"S","passive")],15.24)
    b.part("Q1","2N7002","2N7002",304.8,218.44,{"1":"BUS_GOOD","2":"GND","3":"BUS_OE_N"},
           "Package_TO_SOT_SMD:SOT-23")
    for ref,val,a,c,x,y in [("R1","10k","+3V3","BUS_GOOD",66.04,254),
                           ("R2","100k","BUS_GOOD","GND",180.34,254),
                           ("R3","4.7k","+3V3","BUS_OE_N",304.8,254),
                           ("R4","10k","+3V3","RUN_N",66.04,284.48)]:
        b.two(ref,val,a,c,x,y)
    b.two("D1","SS14","+5V_MOD","+5V_FUSED",66.04,332.74,"D")
    b.two("D2","SS14","+5V_MOD","USB_VBUS",180.34,332.74,"D")
    b.two("F1","500mA PTC","+5V_SLOT","+5V_FUSED",66.04,304.8,"Fuse")
    b.two("F2","100mA PTC","+5V_FUSED","+5V_DB",304.8,332.74,"Fuse")
    for i,rail,x,y,value in [(6,"+3V3",66.04,363.22,"100nF"),
        (7,"+3V3",180.34,363.22,"100nF"),(8,"+5V_SLOT",304.8,363.22,"100nF"),
        (9,"+5V_MOD",447.04,304.8,"10uF"),(10,"+3V3",447.04,332.74,"10uF")]:
        b.two(f"C{i}",value,rail,"GND",x,y,"C")
    b.symbol("PowerFlag",[(1,"PWR_FLAG","power_out")],[],7.62)
    for i,net in enumerate(["+3V3","GND"]):
        b.part(f"#FLG0{i+1}","PowerFlag","PWR_FLAG",530.86,304.8+i*25.4,{"1":net})
    b.text("BUS ISOLATION / POWER SEQUENCING PROTOTYPE\nPhysical acceptance required before connection to a host.",30.48,15.24)
    b.text("M1: remove onboard U2; carrier D1/D2 provide explicit supply OR-ing.\nRemove R16/R19/R14. No secondary flash/PSRAM.\nIRQ/NMI: firmware assert-low or release only.\nRUN_N is module reset, separate from Apple II /RES.",30.48,170.18)
    b.text("CB3T devices limit high levels to VCC; not CB3Q substitutes.\nBUS_OE_N defaults high; Q1 enables only after both supervisors release.\nUnused channels: NC. Each switch needs a local 100nF capacitor.\nSlot SYNC jumper is open unless pin 19 is verified.",294.64,114.3)
    b.save()


def vga():
    b = base("a2ext-vga")
    b.part("J1", "IDC20", "Carrier IDC20", 50.8, 71.12, idc_nets("vga"))
    signals={1:"RED",2:"GREEN",3:"BLUE",4:"ID2",5:"GND",6:"RGND",7:"GGND",8:"BGND",
             9:"KEY",10:"SGND",11:"ID0",12:"DDC_SDA",13:"HSYNC",14:"VSYNC",15:"DDC_SCL"}
    b.symbol("VGA_Female",[(i,signals[i],"passive") for i in range(1,16)],
             [("SH","SHELL","passive")],30.48)
    nets={str(i):None for i in range(1,16)}
    nets.update({"1":"VGA_R","2":"VGA_G","3":"VGA_B","13":"VGA_HSYNC","14":"VGA_VSYNC","SH":"GND"})
    nets.update({str(i):"GND" for i in [5,6,7,8,10]})
    b.part("J2","VGA_Female","DE-15HD female",350.52,83.82,nets,
           note="Shell contact modeled as SH; select physical connector before PCB layout")
    for channel, color in enumerate("RGB"):
        for bit, value in enumerate(["2k 1%","1k 1%","500R 1%"]):
            b.two(f"R{channel*3+bit+1}",value,f"{color}{bit}",f"VGA_{color}",
                  157.48+bit*71.12,55.88+channel*40.64)
    b.two("R10","47R","HSYNC","VGA_HSYNC",157.48,187.96)
    b.two("R11","47R","VSYNC","VGA_VSYNC",269.24,187.96)
    b.text("VGA / 3-bit resistor DAC per color\n640x480 approximately 60 Hz; 75 ohm monitor termination",20.32,15.24)
    b.text("R0/G0/B0 are the least-significant bits (2k).\nR2/G2/B2 are the most-significant bits (500 ohm).\nCalculated full-scale: 0.686 V at ideal 3.3 V GPIO levels.\nPhysical levels, rise time, and sync timing need validation.\nIDC power, UART, RUN, and GPIO46/47 are unused.",30.48,223.52)
    b.save()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board",choices=["carrier", "vga"])
    args=parser.parse_args()
    if args.board == "carrier":
        carrier()
    elif args.board == "vga":
        vga()


if __name__ == "__main__":
    main()
