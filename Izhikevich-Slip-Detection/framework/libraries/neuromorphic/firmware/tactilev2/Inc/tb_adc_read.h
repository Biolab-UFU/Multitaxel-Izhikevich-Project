/*
 * tb_adc_read.h
 *
 *  Created on: Aug 7, 2018
 *      Author: ner
 */

#ifndef TB_ADC_READ_H_
#define TB_ADC_READ_H_

#include "stdint.h"

//functions
void select_row(uint8_t rowId); //determine the row to be read from the tactile sensor
void select_column(uint8_t colId); //determine the column to be read from the tactile sensor
void set_adc(); //setup adc for single channel conversion
uint16_t read_adc(uint8_t channel); //read from the selected adc channel

#endif /* TB_ADC_READ_H_ */
