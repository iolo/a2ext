#!/usr/bin/env python3
"""Embed the demo's ca65-linked slot/expansion ROM as C bytes."""
from pathlib import Path
import sys

data = Path(sys.argv[1]).read_bytes()
if len(data) != 4096:
    raise SystemExit("Expected a 4096-byte slot ROM image")
rows = [", ".join(f"0x{x:02x}" for x in data[i:i+16]) for i in range(0,len(data),16)]
Path(sys.argv[2]).write_text("/* Generated from a2pico-derived firmware.S. */\n"
    "#include <stdint.h>\nstatic const uint8_t firmware_rom[4096] = {\n"
    + ",\n".join(rows) + "\n};\n")
