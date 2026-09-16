#ifndef A2EXT_WEACT_H
#define A2EXT_WEACT_H
/* Prepared WeAct RP2350B Core Board V1.0. See module removal instructions. */
pico_board_cmake_set(PICO_PLATFORM, rp2350)
#define PICO_RP2350A 0
#define A2EXT_WEACT 1
#define PICO_DEFAULT_UART 0
#define PICO_DEFAULT_UART_TX_PIN 0
#define PICO_DEFAULT_UART_RX_PIN 1
/* No default LED/button/SPI/I2C: those GPIOs are Apple II bus signals. */
#define PICO_FLASH_SIZE_BYTES (16 * 1024 * 1024)
pico_board_cmake_set_default(PICO_FLASH_SIZE_BYTES, (16 * 1024 * 1024))
#define PICO_FLASH_SPI_CLKDIV 4
#define PICO_RP2350_A2_SUPPORTED 1
pico_board_cmake_set_default(PICO_RP2350_A2_SUPPORTED, 1)
#endif
