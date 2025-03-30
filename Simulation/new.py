import numpy as np
import matplotlib.pyplot as plt

# Parâmetros do modelo de Izhikevich
a = 0.02
b = 0.2
c = -65
d = 8
dt = 1  # Passo de tempo (ms)
G = 20  # Ganho

total_time = 10000  # Tempo total da simulação em ms
steps = total_time // dt

def generate_V():
    return np.random.uniform(1.65, 3.3)

# Inicialização das variáveis
vi = -65  # Potencial de membrana inicial
ui = b * vi  # Variável de recuperação
Vi_1 = generate_V()
Vi = generate_V()

# Listas para armazenar valores
time = np.arange(0, total_time, dt)
spike_train = np.zeros_like(time)  # Vetor para armazenar os impulsos

for i in range(steps):
    # Normalização das leituras
    Vi_normalizado = (Vi - 1.65) / (3.3 - 1.65)
    Vi_1_normalizado = (Vi_1 - 1.65) / (3.3 - 1.65)
    
    # Cálculo da corrente
    I = G * (Vi_normalizado - Vi_1_normalizado) / dt
    
    # Atualização das variáveis
    vi_new = vi + dt * (0.04 * vi ** 2 + 5 * vi + 140 + I - ui)
    ui_new = ui + dt * (a * (b * vi - ui))
    
    # Disparo do neurônio
    if vi_new >= 30:
        vi_new = c
        ui_new += d
        spike_train[i:i+2] = 1  # Gera um impulso de 2 ms
    
    # Atualiza as variáveis para o próximo passo
    vi, ui = vi_new, ui_new
    Vi_1 = Vi
    Vi = generate_V()

# Plotando os impulsos
plt.figure(figsize=(12, 5))
plt.plot(time, spike_train, drawstyle='steps-post', label='Spikes')
plt.xlabel('Tempo (ms)')
plt.ylabel('Impulsos')
plt.title('Modelo de Izhikevich - Treinamento de Spikes')
plt.legend()
plt.grid()
plt.show()