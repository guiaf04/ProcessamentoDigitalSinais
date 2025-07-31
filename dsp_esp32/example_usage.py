#!/usr/bin/env python3
"""
Exemplo de Uso da Integração ESP32-NILMTK
=======================================
Script de demonstração para conversão e análise de dados ESP32 com NILMTK.

Uso:
    python example_usage.py
"""

import os
import sys
from datetime import datetime

def main():
    print("🚀 Exemplo de Integração ESP32-NILMTK")
    print("=" * 50)
    
    # Arquivos de entrada e saída
    csv_file = "signal_analysis_data.csv"
    hdf5_file = "esp32_nilmtk_dataset.h5"
    
    # Verifica se arquivo CSV existe
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo CSV não encontrado: {csv_file}")
        print("💡 Certifique-se de que os dados da ESP32 estão disponíveis.")
        return False
    
    try:
        # Importa módulos
        print("📦 Importando módulos...")
        from esp32_to_nilmtk import convert_esp32_to_nilmtk
        from nilmtk_analyzer import analyze_esp32_nilmtk_data
        
        # Etapa 1: Conversão ESP32 → NILMTK
        print("\n🔄 Etapa 1: Conversão ESP32 → NILMTK")
        print("-" * 30)
        
        report = convert_esp32_to_nilmtk(
            csv_file=csv_file,
            output_hdf5=hdf5_file,
            building_number=1
        )
        
        print("✅ Conversão concluída!")
        
        # Etapa 2: Análise dos dados NILMTK
        print("\n📊 Etapa 2: Análise dos dados NILMTK")
        print("-" * 30)
        
        results = analyze_esp32_nilmtk_data(
            hdf5_file=hdf5_file,
            output_dir="."
        )
        
        # Etapa 3: Resumo dos resultados
        print("\n📋 Etapa 3: Resumo dos resultados")
        print("-" * 30)
        
        stats = results['statistics']
        events = results['events']
        
        print(f"📈 Potência média: {stats['consumption_stats']['mean_power']:.2f} W")
        print(f"🎯 Eventos detectados: {len(events)}")
        print(f"📄 Relatório: {results['report_file']}")
        
        print("\n🎉 Análise completa finalizada com sucesso!")
        print("\n💡 Próximos passos:")
        print("   1. Abra o notebook ESP32_NILMTK_Integration.ipynb")
        print("   2. Execute as células para análise interativa")
        print("   3. Leia o relatório gerado em Markdown")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Instale as dependências com: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
