#Sensor Multitaxel com Modelo de Izhikevich

## 📌 **Descrição do Projeto**
Este projeto consiste na aplicação do **Modelo de Izhikevich** para a detecção de **escorregamento** em uma **matriz piezoresistiva**, acoplada à ponta dos dedos de uma **prótese robótica**. A matriz é composta por **4 linhas e 4 colunas**, formando um total de **16 unidades tácteis (taxels)**.

A leitura do sensor é realizada por uma **placa Nucleo STM32F767ZI**, com o firmware desenvolvido na **STM32CubeIDE**. O processamento do sinal permite detectar padrões tácteis e inferir a presença de escorregamento, contribuindo para o aprimoramento do controle da prótese.

---

## 🛠 **Arquitetura do Sistema**
### 🔹 **Hardware**
- **Matriz piezoresistiva:** 4×4 taxels.
- **Placa de aquisição:** Utiliza **multiplexadores** para selecionar os taxels.
- **Filtro passa-baixa de 10Hz:** Realiza o pré-processamento dos sinais.
- **STM32F767ZI:** Responsável pela aquisição e processamento do sinal.

### 🔹 **Esquema de Leitura**
- **As 4 colunas** da matriz estão conectadas aos **canais do ADC1** do STM32F767, com **pull-up de 5.6kΩ**.
- **As 4 linhas** estão conectadas a **GPIOs** e são ativadas sequencialmente para permitir a multiplexação.
- O firmware controla a ativação das linhas e a aquisição dos valores analógicos das colunas via **ADC**, permitindo a reconstrução da distribuição de pressão na matriz.

---

## 🧠 **Modelo de Izhikevich**
O modelo de **Izhikevich (2003)** é um modelo matemático de neurônios que equilibra **simplicidade computacional** e **realismo biológico**. Ele é definido pelas seguintes equações diferenciais:

\[ \frac{dv}{dt} = 0.04v^2 + 5v + 140 - u + I \]
\[ \frac{du}{dt} = a(bv - u) \]

Onde:
- **v** representa o potencial de membrana do neurônio.
- **u** é uma variável de recuperação do neurônio.
- **I** é a corrente de entrada.
- **a, b, c, d** são parâmetros ajustáveis que definem diferentes tipos de comportamento neural.

Quando **v atinge um limite**, ocorre um disparo neuronal, e ele é resetado:
\[ \text{se } v \geq 30mV, \text{ então } v \leftarrow c, u \leftarrow u + d \]

No contexto deste projeto, esse modelo é aplicado à saída da matriz tátil, permitindo a identificação de padrões temporais associados ao **escorregamento**.

---

## 📂 **Estrutura do Repositório**
📁 **/STM32F767** - A documentação necessária para o desenvolvimento na Nucleo Board (Ler Main User Manual e Reference Manual)
📁 **/hardware** - Hardware, Esquemáticos e diagramas do sensor multitaxel.  
📁 **/firmware** - Código-fonte para aquisição, geração e processamento dos sinais, e visualização gráfica.  
📁 **/Artigos** - Artigos desenvolvidos pelo Biolab, e pelo laboratório SINAPSE de Singapura (fabricante do sensor), além de artigos úteis.  

Cada subdiretório contém um **README** específico com detalhes sobre sua funcionalidade.

---

## 🚀 **Como Usar**
### 📌 **Requisitos**
- **Placa STM32F767ZI**
- **STM32CubeIDE**
- **Cabo USB para programação**

### 🔧 **Passos**
1. Clone este repositório:  
   ```bash
   git clone https://github.com/seu-repositorio.git
   ```
2. Abra o **STM32CubeIDE** e importe o projeto.
3. Compile e grave o firmware na placa.
4. Conecte o sensor e monitore a aquisição dos sinais.

---

## 📜 **Referências**
- Izhikevich, E. M. (2003). "Simple Model of Spiking Neurons". _IEEE Transactions on Neural Networks._
- Documentação da **STMicroelectronics** para o STM32F767ZI.

---

📌 **Autor:** [Stephan Costa Barros]  
📅 **Última atualização:** [29/03/2025]  
💡 **Contato:** [stephanbrrs8@gmail.com]


