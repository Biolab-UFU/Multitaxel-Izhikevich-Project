/*
 * app.c
 *
 *  Created on: Sep 23, 2024
 *      Author: stephan
 */

#include "main.h"
#include "app.h"
#include "hw.h"

// Parâmetros do modelo de Izhikevich (se necessários)
#define NUM_TAXELS 16

void app_setup(void)
{
    HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buffer, buffer_size); // Iniciar ADC com DMA
    HAL_TIM_Base_Start_IT(&htim6); // Iniciar Timer com interrupção
    initialize_taxels(taxels, NUM_TAXELS); // Inicializar taxels
}


