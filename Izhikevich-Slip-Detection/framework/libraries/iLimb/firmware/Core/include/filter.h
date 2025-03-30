#ifndef FILTER_H
#define FILTER_H

#define MAX_ADS_OUT 8388607     // 2^23-1 i.e. the max 24-bit 2s complement #   
#define MIN_ADS_OUT -8388608    // -2^23 i.e. the min 24-bit 2s complement #

int Filter_process_sensor_input(int index, int emg_data);
void Filter_init();

#endif