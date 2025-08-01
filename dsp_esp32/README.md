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
- **NILMTK Integration**: Conversão para formato NILMTK (HDF5)
- **NILM Analysis**: Análise especializada para detecção de cargas

## 🛠️ Estrutura do Projeto

```
dsp_esp32/
├── data_analyzer.py        #código para leitura da base de dados obtida
├── esp32_to_nilmtk.py      #conversão ESP32 → NILMTK (HDF5)
├── nilmtk_analyzer.py      #análise de dados NILMTK
├── example_usage.py        #exemplo de uso integração NILMTK
├── ESP32_NILMTK_Integration.ipynb  #jupyter notebook demonstração
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

# Para integração NILMTK (opcional)
pip install h5py seaborn
# pip install nilmtk  # Instalação opcional para funcionalidades avançadas
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

### 4. Integração NILMTK (Non-Intrusive Load Monitoring)

#### Conversão ESP32 → NILMTK
```bash
# Conversão básica para formato NILMTK (HDF5)
python -c "
from esp32_to_nilmtk import convert_esp32_to_nilmtk
convert_esp32_to_nilmtk('signal_analysis_data.csv', 'dataset_nilmtk.h5')
"

# Exemplo completo de uso
python example_usage.py
```

#### Análise NILMTK dos dados
```bash
# Análise exploratória
python -c "
from nilmtk_analyzer import analyze_esp32_nilmtk_data
analyze_esp32_nilmtk_data('dataset_nilmtk.h5')
"
```

#### Funcionalidades NILMTK:
- **Conversão automática**: CSV ESP32 → HDF5 NILMTK
- **Metadata configurável**: Informações do dataset
- **Análise de potência**: Cálculo automático P = V × I
- **Visualizações NILM**: Gráficos especializados para detecção de cargas
- **Compatibilidade**: Funciona com/sem NILMTK instalado
- **Jupyter Integration**: Notebook demonstrativo incluído

## � Módulo NILMTK Integration

### Visão Geral
O sistema agora inclui integração completa com NILMTK (Non-Intrusive Load Monitoring Toolkit) para análise avançada de cargas elétricas. Os dados coletados pela ESP32 podem ser convertidos automaticamente para o formato padrão NILMTK (HDF5) e analisados com ferramentas especializadas.

### Arquivos do Módulo NILMTK:
- **`esp32_to_nilmtk.py`**: Conversor ESP32 CSV → NILMTK HDF5
- **`nilmtk_analyzer.py`**: Analisador especializado para dados NILMTK
- **`example_usage.py`**: Script de demonstração completa
- **`ESP32_NILMTK_Integration.ipynb`**: Jupyter Notebook interativo

### Funcionalidades Principais:

#### 1. Conversão Automática
```python
from esp32_to_nilmtk import convert_esp32_to_nilmtk

# Conversão simples
convert_esp32_to_nilmtk(
    csv_file='signal_analysis_data.csv',
    output_hdf5='dataset_nilmtk.h5'
)
```

#### 2. Análise NILM Avançada
```python
from nilmtk_analyzer import analyze_esp32_nilmtk_data

# Análise completa com visualizações
report = analyze_esp32_nilmtk_data('dataset_nilmtk.h5')
```

#### 3. Processamento de Potência
- Cálculo automático de potência: P = V × I
- Estimativa de corrente baseada em tensão ADC
- Detecção de eventos de ligar/desligar cargas
- Análise de consumo energético

#### 4. Visualizações Especializadas
- Gráficos de potência vs tempo
- Histogramas de consumo
- Detecção de padrões de uso
- Análise de harmônicos
- Mapas de calor de atividade

#### 5. Compatibilidade
- **Com NILMTK**: Funcionalidades completas de disagregação
- **Sem NILMTK**: Carregamento manual HDF5 e análises básicas
- **Jupyter Ready**: Notebooks prontos para exploração

### Workflow Completo:
1. **Coleta**: ESP32 → Serial → CSV
2. **Conversão**: CSV → HDF5 (formato NILMTK)
3. **Análise**: Carregamento e processamento NILMTK
4. **Visualização**: Gráficos especializados NILM
5. **Relatório**: Geração de relatórios automáticos

## �📊 Formato dos Dados

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

### Formato NILMTK (HDF5):
```
dataset_nilmtk.h5
├── building1/
│   ├── elec/
│   │   └── meter1/
│   │       ├── power/active    # Potência ativa calculada
│   │       ├── voltage         # Tensão do sinal
│   │       ├── current         # Corrente estimada
│   │       └── timestamps      # Timestamps Unix
│   └── metadata/               # Metadata do dataset
```

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

### NILMTK (esp32_to_nilmtk.py):
```python
# Configurações de conversão
VOLTAGE_SCALE = 3.3/4096       # Escala ADC para tensão
CURRENT_ESTIMATION = True      # Estimar corrente a partir da tensão
POWER_CALCULATION = True       # Calcular potência P = V × I
SAMPLE_RATE = 10000            # Taxa de amostragem (Hz)
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

### 4. Análise NILM com NILMTK
```python
from esp32_to_nilmtk import ESP32ToNILMTK
from nilmtk_analyzer import NILMTKAnalyzer

# Conversão para NILMTK
converter = ESP32ToNILMTK('signal_analysis_data.csv')
converter.load_esp32_data()
hdf5_file = converter.convert_to_nilmtk('dataset.h5')

# Análise NILMTK
analyzer = NILMTKAnalyzer(hdf5_file)
analyzer.load_dataset()

# Análise de potência
power_data = analyzer.get_power_data()
analyzer.plot_power_analysis()

# Detecção de eventos
events = analyzer.detect_power_events()
analyzer.plot_event_detection()
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

### NILMTK - Console
```
📂 Carregando dados de: signal_analysis_data.csv
✅ Dados carregados: 2048 registros
📊 Período: 2025-07-29 10:30:15 até 2025-07-29 10:30:16
🔄 Convertendo para formato NILMTK...
💾 Dataset salvo: dataset_nilmtk.h5
📈 Análise NILM concluída
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

5. **Problemas na conversão NILMTK**
   - Verificar formato do CSV ESP32
   - Instalar dependências: `pip install h5py`
   - Verificar espaço em disco para arquivo HDF5

6. **NILMTK não instalado**
   - Módulo funciona sem NILMTK (modo manual)
   - Para funcionalidades completas: `pip install nilmtk`
   - Use Jupyter Notebook para exploração interativa

## 🚀 Melhorias Futuras

- [ ] Interface web em tempo real
- [ ] Análise de múltiplos canais ADC
- [ ] Filtros configuráveis dinamicamente
- [ ] Triggers automáticos para captura
- [ ] Exportação para formatos científicos (HDF5, MAT)
- [x] Integração com NILMTK para análise NILM
- [x] Jupyter Notebooks para exploração interativa
- [ ] Algoritmos de disagregação de cargas
- [ ] Interface gráfica para análise NILMTK
- [ ] Detecção automática de appliances
- [ ] Dashboard web para monitoramento NILM

## 📝 Licença

Este projeto segue a licença Apache 2.0 do ESP-IDF.

---