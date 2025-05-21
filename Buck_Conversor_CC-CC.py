import numpy as np
import matplotlib.pyplot as plt

# Parâmetros do Conversor Buck CC-CC
Vin = 36.0          # Tensão de entrada (V)
Vout_desejado = 12.0 # Tensão de saída desejada (V)
Iout = 2.0          # Corrente de saída máxima (A)
R_load = Vout_desejado / Iout  # Resistência da carga (Ohms)
fsw = 50000         # Frequência de chaveamento (Hz)
D = Vout_desejado / Vin  # Duty Cycle (33.3%)

# Componentes calculados (valores comerciais)
L = 220e-6          # Indutor (H)
Cout = 47e-6        # Capacitor de saída (F)
R_esr = 0.01        # Resistência série do capacitor (ESR) - estimativa

# Tempo de simulação
t_sim = 5e-3        # 5 ms de simulação
dt = 1 / (fsw * 200) # Passo de tempo pequeno para precisão
t = np.arange(0, t_sim, dt)

# Inicialização das variáveis
Vout = np.zeros_like(t)      # Tensão na carga
V_L = np.zeros_like(t)       # Tensão no indutor
V_C = np.zeros_like(t)       # Tensão no capacitor
I_L = np.zeros_like(t)       # Corrente no indutor
I_C = np.zeros_like(t)       # Corrente no capacitor
state = 0                    # Estado do MOSFET (0 ou 1)

# Condições iniciais
V_C[0] = 0.0
I_L[0] = 0.0

# Simulação do conversor Buck
for i in range(1, len(t)):
    # Controle PWM do MOSFET
    if (t[i] * fsw) % 1.0 < D:
        state = 1  # MOSFET LIGADO
    else:
        state = 0  # MOSFET DESLIGADO

    # Tensão no indutor (V_L = Vin - Vout quando ligado, V_L = -Vout quando desligado)
    if state == 1:
        V_L[i] = Vin - V_C[i-1]
    else:
        V_L[i] = -V_C[i-1]

    # Corrente no indutor (integral de V_L / L)
    I_L[i] = I_L[i-1] + (V_L[i] / L) * dt

    # Corrente no capacitor (I_C = I_L - Iout)
    I_C[i] = I_L[i] - (V_C[i-1] / R_load)

    # Tensão no capacitor (integral de I_C / C)
    V_C[i] = V_C[i-1] + (I_C[i] / Cout) * dt

    # Tensão na carga (incluindo ESR do capacitor)
    Vout[i] = V_C[i] + (I_C[i] * R_esr)

# Gráficos
plt.figure(figsize=(14, 10))

# 1. Tensão na Carga
plt.subplot(3, 1, 1)
plt.plot(t * 1000, Vout, 'b', label='Tensão na Carga')
plt.axhline(y=Vout_desejado, color='r', linestyle='--', label='12V Desejado')
plt.xlabel('Tempo (ms)')
plt.ylabel('Tensão (V)')
plt.title('Tensão na Carga (R_load = {:.1f} Ω)'.format(R_load))
plt.legend()
plt.grid(True)

# 2. Tensão no Indutor
plt.subplot(3, 1, 2)
plt.plot(t * 1000, V_L, 'g', label='Tensão no Indutor')
plt.xlabel('Tempo (ms)')
plt.ylabel('Tensão (V)')
plt.title('Tensão no Indutor (L = 220 µH)')
plt.grid(True)

# 3. Tensão no Capacitor
plt.subplot(3, 1, 3)
plt.plot(t * 1000, V_C, 'm', label='Tensão no Capacitor')
plt.xlabel('Tempo (ms)')
plt.ylabel('Tensão (V)')
plt.title('Tensão no Capacitor (C = 47 µF)')
plt.grid(True)

plt.tight_layout()
plt.show()

# Gráficos Adicionais (Correntes)
plt.figure(figsize=(14, 6))

# 4. Corrente no Indutor
plt.subplot(2, 1, 1)
plt.plot(t * 1000, I_L, 'r', label='Corrente no Indutor')
plt.xlabel('Tempo (ms)')
plt.ylabel('Corrente (A)')
plt.title('Corrente no Indutor (Ripple = {:.2f} A)'.format(np.max(I_L) - np.min(I_L)))
plt.grid(True)

# 5. Corrente no Capacitor
plt.subplot(2, 1, 2)
plt.plot(t * 1000, I_C, 'purple', label='Corrente no Capacitor')
plt.xlabel('Tempo (ms)')
plt.ylabel('Corrente (A)')
plt.title('Corrente no Capacitor')
plt.grid(True)

plt.tight_layout()
plt.show()

# Resultados Numéricos
print("\n--- Resultados Finais ---")
print(f"Tensão média na carga: {np.mean(Vout[int(0.9 * len(Vout)):]):.3f} V")
print(f"Ripple de tensão na carga: {np.max(Vout[int(0.9 * len(Vout)):]) - np.min(Vout[int(0.9 * len(Vout)):]):.3f} V")
print(f"Ripple de corrente no indutor: {np.max(I_L) - np.min(I_L):.3f} A")