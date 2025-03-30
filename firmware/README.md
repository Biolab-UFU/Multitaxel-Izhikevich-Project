# TaxelProjet_CubeIDE

Este projeto foi desenvolvido para gerar **Fast-Spikes** com base no nível de pressão detectado pelos sensores taxels. O sistema utiliza o modelo de **Izhikevich** para simular o comportamento neuronal dos sensores.

## 📌 Funcionamento Geral

1. **Estruturas de Dados:**
   - Uma `struct` para armazenar os parâmetros do modelo Izhikevich para 16 taxels.
   - Uma `struct` para mapear os pinos GPIO aos quais os taxels estão conectados.

2. **Configuração do ADC (via DMA):**
   - **Clock:** Barramento dividido por 4.
   - **Resolução:** 12 bits.
   - **Scan Conversion Mode:** Habilitado.
   - **Continuous Conversion Mode:** Habilitado.
   - **Data Align:** Right.
   - **Number of Conversion:** 4 (um para cada coluna do sensor).
   - **DMA Continuous Requests:** Enable.
   - **Sample-Time:** 15 cycles por canal.

3. **Configuração do Timer:**
   - Um **timer de 4 kHz** é utilizado para:
     - Atualizar os parâmetros do modelo Izhikevich.
     - Incrementar a coluna ativa e desativar as demais.
     - Selecionar os taxels para leitura.
   - Cada taxel é lido a **1 kHz** (4 colunas = 4 kHz / 4).

## 🔄 Fluxo de Execução

1. O **ADC** coleta leituras das colunas de taxels através de **DMA**.
2. A cada interrupção do **Timer 6 (4 kHz)**:
   - O sistema processa as leituras.
   - A coluna ativa é alternada.
   - O potencial de membrana é atualizado com base no modelo de Izhikevich.
   - O sistema verifica se houve um **spike**.
   - Se um spike for detectado, um pulso é gerado no GPIO correspondente (~10-15µs).

## ⚙️ Modelo de Izhikevich Implementado

Os parâmetros utilizados são:

| Parâmetro | Valor |
|-----------|-------|
| a | 0.02 |
| b | 0.2 |
| c | -65 |
| d | 8 |
| vth (limiar) | 30 |
| V_min | 1.5V |
| V_max | 3.3V |
| dt | 0.001s |
| G (ganho da corrente) | 100 |

A equação do modelo neuronal é:

\[ v_{new} = v_{old} + dt \cdot (0.04 \cdot v_{old}^2 + 5 \cdot v_{old} + 140 - u_{old} + I) \]

\[ u_{new} = u_{old} + dt \cdot (a \cdot (b \cdot v_{old} - u_{old})) \]

Se **v ≥ vth**, então:
- **v = c**
- **u = u + d**
- **Pulso GPIO** é gerado (~10-15µs)

## 📡 Configuração dos GPIOs

Cada taxel está associado a um GPIO específico para indicar um disparo. A tabela abaixo apresenta o mapeamento:

| Taxel | GPIO Port | GPIO Pin |
|--------|-----------|----------|
| 1 | GPIOD | 13 |
| 2 | GPIOD | 12 |
| 3 | GPIOD | 11 |
| 4 | GPIOE | 2 |
| ... | ... | ... |

## 🏁 Inicialização do Sistema

A função `app_setup()` inicializa:
- Os taxels com valores iniciais.
- O ADC em modo DMA.
- O Timer 6 para gerar interrupções periódicas.

## 📢 Detecção de Spikes

Os spikes são detectados comparando o potencial de membrana com o limiar de disparo (`vth = 30`).

Caso um spike ocorra:
1. O valor de `v_m` é resetado para `c = -65`.
2. `u` é incrementado pelo fator `d = 8`.
3. O GPIO correspondente ao taxel gera um pulso (~10-15µs).

## 📝 Conclusão

Este projeto implementa um sistema baseado no modelo de Izhikevich para gerar respostas rápidas (Fast-Spikes) em sensores taxels. O uso de **DMA** para leitura do ADC e **interrupções** para processamento dos spikes garante um sistema eficiente e de baixa latência.


