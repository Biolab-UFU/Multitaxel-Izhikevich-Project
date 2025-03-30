/*
 * app.c
 *
 *  Created on: Jan 12, 2025
 *      Author: stephan
 */

#include "main.h"
#include "app.h"
#include <stdlib.h>

#define NUM_TAXELS 16

// ==================== CONSTANTES DO MODELO IZHIKEVICH ====================
#define a_FA       0.1    // Parâmetro de recuperação
#define b_FA       0.2     // Parâmetro de recuperação
#define c_FA       -65     // Potencial de repouso após um spike
#define d_FA       2       // Ajuste na recuperação após um spike
#define G_FA       2000      // Ganho da corrente do modelo
#define a_SA       0.02    // Parâmetro de recuperação
#define b_SA       0.2     // Parâmetro de recuperação
#define c_SA       -65     // Potencial de repouso após um spike
#define d_SA       8       // Ajuste na recuperação após um spike
#define G_SA       20      // Ganho da corrente do modelo
#define vth     30      // Potencial de limiar (threshold)
#define V_min   1.65     // Valor mínimo de tensão do sensor
#define V_max   3.3     // Valor máximo de tensão do sensor
#define dt      0.001       // Intervalo de tempo para discretização

// ==================== VARIÁVEIS EXTERNAS ====================
extern ADC_HandleTypeDef hadc1;      // Manipulador do ADC
extern TIM_HandleTypeDef htim6;      // Manipulador do Timer 6

// ==================== VARIÁVEIS GLOBAIS ====================
const uint8_t buffer_size = 4;       // Tamanho do buffer do ADC
uint32_t adc_buffer[4];              // Buffer de leitura do ADC
uint8_t adc_ready = 0;               // Flag indicando que o ADC está pronto
uint8_t current_row = 0; 			 // Linha inicial

// Array para armazenar os estados dos FAs
FA fast_response[NUM_TAXELS];
SA slow_response[4];

// Estrutura de mapeamento de pinos GPIO para controle dos taxels
FS_Channels FS[NUM_TAXELS] = {
    {GPIOD, GPIO_PIN_13}, {GPIOD, GPIO_PIN_12}, {GPIOD, GPIO_PIN_11}, {GPIOE, GPIO_PIN_2},
    {GPIOC, GPIO_PIN_2},  {GPIOF, GPIO_PIN_4},  {GPIOB, GPIO_PIN_6},  {GPIOB, GPIO_PIN_2},
    {GPIOE, GPIO_PIN_13}, {GPIOF, GPIO_PIN_15}, {GPIOG, GPIO_PIN_14}, {GPIOG, GPIO_PIN_9},
    {GPIOE, GPIO_PIN_8},  {GPIOE, GPIO_PIN_7},  {GPIOE, GPIO_PIN_10}, {GPIOE, GPIO_PIN_12}
};

// Estrutura de mapeamento de pinos GPIO para controle dos taxels
RS_Channels RS[4] = {
    {GPIOx, GPIO_PIN_x}, {GPIOy, GPIO_PIN_y}, {GPIOz, GPIO_PIN_z}, {GPIOk, GPIO_PIN_k}
};


// ==================== FUNÇÕES ====================

/**
 * @brief Inicializa os taxels com valores padrão.
 * @param Array de taxels a ser inicializado.
 * @param num Número total de taxels.
 */


void initialize_taxels(FA *fast_response,SA *slow_response){
    for (int i = 0; i < 16; i++) {
        fast_response[i].V_sensor_old = 0;
        fast_response[i].V_sensor_new = 3.3; 
        fast_response[i].v_m_old = -30;
        fast_response[i].v_m_new = -30;
        fast_response[i].u_old = 0;
        fast_response[i].u_new = 0;
        fast_response[i].I = 0;
    }
    for(int i = 0; i < 4; i++){
    	slow_response[i].V_sensor = 0;
    	slow_response[i].v_m_old = -30;
    	slow_response[i].v_m_new = -30;
    	slow_response[i].u_old = 0;
    	slow_response[i].u_new = 0;
    	slow_response[i].I = 0;
    }
}

void app_setup(void)
{
	initialize_taxels(FA *fast_response,SA *slow_response);
	select_row(current_row);
	HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buffer, buffer_size); // Iniciar ADC com DMA
    HAL_TIM_Base_Start_IT(&htim6);
}

/**
 * @brief Alterna a linha ativa dos sensores.
 * @param row Número da linha a ser ativada (0 a 3).
 */
