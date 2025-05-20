import math
import tkinter as tk
from tkinter import messagebox, filedialog
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.integrate import odeint  # Para resolver as equações diferenciais


class CircuitoRetificadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Circuito Retificador com Filtro LC")
        self.root.geometry("1100x700")

        # Variáveis do circuito
        self.Vrms = tk.DoubleVar(value=36)
        self.freq = tk.DoubleVar(value=60)
        self.R = tk.DoubleVar(value=10)
        self.L = tk.DoubleVar(value=1)
        self.C = tk.DoubleVar(value=1000e-6)  # 1000 μF
        self.Vd_schottky = tk.DoubleVar(value=0.3)
        self.Vd_common = tk.DoubleVar(value=0.7)

        # Criar interface
        self.criar_widgets()

        # Calcular automaticamente ao iniciar
        self.calcular()

    def criar_widgets(self):
        # Frame de controles
        frame_controles = tk.Frame(self.root, padx=10, pady=10)
        frame_controles.pack(side=tk.LEFT, fill=tk.Y)

        # Frame do circuito
        frame_circuito = tk.LabelFrame(self.root, text="Diagrama do Circuito", padx=5, pady=5)
        frame_circuito.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas_circuito = tk.Canvas(frame_circuito, width=500, height=400, bg='white')
        self.canvas_circuito.pack(fill=tk.BOTH, expand=True)

        # Frame de gráficos
        frame_graficos = tk.Frame(self.root)
        frame_graficos.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Entradas de parâmetros
        self.criar_entradas(frame_controles)

        # Botões
        frame_botoes = tk.Frame(frame_controles)
        frame_botoes.pack(pady=10)

        tk.Button(frame_botoes, text="Calcular", command=self.calcular,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(frame_botoes, text="Exportar Dados", command=self.exportar_dados,
                  bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)

        # Resultados
        self.frame_resultados = tk.LabelFrame(frame_controles, text="Resultados", padx=5, pady=5)
        self.frame_resultados.pack(fill=tk.X, pady=5)

        self.labels_resultados = {}
        parametros = [
            ("Tensão de Pico (Vp)", "V"),
            ("Tensão Média Retificada (Vavg)", "V"),
            ("Tensão Média na Carga (V_R)", "V"),
            ("Corrente Média na Carga (Iavg)", "A"),
            ("Ondulação de Tensão (ΔV)", "V"),
            ("Fator de Ripple", ""),
            ("Frequência de Corte", "Hz")
        ]

        for i, (nome, unidade) in enumerate(parametros):
            tk.Label(self.frame_resultados, text=f"{nome}:").grid(row=i, column=0, sticky="w")
            self.labels_resultados[nome] = tk.Label(self.frame_resultados, text="---", fg="blue")
            self.labels_resultados[nome].grid(row=i, column=1, sticky="e")
            tk.Label(self.frame_resultados, text=unidade).grid(row=i, column=2, sticky="w")

        # Gráficos Matplotlib
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(8, 6))
        self.canvas_graficos = FigureCanvasTkAgg(self.fig, master=frame_graficos)
        self.canvas_graficos.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Barra de ferramentas para os gráficos
        toolbar = NavigationToolbar2Tk(self.canvas_graficos, frame_graficos)
        toolbar.update()
        self.canvas_graficos.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def criar_entradas(self, parent):
        entradas = [
            ("Tensão RMS (V)", self.Vrms),
            ("Frequência (Hz)", self.freq),
            ("Resistência (Ω)", self.R),
            ("Indutância (H)", self.L),
            ("Capacitância (μF)", self.C),
            ("Queda Schottky (V)", self.Vd_schottky),
            ("Queda Diodo Comum (V)", self.Vd_common)
        ]

        for i, (texto, var) in enumerate(entradas):
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=texto, width=20, anchor="w").pack(side=tk.LEFT)
            tk.Entry(frame, textvariable=var, width=10).pack(side=tk.RIGHT)

    def desenhar_circuito(self):
        c = self.canvas_circuito
        c.delete("all")

        # Fonte AC (com valores dinâmicos)
        c.create_oval(50, 100, 100, 150, outline='blue')
        c.create_text(75, 125, text=f"AC\n{self.Vrms.get()}V\n{self.freq.get()}Hz",
                      font=('Arial', 9))

        # Diodo Schottky (1N5819)
        c.create_line(100, 125, 130, 125, width=2)
        self.desenhar_diodo(130, 125, 'right', '1N5819', 'red')

        # Nó de conexão
        c.create_oval(155, 122, 158, 128, fill='black')

        # Ramo 1: Indutor + Resistor
        c.create_line(158, 125, 200, 125, width=2)
        self.desenhar_indutor(200, 125)
        c.create_line(200, 125, 250, 125, width=2)
        self.desenhar_resistor(250, 175, f"{self.R.get()}Ω")
        c.create_line(250, 125, 250, 165, width=2)

        #  Capacitor em Paralelo com Resistor
        self.desenhar_capacitor(300, 175, f"{self.C.get() * 1e6:.0f}μF")  # Mostrar em μF
        c.create_line(250, 185, 250, 210, width=2)

        # Ramo 2: Diodo de roda livre (1N4007) - POLARIDADE CORRIGIDA
        c.create_line(158, 125, 158, 175, width=2)
        self.desenhar_diodo(158, 175, 'up', '1N4007', 'green')
        c.create_line(158, 175, 158, 210, width=2)

        # Ramo 3: conexão do nó do resistor, diodo 1N4007 e fonte
        c.create_line(250, 210, 70, 210, width=2)
        c.create_line(70, 210, 70, 150, width=2)

        # Legenda
        c.create_text(250, 50, text="Circuito Retificador Corrigido",
                      font=('Arial', 12, 'bold'))
        c.create_text(250, 80, text="Com diodo de roda livre e filtro indutivo",
                      font=('Arial', 10))

    def desenhar_diodo(self, x, y, direcao, modelo, cor):
        """Função auxiliar para desenhar diodos"""
        if direcao == 'right':
            points = [x, y - 10, x + 20, y, x, y + 10]  # →
            c_text = (x + 25, y)
        elif direcao == 'up':
            points = [x - 10, y, x, y - 20, x + 10, y]  # ↑
            c_text = (x, y - 25)
        self.canvas_circuito.create_polygon(points, fill=cor)
        self.canvas_circuito.create_text(*c_text, text=modelo, font=('Arial', 8))

    def desenhar_indutor(self, x, y):
        """Função auxiliar para desenhar indutores"""
        for i in range(5):
            self.canvas_circuito.create_arc(
                x - 20 + i * 8, y - 10, x - 12 + i * 8, y + 10,
                start=0, extent=180, style='arc'
            )
        self.canvas_circuito.create_text(x, y - 15, text=f"{self.L.get()}H", font=('Arial', 8))

    def desenhar_resistor(self, x, y, valor):
        """Função auxiliar para desenhar resistores"""
        self.canvas_circuito.create_rectangle(
            x - 15, y - 10, x + 15, y + 10,
            fill='brown', outline='black'
        )
        self.canvas_circuito.create_text(x, y, text=valor, font=('Arial', 8))

    def desenhar_capacitor(self, x, y, valor):
        """Função auxiliar para desenhar capacitores"""
        # Placas paralelas
        self.canvas_circuito.create_line(x - 20, y - 10, x - 20, y + 10, width=2)
        self.canvas_circuito.create_line(x + 20, y - 10, x + 20, y + 10, width=2)
        # Conexões
        self.canvas_circuito.create_line(x - 30, y, x - 20, y, width=2)
        self.canvas_circuito.create_line(x + 20, y, x + 30, y, width=2)
        # Texto
        self.canvas_circuito.create_text(x, y + 20, text=valor, font=('Arial', 8))

    def calcular(self):
        try:
            # Obter valores
            Vrms = self.Vrms.get()
            f = self.freq.get()
            R = self.R.get()
            L = self.L.get()
            C = self.C.get()  # Valor em Farads
            Vd_schottky = self.Vd_schottky.get()
            Vd_common = self.Vd_common.get()

            # Verificar valores válidos
            if any(v <= 0 for v in [Vrms, f, R, L, C]):
                messagebox.showerror("Erro", "Valores devem ser positivos!")
                return

            # Cálculos básicos
            Vp = Vrms * math.sqrt(2)
            T = 1 / f
            omega = 2 * math.pi * f

            # Frequência de corte do filtro LC
            f_cut = 1 / (2 * math.pi * math.sqrt(L * C))

            # Simulação numérica - agora precisamos resolver o circuito RLC
            t = np.linspace(0, 4 * T, 4000)  # Mais pontos para melhor precisão

            # Condições iniciais [corrente no indutor, tensão no capacitor]
            y0 = [0, 0]

            # Função para resolver as equações diferenciais
            def circuito_deriv(y, t):
                i_L, v_C = y

                # Tensão de entrada no instante t
                v_in = Vp * np.sin(omega * t)
                if v_in > Vd_schottky:
                    v_rect = v_in - Vd_schottky
                else:
                    v_rect = -Vd_common

                # Equações diferenciais do circuito RLC
                di_Ldt = (v_rect - v_C) / L
                dv_Cdt = (i_L - v_C / R) / C

                return [di_Ldt, dv_Cdt]

            # Resolver as equações diferenciais
            sol = odeint(circuito_deriv, y0, t)
            i_L = sol[:, 0]
            v_C = sol[:, 1]

            # Tensão retificada para plotagem
            V_rect = np.array([Vp * np.sin(omega * ti) - Vd_schottky
                               if Vp * np.sin(omega * ti) > Vd_schottky
                               else -Vd_common for ti in t])

            # Cálculo de parâmetros (ignorar os primeiros ciclos para regime permanente)
            start_idx = int(2 * T / (t[1] - t[0]))  # Ignorar os primeiros 2 períodos
            Vavg_rect = np.mean(V_rect[start_idx:])
            Vavg_R = np.mean(v_C[start_idx:])
            Iavg = np.mean(i_L[start_idx:])
            ripple_V = np.max(v_C[start_idx:]) - np.min(v_C[start_idx:])
            ripple_factor = ripple_V / Vavg_R if Vavg_R != 0 else 0

            # Atualizar resultados
            resultados = {
                "Tensão de Pico (Vp)": f"{Vp:.2f}",
                "Tensão Média Retificada (Vavg)": f"{Vavg_rect:.2f}",
                "Tensão Média na Carga (V_R)": f"{Vavg_R:.2f}",
                "Corrente Média na Carga (Iavg)": f"{Iavg:.4f}",
                "Ondulação de Tensão (ΔV)": f"{ripple_V:.4f}",
                "Fator de Ripple": f"{ripple_factor:.4f}",
                "Frequência de Corte": f"{f_cut:.2f}"
            }

            for nome, valor in resultados.items():
                self.labels_resultados[nome].config(text=valor)

            # Atualizar gráficos
            self.atualizar_graficos(t, Vp * np.sin(omega * t), V_rect, v_C)

            # Redesenhar circuito
            self.desenhar_circuito()

        except ValueError:
            messagebox.showerror("Erro", "Digite valores numéricos válidos!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na simulação:\n{str(e)}")

    def atualizar_graficos(self, t, V_ac, V_rect, V_R):
        # Limpar e replotar
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.clear()

        # Gráfico 1: Tensão AC
        self.ax1.plot(t, V_ac, 'b')
        self.ax1.set_title('Tensão da Fonte AC')
        self.ax1.set_ylabel('Tensão (V)')
        self.ax1.grid(True)

        # Gráfico 2: Tensão Retificada
        self.ax2.plot(t, V_rect, 'r')
        self.ax2.set_title('Tensão após Retificação')
        self.ax2.set_ylabel('Tensão (V)')
        self.ax2.grid(True)

        # Gráfico 3: Tensão na Carga
        self.ax3.plot(t, V_R, 'g')
        self.ax3.axhline(np.mean(V_R[len(V_R) // 2:]), color='k', linestyle='--',
                         label=f'Média = {np.mean(V_R[len(V_R) // 2:]):.2f}V')
        self.ax3.set_title('Tensão na Carga (Filtro LC)')
        self.ax3.set_xlabel('Tempo (s)')
        self.ax3.set_ylabel('Tensão (V)')
        self.ax3.legend()
        self.ax3.grid(True)

        # Ajustar layout e redesenhar
        self.fig.tight_layout()
        self.canvas_graficos.draw()

    def exportar_dados(self):
        try:
            # Obter valores
            Vrms = self.Vrms.get()
            f = self.freq.get()
            R = self.R.get()
            L = self.L.get()
            C = self.C.get()

            # Verificar valores
            if any(v <= 0 for v in [Vrms, f, R, L, C]):
                messagebox.showerror("Erro", "Valores devem ser positivos!")
                return

            # Cálculos básicos
            Vp = Vrms * math.sqrt(2)
            T = 1 / f
            omega = 2 * math.pi * f
            t = np.linspace(0, 4 * T, 4000)

            # Resolver o circuito RLC
            y0 = [0, 0]

            def circuito_deriv(y, t):
                i_L, v_C = y
                v_in = Vp * np.sin(omega * t)
                if v_in > self.Vd_schottky.get():
                    v_rect = v_in - self.Vd_schottky.get()
                else:
                    v_rect = -self.Vd_common.get()

                di_Ldt = (v_rect - v_C) / L
                dv_Cdt = (i_L - v_C / R) / C

                return [di_Ldt, dv_Cdt]

            sol = odeint(circuito_deriv, y0, t)
            v_C = sol[:, 1]

            # Preparar dados para exportação
            dados = [
                ["Tempo (s)", "Tensão AC (V)", "Tensão Retificada (V)", "Tensão na Carga (V)"]
            ]

            for i in range(len(t)):
                v_in = Vp * np.sin(omega * t[i])
                if v_in > self.Vd_schottky.get():
                    v_rect = v_in - self.Vd_schottky.get()
                else:
                    v_rect = -self.Vd_common.get()

                dados.append([t[i], v_in, v_rect, v_C[i]])

            # Salvar arquivo
            arquivo = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv"), ("Todos os arquivos", "*.*")],
                title="Salvar dados da simulação"
            )

            if arquivo:
                with open(arquivo, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(dados)

                messagebox.showinfo("Sucesso", f"Dados salvos em:\n{arquivo}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar dados:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CircuitoRetificadorApp(root)
    root.mainloop()