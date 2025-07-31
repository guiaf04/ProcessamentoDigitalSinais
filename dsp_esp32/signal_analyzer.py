import sys
import serial
import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import os
from datetime import datetime
import time

# Configurações da porta serial
SERIAL_PORT = '/dev/ttyACM0'  # Ajuste conforme necessário
BAUD_RATE = 115200

# Arquivo CSV para salvar dados
CSV_FILENAME = 'signal_analysis_data.csv'

# Eixo X logarítmico para FFT
class LogAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [f"{10**v:.0f}" if v > 0 else "1" for v in values]

class SignalAnalyzer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Analisador de Sinais - Original vs Filtrado")
        self.resize(1400, 800)
        
        # Inicializar arquivo CSV
        self.init_csv_file()
        
        # Layout principal
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Barra de status
        self.status_label = QtWidgets.QLabel("Status: Inicializando...")
        layout.addWidget(self.status_label)
        
        # Layout dos gráficos (2x2)
        plots_widget = QtWidgets.QWidget()
        plots_layout = QtWidgets.QGridLayout(plots_widget)
        layout.addWidget(plots_widget)
        
        # Gráfico 1: Sinal Original
        self.plot_signal_orig = pg.PlotWidget(title="Sinal Original no Tempo")
        self.plot_signal_orig.setLabel('bottom', 'Tempo (s)')
        self.plot_signal_orig.setLabel('left', 'Amplitude (V)')
        self.plot_signal_orig.showGrid(x=True, y=True)
        self.curve_signal_orig = self.plot_signal_orig.plot(pen=pg.mkPen('y', width=2))
        
        # Gráfico 2: Sinal Filtrado
        self.plot_signal_filt = pg.PlotWidget(title="Sinal Filtrado no Tempo")
        self.plot_signal_filt.setLabel('bottom', 'Tempo (s)')
        self.plot_signal_filt.setLabel('left', 'Amplitude (V)')
        self.plot_signal_filt.showGrid(x=True, y=True)
        self.curve_signal_filt = self.plot_signal_filt.plot(pen=pg.mkPen('c', width=2))
        
        # Gráfico 3: FFT Original
        log_axis1 = LogAxisItem(orientation='bottom')
        self.plot_fft_orig = pg.PlotWidget(title="FFT do Sinal Original", axisItems={'bottom': log_axis1})
        self.plot_fft_orig.setLabel('bottom', 'Frequência (Hz)')
        self.plot_fft_orig.setLabel('left', 'Magnitude (dB)')
        self.plot_fft_orig.showGrid(x=True, y=True)
        self.curve_fft_orig = self.plot_fft_orig.plot(pen=pg.mkPen('orange', width=2))
        
        # Gráfico 4: FFT Filtrado
        log_axis2 = LogAxisItem(orientation='bottom')
        self.plot_fft_filt = pg.PlotWidget(title="FFT do Sinal Filtrado", axisItems={'bottom': log_axis2})
        self.plot_fft_filt.setLabel('bottom', 'Frequência (Hz)')
        self.plot_fft_filt.setLabel('left', 'Magnitude (dB)')
        self.plot_fft_filt.showGrid(x=True, y=True)
        self.curve_fft_filt = self.plot_fft_filt.plot(pen=pg.mkPen('g', width=2))
        
        # Organizar gráficos em grade 2x2
        plots_layout.addWidget(self.plot_signal_orig, 0, 0)
        plots_layout.addWidget(self.plot_signal_filt, 0, 1)
        plots_layout.addWidget(self.plot_fft_orig, 1, 0)
        plots_layout.addWidget(self.plot_fft_filt, 1, 1)
        
        # Botões de controle
        buttons_widget = QtWidgets.QWidget()
        buttons_layout = QtWidgets.QHBoxLayout(buttons_widget)
        layout.addWidget(buttons_widget)
        
        self.save_btn = QtWidgets.QPushButton("Salvar Dados Atuais")
        self.save_btn.clicked.connect(self.save_current_data)
        self.clear_btn = QtWidgets.QPushButton("Limpar Gráficos")
        self.clear_btn.clicked.connect(self.clear_plots)
        self.export_btn = QtWidgets.QPushButton("Exportar CSV")
        self.export_btn.clicked.connect(self.export_csv)
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addStretch()
        
        # Inicializar porta serial
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            self.status_label.setText(f"Status: Conectado a {SERIAL_PORT}")
            print(f"[INFO] Porta serial {SERIAL_PORT} aberta com sucesso.")
        except serial.SerialException as e:
            self.status_label.setText(f"Status: ERRO - {e}")
            print(f"[ERRO] Não foi possível abrir {SERIAL_PORT}: {e}")
            sys.exit(1)
        
        # Variáveis para armazenar dados
        self.current_data = {
            'signal_original': {'time': [], 'amplitude': []},
            'signal_filtered': {'time': [], 'amplitude': []},
            'fft_original': {'frequency': [], 'magnitude': []},
            'fft_filtered': {'frequency': [], 'magnitude': []}
        }
        
        # Estado da leitura
        self.reading_state = None
        self.packet_counter = 0
        
        # Timer para leitura serial
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.read_serial)
        self.timer.start(10)  # 10ms
        
    def init_csv_file(self):
        """Inicializa arquivo CSV com cabeçalhos se não existir"""
        if not os.path.exists(CSV_FILENAME):
            # Criar DataFrame vazio com colunas apropriadas
            df = pd.DataFrame(columns=[
                'timestamp', 'packet_id', 'data_type', 'index', 
                'time_or_freq', 'amplitude_or_magnitude'
            ])
            df.to_csv(CSV_FILENAME, index=False)
            print(f"[INFO] Arquivo CSV criado: {CSV_FILENAME}")
        else:
            print(f"[INFO] Usando arquivo CSV existente: {CSV_FILENAME}")
    
    def read_serial(self):
        """Lê dados da porta serial"""
        while self.ser.in_waiting:
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Processa marcadores de início/fim
                if line == "---SIGNAL_ORIGINAL_START---":
                    self.reading_state = 'signal_original'
                    self.current_data['signal_original'] = {'time': [], 'amplitude': []}
                    continue
                elif line == "---SIGNAL_ORIGINAL_END---":
                    self.reading_state = None
                    continue
                elif line == "---SIGNAL_FILTERED_START---":
                    self.reading_state = 'signal_filtered'
                    self.current_data['signal_filtered'] = {'time': [], 'amplitude': []}
                    continue
                elif line == "---SIGNAL_FILTERED_END---":
                    self.reading_state = None
                    continue
                elif line == "---FFT_ORIGINAL_START---":
                    self.reading_state = 'fft_original'
                    self.current_data['fft_original'] = {'frequency': [], 'magnitude': []}
                    continue
                elif line == "---FFT_ORIGINAL_END---":
                    self.reading_state = None
                    continue
                elif line == "---FFT_FILTERED_START---":
                    self.reading_state = 'fft_filtered'
                    self.current_data['fft_filtered'] = {'frequency': [], 'magnitude': []}
                    continue
                elif line == "---FFT_FILTERED_END---":
                    self.reading_state = None
                    continue
                elif line == "---DATA_COMPLETE---":
                    self.packet_counter += 1
                    self.update_plots()
                    self.save_to_csv()
                    self.status_label.setText(f"Status: Pacote #{self.packet_counter} recebido")
                    continue
                
                # Processa dados baseado no estado atual
                if self.reading_state and line:
                    parts = line.split(',')
                    if len(parts) == 2:
                        try:
                            x_val = float(parts[0])
                            y_val = float(parts[1])
                            
                            if self.reading_state == 'signal_original':
                                self.current_data['signal_original']['time'].append(x_val)
                                self.current_data['signal_original']['amplitude'].append(y_val)
                            elif self.reading_state == 'signal_filtered':
                                self.current_data['signal_filtered']['time'].append(x_val)
                                self.current_data['signal_filtered']['amplitude'].append(y_val)
                            elif self.reading_state == 'fft_original':
                                if x_val > 0:  # Evita log(0)
                                    self.current_data['fft_original']['frequency'].append(np.log10(x_val))
                                    self.current_data['fft_original']['magnitude'].append(y_val)
                            elif self.reading_state == 'fft_filtered':
                                if x_val > 0:  # Evita log(0)
                                    self.current_data['fft_filtered']['frequency'].append(np.log10(x_val))
                                    self.current_data['fft_filtered']['magnitude'].append(y_val)
                        except ValueError:
                            print(f"[WARNING] Valor inválido ignorado: {line}")
                
            except Exception as e:
                print(f"[ERROR] Erro ao processar linha: {e}")
    
    def update_plots(self):
        """Atualiza todos os gráficos com os dados atuais"""
        try:
            # Atualizar sinal original
            if self.current_data['signal_original']['time']:
                self.curve_signal_orig.setData(
                    self.current_data['signal_original']['time'],
                    self.current_data['signal_original']['amplitude']
                )
            
            # Atualizar sinal filtrado
            if self.current_data['signal_filtered']['time']:
                self.curve_signal_filt.setData(
                    self.current_data['signal_filtered']['time'],
                    self.current_data['signal_filtered']['amplitude']
                )
            
            # Atualizar FFT original
            if self.current_data['fft_original']['frequency']:
                self.curve_fft_orig.setData(
                    self.current_data['fft_original']['frequency'],
                    self.current_data['fft_original']['magnitude']
                )
            
            # Atualizar FFT filtrado
            if self.current_data['fft_filtered']['frequency']:
                self.curve_fft_filt.setData(
                    self.current_data['fft_filtered']['frequency'],
                    self.current_data['fft_filtered']['magnitude']
                )
                
            print(f"[INFO] Gráficos atualizados - Pacote #{self.packet_counter}")
            
        except Exception as e:
            print(f"[ERROR] Erro ao atualizar gráficos: {e}")
    
    def save_to_csv(self):
        """Salva dados atuais no arquivo CSV"""
        try:
            timestamp = datetime.now().isoformat()
            rows = []
            
            # Salvar sinal original
            for i, (t, amp) in enumerate(zip(
                self.current_data['signal_original']['time'],
                self.current_data['signal_original']['amplitude']
            )):
                rows.append([timestamp, self.packet_counter, 'signal_original', i, t, amp])
            
            # Salvar sinal filtrado
            for i, (t, amp) in enumerate(zip(
                self.current_data['signal_filtered']['time'],
                self.current_data['signal_filtered']['amplitude']
            )):
                rows.append([timestamp, self.packet_counter, 'signal_filtered', i, t, amp])
            
            # Salvar FFT original (converter log de volta para Hz)
            for i, (log_f, mag) in enumerate(zip(
                self.current_data['fft_original']['frequency'],
                self.current_data['fft_original']['magnitude']
            )):
                freq_hz = 10 ** log_f
                rows.append([timestamp, self.packet_counter, 'fft_original', i, freq_hz, mag])
            
            # Salvar FFT filtrado (converter log de volta para Hz)
            for i, (log_f, mag) in enumerate(zip(
                self.current_data['fft_filtered']['frequency'],
                self.current_data['fft_filtered']['magnitude']
            )):
                freq_hz = 10 ** log_f
                rows.append([timestamp, self.packet_counter, 'fft_filtered', i, freq_hz, mag])
            
            # Adicionar ao CSV
            if rows:
                df = pd.DataFrame(rows, columns=[
                    'timestamp', 'packet_id', 'data_type', 'index', 
                    'time_or_freq', 'amplitude_or_magnitude'
                ])
                df.to_csv(CSV_FILENAME, mode='a', header=False, index=False)
                print(f"[INFO] {len(rows)} pontos salvos no CSV")
            
        except Exception as e:
            print(f"[ERROR] Erro ao salvar CSV: {e}")
    
    def save_current_data(self):
        """Salva manualmente os dados atuais"""
        self.save_to_csv()
        QtWidgets.QMessageBox.information(self, "Salvar", f"Dados salvos em {CSV_FILENAME}")
    
    def clear_plots(self):
        """Limpa todos os gráficos"""
        self.curve_signal_orig.clear()
        self.curve_signal_filt.clear()
        self.curve_fft_orig.clear()
        self.curve_fft_filt.clear()
        print("[INFO] Gráficos limpos")
    
    def export_csv(self):
        """Exporta dados para um novo arquivo CSV com timestamp"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"signal_export_{timestamp}.csv"
            
            # Copia arquivo atual
            df = pd.read_csv(CSV_FILENAME)
            df.to_csv(new_filename, index=False)
            
            QtWidgets.QMessageBox.information(
                self, "Exportar", f"Dados exportados para {new_filename}\n"
                f"Total de registros: {len(df)}"
            )
            print(f"[INFO] Dados exportados para {new_filename}")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao exportar: {e}")
    
    def closeEvent(self, event):
        """Fechar aplicação"""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Configurar estilo
    app.setStyle('Fusion')
    
    main_window = SignalAnalyzer()
    main_window.show()
    
    print("[INFO] Aplicação iniciada. Aguardando dados do ESP32...")
    print(f"[INFO] Dados serão salvos em: {CSV_FILENAME}")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
