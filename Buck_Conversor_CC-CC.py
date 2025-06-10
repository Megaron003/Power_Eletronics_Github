import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib

# Configurar matplotlib para usar o backend TkAgg
matplotlib.use('TkAgg')

class BuckConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Conversor Buck CC-CC")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configurar estilo
        self.setup_style()
        
        # Variáveis do circuito
        self.setup_variables()
        
        # Criar interface
        self.create_widgets()
        
        # Simulação inicial
        self.run_simulation()

    def setup_style(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configurar cores
        self.bg_color = '#f0f3f5'
        self.frame_color = '#ffffff'
        self.accent_color = '#4e73df'
        self.text_color = '#2e2e2e'
        
        # Configurar estilos
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TButton', font=('Segoe UI', 10), padding=6)
        self.style.configure('TEntry', padding=5)
        self.style.configure('TLabelframe', background=self.bg_color)
        self.style.configure('TLabelframe.Label', background=self.bg_color, 
                           foreground=self.accent_color, font=('Segoe UI', 10, 'bold'))
        self.style.configure('Accent.TButton', background=self.accent_color, 
                           foreground='white', font=('Segoe UI', 10, 'bold'))
        
    def setup_variables(self):
        # Parâmetros iniciais
        self.Vin = tk.DoubleVar(value=36.0)
        self.Vout = tk.DoubleVar(value=12.0)
        self.Iout = tk.DoubleVar(value=2.0)
        self.fsw = tk.DoubleVar(value=50000)
        self.L = tk.DoubleVar(value=220e-6)
        self.C = tk.DoubleVar(value=47e-6)
        self.R_esr = tk.DoubleVar(value=0.01)
        
        # Resultados
        self.results = {
            'Vavg': tk.StringVar(value='---'),
            'Vripple': tk.StringVar(value='---'),
            'Iripple': tk.StringVar(value='---'),
            'Duty': tk.StringVar(value='---')
        }

    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Painel esquerdo (controles)
        left_panel = ttk.Frame(main_frame, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        left_panel.pack_propagate(False)
        
        # Painel direito (gráficos)
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Criar seções
        self.create_parameter_section(left_panel)
        self.create_results_section(left_panel)
        self.create_graph_section(right_panel)
        
    def create_parameter_section(self, parent):
        frame = ttk.LabelFrame(parent, text="PARÂMETROS DO CIRCUITO", padding=(15, 10))
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Entradas de parâmetros
        params = [
            ("Tensão de Entrada (V)", self.Vin),
            ("Tensão de Saída (V)", self.Vout),
            ("Corrente de Saída (A)", self.Iout),
            ("Frequência (Hz)", self.fsw),
            ("Indutância (µH)", self.L),
            ("Capacitância (µF)", self.C),
            ("ESR Capacitor (Ω)", self.R_esr)
        ]
        
        for text, var in params:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=5)
            
            ttk.Label(row, text=text, width=20, anchor=tk.W).pack(side=tk.LEFT)
            entry = ttk.Entry(row, textvariable=var, width=10, justify=tk.RIGHT)
            entry.pack(side=tk.RIGHT)
            entry.bind('<KeyRelease>', lambda e: self.validate_entry(e.widget))
        
        # Botão de simulação
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="SIMULAR", command=self.run_simulation,
                  style='Accent.TButton').pack(fill=tk.X)
    
    def create_results_section(self, parent):
        frame = ttk.LabelFrame(parent, text="RESULTADOS", padding=(15, 10))
        frame.pack(fill=tk.BOTH, expand=True)
        
        results = [
            ("Tensão Média (V)", 'Vavg'),
            ("Ripple de Tensão (V)", 'Vripple'),
            ("Ripple de Corrente (A)", 'Iripple'),
            ("Duty Cycle (%)", 'Duty')
        ]
        
        for text, key in results:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=5)
            
            ttk.Label(row, text=text, width=20, anchor=tk.W).pack(side=tk.LEFT)
            ttk.Label(row, textvariable=self.results[key], width=10, 
                     foreground='blue', anchor=tk.E).pack(side=tk.RIGHT)
    
    def create_graph_section(self, parent):
        # Frame para os gráficos
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Criar figura matplotlib
        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor=self.bg_color)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Barra de ferramentas
        toolbar = NavigationToolbar2Tk(self.canvas, graph_frame, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(fill=tk.X)
        
        # Configurar subplots
        self.ax1 = self.fig.add_subplot(311)  # Tensão na carga
        self.ax2 = self.fig.add_subplot(312)  # Tensão no indutor
        self.ax3 = self.fig.add_subplot(313)  # Tensão no capacitor
        
        self.fig.tight_layout()
    
    def validate_entry(self, widget):
        try:
            float(widget.get())
            widget.config(foreground='black')
        except ValueError:
            widget.config(foreground='red')
    
    def run_simulation(self):
        try:
            # Obter parâmetros
            Vin = self.Vin.get()
            Vout = self.Vout.get()
            Iout = self.Iout.get()
            fsw = self.fsw.get()
            L = self.L.get()
            C = self.C.get()
            R_esr = self.R_esr.get()
            R_load = Vout / Iout
            
            # Verificar valores
            if Vin <= Vout:
                raise ValueError("A tensão de entrada deve ser maior que a saída!")
            
            # Calcular duty cycle
            D = Vout / Vin
            
            # Tempo de simulação
            t_sim = 5e-3  # 5 ms
            dt = 1 / (fsw * 200)
            t = np.arange(0, t_sim, dt)
            
            # Inicializar variáveis
            Vout = np.zeros_like(t)
            V_L = np.zeros_like(t)
            V_C = np.zeros_like(t)
            I_L = np.zeros_like(t)
            I_C = np.zeros_like(t)
            
            # Condições iniciais
            V_C[0] = 0.0
            I_L[0] = 0.0
            
            # Simulação
            for i in range(1, len(t)):
                # Controle PWM
                if (t[i] * fsw) % 1.0 < D:
                    V_L[i] = Vin - V_C[i-1]  # MOSFET ligado
                else:
                    V_L[i] = -V_C[i-1]       # MOSFET desligado
                
                # Atualizar corrente no indutor
                I_L[i] = I_L[i-1] + (V_L[i] / L) * dt
                
                # Atualizar corrente no capacitor
                I_C[i] = I_L[i] - (V_C[i-1] / R_load)
                
                # Atualizar tensão no capacitor
                V_C[i] = V_C[i-1] + (I_C[i] / C) * dt
                
                # Tensão na carga (com ESR)
                Vout[i] = V_C[i] + (I_C[i] * R_esr)
            
            # Calcular resultados
            start_idx = int(0.9 * len(t))  # Ignorar transitório
            Vavg = np.mean(Vout[start_idx:])
            Vripple = np.max(Vout[start_idx:]) - np.min(Vout[start_idx:])
            Iripple = np.max(I_L) - np.min(I_L)
            
            # Atualizar interface
            self.results['Vavg'].set(f"{Vavg:.3f}")
            self.results['Vripple'].set(f"{Vripple:.3f}")
            self.results['Iripple'].set(f"{Iripple:.3f}")
            self.results['Duty'].set(f"{D*100:.1f}")
            
            # Atualizar gráficos
            self.update_plots(t, Vout, V_L, V_C, Vavg)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na simulação:\n{str(e)}")
    
    def update_plots(self, t, Vout, V_L, V_C, Vavg):
        # Converter tempo para ms
        t_ms = t * 1000
        
        # Limpar e atualizar gráficos
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.clear()
        
        # Gráfico 1: Tensão na Carga
        self.ax1.plot(t_ms, Vout, 'b', label='Tensão na Carga')
        self.ax1.axhline(y=Vavg, color='r', linestyle='--', label=f'Média: {Vavg:.2f}V')
        self.ax1.set_title('Tensão na Carga')
        self.ax1.set_ylabel('Tensão (V)')
        self.ax1.legend()
        self.ax1.grid(True)
        
        # Gráfico 2: Tensão no Indutor
        self.ax2.plot(t_ms, V_L, 'g')
        self.ax2.set_title('Tensão no Indutor')
        self.ax2.set_ylabel('Tensão (V)')
        self.ax2.grid(True)
        
        # Gráfico 3: Tensão no Capacitor
        self.ax3.plot(t_ms, V_C, 'm')
        self.ax3.set_title('Tensão no Capacitor')
        self.ax3.set_xlabel('Tempo (ms)')
        self.ax3.set_ylabel('Tensão (V)')
        self.ax3.grid(True)
        
        # Ajustar layout e redesenhar
        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = BuckConverterApp(root)
    root.mainloop()