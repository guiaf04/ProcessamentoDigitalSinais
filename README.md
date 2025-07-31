# Processamento Digital de Sinais - Implementações e Aplicações
## Conceitos de DSP em Python e Sistema NILM com ESP32-S3

[![ESP32](https://img.shields.io/badge/Platform-ESP32--S3-red)](https://www.espressif.com/en/products/socs/esp32-s3)
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **Desenvolvido por:** Guilherme Araújo Floriano, Eliton Pereira Melo e Ryan Guilherme Moraes Nascimento  
> **Instituição:** Universidade Federal do Ceará - Campus Quixadá  
> **Curso:** Engenharia de Computação

## 📖 Sobre o Projeto

Este repositório contém implementações práticas de **Processamento Digital de Sinais (DSP)** organizadas em dois módulos principais:

### 🔬 **Módulo 1: Conceitos Fundamentais de DSP**
Implementações educacionais em Python dos principais conceitos de processamento digital de sinais, incluindo filtros digitais (FIR/IIR) e algoritmos de FFT otimizados.

### ⚡ **Módulo 2: Sistema NILM (Non-Intrusive Load Monitoring)**
Sistema completo para análise e identificação de cargas elétricas domésticas utilizando técnicas de DSP aplicadas em hardware embarcado (ESP32-S3) com interface Python para monitoramento energético sem sensores individuais.

### 🎯 Objetivos

#### 📚 Módulo DSP - Conceitos Fundamentais
- **Filtros Digitais**: Implementação e análise de filtros FIR e IIR
- **Análise Espectral**: Algoritmos FFT com otimizações (Split-Radix)
- **Aprendizado Prático**: Notebooks interativos com exemplos educacionais

#### ⚡ Módulo NILM - Sistema Aplicado
- **Monitoramento Não Intrusivo**: Analisar o consumo total de energia e identificar aparelhos individuais
- **Processamento em Tempo Real**: Análise espectral e filtragem digital usando ESP32-S3
- **Interface Intuitiva**: Visualização em tempo real com Python/PyQt5
- **Detecção Inteligente**: Algoritmos de identificação automática de eventos

## 🏗️ Estrutura do Projeto

```
ProcessamentoDigitalSinais/
├── 📁 dsp_esp32/                  # 🚀 Sistema NILM - ESP32-S3
│   ├── main_NILM_Event_Detector.c   # Detector de eventos NILM
│   ├── signal_analyzer.c            # Analisador de sinais principal
│   ├── signal_analyzer.py           # Interface Python tempo real
│   ├── data_analyzer.py             # Análise offline de dados
│   ├── nilm_filters.c/.h            # Biblioteca de filtros
│   ├── signal_analysis_data.csv     # Base de dados coletados
│   ├── esp32_to_nilmtk.py          # 🔄 Conversor ESP32 → NILMTK
│   ├── nilmtk_analyzer.py          # 📊 Analisador de dados NILMTK
│   ├── ESP32_NILMTK_Integration.ipynb # 📓 Notebook integração NILMTK
│   └── example_usage.py            # 🎯 Exemplo de uso completo
│
├── 📁 Filtros/                    # 📚 Conceitos DSP - Filtros Digitais
│   ├── Filtro_FIR.ipynb             # Implementação e teoria filtros FIR
│   ├── Filtro_IIR.ipynb             # Implementação e teoria filtros IIR
│   └── plc.py                       # Aplicação em comunicação PLC
│
├── 📁 FFT/                        # 📚 Conceitos DSP - Análise Espectral
│   ├── Uso_da_FFT_em_python_Exemplo_1.ipynb  # Fundamentos FFT
│   ├── Uso_da_FFT_em_python_Exemplo_2.ipynb  # Aplicações práticas
│   └── Uso_da_FFT_em_python_Exemplo_3.ipynb  # Casos avançados
│
└── 📁 AlgoritmoFFT/              # 📚 Conceitos DSP - Algoritmos Otimizados
    └── Split_Radix.ipynb            # Implementação Split-Radix FFT
```

## 🚀 Características Principais

### � **Módulo DSP - Conceitos Fundamentais**
- **Filtros Digitais**: Implementações completas de FIR e IIR com análise teórica
- **FFT Educacional**: Exemplos práticos desde conceitos básicos até aplicações avançadas
- **Algoritmos Otimizados**: Split-Radix FFT com análise de complexidade computacional
- **Notebooks Interativos**: Material educacional com visualizações e explicações detalhadas

### ⚡ **Módulo NILM - Sistema Aplicado**

#### �🔧 Hardware (ESP32-S3)
- **Aquisição**: ADC contínuo a 10-20 kHz
- **Processamento**: Filtros IIR passa-baixas em tempo real
- **FFT**: Análise espectral de 512 pontos
- **Comunicação**: Transmissão via UART para análise Python
- **Detecção**: Algoritmo de detecção de eventos com threshold adaptativo

#### 💻 Software (Python)
- **Visualização**: Interface com 4 gráficos em tempo real
- **Armazenamento**: Dados salvos automaticamente em CSV
- **Análise Offline**: Ferramentas para processamento pós-coleta
- **Integração DSP**: Aplicação prática dos conceitos implementados nos notebooks
- **🔄 Integração NILMTK**: Conversão automática para formato NILMTK (HDF5)
- **📊 Análise Avançada**: Detecção de eventos, padrões de consumo e relatórios

## ⚙️ Configuração e Instalação

### 1. � Ambiente Python (Ambos os Módulos)

#### Instalação de Dependências
```bash
pip install -r requirements.txt
```

#### Dependências Principais
```python
# Interface e visualização
PyQt5 >= 5.15.0
matplotlib >= 3.5.0
numpy >= 1.21.0

# Análise de sinais
scipy >= 1.7.0
pandas >= 1.3.0

# Notebooks educacionais
jupyter >= 1.0.0
sympy >= 1.8.0

# Comunicação serial (NILM)
pyserial >= 3.5

# NILMTK e análise NILM
h5py >= 3.1.0
tables >= 3.6.1
# nilmtk >= 0.4.0 (opcional)
```

### 2. �🔧 Hardware ESP32-S3 (Módulo NILM)

#### Dependências
```bash
# ESP-IDF v4.4+
# ESP-DSP library
```

#### Compilação e Flash
```bash
cd dsp_esp32/
idf.py set-target esp32s3
idf.py menuconfig  # Configurar ESP-DSP
idf.py build
idf.py flash monitor
```

#### Configurações Importantes (menuconfig)
- Habilitar ESP-DSP Components
- Configurar ADC continuous mode
- Ajustar buffer sizes para FFT
- Configurar UART com baud rate 115200

### 3. � Execução dos Projetos

#### Notebooks DSP (Conceitos)
```bash
# Iniciar Jupyter
jupyter notebook

# Navegar para os diretórios:
# - Filtros/ (Filtros FIR/IIR)
# - FFT/ (Análise espectral)
# - AlgoritmoFFT/ (Split-Radix)
```

#### Sistema NILM (Aplicação)
```bash
# Análise em tempo real
python dsp_esp32/signal_analyzer.py

# Análise de dados offline
python dsp_esp32/data_analyzer.py

# 🔄 Conversão para NILMTK
python dsp_esp32/esp32_to_nilmtk.py

# 📊 Análise com NILMTK
python dsp_esp32/nilmtk_analyzer.py

# 🎯 Exemplo completo
python dsp_esp32/example_usage.py
```

## 📝 Conteúdo dos Módulos

### 📚 **Módulo DSP - Conceitos Fundamentais**

#### � Filtros Digitais (`Filtros/`)
- **`Filtro_FIR.ipynb`**: 
  - Teoria e implementação de filtros FIR
  - Métodos de projeto (janelamento, amostragem em frequência)
  - Aplicações práticas em sinais de cargas elétricas
  - Análise de resposta em frequência e fase
- **`Filtro_IIR.ipynb`**: 
  - Teoria e implementação de filtros IIR
  - Transformação de filtros analógicos (Butterworth, Chebyshev)
  - Comparação de performance com filtros FIR
  - Estabilidade e projeto de filtros

#### 🔄 Análise Espectral (`FFT/`)
- **`Uso_da_FFT_em_python_Exemplo_1.ipynb`**: 
  - Fundamentos da Transformada Discreta de Fourier (DFT)
  - Conceitos de amostragem e teorema de Nyquist
  - Implementação básica e interpretação de resultados
- **`Uso_da_FFT_em_python_Exemplo_2.ipynb`**: 
  - Aplicações práticas da FFT
  - Análise de sinais reais e processamento
  - Windowing e vazamento espectral
- **`Uso_da_FFT_em_python_Exemplo_3.ipynb`**: 
  - Casos de uso avançados
  - FFT 2D e aplicações em imagens
  - Análise tempo-frequência

#### ⚡ Algoritmos Otimizados (`AlgoritmoFFT/`)
- **`Split_Radix.ipynb`**: 
  - Implementação do algoritmo Split-Radix FFT
  - Comparação de performance com NumPy FFT e DFT direta
  - Análise de complexidade computacional O(N log N)
  - Otimizações e técnicas de implementação eficiente

### ⚡ **Módulo NILM - Sistema Aplicado** (`dsp_esp32/`)

#### 🎯 Aplicação Prática dos Conceitos DSP
O sistema NILM demonstra a aplicação prática dos conceitos estudados nos notebooks:
- **Filtros em Tempo Real**: Implementação de filtros IIR em C para ESP32
- **FFT Embarcada**: Análise espectral em tempo real com 512 pontos
- **Processamento de Sinais**: Pipeline completo desde aquisição até classificação

#### 🔄 Integração com NILMTK
Nova funcionalidade que permite integração completa com o ecossistema NILMTK:

**📊 Conversão de Dados**:
- **`esp32_to_nilmtk.py`**: Converte dados CSV da ESP32 para formato HDF5 compatível com NILMTK
- **Metadata Automático**: Gera metadados necessários para análise NILM
- **Calibração**: Converte valores ADC para unidades físicas (V, A, W)

**📈 Análise Avançada**:
- **`nilmtk_analyzer.py`**: Carrega e analisa dados NILMTK convertidos
- **Detecção de Eventos**: Identifica automaticamente liga/desliga de aparelhos
- **Padrões de Consumo**: Análise temporal e estatística do consumo
- **Visualizações**: Gráficos especializados para análise NILM

**📓 Notebook Interativo**:
- **`ESP32_NILMTK_Integration.ipynb`**: Tutorial completo de integração
- **Passo a passo**: Desde conversão até análise avançada
- **Exemplos Práticos**: Casos de uso reais com dados da ESP32

#### 🚀 Uso Rápido
```bash
# Conversão e análise em um comando
python dsp_esp32/example_usage.py

# Ou usando o notebook interativo
jupyter notebook dsp_esp32/ESP32_NILMTK_Integration.ipynb
```

## 🔬 Metodologia NILM

### 1. **Aquisição de Dados**
- Medição contínua de corrente e tensão
- Amostragem sincronizada a 10-20 kHz
- Filtragem anti-aliasing em hardware

### 2. **Pré-processamento**
- Filtros passa-baixas para redução de ruído
- Cálculo de potência instantânea
- Decimação para frequências de análise adequadas

### 3. **Detecção de Eventos**
- Algoritmo de threshold adaptativo
- Debounce temporal para evitar falsos positivos
- Classificação automática de eventos liga/desliga

### 4. **Análise Espectral**
- FFT para caracterização de harmônicos
- Identificação de assinaturas espectrais
- Correlação com banco de dados de aparelhos

### 5. **Classificação de Cargas**
- Análise de características tempo-frequência
- Correlação com padrões conhecidos
- Estimativa de potência por aparelho

## 📊 Resultados e Performance

### 🎯 Métricas de Detecção
- **Precisão**: >90% para aparelhos de alta potência (>100W)
- **Recall**: >85% para eventos de liga/desliga
- **Latência**: <2 segundos para detecção de eventos

### ⚡ Performance Computacional
- **ESP32-S3**: Processamento em tempo real até 20 kHz
- **Split-Radix FFT**: 30-40% mais rápido que FFT padrão
- **Interface Python**: Atualização gráfica a 10 FPS

## 🔧 Configurações Avançadas

### 📊 Parâmetros de Análise
```c
#define SAMPLE_RATE_HZ          10.0f       // Taxa para NILM (10 Hz)
#define ADC_SAMPLE_RATE_HZ      20000       // Taxa do ADC (20 kHz)
#define EVENT_THRESHOLD         50.0f       // Limiar detecção (W)
#define DEBOUNCE_TIME_MS        2000        // Tempo debounce (2s)
```

### 🎛️ Filtros Configuráveis
```c
// Filtro IIR Butterworth passa-baixas
float cutoff_freq = 1000.0f;    // Frequência de corte (Hz)
int filter_order = 4;           // Ordem do filtro
float Q_factor = 0.707f;        // Fator de qualidade
```

## 📈 Aplicações e Casos de Uso

### 📚 **Módulo DSP - Educacional**
- **Ensino de DSP**: Material didático para cursos de processamento de sinais
- **Pesquisa Acadêmica**: Base para desenvolvimento de novos algoritmos
- **Prototipagem Rápida**: Implementações prontas para testes e validação
- **Comparação de Algoritmos**: Benchmarks entre diferentes técnicas

### ⚡ **Módulo NILM - Aplicações Práticas**

#### 🏠 **Residencial**
- Monitoramento do consumo doméstico
- Identificação de aparelhos defeituosos
- Otimização do uso de energia

#### 🏢 **Comercial/Industrial**
- Auditoria energética automatizada
- Manutenção preditiva de equipamentos
- Análise de eficiência energética

#### 🔬 **Pesquisa e Desenvolvimento**
- Estudo de padrões de consumo
- Validação de algoritmos NILM
- Desenvolvimento de novas técnicas

## 📚 Base Teórica

### 📖 Conceitos Fundamentais

#### 🔬 **Módulo DSP**
- **Processamento Digital de Sinais**: Teoria de filtros, transformadas, análise espectral
- **Algoritmos FFT**: DFT, Radix-2, Split-Radix, otimizações computacionais
- **Filtros Digitais**: FIR, IIR, métodos de projeto, análise de estabilidade

#### ⚡ **Módulo NILM**
- **NILM**: Técnicas de desagregação energética não intrusiva
- **Sistemas Embarcados**: Programação ESP32, processamento em tempo real
- **Análise de Cargas**: Caracterização espectral de aparelhos elétricos

### 🔗 Referências
- UK-DALE Dataset para validação NILM
- IEEE Standards para qualidade de energia
- Literatura clássica de DSP (Oppenheim, Proakis)
- Algoritmos de machine learning para classificação

## 🛠️ Desenvolvimento e Contribuição

### 📋 TO-DO

#### 📚 **Módulo DSP**
- [ ] Adicionar mais exemplos de filtros adaptativos
- [ ] Implementar FFT 2D otimizada
- [ ] Criar notebooks sobre análise tempo-frequência
- [ ] Adicionar exercícios interativos

#### ⚡ **Módulo NILM**
- [ ] Implementar classificação por machine learning
- [ ] Adicionar suporte para mais tipos de cargas
- [ ] Otimizar algoritmos para consumo energético
- [ ] Desenvolver interface web
- [ ] Integração com sistemas de automação residencial

### 🤝 Como Contribuir
1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Contato

**Equipe de Desenvolvimento:**
- **Guilherme Araújo Floriano** - [Guilherme](https://github.com/guiaf04)
- **Eliton Pereira Melo** - [eliton](https://github.com/elitonnmelo)
- **Ryan Guilherme Moraes Nascimento** - [Ryan Guilherme](https://github.com/ryanguilherme)

**Instituição:** UFC Campus Quixadá - Engenharia de Computação

---

## 🙏 Agradecimentos

- Universidade Federal do Ceará - Campus Quixadá
- Professores do curso de Engenharia de Computação
- Comunidade ESP32 e desenvolvedores das bibliotecas utilizadas
- UK-DALE Dataset pelos dados de validação do sistema NILM
- Comunidade Python científico (NumPy, SciPy, Matplotlib)

---

**⭐ Se este projeto foi útil para você, considere dar uma estrela! ⭐**

[🔝 Voltar ao topo](#processamento-digital-de-sinais---implementações-e-aplicações)

</div>
