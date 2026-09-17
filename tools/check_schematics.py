#!/usr/bin/env python3
"""Run KiCad ERC and compare exported connectivity to the board contract."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def check(board):
    folder = ROOT / "hw" / board
    source = folder / (board + ".kicad_sch")
    with tempfile.TemporaryDirectory(prefix="a2ext-erc-") as tmp:
        subprocess.run(["kicad-cli", "sch", "erc", "--exit-code-violations",
                        "--format", "json", "-o", tmp + "/erc.json", str(source)], check=True)
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml",
                        "-o", tmp + "/netlist.xml", str(source)], check=True)
        tree = ET.parse(tmp + "/netlist.xml")
        nets = {n.get("name").lstrip("/"): {(node.get("ref"), node.get("pin"))
                 for node in n.findall("node")} for n in tree.findall(".//nets/net")}
        expected = json.loads((folder / "connections.json").read_text())
        for name, nodes in expected.items():
            # KiCad omits virtual power flags from physical netlist nodes.
            assert nets.get(name) == {tuple(n) for n in nodes if not n[0].startswith("#")}, (name, nets.get(name), nodes)
        if board == "a2ext-carrier":
            pins = json.loads((ROOT / "hw/pinout.json").read_text())
            gpio_nets = {p["gpio"]: p["signal"] for p in pins["bus"]}
            for p in pins["idc"]:
                net = (f'IDC{p["pin"]:02d}_GPIO{p["gpio"]}'
                       if p.get("gpio") in pins["daughter_gpios"] else p["signal"])
                if "gpio" in p:
                    gpio_nets[p["gpio"]] = net
                assert ("J2", str(p["pin"])) in nets[net]
            for gpio in range(48):
                if gpio <= 24:
                    contact = f"H1.{gpio+6}"
                elif gpio == 47:
                    contact = "H2.7"
                elif gpio % 2:
                    contact = f"H2.{54-gpio}"
                else:
                    contact = f"H2.{56-gpio}"
                assert ("M1", contact) in nets[gpio_nets[gpio]], (gpio, contact)
            for p in pins["bus"]:
                gpio = p["gpio"]
                contact = (f"H1.{gpio+6}" if gpio <= 24 else
                           f"H2.{54-gpio}" if gpio % 2 else f"H2.{56-gpio}")
                host = ("JP1", "2") if p["signal"] == "SYNC" else ("J1", str(p["slot"]))
                assert nets[gpio_nets[gpio]] == {host, ("M1", contact)}, p
            assert nets["SLOT19_OPTIONAL"] == {("J1", "19"), ("JP1", "1")}
            assert "BUS_GOOD" not in nets and "BUS_OE_N" not in nets
            # Slot-only power: D1 anode is pin 2, cathode is pin 1.
            assert nets["+5V_SLOT"] == {("J1", "25"), ("F1", "1"), ("C8", "1")}
            assert nets["+5V_FUSED"] == {("F1", "2"), ("D1", "2"), ("F2", "1")}
            assert nets["VSYS"] == {("D1", "1"), ("M1", "H1.2"), ("C9", "1")}
            assert "USB_VBUS" not in nets
            # KiCad may export an NC pin as its own singleton net.
            assert all(nodes == {("M1", "H1.1")} for nodes in nets.values()
                       if ("M1", "H1.1") in nodes)
            assert "D2" not in {c.get("ref") for c in tree.findall(".//components/comp")}
            assert nets["INT_CHAIN"] == {("J1","23"),("J1","28")}
            assert nets["DMA_CHAIN"] == {("J1","24"),("J1","27")}
        print(f"{board}: ERC and {len(expected)} named net connectivity checks passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("boards", nargs="+", choices=["a2ext-carrier", "a2ext-vga", "a2ext-dvi"])
    for board in parser.parse_args().boards:
        check(board)
