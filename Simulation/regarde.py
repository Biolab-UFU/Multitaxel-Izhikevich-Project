import matplotlib.pyplot as plt

# Configuração inicial
voltage_array = []
# voltage_array = [3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3]
for i in range(1000):
    voltage_array.append(3.3)

# Variáveis iniciais
membrane_potential = -30  # Potencial de membrana inicial (mV)
recovery_variable = 0  # Variável de recuperação inicial
time_step = 0.001  # Passo de tempo para a simulação (ms)
count_spikes = 0
# Constantes do modelo Izhikevich
a = 0.02
b = 0.2
c = -65
d = 8

# Histórico para visualização
membrane_potentials = []
recovery_variables = []
currents = []

def main():
    global membrane_potential, recovery_variable, count_spikes
    print(len(voltage_array))
    for i, voltage in enumerate(voltage_array):
        # Normalizar a tensão e calcular a corrente
        norm = normalize(voltage)
        current = calculate_current(norm)

        # Atualizar as variáveis de estado
        old_membrane_potential = membrane_potential
        old_recovery_variable = recovery_variable
        membrane_potential = calculate_membrane_potential(
            old_membrane_potential, old_recovery_variable, current
        )
        recovery_variable = calculate_recovery_variable(
            old_membrane_potential, old_recovery_variable
        )

        # Registra os valores para análise
        membrane_potentials.append(membrane_potential)
        recovery_variables.append(recovery_variable)
        currents.append(current)

        # Dispara um spike caso o potencial ultrapasse o limite
        if membrane_potential >= 30:
            print(f"Spike detectado no tempo {i * time_step:.4f}s!")
            membrane_potential = c
            recovery_variable += d
            count_spikes += 1

        # Imprime os valores para debug
        print(f"Iteração {i + 1}:")
        print(f"  Tensão normalizada: {norm:.4f}")
        print(f"  Corrente: {current:.2f}")
        print(f"  Potencial de membrana: {membrane_potential:.2f}")
        print(f"  Variável de recuperação: {recovery_variable:.2f}")
        print("-" * 40)

    # Plotar os resultados
    print(f"Total de spikes detectados: {count_spikes}")
    plot_results()

def normalize(voltage):
    """Normaliza a tensão para o intervalo esperado."""
    return (voltage - 1.65) / (3.3 - 1.65)

def calculate_current(norm):
    """Calcula a corrente com base na tensão normalizada."""
    return 2000 * norm  # Corrente arbitrária (pico Ampères)

def calculate_membrane_potential(old_membrane_potential, old_recovery_variable, current):
    """Calcula o próximo potencial de membrana."""
    return old_membrane_potential + time_step * (
        0.04 * old_membrane_potential**2
        + 5 * old_membrane_potential
        + 140
        - old_recovery_variable
        + current
    )

def calculate_recovery_variable(old_membrane_potential, old_recovery_variable):
    """Calcula a próxima variável de recuperação."""
    return old_recovery_variable + time_step * (
        a * (b * old_membrane_potential - old_recovery_variable)
    )

def plot_results():
    """Plota os resultados da simulação."""
    time = [i * time_step for i in range(len(membrane_potentials))]
    
    plt.figure(figsize=(12, 6))

    # Plot do potencial de membrana
    plt.subplot(2, 1, 1)
    plt.plot(time, membrane_potentials, label="Potencial de Membrana (mV)")
    plt.axhline(30, color="red", linestyle="--", label="Limiar de Spike (30 mV)")
    plt.xlabel("Tempo (s)")
    plt.ylabel("Potencial de Membrana (mV)")
    plt.title("Dinâmica do Potencial de Membrana")
    plt.legend()
    plt.grid()

    # Plot da variável de recuperação
    plt.subplot(2, 1, 2)
    plt.plot(time, recovery_variables, label="Variável de Recuperação (u)", color="orange")
    plt.xlabel("Tempo (s)")
    plt.ylabel("Variável de Recuperação")
    plt.title("Dinâmica da Variável de Recuperação")
    plt.legend()
    plt.grid()

    plt.tight_layout()
    plt.show()

# Executa o programa
main()
