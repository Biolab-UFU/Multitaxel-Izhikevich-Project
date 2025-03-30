#ifndef ELECTRODE_H
#define ELECTRODE_H
#include "mbed.h"
#include "errors.h"

#define MAX_ELECTRODES 8

ReturnCode Electrode_read_data(unsigned char index, int *data);
ReturnCode Electrode_read_ID(int index, int *ID);
ReturnCode Electrode_init(unsigned char index, SPI *spi_device, PinName spi_cs);
ReturnCode Electrode_BIT(int index);

#endif // ELECTRODE_H