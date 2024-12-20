/*
 * hw.h
 *
 *  Created on: Sep 23, 2024
 *      Author: stephan
 */

#ifndef HW_H_
#define HW_H_

#include "main.h"

// Definições de constantes do modelo de Izhikevich
#define NUM_TAXELS 16
#define V_min 1.5
#define V_max 3.3
#define G 20

// Estrutura para mapear os pinos GPIO dos taxels
typedef struct {
    GPIO_TypeDef *port;
    uint16_t pin;
} GPIO_Map;

// Estrutura para armazenar os estados do modelo Izhikevich para cada taxel
typedef struct {
    float V_sensor_old;
    float V_sensor_new;
    float v_m_old;
    float v_m_new;
    float u_old;
    float u_new;
    float I;
} Taxel;

// Variáveis globais
extern GPIO_Map gpio_map[NUM_TAXELS];
extern Taxel taxels[NUM_TAXELS];
extern uint32_t sensor_map[4][4];

// Declarações de funções
void initialize_taxels(Taxel *taxels, int num);
void update_taxels(Taxel *taxels, uint16_t *adc_values, int num);
void AlternarColuna(uint8_t coluna);
float NormalizedSignal(float V);

#endif /* HW_H_ */
