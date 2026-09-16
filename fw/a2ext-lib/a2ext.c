#include "a2ext.h"
#include "a2ext_pins.h"
#include "hardware/gpio.h"

void a2ext_init(void) {
    for (unsigned pin = A2EXT_GPIO_A0; pin <= A2EXT_GPIO_SYNC; ++pin) {
        gpio_init(pin);
        gpio_disable_pulls(pin);
        gpio_put(pin, false);
        gpio_set_dir(pin, GPIO_IN);
    }
}
