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
            for i, p in enumerate(pins["bus"]):
                ref, channel = f"U{i//8+1}", i % 8
                assert (ref, str(channel+2)) in nets["A2_"+p["signal"]]
                assert (ref, str(18-channel)) in nets[f'GP{p["gpio"]}']
                if p["signal"] != "SYNC":
                    assert ("J1", str(p["slot"])) in nets["A2_"+p["signal"]]
            for p in pins["idc"]:
                net = f'GP{p["gpio"]}' if "gpio" in p else p["signal"]
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
                assert ("M1", contact) in nets[f"GP{gpio}"], (gpio, contact)
            assert nets["INT_CHAIN"] == {("J1","23"),("J1","28")}
            assert nets["DMA_CHAIN"] == {("J1","24"),("J1","27")}
        print(f"{board}: ERC and {len(expected)} named net connectivity checks passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("boards", nargs="+", choices=["a2ext-carrier", "a2ext-vga", "a2ext-dvi"])
    for board in parser.parse_args().boards:
        check(board)
