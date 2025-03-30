import serial
import matplotlib.pyplot as plt
import time
from collections import defaultdict

# Configurar a porta serial
SERIAL_PORT = "/dev/ttyUSB0"  # Ajuste conforme necessário
BAUD_RATE = 115200

def read_serial_data():
    """Lê dados da porta serial e armazena em um dicionário."""
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Tempo para estabilizar a conexão
    
    spike_data = defaultdict(list)
    
    print("Lendo dados da porta serial...")
    try:
        while True:
            line = ser.readline().decode('utf-8').strip()
            if line:
                try:
                    channel, timestamp = map(int, line.split(","))
                    spike_data[channel].append(timestamp)
                    print(f"Canal {channel}: {timestamp}")
                except ValueError:
                    print("Erro ao processar linha:", line)
    except KeyboardInterrupt:
        print("Leitura interrompida pelo usuário.")
    finally:
        ser.close()
        return spike_data

def plot_data(spike_data):
    """Plota os eventos de spike para cada canal."""
    plt.figure(figsize=(10, 6))
    for channel, timestamps in spike_data.items():
        plt.scatter(timestamps, [channel] * len(timestamps), label=f'Canal {channel}')
    
    plt.xlabel("Timestamp")
    plt.ylabel("Canais")
    plt.title("Eventos de Spike por Canal")
    plt.legend()
    plt.grid()
    plt.show()

if __name__ == "__main__":
    data = read_serial_data()
    plot_data(data)
