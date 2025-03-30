/*
 * tb_adc_read.c
 *
 *  Created on: Aug 7, 2018
 *      Author: ner
 */


#include "tb_adc_read.h"
#include "definitions.h"
#include "stm32f1xx_hal.h"

/* Global Variables */
extern ADC_HandleTypeDef hadc1;

//variables
uint8_t rows[4] = {0,1,3,2};
uint8_t cols[4] = {0,1,2,3};

//determine the row to be read from the tactile sensor
void select_row(uint8_t rowId)
{
	//first mux
	HAL_GPIO_WritePin(GPIOB, SW_ADC89_A1_1, (int)(rows[rowId]/2));
	HAL_GPIO_WritePin(GPIOB, SW_ADC89_A0_1, rows[rowId]%2);
	HAL_GPIO_WritePin(GPIOB, SW_ADC89_EN_1, GPIO_PIN_SET);

	//second mux
	HAL_GPIO_WritePin(GPIOB, SW_ADC89_A1_2, (int)(rows[rowId]/2) );
	HAL_GPIO_WritePin(GPIOB, SW_ADC89_A0_2, rows[rowId]%2);
	HAL_GPIO_WritePin(GPIOB, SW_ADC89_EN_2, GPIO_PIN_SET);
}

//determine the column to be read from the tactile sensor
void select_column(uint8_t colId)
{
	//switching columns
	if(colId == 0) //ground the first column
	{
		HAL_GPIO_WritePin(GPIOA, IN_C1, GPIO_PIN_RESET);
		HAL_GPIO_WritePin(GPIOB, IN_C2, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOB, IN_C3, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOA, IN_C4, GPIO_PIN_SET);
	}
	else if(colId == 1) //ground the second column
	{
		HAL_GPIO_WritePin(GPIOA, IN_C1, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOB, IN_C2, GPIO_PIN_RESET);
		HAL_GPIO_WritePin(GPIOB, IN_C3, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOA, IN_C4, GPIO_PIN_SET);
	}
	else if(colId == 2) //ground the third column
	{
		HAL_GPIO_WritePin(GPIOA, IN_C1, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOB, IN_C2, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOB, IN_C3, GPIO_PIN_RESET);
		HAL_GPIO_WritePin(GPIOA, IN_C4, GPIO_PIN_SET);
	}
	else if(colId == 3) //ground the fourth column
	{
		HAL_GPIO_WritePin(GPIOA, IN_C1, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOB, IN_C2, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOB, IN_C3, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOA, IN_C4, GPIO_PIN_RESET);
	}
}

//setup adc for single channel conversion
void set_adc()
{
	hadc1.Instance = ADC1;
	hadc1.Init.ScanConvMode = DISABLE;
	hadc1.Init.ContinuousConvMode = DISABLE;
	hadc1.Init.DiscontinuousConvMode = DISABLE;
	hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
	hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
	hadc1.Init.NbrOfConversion = 1;
	if (HAL_ADC_Init(&hadc1) != HAL_OK)
	{
		_Error_Handler(__FILE__, __LINE__);
	}
}

//read from the selected adc channel
uint16_t read_adc(uint8_t channel)
{
	ADC_ChannelConfTypeDef sConfig;

	/**Configure Regular Channel
	 */
	//look for a better approach of doing the same thing
	//select proper adc channel to be read
	switch(channel)
	{
		case 0:
			sConfig.Channel = ADC_CHANNEL_0;
			break;
		case 1:
			sConfig.Channel = ADC_CHANNEL_1;
			break;
		case 2:
			sConfig.Channel = ADC_CHANNEL_2;
			break;
		case 3:
			sConfig.Channel = ADC_CHANNEL_3;
			break;
		case 4:
			sConfig.Channel = ADC_CHANNEL_4;
			break;
		case 5:
			sConfig.Channel = ADC_CHANNEL_5;
			break;
		case 6:
			sConfig.Channel = ADC_CHANNEL_6;
			break;
		case 7:
			sConfig.Channel = ADC_CHANNEL_7;
			break;
		case 8:
			sConfig.Channel = ADC_CHANNEL_8;
			break;
	}

	sConfig.Rank = ADC_REGULAR_RANK_1;
	sConfig.SamplingTime = ADC_SAMPLETIME_13CYCLES_5;
	if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
	{
		_Error_Handler(__FILE__, __LINE__);
	}

	//
	HAL_ADC_Start(&hadc1);
	HAL_ADC_PollForConversion(&hadc1,100);
	uint16_t adcv = HAL_ADC_GetValue(&hadc1);

	return adcv;
}
