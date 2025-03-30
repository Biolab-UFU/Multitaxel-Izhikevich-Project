/*
 * definitions.h
 *
 *  Created on: Aug 7, 2018
 *      Author: ner
 */

#ifndef DEFINITIONS_H_
#define DEFINITIONS_H_

/*
 * definitions.h
 *
 *  Created on: 6 de jun de 2018
 *      Author: Andrei
 */

#ifndef INC_DEFINITIONS_H_
#define INC_DEFINITIONS_H_

//PORTA
#define ADC_0 GPIO_PIN_0
#define ADC_1 GPIO_PIN_1
#define ADC_2 GPIO_PIN_2
#define ADC_3 GPIO_PIN_3
#define ADC_4 GPIO_PIN_4
#define ADC_5 GPIO_PIN_5
#define ADC_6 GPIO_PIN_6
#define ADC_7 GPIO_PIN_7
#define ADC_8 GPIO_PIN_8
#define IN_C1 GPIO_PIN_15 //PORTA
#define IN_C4 GPIO_PIN_10 //PORTA

//PORTB
#define SW_ADC89_A0_1 GPIO_PIN_3
#define SW_ADC89_A1_1 GPIO_PIN_4
#define SW_ADC89_EN_1 GPIO_PIN_5
#define SW_ADC89_A0_2 GPIO_PIN_13
#define SW_ADC89_A1_2 GPIO_PIN_14
#define SW_ADC89_EN_2 GPIO_PIN_15
#define IN_C2 GPIO_PIN_7 //PORTB
#define IN_C3 GPIO_PIN_6 //PORTB

//tactile sensors definitions
#define NROWS 4 //number of rows
#define NCOLS 4 //number of columns
#define NPATCH 5 //number of patches
#define MAX_ADC 9 //number of adc channels
#define DATA_BUFFER_SIZE 164 //5*2*16 + 2 + 2
#define PKG_ST 0x24
#define PKG_ET 0x21

//GLOBAL VARIABLES

//FUNCTIONS
void setup(); //initialize the hardware
void runTimer(); //handles timer interrupt


#endif /* INC_DEFINITIONS_H_ */


#endif /* DEFINITIONS_H_ */
