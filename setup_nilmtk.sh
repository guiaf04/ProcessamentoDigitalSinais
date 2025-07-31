#!/bin/bash
# Script de Configuração NILMTK para ESP32
# =====================================
# Este script configura o ambiente para integração ESP32-NILMTK

echo "🚀 Configurando ambiente ESP32-NILMTK..."
echo "======================================="

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verifica Python
if ! command_exists python3; then
    echo "❌ Python 3 não encontrado. Instale Python 3.8+ primeiro."
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Cria ambiente virtual (opcional)
read -p "🤔 Deseja criar um ambiente virtual? (y/n): " create_venv
if [[ $create_venv == "y" || $create_venv == "Y" ]]; then
    echo "🔧 Criando ambiente virtual..."
    python3 -m venv esp32_nilmtk_env
    source esp32_nilmtk_env/bin/activate
    echo "✅ Ambiente virtual criado e ativado"
fi

# Atualiza pip
echo "🔄 Atualizando pip..."
python3 -m pip install --upgrade pip

# Instala dependências básicas
echo "📦 Instalando dependências básicas..."
pip install -r requirements.txt

# Tenta instalar NILMTK
echo "🔧 Tentando instalar NILMTK..."
pip install nilmtk 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ NILMTK instalado com sucesso!"
else
    echo "⚠️  NILMTK não pôde ser instalado (normal - dependências complexas)"
    echo "💡 O sistema funcionará sem NILMTK usando carregamento manual de HDF5"
fi

# Verifica se arquivo de dados existe
if [ -f "dsp_esp32/signal_analysis_data.csv" ]; then
    echo "✅ Dados ESP32 encontrados"
else
    echo "⚠️  Dados ESP32 não encontrados em dsp_esp32/signal_analysis_data.csv"
    echo "💡 Execute a coleta de dados ESP32 primeiro"
fi

# Testa a instalação
echo "🧪 Testando instalação..."
cd dsp_esp32

python3 -c "
try:
    import pandas as pd
    import numpy as np
    import h5py
    import matplotlib.pyplot as plt
    print('✅ Dependências básicas OK')
    
    from esp32_to_nilmtk import ESP32ToNILMTK
    from nilmtk_analyzer import NILMTKAnalyzer
    print('✅ Módulos ESP32-NILMTK OK')
    
    print('🎉 Instalação concluída com sucesso!')
    
except ImportError as e:
    print(f'❌ Erro de importação: {e}')
    print('💡 Execute: pip install -r requirements.txt')
"

echo ""
echo "🎯 PRÓXIMOS PASSOS:"
echo "==================="
echo "1. 📊 Execute coleta de dados ESP32 (se não feito)"
echo "2. 🔄 Teste conversão: python example_usage.py"
echo "3. 📓 Abra notebook: jupyter notebook ESP32_NILMTK_Integration.ipynb"
echo "4. 📈 Analise dados e gere relatórios"
echo ""
echo "📚 RECURSOS:"
echo "- 📁 Dados em: dsp_esp32/signal_analysis_data.csv"
echo "- 🔄 Conversor: dsp_esp32/esp32_to_nilmtk.py"
echo "- 📊 Analisador: dsp_esp32/nilmtk_analyzer.py"
echo "- 📓 Notebook: dsp_esp32/ESP32_NILMTK_Integration.ipynb"
echo ""
echo "✅ Configuração ESP32-NILMTK concluída!"
