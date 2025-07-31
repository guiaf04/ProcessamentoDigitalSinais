"""
ESP32 to NILMTK Data Converter
===============================
Converte dados coletados pela ESP32 para formato compatível com NILMTK.

Este módulo permite:
1. Carregar dados CSV da ESP32
2. Converter para formato NILMTK (HDF5)
3. Configurar metadata necessário
4. Preparar dados para análise NILM
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import h5py
import os
from typing import Dict, List, Optional, Tuple
import warnings

class ESP32ToNILMTK:
    """
    Classe para conversão de dados ESP32 para formato NILMTK.
    """
    
    def __init__(self, csv_file_path: str):
        """
        Inicializa o conversor com arquivo CSV da ESP32.
        
        Parameters:
        -----------
        csv_file_path : str
            Caminho para o arquivo CSV gerado pela ESP32
        """
        self.csv_file_path = csv_file_path
        self.raw_data = None
        self.nilmtk_data = None
        self.metadata = self._create_default_metadata()
        
    def _create_default_metadata(self) -> Dict:
        """
        Cria metadata padrão para o dataset NILMTK.
        """
        return {
            'name': 'ESP32_NILM_Dataset',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'description': 'Dataset coletado via ESP32-S3 para análise NILM',
            'contact': 'UFC Quixadá - Eng. Computação',
            'timezone': 'America/Fortaleza',
            'geo_location': {
                'locality': 'Quixadá',
                'country': 'BR',
                'latitude': -4.9691,
                'longitude': -39.0197
            },
            'related_documents': [
                'Relatório técnico ESP32-S3 NILM'
            ]
        }
    
    def load_esp32_data(self) -> pd.DataFrame:
        """
        Carrega e processa dados CSV da ESP32.
        
        Returns:
        --------
        pd.DataFrame
            DataFrame com dados processados
        """
        print(f"📂 Carregando dados de: {self.csv_file_path}")
        
        try:
            # Carrega dados CSV
            self.raw_data = pd.read_csv(self.csv_file_path)
            
            # Converte timestamp para datetime
            self.raw_data['timestamp'] = pd.to_datetime(self.raw_data['timestamp'])
            
            print(f"✅ Dados carregados: {len(self.raw_data)} registros")
            print(f"📊 Período: {self.raw_data['timestamp'].min()} até {self.raw_data['timestamp'].max()}")
            
            return self.raw_data
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            raise
    
    def extract_power_data(self, voltage_column: str = 'amplitude_or_magnitude', 
                          current_column: str = 'amplitude_or_magnitude') -> pd.DataFrame:
        """
        Extrai dados de potência dos sinais coletados.
        
        Parameters:
        -----------
        voltage_column : str
            Nome da coluna com dados de tensão
        current_column : str
            Nome da coluna com dados de corrente
            
        Returns:
        --------
        pd.DataFrame
            DataFrame com dados de potência no formato NILMTK
        """
        if self.raw_data is None:
            self.load_esp32_data()
        
        print("⚡ Processando dados de potência...")
        
        # Filtra apenas dados de sinal original (não FFT)
        signal_data = self.raw_data[self.raw_data['data_type'] == 'signal_original'].copy()
        
        # Agrupa por timestamp para calcular potência
        power_data = []
        
        for timestamp, group in signal_data.groupby('timestamp'):
            # Assume que temos dados de tensão e corrente intercalados ou em canais diferentes
            # Por simplicidade, vamos calcular potência RMS baseada na amplitude
            
            amplitude_values = group['amplitude_or_magnitude'].values
            
            # Calcula potência RMS (simulada)
            if len(amplitude_values) > 0:
                # Conversão simplificada - ajustar conforme calibração real
                voltage_rms = np.sqrt(np.mean(amplitude_values**2)) * 110  # Assume 110V nominal
                current_rms = np.sqrt(np.mean(amplitude_values**2)) * 10   # Escala para corrente
                power = voltage_rms * current_rms  # Potência aparente
                
                power_data.append({
                    'timestamp': timestamp,
                    'power': power,
                    'voltage': voltage_rms,
                    'current': current_rms
                })
        
        power_df = pd.DataFrame(power_data)
        power_df.set_index('timestamp', inplace=True)
        
        print(f"✅ {len(power_df)} pontos de potência extraídos")
        print(f"📈 Potência média: {power_df['power'].mean():.2f} W")
        
        return power_df
    
    def create_nilmtk_format(self, power_data: pd.DataFrame, 
                           building_number: int = 1,
                           meter_number: int = 1) -> Dict:
        """
        Converte dados para formato NILMTK.
        
        Parameters:
        -----------
        power_data : pd.DataFrame
            DataFrame com dados de potência
        building_number : int
            Número do prédio/residência
        meter_number : int
            Número do medidor
            
        Returns:
        --------
        Dict
            Dados no formato NILMTK
        """
        print("🔄 Convertendo para formato NILMTK...")
        
        # Cria estrutura NILMTK
        nilmtk_data = {
            f'building{building_number}': {
                'elec': {
                    'meter1': {
                        'power': {
                            'active': power_data['power'].values,
                            'reactive': np.zeros(len(power_data)),  # Placeholder
                            'apparent': power_data['power'].values
                        },
                        'voltage': power_data['voltage'].values,
                        'current': power_data['current'].values,
                        'timestamps': power_data.index
                    }
                },
                'metadata': {
                    'instance': building_number,
                    'original_name': f'ESP32_Building_{building_number}',
                    'timeframe': {
                        'start': power_data.index.min(),
                        'end': power_data.index.max()
                    },
                    'elec_meters': {
                        1: {
                            'device_model': 'ESP32-S3',
                            'site_meter': True,
                            'data_location': 'ESP32_ADC',
                            'preprocessing_applied': {
                                'clip_appliance_power': False,
                                'downsample': False
                            },
                            'statistics': {
                                'count': len(power_data),
                                'mean': float(power_data['power'].mean()),
                                'std': float(power_data['power'].std()),
                                'min': float(power_data['power'].min()),
                                'max': float(power_data['power'].max())
                            }
                        }
                    }
                }
            }
        }
        
        self.nilmtk_data = nilmtk_data
        print("✅ Conversão para NILMTK concluída")
        
        return nilmtk_data
    
    def save_to_hdf5(self, output_path: str, 
                     building_number: int = 1) -> str:
        """
        Salva dados no formato HDF5 compatível com NILMTK.
        
        Parameters:
        -----------
        output_path : str
            Caminho para salvar o arquivo HDF5
        building_number : int
            Número do prédio
            
        Returns:
        --------
        str
            Caminho do arquivo salvo
        """
        if self.nilmtk_data is None:
            raise ValueError("Dados NILMTK não foram criados. Execute create_nilmtk_format() primeiro.")
        
        print(f"💾 Salvando em HDF5: {output_path}")
        
        try:
            with h5py.File(output_path, 'w') as f:
                building_data = self.nilmtk_data[f'building{building_number}']
                
                # Cria grupo do prédio
                building_group = f.create_group(f'building{building_number}')
                
                # Salva dados de eletricidade
                elec_group = building_group.create_group('elec')
                meter_group = elec_group.create_group('meter1')
                
                # Salva dados de potência
                meter_data = building_data['elec']['meter1']
                
                # Timestamps - converte para Unix timestamp
                timestamps = pd.DatetimeIndex(meter_data['timestamps'])
                timestamps_unix = timestamps.astype(np.int64) // 10**9
                meter_group.create_dataset('timestamps', data=timestamps_unix)
                
                # Dados de potência
                power_group = meter_group.create_group('power')
                power_group.create_dataset('active', data=meter_data['power']['active'])
                power_group.create_dataset('reactive', data=meter_data['power']['reactive'])
                power_group.create_dataset('apparent', data=meter_data['power']['apparent'])
                
                # Dados de tensão e corrente
                meter_group.create_dataset('voltage', data=meter_data['voltage'])
                meter_group.create_dataset('current', data=meter_data['current'])
                
                # Metadata - salva apenas valores serializáveis
                metadata_group = building_group.create_group('metadata')
                building_metadata = building_data['metadata']
                
                # Salva metadados básicos
                metadata_group.attrs['instance'] = building_metadata['instance']
                metadata_group.attrs['original_name'] = building_metadata['original_name']
                
                # Timeframe - converte datetime para string
                timeframe_group = metadata_group.create_group('timeframe')
                timeframe_group.attrs['start'] = str(building_metadata['timeframe']['start'])
                timeframe_group.attrs['end'] = str(building_metadata['timeframe']['end'])
                
                # Elec meters metadata
                elec_meters_group = metadata_group.create_group('elec_meters')
                meter1_group = elec_meters_group.create_group('1')
                
                meter_metadata = building_metadata['elec_meters'][1]
                meter1_group.attrs['device_model'] = meter_metadata['device_model']
                meter1_group.attrs['site_meter'] = meter_metadata['site_meter']
                meter1_group.attrs['data_location'] = meter_metadata['data_location']
                
                # Statistics
                stats_group = meter1_group.create_group('statistics')
                for key, value in meter_metadata['statistics'].items():
                    stats_group.attrs[key] = float(value)
            
            print(f"✅ Arquivo HDF5 salvo: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Erro ao salvar HDF5: {e}")
            raise
    
    def generate_summary_report(self) -> str:
        """
        Gera relatório resumo dos dados convertidos.
        
        Returns:
        --------
        str
            Relatório em formato texto
        """
        if self.nilmtk_data is None:
            return "❌ Dados NILMTK não disponíveis"
        
        building_data = list(self.nilmtk_data.values())[0]
        meter_data = building_data['elec']['meter1']
        metadata = building_data['metadata']['elec_meters'][1]
        
        report = f"""
