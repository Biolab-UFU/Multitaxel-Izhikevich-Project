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
#define a       0.02    // Parâmetro de recuperação
#define b       0.2     // Parâmetro de recuperação
#define c       -65     // Potencial de repouso após um spike
#define d       8       // Ajuste na recuperação após um spike
#define vth     30      // Potencial de limiar (threshold)
#define V_min   1.5     // Valor mínimo de tensão do sensor
#define V_max   3.3     // Valor máximo de tensão do sensor
#define dt      0.001       // Intervalo de tempo para discretização
#define G       100      // Ganho da corrente do modelo (fast G = 500, regular = 700)

// ==================== VARIÁVEIS EXTERNAS ====================
extern ADC_HandleTypeDef hadc1;      // Manipulador do ADC
extern TIM_HandleTypeDef htim6;      // Manipulador do Timer 6
extern TIM_HandleTypeDef htim2;		 // Manipulador do Timer 2
extern UART_HandleTypeDef huart1;   // Manipulador da USART 1

// ==================== VARIÁVEIS GLOBAIS ====================
const uint8_t buffer_size = 4;       // Tamanho do buffer do ADC
uint32_t adc_buffer[4];              // Buffer de leitura do ADC
uint8_t adc_ready = 0;               // Flag indicando que o ADC está pronto
uint8_t current_row = 0; 			 // Linha inicial

// Array para armazenar os estados dos taxels
Taxel taxels[NUM_TAXELS];

// Estrutura de mapeamento de pinos GPIO para controle dos taxels
GPIO_Map gpio_map[NUM_TAXELS] = {
    {GPIOD, GPIO_PIN_13}, {GPIOD, GPIO_PIN_12}, {GPIOD, GPIO_PIN_11}, {GPIOE, GPIO_PIN_2},
    {GPIOC, GPIO_PIN_2},  {GPIOF, GPIO_PIN_4},  {GPIOB, GPIO_PIN_6},  {GPIOB, GPIO_PIN_2},
    {GPIOE, GPIO_PIN_13}, {GPIOF, GPIO_PIN_15}, {GPIOG, GPIO_PIN_14}, {GPIOG, GPIO_PIN_9},
    {GPIOE, GPIO_PIN_8},  {GPIOE, GPIO_PIN_7},  {GPIOE, GPIO_PIN_10}, {GPIOE, GPIO_PIN_12}
};

CircularBuffer spike_buffer;

// Buffer linear temporário para a transmissão via DMA
#define DMA_TX_BUFFER_SIZE  64 // Tamanho do buffer DMA em eventos
SpikeEvent dma_tx_buffer[DMA_TX_BUFFER_SIZE];

volatile uint8_t is_dma_tx_in_progress = 0; // Flag para sincronização

// ==================== FUNÇÕES ====================

/**
 * @brief Inicializa os taxels com valores padrão.
 * @param taxels Array de taxels a ser inicializado.
 * @param num Número total de taxels.
 */


void initialize_taxels(Taxel *taxels, int num) {
    for (int i = 0; i < num; i++) {
        taxels[i].V_sensor_old = 0;
        taxels[i].V_sensor_new = 3.3; // Exemplo de valor inicial
        taxels[i].v_m_old = -30;
        taxels[i].v_m_new = -30;
        taxels[i].u_old = 0;
        taxels[i].u_new = 0; // Para fast u = 1500, regular u = 1000
        taxels[i].I = 0;
    }
}

void app_setup(void)
{
	initialize_taxels(taxels, NUM_TAXELS);
	select_row(current_row);
	HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buffer, buffer_size); // Iniciar ADC com DMA
    HAL_TIM_Base_Start_IT(&htim6);
    HAL_TIM_Base_Start_IT(&htim2);
    spike_buffer.head = 0;
    spike_buffer.tail = 0;
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
 * @brief Adiciona eventos de Spike no buffer circular
 * @param timestamp tempo em microssegundos do evento a partir da execução do código
 * @param gpio_index fonte do Spike
 */
static void write_spike_event(uint32_t timestamp, uint8_t gpio_index) {
    // Verifique se o buffer não está cheio
    if (((spike_buffer.head + 1) % SPIKE_BUFFER_SIZE) != spike_buffer.tail) {
        spike_buffer.buffer[spike_buffer.head].timestamp = timestamp;
        spike_buffer.buffer[spike_buffer.head].channel = gpio_index;
        spike_buffer.head = (spike_buffer.head + 1) % SPIKE_BUFFER_SIZE;
    }
}

/**
 * @brief Acessa o buffer circular para ler os eventos de Spike
 */
static SpikeEvent read_spike_event(void) {
    SpikeEvent event = {0, 0}; // Valor padrão caso o buffer esteja vazio

    // Verifique se o buffer não está vazio
    if (spike_buffer.head != spike_buffer.tail) {
        event = spike_buffer.buffer[spike_buffer.tail];
        spike_buffer.tail = (spike_buffer.tail + 1) % SPIKE_BUFFER_SIZE;
    }

    return event;
}

