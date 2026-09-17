# VGA firmware

Port of the bundled rallepalaveev AppleII-VGA renderer (MIT, see LICENSE).
Uses shared passive capture/shadow on core 1 and frame snapshots/rendering on
core 0. PIO1 base 16 generates RGB333 and sync; DMA IRQ0 feeds eight scanline
buffers. Capture uses PIO0 and DMA IRQ1. No full RGB framebuffer is allocated.

Default output is 640x480 at 60 Hz, centered 560x384 Apple content. Supports
40-column text, lores, hires, mixed mode and page selection; IIe adds 80-column,
alternate charset, double lores and double hires. Defaults to enhanced US IIe
font; `A2EXT_APPLE_MODEL=IIPLUS` selects II/II+ font and bank behavior. Videx,
Video7 control extensions and PAL color emulation are not enabled.

`A2EXT_VIDEO_TEST_PATTERN=ON` renders the upstream test chart while capture
continues. UART `?` reports capture losses and known soft switches. Initial
unobserved bytes render as zero; reset/stream loss may require host switch
initialization and redraw. Physical timing, DAC levels, sustained throughput,
and display correctness are not yet qualified.

Port changes: GPIO35-45 mapping/base 16, RGB channel bit reversal at DMA
submission (including precomputed hires patterns), valid OUT count for nine
pins, 8 mA DAC drive, shared shadow snapshots and finite frame entry point.