📊 RELATÓRIO DE CONVERSÃO ESP32 → NILMTK
{'='*50}

📈 ESTATÍSTICAS DOS DADOS:
  • Total de amostras: {metadata['statistics']['count']:,}
  • Potência média: {metadata['statistics']['mean']:.2f} W
  • Desvio padrão: {metadata['statistics']['std']:.2f} W
  • Potência mínima: {metadata['statistics']['min']:.2f} W
  • Potência máxima: {metadata['statistics']['max']:.2f} W

⏰ PERÍODO DE COLETA:
  • Início: {building_data['metadata']['timeframe']['start']}
  • Fim: {building_data['metadata']['timeframe']['end']}
  • Duração: {building_data['metadata']['timeframe']['end'] - building_data['metadata']['timeframe']['start']}

🔧 CONFIGURAÇÃO:
  • Dispositivo: {metadata['device_model']}
  • Medidor principal: {'Sim' if metadata['site_meter'] else 'Não'}
  • Localização dos dados: {metadata['data_location']}

✅ STATUS: Dados prontos para análise NILMTK
"""
        return report

def convert_esp32_to_nilmtk(csv_file: str, 
                           output_hdf5: str,
                           building_number: int = 1) -> str:
    """
    Função utilitária para conversão completa ESP32 → NILMTK.
    
    Parameters:
    -----------
    csv_file : str
        Caminho do arquivo CSV da ESP32
    output_hdf5 : str
        Caminho de saída do arquivo HDF5
    building_number : int
        Número do prédio
        
    Returns:
    --------
    str
        Relatório da conversão
    """
    print("🚀 Iniciando conversão ESP32 → NILMTK")
    print("-" * 50)
    
    try:
        # Cria conversor
        converter = ESP32ToNILMTK(csv_file)
        
        # Carrega dados
        converter.load_esp32_data()
        
        # Extrai dados de potência
        power_data = converter.extract_power_data()
        
        # Converte para formato NILMTK
        converter.create_nilmtk_format(power_data, building_number)
        
        # Salva em HDF5
        converter.save_to_hdf5(output_hdf5, building_number)
        
        # Gera relatório
        report = converter.generate_summary_report()
        
        print("\n🎉 Conversão concluída com sucesso!")
        print(report)
        
        return report
        
    except Exception as e:
        error_msg = f"❌ Erro na conversão: {e}"
        print(error_msg)
        raise

if __name__ == "__main__":
    # Exemplo de uso
    csv_file = "signal_analysis_data.csv"
    output_file = "esp32_nilmtk_dataset.h5"
    
    if os.path.exists(csv_file):
        convert_esp32_to_nilmtk(csv_file, output_file)
    else:
        print(f"❌ Arquivo não encontrado: {csv_file}")
