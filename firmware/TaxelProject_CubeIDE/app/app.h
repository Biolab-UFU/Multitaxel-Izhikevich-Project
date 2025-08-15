/*
 * app.h
 *
 *  Created on: Jan 12, 2025
 *      Author: stephan
 */

#ifndef APP_H_
#define APP_H_

typedef struct {
    uint16_t V_sensor_old;
    uint16_t V_sensor_new;
    uint16_t v_m_old;
    uint16_t v_m_new;
    uint16_t u_old;
    uint16_t u_new;
    uint16_t I;
} Taxel;

typedef struct {
    GPIO_TypeDef *port;
    uint16_t pin;
} GPIO_Map;

typedef struct {
	uint32_t timestamp;
	uint8_t channel;
} SpikeEvent;

#define SPIKE_BUFFER_SIZE 128 // Tamanho do buffer circular para os eventos

// Estrutura para o buffer circular
typedef struct {
    SpikeEvent buffer[SPIKE_BUFFER_SIZE];
    volatile uint16_t head;
    volatile uint16_t tail;
} CircularBuffer;

void initialize_taxels(Taxel *taxels, int num);
void app_setup(void);
void select_row(uint8_t coluna);
void update_taxels(Taxel *taxels, uint16_t *adc_values, int num);
uint8_t normalized_signal(uint16_t V);
uint16_t absolute_signal(uint16_t V1, uint16_t V2);

#endif /* APP_H_ */

