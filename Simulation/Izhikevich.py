import numpy as np
import matplotlib.pyplot as plt

# Parâmetros do neurônio Izhikevich
a, b, c, d = 0.02, 0.2, -65, 8
dt = 1  # Passo de tempo em ms
t_total = 1000  # Tempo total da simulação em ms

# Inicializando as variáveis
v = c
u = b * v

# Função para simular a corrente com base em uma função degrau de 1.6V a 3.3V
def sensor_input(t):
    # Parâmetros de tensão e corrente
    V_min, V_max = 1.6, 3.3
    I_min, I_max = 0, 15
    
    # Função degrau: a tensão passa de V_min para V_max em t = 500 ms
    if t < 500:
        voltage = V_min
    else:
        voltage = V_max
    
    # Mapeamento da tensão para corrente
    return I_min + (voltage - V_min) * (I_max - I_min) / (V_max - V_min)

# Arrays para armazenar os valores ao longo do tempo
v_array = []
u_array = []
I_array = []

# Loop de simulação
for t in range(t_total):
    I = sensor_input(t)  # Obtemos a corrente a partir da simulação de entrada do sensor
    I_array.append(I)
    
    # Atualiza as variáveis do modelo de Izhikevich
    v += dt * (0.04 * v**2 + 5 * v + 140 - u + I)
    u += dt * (a * (b * v - u))

    # Verifica o disparo
    if v >= 30:
        v_array.append(30)  # Pega o pico de disparo
        v = c
        u += d
    else:
        v_array.append(v)
    
    u_array.append(u)

print(1%4)
# # Visualizando a resposta ao longo do tempo
# plt.figure(figsize=(12, 6))

# # Plot de Membrane Potential
# plt.subplot(2, 1, 1)
# plt.plot(v_array, label="Membrane Potential (v)", color="b")
# plt.xlabel("Time (ms)")
# plt.ylabel("Membrane Potential (mV)")
# plt.legend()

# # Plot de Current Input
# plt.subplot(2, 1, 2)
# plt.plot(I_array, label="Current Input (I)", color="r")
# plt.xlabel("Time (ms)")
# plt.ylabel("Current Input (I)")
# plt.legend()

# plt.tight_layout()
# plt.show()
