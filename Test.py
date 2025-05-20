import math
import tkinter as tk
from tkinter import messagebox, filedialog
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Cursor
from scipy.integrate import odeint
from scipy import signal


class CircuitoRetificadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador Avançado de Circuito Retificador com Filtro LC")
        self.root.geometry("1200x800")

        # Configuração do estilo
        self.root.configure(bg='#f0f0f0')
        self.fonte = ('Arial', 10)
        self.fonte_titulo = ('Arial', 12, 'bold')

        # Variáveis do circuito
        self.Vrms = tk.DoubleVar(value=36)
        self.freq = tk.DoubleVar(value=60)
        self.R = tk.DoubleVar(value=10)
        self.L = tk.DoubleVar(value=1)
        self.C = tk.DoubleVar(value=1000e-6)  # 1000 μF
        self.Vd_schottky = tk.DoubleVar(value=0.3)
        self.Vd_common = tk.DoubleVar(value=0.7)

        # Dados atuais para interação
        self.current_t = None
        self.current_V_ac = None
        self.current_V_rect = None
        self.current_V_R = None
        self.f_cut = None  # Armazenar frequência de corte

        # Criar interface
        self.criar_widgets()

        # Calcular automaticamente ao iniciar
        self.calcular()

    def criar_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame de controles (esquerda)
        frame_controles = tk.Frame(main_frame, bg='#f0f0f0', padx=10, pady=10)
        frame_controles.pack(side=tk.LEFT, fill=tk.Y)
        
        # Frame do circuito (topo esquerdo)
        frame_circuito = tk.LabelFrame(frame_controles, text="Diagrama Esquemático", 
                                     font=self.fonte_titulo, bg='#f0f0f0', padx=5, pady=5)
        frame_circuito.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.canvas_circuito = tk.Canvas(frame_circuito, width=500, height=300, bg='white')
        self.canvas_circuito.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame de parâmetros
        frame_parametros = tk.LabelFrame(frame_controles, text="Parâmetros do Circuito", 
                                       font=self.fonte_titulo, bg='#f0f0f0', padx=5, pady=5)
        frame_parametros.pack(fill=tk.X, pady=(0, 10))
        
        self.criar_entradas(frame_parametros)
        
        # Frame de botões
        frame_botoes = tk.Frame(frame_controles, bg='#f0f0f0')
        frame_botoes.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(frame_botoes, text="Calcular", command=self.calcular,
                 font=self.fonte, bg="#4CAF50", fg="white", padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_botoes, text="Exportar Dados", command=self.exportar_dados,
                 font=self.fonte, bg="#2196F3", fg="white", padx=10).pack(side=tk.LEFT, padx=5)
        
        # Frame de resultados
        self.frame_resultados = tk.LabelFrame(frame_controles, text="Resultados da Simulação", 
                                            font=self.fonte_titulo, bg='#f0f0f0', padx=5, pady=5)
        self.frame_resultados.pack(fill=tk.BOTH, expand=True)
        
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
            frame = tk.Frame(self.frame_resultados, bg='#f0f0f0')
            frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            
            tk.Label(frame, text=nome, width=25, anchor="w", 
                   font=self.fonte, bg='#f0f0f0').pack(side=tk.LEFT)
            self.labels_resultados[nome] = tk.Label(frame, text="---", fg="blue", 
                                                 font=self.fonte, bg='#f0f0f0', width=15)  # Aumentado de 10 para 15
            self.labels_resultados[nome].pack(side=tk.LEFT)
            tk.Label(frame, text=unidade, font=self.fonte, 
                   bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
        
        # Frame de gráficos (direita)
        frame_graficos = tk.Frame(main_frame, bg='#f0f0f0')
        frame_graficos.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Configuração dos gráficos Matplotlib
        self.fig = plt.Figure(figsize=(9, 8), dpi=100, facecolor='#f0f0f0')
        self.canvas_graficos = FigureCanvasTkAgg(self.fig, master=frame_graficos)
        self.canvas_graficos.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Tooltip para valores
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.withdraw()
        self.tooltip.overrideredirect(True)
        self.tooltip_label = tk.Label(self.tooltip, text="", bg="lightyellow", 
                                    relief="solid", borderwidth=1, font=self.fonte)
        self.tooltip_label.pack()

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
            frame = tk.Frame(parent, bg='#f0f0f0')
            frame.pack(fill=tk.X, pady=2)
            
            tk.Label(frame, text=texto, width=20, anchor="w", 
                   font=self.fonte, bg='#f0f0f0').pack(side=tk.LEFT)
            
            entry = tk.Entry(frame, textvariable=var, width=10, 
                           font=self.fonte, justify='right')
            entry.pack(side=tk.RIGHT)
            
            # Validar entrada para números
            entry.bind('<KeyRelease>', lambda e: self.validar_entrada(e.widget))

    def validar_entrada(self, widget):
        try:
            float(widget.get())
            widget.config(bg='white')
        except ValueError:
            if widget.get() == "":
                widget.config(bg='white')
            else:
                widget.config(bg='#ffdddd')

    def desenhar_circuito(self):
        c = self.canvas_circuito
        c.delete("all")
        
        # Fonte AC
        c.create_oval(50, 100, 100, 150, outline='blue', width=2)
        c.create_text(75, 125, text=f"AC\n{self.Vrms.get()}V\n{self.freq.get()}Hz",
                     font=('Arial', 9), fill='blue')
        
        # Diodo Schottky (1N5819)
        c.create_line(100, 125, 130, 125, width=2)
        self.desenhar_diodo(130, 125, 'right', '', 'red')
        c.create_text(138, 105, text='1N5859', font=('Arial', 8), fill='black')
        
        # Nó de conexão
        c.create_oval(155, 122, 158, 128, fill='black')
        
        # Ramo 1: Indutor + Resistor
        c.create_line(150, 125, 200, 125, width=2)
        self.desenhar_indutor(200, 125)
        c.create_line(180, 125, 250, 125, width=2)
        self.desenhar_resistor(300, 175, f"{self.R.get()}Ω")
        c.create_line(250, 125, 250, 160, width=2)
        
        # Capacitor em Paralelo com Resistor
        c.create_line(250, 125, 300, 125, width=2)
        c.create_line(300, 125, 300, 175, width=2)
        self.desenhar_capacitor(250, 175, f"{self.C.get() * 1e9:.0f}pF")
        c.create_line(250, 210, 300, 210, width=2)
        c.create_line(300, 175, 300, 210, width=2)
        c.create_line(250, 190, 250, 210, width=2)
        
        # Ramo 2: Diodo de roda livre (1N4007)
        c.create_line(158, 125, 158, 175, width=2)
        self.desenhar_diodo(158, 175, 'up', '', 'green')
        c.create_text(180, 150, text="1N4007", font=('Arial', 8), fill='black')
        c.create_line(158, 175, 158, 210, width=2)
        
        # Ramo 3: conexão do nó do resistor, diodo 1N4007 e fonte
        c.create_line(250, 210, 70, 210, width=2)
        c.create_line(70, 210, 70, 150, width=2)
        
        # Legenda
        c.create_text(250, 50, text="Circuito Retificador",
                     font=('Arial', 12, 'bold'), fill='black')
        c.create_text(250, 80, text="Diodo Schottky (1N5819) e Diodo de Roda Livre (1N4007)",
                     font=('Arial', 10), fill='black')

    def desenhar_diodo(self, x, y, direcao, modelo, cor):
        if direcao == 'right':
            points = [x, y - 10, x + 20, y, x, y + 10]  # →
            c_text = (x + 25, y)
        elif direcao == 'up':
            points = [x - 10, y, x, y - 20, x + 10, y]  # ↑
            c_text = (x, y - 25)
        
        self.canvas_circuito.create_polygon(points, fill=cor, outline='black')
        self.canvas_circuito.create_text(*c_text, text=modelo, font=('Arial', 8))

    def desenhar_indutor(self, x, y):
        for i in range(5):
            self.canvas_circuito.create_arc(
                x - 20 + i * 8, y - 10, x - 12 + i * 8, y + 10,
                start=0, extent=180, style='arc', width=2
            )
        self.canvas_circuito.create_text(x, y - 20, text=f"{self.L.get()}H", font=('Arial', 8))

    def desenhar_resistor(self, x, y, valor):
        self.canvas_circuito.create_rectangle(
            x - 15, y - 10, x + 15, y + 10,
            fill='brown', outline='black', width=2
        )
        self.canvas_circuito.create_text(x + 35, y, text=valor, font=('Arial', 8))

    def desenhar_capacitor(self, x, y, valor):
        # Desenho do capacitor na vertical
        # Linhas horizontais (placas do capacitor)
        self.canvas_circuito.create_line(x - 15, y - 15, x + 15, y - 15, width=2)  # Placa superior
        self.canvas_circuito.create_line(x - 15, y + 15, x + 15, y + 15, width=2)  # Placa inferior
        
        # Conexões verticais
        self.canvas_circuito.create_line(x, y - 25, x, y - 15, width=2)  # Conexão superior
        self.canvas_circuito.create_line(x, y + 15, x, y + 25, width=2)  # Conexão inferior
        
        # Texto do valor (posicionado ao lado)
        self.canvas_circuito.create_text(x - 60, y, text=valor, font=('Arial', 8), anchor='w')

    def calcular_resposta_frequencia(self, R, L, C):
        # Criar função de transferência do filtro LC
        num = [1]
        den = [L*C, L/R, 1]
        system = signal.TransferFunction(num, den)
        
        # Calcular resposta em frequência
        frequencies = np.logspace(0, 5, 500)  # 1Hz a 100kHz
        w, mag, phase = signal.bode(system, frequencies)
        
        # Converter para Hz e dB
        f = w / (2 * np.pi)
        mag_db = mag
        
        return f, mag_db, phase

    def calcular(self):
        try:
            # Obter valores
            Vrms = self.Vrms.get()
            f = self.freq.get()
            R = self.R.get()
            L = self.L.get()
            C = self.C.get()
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
            self.f_cut = 1 / (2 * math.pi * math.sqrt(L * C))

            # Simulação numérica - Aumentado de 4 para 10 ciclos e de 4000 para 10000 pontos
            t = np.linspace(0, 10 * T, 10000)  # 10 ciclos com 10000 pontos
            y0 = [0, 0]  # [corrente no indutor, tensão no capacitor]

            def circuito_deriv(y, t):
                i_L, v_C = y
                v_in = Vp * np.sin(omega * t)

                if v_in > Vd_schottky:
                    v_rect = v_in - Vd_schottky
                else:
                    v_rect = -Vd_common

                di_Ldt = (v_rect - v_C) / L
                dv_Cdt = (i_L - v_C / R) / C

                return [di_Ldt, dv_Cdt]

            sol = odeint(circuito_deriv, y0, t)
            i_L = sol[:, 0]
            v_C = sol[:, 1]

            # Tensão retificada para plotagem
            V_rect = np.array([Vp * np.sin(omega * ti) - Vd_schottky
                               if Vp * np.sin(omega * ti) > Vd_schottky
                               else -Vd_common for ti in t])

            # Cálculo de parâmetros (ignorar os primeiros ciclos para regime permanente)
            start_idx = int(2 * T / (t[1] - t[0]))
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
                "Frequência de Corte": f"{self.f_cut:.2f}"
            }

            for nome, valor in resultados.items():
                self.labels_resultados[nome].config(text=valor)

            # Armazenar dados para interação
            self.current_t = t
            self.current_V_ac = Vp * np.sin(omega * t)
            self.current_V_rect = V_rect
            self.current_V_R = v_C

            # Atualizar gráficos
            self.atualizar_graficos(t, self.current_V_ac, V_rect, v_C, R, L, C)

            # Redesenhar circuito
            self.desenhar_circuito()

        except ValueError:
            messagebox.showerror("Erro", "Digite valores numéricos válidos!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na simulação:\n{str(e)}")

    def atualizar_graficos(self, t, V_ac, V_rect, V_R, R, L, C):
        self.fig.clear()
        
        # Criar 4 subplots (3 para formas de onda, 1 para Bode)
        ax1 = self.fig.add_subplot(321)
        ax2 = self.fig.add_subplot(323)
        ax3 = self.fig.add_subplot(325)
        ax4 = self.fig.add_subplot(122)  # Gráfico de Bode
        
        # Configurar cores e estilos
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        # Gráfico 1: Tensão AC
        line1, = ax1.plot(t, V_ac, color=colors[0], linewidth=1.5, picker=5)
        ax1.set_title('1. Tensão da Fonte AC', fontsize=10, pad=10)
        ax1.set_ylabel('Tensão (V)', fontsize=9)
        ax1.grid(True, linestyle=':', alpha=0.7)
        ax1.tick_params(labelsize=8)
        
        # Gráfico 2: Tensão Retificada
        line2, = ax2.plot(t, V_rect, color=colors[1], linewidth=1.5, picker=5)
        ax2.set_title('2. Tensão após Retificação', fontsize=10, pad=10)
        ax2.set_ylabel('Tensão (V)', fontsize=9)
        ax2.grid(True, linestyle=':', alpha=0.7)
        ax2.tick_params(labelsize=8)
        
        # Gráfico 3: Tensão na Carga
        line3, = ax3.plot(t, V_R, color=colors[2], linewidth=1.5, picker=5)
        mean_V_R = np.mean(V_R[len(V_R) // 2:])
        ax3.axhline(mean_V_R, color='k', linestyle='--', linewidth=1,
                   label=f'Média = {mean_V_R:.2f}V')
        ax3.set_title('3. Tensão na Carga', fontsize=10, pad=10)
        ax3.set_xlabel('Tempo (s)', fontsize=9)
        ax3.set_ylabel('Tensão (V)', fontsize=9)
        ax3.legend(fontsize=8, loc='upper right')
        ax3.grid(True, linestyle=':', alpha=0.7)
        ax3.tick_params(labelsize=8)
        
        # Gráfico 4: Diagrama de Bode (Resposta em Frequência)
        f, mag, phase = self.calcular_resposta_frequencia(R, L, C)
        
        # Plotar magnitude
        ax4.semilogx(f, mag, color=colors[0], linewidth=1.5, label='Magnitude')
        ax4.axvline(self.f_cut, color='r', linestyle='--', linewidth=1, 
                   label=f'Fc = {self.f_cut:.2f} Hz')
        ax4.set_title('4. Resposta em Frequência do Filtro LC', fontsize=10, pad=10)
        ax4.set_xlabel('Frequência (Hz)', fontsize=9)
        ax4.set_ylabel('Ganho (dB)', fontsize=9)
        ax4.grid(True, which="both", linestyle=':', alpha=0.7)
        ax4.legend(fontsize=8, loc='upper right')
        ax4.tick_params(labelsize=8)
        
        # Configurar cursores
        cursor1 = Cursor(ax1, useblit=True, color='red', linewidth=0.5, alpha=0.5)
        cursor2 = Cursor(ax2, useblit=True, color='red', linewidth=0.5, alpha=0.5)
        cursor3 = Cursor(ax3, useblit=True, color='red', linewidth=0.5, alpha=0.5)
        
        # Configurar interações
        def on_move(event):
            if event.inaxes in [ax1, ax2, ax3]:
                x, y = event.xdata, event.ydata
                if x is not None and y is not None:
                    idx = np.searchsorted(t, x)
                    if 0 <= idx < len(t):
                        # Formatar valores com unidades
                        text = (f"Tempo: {x:.4f} s\n"
                                f"Tensão: {y:.2f} V")
                        
                        self.tooltip_label.config(text=text)
                        self.tooltip.deiconify()
                        
                        # Obter posição do canvas na tela
                        canvas = self.canvas_graficos.get_tk_widget()
                        canvas_x = canvas.winfo_rootx()
                        canvas_y = canvas.winfo_rooty()
                        
                        # Obter posição do mouse relativa à tela
                        x_root = canvas_x + event.x
                        y_root = canvas_y + event.y
                        
                        # Ajustar posição (15 pixels de offset)
                        offset = 15
                        self.tooltip.geometry(f"+{x_root + offset}+{y_root + offset}")
        
        def on_leave(event):
            self.tooltip.withdraw()
        
        def on_pick(event):
            if event.artist not in [line1, line2, line3]:
                return
                
            ind = event.ind[0]
            t_val = t[ind]
            
            # Criar janela de detalhes
            detail_win = tk.Toplevel(self.root)
            detail_win.title("Valores Detalhados no Ponto Selecionado")
            detail_win.geometry("350x220")
            detail_win.resizable(False, False)
            
            tk.Label(detail_win, text="Valores Instantâneos:", 
                   font=self.fonte_titulo).pack(pady=5)
            
            frame_dados = tk.Frame(detail_win)
            frame_dados.pack(pady=5)
            
            dados = [
                ("Tempo:", f"{t_val:.6f} s"),
                ("Tensão AC:", f"{V_ac[ind]:.4f} V"),
                ("Tensão Retificada:", f"{V_rect[ind]:.4f} V"),
                ("Tensão na Carga:", f"{V_R[ind]:.4f} V")
            ]
            
            for i, (label, value) in enumerate(dados):
                tk.Label(frame_dados, text=label, anchor="e", width=20, 
                        font=self.fonte).grid(row=i, column=0, sticky="e", padx=5)
                tk.Label(frame_dados, text=value, anchor="w", width=15,
                        font=self.fonte).grid(row=i, column=1, sticky="w")
            
            tk.Button(detail_win, text="Fechar", command=detail_win.destroy,
                     font=self.fonte, padx=10).pack(pady=10)
        
        # Conectar eventos
        self.fig.canvas.mpl_connect('motion_notify_event', on_move)
        self.fig.canvas.mpl_connect('axes_leave_event', on_leave)
        self.fig.canvas.mpl_connect('pick_event', on_pick)
        
        # Ajustar layout
        self.fig.tight_layout()
        self.canvas_graficos.draw()

    def exportar_dados(self):
        try:
            if self.current_t is None:
                messagebox.showwarning("Aviso", "Nenhum dado para exportar. Execute a simulação primeiro.")
                return
                
            # Preparar dados para exportação
            dados = [
                ["Tempo (s)", "Tensão AC (V)", "Tensão Retificada (V)", "Tensão na Carga (V)"]
            ]
            
            for i in range(len(self.current_t)):
                dados.append([
                    f"{self.current_t[i]:.6f}",
                    f"{self.current_V_ac[i]:.4f}",
                    f"{self.current_V_rect[i]:.4f}",
                    f"{self.current_V_R[i]:.4f}"
                ])
            
            # Solicitar local para salvar
            arquivo = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv"), ("Todos os arquivos", "*.*")],
                title="Salvar dados da simulação"
            )
            
            if arquivo:
                with open(arquivo, 'w', newline='') as f:
                    writer = csv.writer(f, delimiter=',')
                    writer.writerows(dados)
                
                messagebox.showinfo("Sucesso", f"Dados salvos em:\n{arquivo}")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar dados:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CircuitoRetificadorApp(root)
    root.mainloop()