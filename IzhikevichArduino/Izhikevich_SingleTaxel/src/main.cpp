#include <Arduino.h>
#include <avr/io.h>
#include <avr/interrupt.h>

#define G 200
#define vth 30
#define a 0.02
#define b 0.2
#define c -65
#define d 8

volatile uint16_t adc_value = 0; // Armazena a leitura do ADC
const float dt = 0.05; // Definindo dt como o período do Timer1 (50ms)

struct Taxel {
    float V_sensor_old, V_sensor_new;
    float v_m_old, v_m_new;
    float u_old, u_new;
    float I;
};

Taxel taxel;

void setupTimer() {
    cli(); // Desabilita interrupções globais
    TCCR1A = 0;
    TCCR1B = (1 << WGM12) | (1 << CS12); // Modo CTC, prescaler 256
    OCR1A = 62499; // Interrupção a cada 50 ms (16 MHz / (256 * 50 Hz) - 1)
    TIMSK1 |= (1 << OCIE1A); // Habilita interrupção do Timer1
    sei(); // Habilita interrupções globais
}

ISR(TIMER1_COMPA_vect) {
    adc_value = analogRead(A1); // Lê o ADC no pino A1
    Serial.print("ADC: ");Serial.println(adc_value);
    update_taxel();
}

void initialize_taxel(Taxel &t) {
    t.V_sensor_old = 0;
    t.V_sensor_new = 3.3;
    t.v_m_old = -30;
    t.v_m_new = -30;
    t.u_old = 0;
    t.u_new = 0;
    t.I = 0;
}

void update_taxel() {
    taxel.V_sensor_old = taxel.V_sensor_new;
    taxel.V_sensor_new = adc_value * (5.0 / 1023.0); // Conversão ADC

    float V_old_normalized = (taxel.V_sensor_old - 2.93) / (5 - 1.65);
    float V_new_normalized = (taxel.V_sensor_new - 2.93) / (5 - 1.65);

    taxel.I = G * (V_new_normalized - V_old_normalized) / dt;

    taxel.v_m_old = taxel.v_m_new;
    taxel.u_old = taxel.u_new;

    taxel.v_m_new = taxel.v_m_old + dt * (0.04 * taxel.v_m_old * taxel.v_m_old + 5 * taxel.v_m_old + 140 - taxel.u_old + taxel.I);
    taxel.u_new = taxel.u_old + dt * (a * (b * taxel.v_m_old - taxel.u_old));

    if(taxel.v_m_new < -30){
      taxel.v_m_new = -30;
    }

    Serial.print("Membrane Potential: ");Serial.println(taxel.v_m_new);
    Serial.print("Recovery Potential: ");Serial.println(taxel.u_new);

    if (taxel.v_m_new >= vth) {
        taxel.v_m_new = c;
        taxel.u_new += d;
        //digitalWrite(13, !digitalRead(13)); // Toggle
        digitalWrite(13, HIGH);
        digitalWrite(13, LOW);
    } 
}

void setup() {
    Serial.begin(9600);
    pinMode(A1, INPUT); // LED indicador de spike
    pinMode(13, OUTPUT); // LED indicador de spike
    setupTimer();
    initialize_taxel(taxel);
}

void loop() {
    // O código principal pode rodar livremente, pois as leituras acontecem no Timer1 ISR
}