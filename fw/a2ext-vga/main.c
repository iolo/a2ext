#include "a2ext.h"
#include "pico/stdlib.h"

int main(void) {
    a2ext_init();
    /* Build bring-up only; VGA output is implemented in plan step 16. */
    while (true) tight_loop_contents();
}