void select_row(uint8_t row) {
    // Desativa todas as colunas
    HAL_GPIO_WritePin(Row_1_GPIO_Port, Row_1_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(Row_2_GPIO_Port, Row_2_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(Row_3_GPIO_Port, Row_3_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(Row_4_GPIO_Port, Row_4_Pin, GPIO_PIN_SET);

    // Ativa a coluna especificada
    switch (row) {
        case 0: HAL_GPIO_WritePin(Row_1_GPIO_Port, Row_1_Pin, GPIO_PIN_RESET); break;
        case 1: HAL_GPIO_WritePin(Row_2_GPIO_Port, Row_2_Pin, GPIO_PIN_RESET); break;
        case 2: HAL_GPIO_WritePin(Row_3_GPIO_Port, Row_3_Pin, GPIO_PIN_RESET); break;
        case 3: HAL_GPIO_WritePin(Row_4_GPIO_Port, Row_4_Pin, GPIO_PIN_RESET); break;
        default: break;
    }
}

/**
 * @brief Callback executado a cada evento do Timer 6.
 * @param htim Manipulador do timer que gerou o evento.
 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
	// Verifica se a interrupção veio do Timer 6
    if (htim == &htim6) {
        // Buffer temporário para armazenar leituras do ADC para uma linha
        uint16_t adc_values[4];

        // Realiza a leitura do ADC para a linha ativa
        for (uint8_t column = 0; column < 4; column++) {
        	adc_values[column] = adc_buffer[column];
        }

        // Atualiza a estrutura dos taxels com os valores lidos
        update_taxels(&fast_response[current_row * 4], &slow_response[current_row],adc_values, 4);
        // Alterna para a próxima linha
        current_row = (current_row + 1) % 4;
        select_row(current_row);
    }
}


/**
 * @brief Atualiza os estados dos taxels com base nas leituras do ADC.
 * @param update_taxels Array de taxels a ser atualizado.
 * @param adc_values Leituras do ADC correspondentes aos taxels.
 * @param num Número de taxels a serem atualizados.
 */
void update_taxels(FA *fast_response, SA *slow_response,uint16_t *adc_values, int num) {
    for (int i = 0; i < num; i++) {
        fast_response[i].V_sensor_old = fast_response[i].V_sensor_new;
        fast_response[i].V_sensor_new = adc_values[i] * (3.3 / 4095.0); 
        float V_old_normalized = normalized_signal(fast_response[i].V_sensor_old);
        float V_new_normalized = normalized_signal(fast_response[i].V_sensor_new);
        fast_response[i].I = G*(absolute_signal(V_new_normalized, V_old_normalized))/ dt;
        fast_response[i].v_m_old = fast_response[i].v_m_new;
        fast_response[i].u_old = fast_response[i].u_new;
        fast_response[i].v_m_new = fast_response[i].v_m_old + dt * (0.04 * fast_response[i].v_m_old * fast_response[i].v_m_old
                             + 5 * fast_response[i].v_m_old + 140 - fast_response[i].u_old + fast_response[i].I);
        fast_response[i].u_new = fast_response[i].u_old + dt * (a_FA * (b_FA * fast_response[i].v_m_old - fast_response[i].u_old));
        if(fast_response[i].v_m_new < -30){
        	fast_response[i].v_m_new = -30;
        }
        if (fast_response[i].v_m_new >= vth) {
           fast_response[i].v_m_new = c_FA;
           fast_response[i].u_new += d_FA;
           int gpio_index = current_row * 4 + i;
           HAL_GPIO_WritePin(FS[gpio_index].port, FS[gpio_index].pin, GPIO_PIN_SET); // Sinaliza spike ~10-15us
           HAL_GPIO_WritePin(FS[gpio_index].port, FS[gpio_index].pin, GPIO_PIN_RESET);
        }
    }

    if(current_row == 1){
        for(int j = 0; j < 4; j++){
            slow_response[j].V_sensor = adc_values[j] * (3.3 / 4095.0);
            float V_normalized = normalized_signal(slow_response[j].V_sensor);
            slow_response[j].I = G_SA*V_normalized;
            slow_response[j].v_m_old = slow_response[j].v_m_new;
            slow_response[j].u_old = slow_response[j].u_new;
            slow_response[j].v_m_new = slow_response[j].v_m_old + dt * (0.04 * slow_response[j].v_m_old * slow_response[j].v_m_old
                                + 5 * slow_response[j].v_m_old + 140 - slow_response[j].u_old + slow_response[j].I);
            slow_response[j].u_new = slow_response[j].u_old + dt * (a_SA * (b_SA * slow_response[j].v_m_old - slow_response[j].u_old));
            if(slow_response[j].v_m_new < -30){
                slow_response[j].v_m_new = -30;
            }
            if (slow_response[j].v_m_new >= vth) {
            slow_response[j].v_m_new = c_SA;
            slow_response[j].u_new += d_SA;
            HAL_GPIO_WritePin(RS[j].port, RS[j].pin, GPIO_PIN_SET); 
            HAL_GPIO_WritePin(RS[j].port, RS[j].pin, GPIO_PIN_RESET);
            }                     
        }
    }
}

/**
 * @brief Normaliza os valores de tensão lidos pelos sensores.
 * @param V Tensão a ser normalizada.
 * @return Valor normalizado.
 */
float normalized_signal(float V) {
    return V/V_max;
}


/**
 * @brief Utiliza apenas o módulo
 * @param V1, V2 Tensões lidas pelo sensor
 */

float absolute_signal(float V1, float V2) {
    return (V1 > V2) ? (V1 - V2) : (V2 - V1);
}


