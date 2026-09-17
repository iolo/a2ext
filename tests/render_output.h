#pragma once
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
static uint8_t pixels[480][640][3];
static unsigned row;
static void save_frame(const char *dir, const char *name) {
    char path[512]; snprintf(path,sizeof path,"%s/%s.ppm",dir,name);
    FILE *f=fopen(path,"wb"); assert(f);
    fprintf(f,"P6\n640 480\n255\n");
    assert(fwrite(pixels,1,sizeof pixels,f)==sizeof pixels); fclose(f);
}
