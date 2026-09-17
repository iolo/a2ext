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


def effects(size=1.778, extra=""):
    return f"(effects (font (size {size} {size})) {extra})"


class Board:
    def __init__(self, name, paper="A4"):
        self.name, self.paper = name, paper
        self.revision = "0.1-draft"
        self.outward_labels = True
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
                            f'(name {q(label)} {effects(1.524)}) (number {q(number)} {effects(1.27)}))')
        data = (f'(symbol {q(name)} (pin_names (offset 1.016)) (in_bom yes) (on_board yes) '
                f'(property "Reference" "U" (at 0 {height/2+7.62} 0) {effects()}) '
                f'(property "Value" {q(name)} (at 0 {height/2+3.81} 0) {effects()}) '
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
            f'(property "Reference" {q(ref)} (at {x} {y-height/2-7.62} 0) {effects()}) '
            f'(property "Value" {q(value)} (at {x} {y-height/2-3.81} 0) {effects(1.524)}) '
            f'(property "Footprint" {q(footprint)} (at {x} {y} 0) {effects(1.524,"hide")}) '
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
            if self.outward_labels:
                angle, justify = 0, "right bottom" if side == -1 else "left bottom"
            else:
                angle, justify = (0 if side == -1 else 180), "left bottom"
            self.items.append(f'(label {q(net)} (at {ex} {py} {angle}) '
                              f'{effects(1.524, "(justify "+justify+")")} (uuid "{uid(suffix+"l")}"))')
            self.nets.setdefault(net, []).append([ref, number])
        self.parts.append([ref, value, footprint, note])

    def text(self, content, x, y, size=1.778):
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
               f'(title_block (title {q(self.name)}) (date "2026-09-18") (rev {q(self.revision)}) '
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
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(["Reference", "Value", "Footprint", "Assembly note"])
            writer.writerows(self.parts)
        (folder / "connections.json").write_text(json.dumps(self.nets, indent=2) + "\n")


def base(name, paper="A4"):
    b = Board(name, paper)
    for kind, labels in (("R", ("1", "2")), ("C", ("1", "2")),
                         ("D", ("K", "A")), ("Fuse", ("1", "2")),
                         ("Jumper", ("1", "2"))):
        b.symbol(kind, [(1, labels[0], "passive")], [(2, labels[1], "passive")], 7.62)
    b.symbol("IDC20", [(i, f"{i}", "passive") for i in range(1, 21, 2)],
             [(i, f"{i}", "passive") for i in range(2, 21, 2)], 15.24)
    return b


def carrier_gpio_nets():
    names = {p["gpio"]: p["signal"] for p in PINS["bus"]}
    for p in PINS["idc"]:
        if "gpio" in p:
            names[p["gpio"]] = (p["signal"] if p["gpio"] in PINS["uart"].values()
                                else f'IDC{p["pin"]:02d}_GPIO{p["gpio"]}')
    return names


def idc_nets(mode=None):
    result = {}
    for p in PINS["idc"]:
        if "gpio" in p:
            names = {v: k for k, v in PINS.get(mode, {}).items()} if mode else {}
            result[str(p["pin"])] = names.get(p["gpio"]) if mode else carrier_gpio_nets()[p["gpio"]]
        else:
            result[str(p["pin"])] = p["signal"] if mode is None else (
                p["signal"] if p["signal"] == "GND" or (mode == "dvi" and p["pin"] == 19) else None)
    return result


def carrier():
    b = base("a2ext-carrier")
    b.revision = "0.5"
    # Labels extend away from symbols so names do not overlap pin numbers.
    b.outward_labels = True
    gpio_nets = carrier_gpio_nets()
    slot = {p["slot"]: p["signal"] for p in PINS["bus"]}
    slot.update({21: "RDY_N", 22: "DMA_N", 23: "INTOUT_N", 24: "DMAOUT_N", 25: "+5V_SLOT",
                 26: "GND", 27: "DMAIN_N", 28: "INTIN_N", 32: "INH_N", 33: "-12V",
                 34: "-5V", 35: "COLORREF", 36: "7M", 37: "Q3", 38: "PH1", 39: "USER1", 50: "+12V"})
    b.symbol("AppleII_Slot", [(i, slot[i], "passive") for i in range(1,26)],
             [(i, slot[i], "passive") for i in range(50,25,-1)], 35.56)
    bus_nets = {p["slot"]: gpio_nets[p["gpio"]] for p in PINS["bus"]}
    nets = {str(i): bus_nets.get(i) for i in slot}
    nets.update({"25": "+5V_SLOT", "26": "GND", "23": "INT_CHAIN", "28": "INT_CHAIN",
                 "24": "DMA_CHAIN", "27": "DMA_CHAIN"})
    nets["19"] = "SLOT19_OPTIONAL"
    b.part("J1", "AppleII_Slot", "Apple II slot, counter-clockwise numbering", 60.96, 73.66, nets)
    b.two("JP1", "SYNC: OPEN except verified slot 7", "SLOT19_OPTIONAL", bus_nets[19], 55.88, 119.38, "Jumper")
    h1 = {1:"VBUS",2:"5V",3:"GND",4:"GND",5:"VREF",6:"GPIO0"}
    h1.update({i+6:f"GPIO{i}" for i in range(1,25)})
    h2 = {1:"GND",2:"GND",3:"3V3_EN",4:"GND",5:"3V3",6:"3V3",7:"GPIO47",8:"RUN"}
    h2.update({i:f"GPIO{56-i}" for i in range(9,31)})
    # H2 rows after RUN: odd contacts descend 47,45,...25; even descend 46,...26.
    h2.update({i:f"GPIO{54-i}" for i in range(9,31,2)})
    h2.update({i:f"GPIO{56-i}" for i in range(10,31,2)})
    power_labels = {"5V": "5V (VSYS)", "VBUS": "VBUS (USB)", "RUN": "RUN (RESET)"}
    b.symbol("WeAct_RP2350B_V1", [(f"H1.{i}",power_labels.get(h1[i],h1[i]),"passive") for i in range(1,31)],
             [(f"H2.{i}",power_labels.get(h2[i],h2[i]),"passive") for i in range(1,31)], 50.8)
    module = {}
    for header, mapping in (("H1",h1),("H2",h2)):
        for number,name in mapping.items():
            net = gpio_nets[int(name[4:])] if name.startswith("GPIO") else {
                "5V":"VSYS", "3V3":"+3V3", "GND":"GND", "RUN":"RUN_N"}.get(name)
            module[f"{header}.{number}"] = net
    b.part("M1", "WeAct_RP2350B_V1", "WeAct RP2350B V1.0 (prepared module)", 154.94, 73.66, module,
           note="Remove R16, R19, R14, U2; U7/R13/C23 unpopulated. H1.2 5V is VSYS; H1.1 VBUS is NC. USB data only.")
    b.symbol("IDC20", [(p["pin"],p["signal"],"passive") for p in PINS["idc"] if p["pin"] % 2],
             [(p["pin"],p["signal"],"passive") for p in PINS["idc"] if not p["pin"] % 2], 30.48)
    b.part("J2", "IDC20", "Daughterboard IDC20", 241.3, 134.62, idc_nets())
    b.two("R4","10k","+3V3","RUN_N",38.1,160.02)
    b.two("D1","SS14","VSYS","+5V_FUSED",96.52,137.16,"D")
    b.two("F1","500mA PTC","+5V_SLOT","+5V_FUSED",38.1,137.16,"Fuse")
    b.two("F2","100mA PTC","+5V_FUSED","+5V_DB",154.94,137.16,"Fuse")
    for i,rail,x,y,value in [(8,"+5V_SLOT",38.1,182.88,"100nF"),
        (9,"VSYS",96.52,182.88,"10uF"),(10,"+3V3",154.94,182.88,"10uF")]:
        b.two(f"C{i}",value,rail,"GND",x,y,"C")
    b.symbol("PowerFlag",[(1,"PWR_FLAG","power_out")],[],7.62)
    for i,net in enumerate(["+3V3","GND"]):
        b.part(f"#FLG0{i+1}","PowerFlag","PWR_FLAG",96.52+i*58.42,160.02,{"1":net})
    b.text("APPLE II / RP2350B CARRIER\nDirect bus; slot-only power",12.7,12.7,2.032)
    b.text("MODULE PREPARATION\nRemove R16, R19, R14, U2.\nLeave U7/R13/C23 empty.\nVBUS: NC; USB data only.\nSee carrier README.",218.44,27.94)
    b.text("SIGNAL LABELS\n_N = active low.\nUART: carrier TX / RX.\nH1.n / H2.n: module pins.\nJP1: open except slot 7.\nIRQ/NMI: low or release.",218.44,58.42)
    b.text("Slot 25 -> F1/D1 -> VSYS.\n5V inputs need powered IOVDD.\nRUN is separate from /RES.\nNo hot-plugging; flash off-host.\nUse a 5V fixture at slot 25/26.",218.44,88.9)
    b.save()


def vga():
    b = base("a2ext-vga")
    b.revision = "0.2"
    b.part("J1", "IDC20", "Carrier IDC20", 40.64, 66.04, idc_nets("vga"))
    signals={1:"RED",2:"GREEN",3:"BLUE",4:"ID2",5:"GND",6:"RGND",7:"GGND",8:"BGND",
             9:"KEY",10:"SGND",11:"ID0",12:"DDC_SDA",13:"HSYNC",14:"VSYNC",15:"DDC_SCL"}
    b.symbol("VGA_Female",[(i,signals[i],"passive") for i in range(1,16)],
             [("SH","SHELL","passive")],30.48)
    nets={str(i):None for i in range(1,16)}
    nets.update({"1":"VGA_R","2":"VGA_G","3":"VGA_B","13":"VGA_HSYNC","14":"VGA_VSYNC","SH":"GND"})
    nets.update({str(i):"GND" for i in [5,6,7,8,10]})
    b.part("J2","VGA_Female","DE-15HD female",251.46,78.74,nets,
           note="Shell contact modeled as SH; select physical connector before PCB layout")
    for channel, color in enumerate("RGB"):
        for bit, value in enumerate(["2k 1%","1k 1%","500R 1%"]):
            b.two(f"R{channel*3+bit+1}",value,f"{color}{bit}",f"VGA_{color}",
                  91.44+bit*45.72,48.26+channel*30.48)
    b.two("R10","47R","HSYNC","VGA_HSYNC",91.44,139.7)
    b.two("R11","47R","VSYNC","VGA_VSYNC",182.88,139.7)
    b.text("VGA / RGB333 RESISTOR DAC\n640x480 / 60 Hz; 75 ohm monitor termination",12.7,12.7,2.032)
    b.text("R0/G0/B0: LSB (2k). R2/G2/B2: MSB (500 ohm).\nIdeal full-scale: 0.686 V with 3.3 V GPIO and 75 ohm load.\nVerify levels, rise times, and sync timing on hardware.\nIDC power, UART, RUN, and GPIO46/47 are unused.",12.7,165.1)
    b.save()


def dvi():
    b = base("a2ext-dvi")
    b.revision = "0.2"
    b.part("J1", "IDC20", "Carrier IDC20",40.64,76.2,idc_nets("dvi"))
    hdmi={1:"D2_P",2:"D2_SHIELD",3:"D2_N",4:"D1_P",5:"D1_SHIELD",6:"D1_N",
          7:"D0_P",8:"D0_SHIELD",9:"D0_N",10:"CLK_P",11:"CLK_SHIELD",12:"CLK_N",
          13:"CEC",14:"UTILITY",15:"SCL",16:"SDA",17:"GND",18:"+5V",19:"HPD"}
    b.symbol("HDMI_Type_A",[(i,hdmi[i],"passive") for i in range(1,20)],
             [("SH","SHELL","passive")],30.48)
    nets={str(i):None for i in range(1,20)}
    for i in [1,3,4,6,7,9,10,12]:
        nets[str(i)]="TMDS_"+hdmi[i]
    nets.update({str(i):"GND" for i in [2,5,8,11,17]})
    nets.update({"18":"+5V_DB","SH":"GND"})
    b.part("J2","HDMI_Type_A","HDMI-SWM-19 / Type A",251.46,83.82,nets,
           note="Verify chosen connector footprint; SH represents all shell contacts")
    for row,lane in enumerate(["D2","D1","D0","CLK"]):
        for column,polarity in enumerate(["P","N"]):
            signal=f"{lane}_{polarity}"
            b.two(f"R{row*2+column+1}","270R 1%",signal,"TMDS_"+signal,
                  96.52+column*63.5,48.26+row*27.94)
    b.two("C1","100nF","+5V_DB","GND",251.46,139.7,"C")
    b.text("DVI / HDMI TYPE A / RESISTOR-DRIVEN TMDS\n640x480 / 60 Hz; no audio or EDID negotiation",12.7,12.7,2.032)
    b.text("Even GPIO: positive. Odd GPIO: negative.\nlibdvi: invert_diffpairs=false; use 64-bit GPIO masks.\n+5V_DB: fused slot supply. DDC/HPD/CEC: NC.\nStart with direct mating; verify signal integrity and monitor lock.",12.7,165.1)
    b.save()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board",choices=["carrier", "vga", "dvi"])
    args=parser.parse_args()
    if args.board == "carrier":
        carrier()
    elif args.board == "vga":
        vga()
    elif args.board == "dvi":
        dvi()


if __name__ == "__main__":
    main()
