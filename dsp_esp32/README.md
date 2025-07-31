# Signal Analyzer - ESP32 + Python

Sistema completo para análise de sinais em tempo real usando ESP32-S3 e interface Python com PyQt5.

## 📋 Características

### ESP32 (C)
- **Aquisição**: ADC contínuo a 10 kHz
- **Processamento**: Filtro IIR passa-baixas (1 kHz)
- **FFT**: Análise espectral de 512 pontos
- **Envio**: Dados via UART para análise

### Python (Interface)
- **Visualização**: 4 gráficos em tempo real
- **Armazenamento**: Dados salvos automaticamente em CSV
- **Análise**: Ferramentas para análise offline dos dados

## 🛠️ Estrutura do Projeto

```
dsp_esp32/
├── data_analyzer.py        #código para leitura da base de dados obtida
├── Processamento_Digital_de_Sinais_com_a_ESP32S3.pdf  #relatório
├── README.md
├── signal_analysis_data.csv #base de dados criada com algumas amostras
├── signal_analyzer.c        #código para ESP32-s3
└── signal_analyzer.py       #código para leitura dos gráficos em tempo real
```

## ⚙️ Configuração e Uso

### 1. ESP32 - Código C

#### Dependências
```bash
# ESP-IDF v4.4+
# ESP-DSP library
```

#### Compilação
```bash
cd esp-dsp/
idf.py set-target esp32s3
idf.py menuconfig  # Configurar ESP-DSP
idf.py build
idf.py flash monitor
```

#### Configurações importantes no menuconfig:
```
Component config → ESP-DSP Library → 
  ✓ Enable optimized DSP implementations
  Max FFT size: 1024

Component config → ADC → 
  ✓ Enable ADC continuous mode ISR in IRAM
```

### 2. Python - Interface em Tempo Real

#### Dependências
```bash
pip install pyqt5 pyqtgraph serial pandas numpy matplotlib
```

#### Execução
```bash
# Ajustar porta serial no código (linha 8)
SERIAL_PORT = '/dev/ttyACM0'  # ou 'COM3' no Windows

python signal_analyzer.py
```

#### Funcionalidades da Interface:
- **4 Gráficos Simultâneos**:
  - Sinal original no tempo
  - Sinal filtrado no tempo  
  - FFT do sinal original
  - FFT do sinal filtrado
- **Controles**:
  - Salvar dados atuais
  - Limpar gráficos
  - Exportar CSV com timestamp
- **Armazenamento Automático**: Todos os dados são salvos em `signal_analysis_data.csv`

### 3. Análise Offline dos Dados

#### Uso do data_analyzer.py:
```bash
# Análise do último pacote
python data_analyzer.py

# Análise de pacote específico
python data_analyzer.py --packet 5

# Evolução temporal de tipo específico
python data_analyzer.py --evolution signal_original

# Resumo estatístico
python data_analyzer.py --stats

# Salvar gráficos em PNG
python data_analyzer.py --stats --save

# Ajuda completa
python data_analyzer.py --help
```

## 📊 Formato dos Dados

### Arquivo CSV
```csv
timestamp,packet_id,data_type,index,time_or_freq,amplitude_or_magnitude
2025-07-29T10:30:15.123456,1,signal_original,0,0.000000,1.653456
2025-07-29T10:30:15.123456,1,signal_original,1,0.000100,1.654123
...
2025-07-29T10:30:15.123456,1,fft_original,0,0.0,45.123456
2025-07-29T10:30:15.123456,1,fft_original,1,19.5,42.987654
```

### Tipos de Dados:
- **signal_original**: Sinal ADC no tempo
- **signal_filtered**: Sinal após filtro passa-baixas
- **fft_original**: FFT do sinal original
- **fft_filtered**: FFT do sinal filtrado

## 🔧 Configurações Importantes

### ESP32 (signal_analyzer.c):
```c
#define N_SAMPLES 512          // Tamanho da FFT
#define SAMPLE_FREQ_HZ 10000   // Taxa de amostragem
#define FILTER_FC 1000         // Frequência de corte (Hz)
#define SEND_INTERVAL 100      // Enviar a cada N aquisições
```

### Python (signal_analyzer.py):
```python
SERIAL_PORT = '/dev/ttyACM0'   # Porta serial
BAUD_RATE = 115200             # Velocidade
CSV_FILENAME = 'signal_analysis_data.csv'  # Arquivo de dados
```

## 📈 Exemplos de Uso

### 1. Monitoramento em Tempo Real
1. Conectar ESP32 via USB
2. Executar `python signal_analyzer.py`
3. Observar gráficos sendo atualizados automaticamente
4. Dados salvos automaticamente no CSV

### 2. Análise de Sinal Específico
```bash
# Ver último pacote recebido
python data_analyzer.py

# Comparar evolução do sinal filtrado
python data_analyzer.py --evolution signal_filtered --max-packets 5

# Gerar relatório completo
python data_analyzer.py --stats --save
```

### 3. Processamento de Dados Históricos
```python
import pandas as pd

# Carregar dados
df = pd.read_csv('signal_analysis_data.csv')

# Filtrar por tipo
signals = df[df['data_type'] == 'signal_original']

# Análise customizada
# ... seu código aqui
```

## 🔍 Monitoramento e Debug

### ESP32 - Logs
```
I (12345) SIGNAL_ANALYZER: Analysis Task Started
I (23456) SIGNAL_ANALYZER: Sending data packet #1
I (34567) SIGNAL_ANALYZER: Avg Original: 1.652V, Avg Filtered: 1.651V
```

### Python - Console
```
[INFO] Porta serial /dev/ttyACM0 aberta com sucesso.
[INFO] Arquivo CSV criado: signal_analysis_data.csv
[INFO] Gráficos atualizados - Pacote #1
[INFO] 2048 pontos salvos no CSV
```

## 🐛 Troubleshooting

### Problemas Comuns:

1. **Porta serial não encontrada**
   - Verificar cabo USB
   - Ajustar `SERIAL_PORT` no código Python
   - Verificar permissões (Linux): `sudo usermod -a -G dialout $USER`

2. **ESP32 não compila**
   - Verificar ESP-IDF instalado
   - Configurar ESP-DSP no menuconfig
   - Verificar target: `idf.py set-target esp32s3`
   - Verificar se o pacote do dsp foi corretamente instalado, caso não esteja, execute: `idf.py add-dependency "espressif/esp-dsp"`

3. **Gráficos não atualizam**
   - Verificar formato dos dados seriais
   - Aumentar timeout no Python
   - Verificar logs de erro no console

4. **Arquivo CSV muito grande**
   - Use `data_analyzer.py --save` para exportar
   - Limpe arquivo periodicamente
   - Ajuste `SEND_INTERVAL` no ESP32

## 🚀 Melhorias Futuras

- [ ] Interface web em tempo real
- [ ] Análise de múltiplos canais ADC
- [ ] Filtros configuráveis dinamicamente
- [ ] Triggers automáticos para captura
- [ ] Exportação para formatos científicos (HDF5, MAT)
- [ ] Integração com Jupyter Notebooks

## 📝 Licença

Este projeto segue a licença Apache 2.0 do ESP-IDF.

---