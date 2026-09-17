cmake_minimum_required(VERSION 3.20)

if(NOT PICO_SDK_PATH AND DEFINED ENV{PICO_SDK_PATH})
    set(PICO_SDK_PATH "$ENV{PICO_SDK_PATH}")
endif()
if(NOT EXISTS "${PICO_SDK_PATH}/pico_sdk_init.cmake")
    message(FATAL_ERROR "Set PICO_SDK_PATH to Pico SDK 2.2.0; see fw/README.md")
endif()
set(PICO_BOARD a2ext_weact CACHE STRING "a2ext prepared WeAct module")
set(PICO_BOARD_HEADER_DIRS "${CMAKE_CURRENT_LIST_DIR}/fw/boards")
set(PICO_PLATFORM rp2350-arm-s CACHE STRING "RP2350 ARM target")
include("${PICO_SDK_PATH}/pico_sdk_init.cmake")
project(a2ext VERSION 0.1.0 LANGUAGES C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()
if(NOT PICO_SDK_VERSION_STRING VERSION_EQUAL "2.2.0")
    message(FATAL_ERROR "This build is pinned to Pico SDK 2.2.0")
endif()

add_subdirectory(fw/a2ext-lib)
option(A2EXT_DEMO_ACTIVE "Enable experimental active demo (requires qualified hardware)" OFF)
foreach(app demo vga dvi)
    add_executable(a2ext-${app} fw/a2ext-${app}/main.c)
    target_link_libraries(a2ext-${app} PRIVATE a2ext-lib pico_multicore)
    target_compile_options(a2ext-${app} PRIVATE -Wall -Wextra -Werror)
    # Firmware uses C only; no C++ allocation support or libstdc++ required.
    target_compile_definitions(a2ext-${app} PRIVATE PICO_CXX_DISABLE_ALLOCATION_OVERRIDES=1)
    set_target_properties(a2ext-${app} PROPERTIES LINKER_LANGUAGE C)
    pico_enable_stdio_uart(a2ext-${app} 0)
    pico_enable_stdio_usb(a2ext-${app} 0)
    pico_add_extra_outputs(a2ext-${app})
endforeach()

if(A2EXT_DEMO_ACTIVE)
    find_program(CA65 ca65 REQUIRED)
    find_program(LD65 ld65 REQUIRED)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/firmware_rom.h
        COMMAND ${CA65} ${CMAKE_CURRENT_SOURCE_DIR}/fw/a2ext-demo/firmware.S -o firmware.o
        COMMAND ${LD65} -C ${CMAKE_CURRENT_SOURCE_DIR}/fw/a2ext-demo/firmware.cfg firmware.o -o firmware.rom
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/embed_rom.py firmware.rom firmware_rom.h
        DEPENDS fw/a2ext-demo/firmware.S fw/a2ext-demo/firmware.cfg tools/embed_rom.py
        VERBATIM)
    target_sources(a2ext-demo PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/firmware_rom.h)
    target_include_directories(a2ext-demo PRIVATE ${CMAKE_CURRENT_BINARY_DIR})
    target_compile_definitions(a2ext-demo PRIVATE A2EXT_DEMO_ACTIVE=1)
    pico_set_binary_type(a2ext-demo copy_to_ram)
endif()

set(A2EXT_APPLE_MODEL "IIE" CACHE STRING "Host model: IIE or IIPLUS (also original II)")
set_property(CACHE A2EXT_APPLE_MODEL PROPERTY STRINGS IIE IIPLUS)
if(NOT A2EXT_APPLE_MODEL MATCHES "^(IIE|IIPLUS)$")
    message(FATAL_ERROR "A2EXT_APPLE_MODEL must be IIE or IIPLUS")
endif()
option(A2EXT_VIDEO_TEST_PATTERN "Render a video test pattern instead of host memory" OFF)
foreach(app vga dvi)
    target_sources(a2ext-${app} PRIVATE fw/video/runtime.c)
    target_include_directories(a2ext-${app} PRIVATE fw/video)
    target_compile_definitions(a2ext-${app} PRIVATE APPLE_MODEL_${A2EXT_APPLE_MODEL}=1)
    if(A2EXT_VIDEO_TEST_PATTERN)
        target_compile_definitions(a2ext-${app} PRIVATE A2EXT_VIDEO_TEST_PATTERN=1)
    endif()
endforeach()
target_sources(a2ext-vga PRIVATE
    fw/a2ext-vga/buffers.c fw/a2ext-vga/colors.c fw/a2ext-vga/render.c
    fw/a2ext-vga/render_text.c fw/a2ext-vga/render_lores.c fw/a2ext-vga/render_hires.c
    fw/a2ext-vga/render_testpat.c fw/a2ext-vga/vga.c
    fw/a2ext-vga/textfont/iie_us_enhanced.c fw/a2ext-vga/textfont/iiplus_us.c)
pico_generate_pio_header(a2ext-vga ${CMAKE_CURRENT_LIST_DIR}/fw/a2ext-vga/vga.pio)

add_subdirectory(fw/a2ext-dvi/libdvi)
target_link_libraries(a2ext-dvi PRIVATE libdvi)
target_include_directories(a2ext-dvi PRIVATE fw/a2ext-dvi)
target_compile_definitions(a2ext-dvi PRIVATE DVI_N_TMDS_BUFFERS=8 DVI_VERTICAL_REPEAT=2)
target_sources(a2ext-dvi PRIVATE
    fw/a2ext-dvi/applebus/buffers.c fw/a2ext-dvi/render/frame.c
    fw/a2ext-dvi/render/render_text.c fw/a2ext-dvi/render/render_lores.c
    fw/a2ext-dvi/render/render_hires.c fw/a2ext-dvi/render/render_dgr.c
    fw/a2ext-dvi/render/render_dhgr.c
    fw/a2ext-dvi/dvi/tmds.c fw/a2ext-dvi/dvi/tmds_lores.c
    fw/a2ext-dvi/dvi/tmds_hires.c fw/a2ext-dvi/dvi/tmds_dhgr.c
    fw/a2ext-dvi/fonts/iie_us_enhanced.c fw/a2ext-dvi/fonts/iiplus_us.c)