/**
 * @brief Callback executado a cada evento completo de transmissão UART
 * @param huart Manipulador da UART que gerou o evento.
 */
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart == &huart1) {
    	// Limpa a flag para permitir uma nova transferência
        is_dma_tx_in_progress = 0;
    }
}

/**
 * @brief Callback executado a cada evento do Timer 6 e Timer 7
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
        update_taxels(&taxels[current_row * 4], adc_values, 4);
        // Alterna para a próxima linha
        current_row = (current_row + 1) % 4;
        select_row(current_row);
    }


    if (htim == &htim2) {
        	// Evita iniciar uma nova transferência se a anterior ainda não terminou
        	if (is_dma_tx_in_progress == 0) {

        		// Verifique se há dados para enviar
        		uint16_t available_events = 0;
        		if (spike_buffer.head >= spike_buffer.tail) {
        			available_events = spike_buffer.head - spike_buffer.tail;
        		} else {
        			available_events = SPIKE_BUFFER_SIZE - spike_buffer.tail + spike_buffer.head;
        		}

        		if (available_events > 0) {
        			// Determine quantos eventos enviar, limitado pelo buffer DMA
        			uint16_t events_to_send = (available_events > DMA_TX_BUFFER_SIZE) ? DMA_TX_BUFFER_SIZE : available_events;

        			// Copia os dados do buffer circular para o buffer linear DMA
        			for (uint16_t event = 0; event < events_to_send; event++) {
        				dma_tx_buffer[event] = read_spike_event();
        			}

        			// Inicia a transferência DMA
        			is_dma_tx_in_progress = 1; // Define a flag
        			HAL_UART_Transmit_DMA(&huart1, (uint8_t*)dma_tx_buffer, events_to_send * sizeof(SpikeEvent));
        		}
        	}
    }
}

/**
 * @brief Atualiza os estados dos taxels com base nas leituras do ADC.
 * @param taxels Array de taxels a ser atualizado.
 * @param adc_values Leituras do ADC correspondentes aos taxels.
 * @param num Número de taxels a serem atualizados.
 */
void update_taxels(Taxel *taxels, uint16_t *adc_values, int num) {
    for (int i = 0; i < num; i++) {
        // Atualiza a leitura do sensor
        taxels[i].V_sensor_old = taxels[i].V_sensor_new;
        taxels[i].V_sensor_new = adc_values[i] * (3.3 / 4095.0); // Conversão ADC -> Tensão

        //float V_old_normalized = normalized_signal(taxels[i].V_sensor_old);
        //float V_new_normalized = normalized_signal(taxels[i].V_sensor_new);

        // Calcula a corrente de entrada
        taxels[i].I = G*(absolute_signal(taxels[i].V_sensor_new,taxels[i].V_sensor_old))/ dt;
        //taxels[i].I = G*V_new_normalized;
        //taxels[i].I = G*taxels[i].V_sensor_new;

        // Atualiza o potencial de membrana e a recuperação
        taxels[i].v_m_old = taxels[i].v_m_new;
        taxels[i].u_old = taxels[i].u_new;

        taxels[i].v_m_new = taxels[i].v_m_old + dt * (0.04 * taxels[i].v_m_old * taxels[i].v_m_old
                             + 5 * taxels[i].v_m_old + 140 - taxels[i].u_old + taxels[i].I);

        taxels[i].u_new = taxels[i].u_old + dt * (a * (b * taxels[i].v_m_old - taxels[i].u_old));

        // Limite inferior
        if(taxels[i].v_m_new < -30){
        	taxels[i].v_m_new = -30;
        }

        // Detecta spikes
        if (taxels[i].v_m_new >= vth) {
           taxels[i].v_m_new = c;
           taxels[i].u_new += d;
           int gpio_index = current_row * 4 + i;
           // Pega o timestamp do timer de alta resolução
           uint32_t timestamp = __HAL_TIM_GET_COUNTER(&htim2);

           // Escreve o evento no buffer
           write_spike_event(timestamp, (uint8_t)gpio_index);

           HAL_GPIO_WritePin(gpio_map[gpio_index].port, gpio_map[gpio_index].pin, GPIO_PIN_SET); // Sinaliza spike ~10-15us
           HAL_GPIO_WritePin(gpio_map[gpio_index].port, gpio_map[gpio_index].pin, GPIO_PIN_RESET);
        }
    }
}

/**
 * @brief Normaliza os valores de tensão lidos pelos sensores.
 * @param V Tensão a ser normalizada.
 * @return Valor normalizado.
 */
uint8_t normalized_signal(uint16_t V) {
    return -1*(V - V_max) / (V_max - V_min);
}


/**
 * @brief Utiliza apenas o módulo
 * @param V1, V2 Tensões lidas pelo sensor
 */

uint16_t absolute_signal(uint16_t V1, uint16_t V2) {
    return (V1 > V2) ? (V1 - V2) : (V2 - V1);
}


