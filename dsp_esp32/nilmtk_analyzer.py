"""
NILMTK Data Loader and Analyzer
==============================
Carrega e analisa dados NILMTK convertidos da ESP32.

Este módulo permite:
1. Carregar datasets NILMTK (HDF5)
2. Aplicar filtros e pré-processamento
3. Análise exploratória de dados
4. Visualizações especializadas para NILM
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Optional, Tuple, Union
import os

# Configuração de visualização
plt.style.use('default')
sns.set_palette("husl")
warnings.filterwarnings('ignore')

class NILMTKAnalyzer:
    """
    Classe para análise de dados NILMTK gerados pela ESP32.
    """
    
    def __init__(self, hdf5_file: Optional[str] = None):
        """
        Inicializa o analisador NILMTK.
        
        Parameters:
        -----------
        hdf5_file : str, optional
            Caminho para arquivo HDF5 NILMTK
        """
        self.hdf5_file = hdf5_file
        self.dataset = None
        self.power_data = None
        self.metadata = None
        
    def load_dataset(self, hdf5_file: Optional[str] = None) -> bool:
        """
        Carrega dataset NILMTK.
        
        Parameters:
        -----------
        hdf5_file : str, optional
            Caminho para arquivo HDF5
            
        Returns:
        --------
        bool
            True se carregado com sucesso
        """
        if hdf5_file:
            self.hdf5_file = hdf5_file
            
        if not self.hdf5_file:
            raise ValueError("Caminho do arquivo HDF5 não especificado")
            
        print(f"📂 Carregando dataset NILMTK: {self.hdf5_file}")
        
        try:
            # Tenta usar NILMTK se disponível
            try:
                import nilmtk
                self.dataset = nilmtk.DataSet(self.hdf5_file)
                print("✅ Dataset carregado via NILMTK")
                return True
            except ImportError:
                print("⚠️  NILMTK não instalado, usando carregamento manual...")
                return self._load_manual()
                
        except Exception as e:
            print(f"❌ Erro ao carregar dataset: {e}")
            return False
    
    def _load_manual(self) -> bool:
        """
        Carregamento manual do HDF5 (quando NILMTK não está disponível).
        
        Returns:
        --------
        bool
            True se carregado com sucesso
        """
        try:
            import h5py
            
            with h5py.File(self.hdf5_file, 'r') as f:
                # Assume building1/elec/meter1
                building_key = list(f.keys())[0]
                meter_path = f"{building_key}/elec/meter1"
                
                # Carrega timestamps - converte de Unix timestamp para datetime
                timestamps_unix = f[f"{meter_path}/timestamps"][:]
                timestamps = pd.to_datetime(timestamps_unix, unit='s')
                
                # Carrega dados de potência
                power_active = f[f"{meter_path}/power/active"][:]
                voltage = f[f"{meter_path}/voltage"][:]
                current = f[f"{meter_path}/current"][:]
                
                # Cria DataFrame
                self.power_data = pd.DataFrame({
                    'power': power_active,
                    'voltage': voltage,
                    'current': current
                }, index=timestamps)
                
                print("✅ Dataset carregado manualmente")
                return True
                
        except Exception as e:
            print(f"❌ Erro no carregamento manual: {e}")
            return False
    
    def get_power_data(self, building: int = 1, meter: int = 1) -> pd.DataFrame:
        """
        Extrai dados de potência do dataset.
        
        Parameters:
        -----------
        building : int
            Número do prédio
        meter : int
            Número do medidor
            
        Returns:
        --------
        pd.DataFrame
            DataFrame com dados de potência
        """
        if self.power_data is not None:
            return self.power_data
            
        if self.dataset is None:
            raise ValueError("Dataset não carregado. Execute load_dataset() primeiro.")
        
        try:
            # Usando NILMTK
            elec = self.dataset.buildings[building].elec
            meter = elec[meter]
            
            # Carrega dados de potência
            power_data = meter.power_series()
            
            self.power_data = power_data
            return power_data
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados de potência: {e}")
            return pd.DataFrame()
    
    def analyze_consumption_patterns(self, resample_freq: str = '1H') -> Dict:
        """
        Analisa padrões de consumo.
        
        Parameters:
        -----------
        resample_freq : str
            Frequência de reamostragem (ex: '1H', '1D')
            
        Returns:
        --------
        Dict
            Estatísticas de consumo
        """
        if self.power_data is None:
            self.get_power_data()
            
        print("📊 Analisando padrões de consumo...")
        
        # Reamostragem
        resampled = self.power_data['power'].resample(resample_freq).mean()
        
        # Estatísticas básicas
        stats = {
            'consumption_stats': {
                'mean_power': float(self.power_data['power'].mean()),
                'max_power': float(self.power_data['power'].max()),
                'min_power': float(self.power_data['power'].min()),
                'std_power': float(self.power_data['power'].std()),
                'total_energy': float(self.power_data['power'].sum() / 3600),  # Wh
            },
            'temporal_patterns': {
                'peak_hour': resampled.idxmax().hour if not resampled.empty else 0,
                'min_hour': resampled.idxmin().hour if not resampled.empty else 0,
                'daily_variation': float(resampled.std()) if not resampled.empty else 0
            },
            'data_quality': {
                'total_samples': len(self.power_data),
                'missing_values': int(self.power_data['power'].isna().sum()),
                'zero_values': int((self.power_data['power'] == 0).sum()),
                'sampling_rate': self._estimate_sampling_rate()
            }
        }
        
        print("✅ Análise de padrões concluída")
        return stats
    
    def _estimate_sampling_rate(self) -> float:
        """
        Estima taxa de amostragem dos dados.
        
        Returns:
        --------
        float
            Taxa de amostragem em Hz
        """
        if len(self.power_data) < 2:
            return 0.0
            
        time_diff = self.power_data.index[1] - self.power_data.index[0]
        return 1.0 / time_diff.total_seconds()
    
    def detect_appliance_events(self, threshold: float = 50.0, 
                               min_duration: str = '10s') -> pd.DataFrame:
        """
        Detecta eventos de aparelhos (liga/desliga).
        
        Parameters:
        -----------
        threshold : float
            Limiar de potência para detecção (W)
        min_duration : str
            Duração mínima do evento
            
        Returns:
        --------
        pd.DataFrame
            DataFrame com eventos detectados
        """
        if self.power_data is None:
            self.get_power_data()
            
        print(f"🔍 Detectando eventos de aparelhos (limiar: {threshold}W)...")
        
        power_series = self.power_data['power']
        
        # Calcula diferença de potência
        power_diff = power_series.diff()
        
        # Detecta eventos significativos
        events = []
        
        for i, diff in enumerate(power_diff):
            if abs(diff) > threshold:
                event_type = 'turn_on' if diff > 0 else 'turn_off'
                
                events.append({
                    'timestamp': power_series.index[i],
                    'event_type': event_type,
                    'power_change': diff,
                    'power_before': power_series.iloc[i-1] if i > 0 else 0,
                    'power_after': power_series.iloc[i]
                })
        
        events_df = pd.DataFrame(events)
        
        if not events_df.empty:
            # Filtra por duração mínima
            events_df = self._filter_events_by_duration(events_df, min_duration)
        
        print(f"✅ {len(events_df)} eventos detectados")
        return events_df
    
    def _filter_events_by_duration(self, events_df: pd.DataFrame, 
                                  min_duration: str) -> pd.DataFrame:
        """
        Filtra eventos por duração mínima.
        
        Parameters:
        -----------
        events_df : pd.DataFrame
            DataFrame com eventos
        min_duration : str
            Duração mínima
            
        Returns:
        --------
        pd.DataFrame
            Eventos filtrados
        """
        # Implementação simplificada - filtra eventos muito próximos
        min_timedelta = pd.Timedelta(min_duration)
        
        filtered_events = []
        last_event_time = None
        
        for _, event in events_df.iterrows():
            if last_event_time is None or (event['timestamp'] - last_event_time) >= min_timedelta:
                filtered_events.append(event)
                last_event_time = event['timestamp']
        
        return pd.DataFrame(filtered_events)
    
    def plot_power_consumption(self, period: str = 'all', 
                              figsize: Tuple[int, int] = (15, 8)) -> None:
        """
        Plota consumo de potência.
        
        Parameters:
        -----------
        period : str
            Período para plotar ('all', 'day', 'hour')
        figsize : tuple
            Tamanho da figura
        """
        if self.power_data is None:
            self.get_power_data()
            
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle('Análise de Consumo de Potência - ESP32 NILM', fontsize=16)
        
        # 1. Série temporal completa
        axes[0,0].plot(self.power_data.index, self.power_data['power'], 
                      linewidth=0.8, alpha=0.7)
        axes[0,0].set_title('Consumo de Potência - Série Temporal')
        axes[0,0].set_ylabel('Potência (W)')
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. Histograma de potência
        axes[0,1].hist(self.power_data['power'], bins=50, alpha=0.7, edgecolor='black')
        axes[0,1].set_title('Distribuição de Potência')
        axes[0,1].set_xlabel('Potência (W)')
        axes[0,1].set_ylabel('Frequência')
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. Padrão horário
        if len(self.power_data) > 24:
            hourly_pattern = self.power_data.groupby(self.power_data.index.hour)['power'].mean()
            axes[1,0].bar(hourly_pattern.index, hourly_pattern.values, alpha=0.7)
            axes[1,0].set_title('Padrão de Consumo por Hora')
            axes[1,0].set_xlabel('Hora do Dia')
            axes[1,0].set_ylabel('Potência Média (W)')
            axes[1,0].grid(True, alpha=0.3)
        
        # 4. Tensão vs Corrente
        if 'voltage' in self.power_data.columns and 'current' in self.power_data.columns:
            axes[1,1].scatter(self.power_data['voltage'], self.power_data['current'], 
                            alpha=0.5, s=1)
            axes[1,1].set_title('Tensão vs Corrente')
            axes[1,1].set_xlabel('Tensão (V)')
            axes[1,1].set_ylabel('Corrente (A)')
            axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_event_detection(self, events_df: pd.DataFrame, 
                           context_minutes: int = 10) -> None:
        """
        Plota eventos detectados com contexto.
        
        Parameters:
        -----------
        events_df : pd.DataFrame
            DataFrame com eventos detectados
        context_minutes : int
            Minutos de contexto antes/depois do evento
        """
        if events_df.empty:
            print("Nenhum evento para plotar")
            return
            
        fig, ax = plt.subplots(figsize=(15, 6))
        
        # Plota série temporal
        ax.plot(self.power_data.index, self.power_data['power'], 
               linewidth=1, alpha=0.7, color='blue', label='Potência')
        
        # Marca eventos
        for _, event in events_df.iterrows():
            color = 'green' if event['event_type'] == 'turn_on' else 'red'
            marker = '^' if event['event_type'] == 'turn_on' else 'v'
            
            ax.scatter(event['timestamp'], event['power_after'], 
                      color=color, s=100, marker=marker, 
                      label=f"Liga/Desliga" if _ == 0 else "", zorder=5)
        
        ax.set_title('Detecção de Eventos de Aparelhos')
        ax.set_xlabel('Tempo')
        ax.set_ylabel('Potência (W)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def export_analysis_report(self, output_file: str) -> str:
        """
        Exporta relatório de análise.
        
        Parameters:
        -----------
        output_file : str
            Caminho do arquivo de saída
            
        Returns:
        --------
        str
            Caminho do relatório gerado
        """
        if self.power_data is None:
            self.get_power_data()
            
        # Análise básica
        stats = self.analyze_consumption_patterns()
        events = self.detect_appliance_events()
        
        # Gera relatório
        report = f"""
# RELATÓRIO DE ANÁLISE NILM - ESP32
Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 ESTATÍSTICAS DE CONSUMO

### Consumo Geral:
- Potência média: {stats['consumption_stats']['mean_power']:.2f} W
- Potência máxima: {stats['consumption_stats']['max_power']:.2f} W
- Potência mínima: {stats['consumption_stats']['min_power']:.2f} W
- Desvio padrão: {stats['consumption_stats']['std_power']:.2f} W
- Energia total: {stats['consumption_stats']['total_energy']:.2f} Wh

### Padrões Temporais:
- Hora de pico: {stats['temporal_patterns']['peak_hour']}:00
- Hora de mínimo: {stats['temporal_patterns']['min_hour']}:00
- Variação diária: {stats['temporal_patterns']['daily_variation']:.2f} W

## 🔍 EVENTOS DETECTADOS

Total de eventos: {len(events)}

### Eventos por Tipo:
"""
        
        if not events.empty:
            event_counts = events['event_type'].value_counts()
            for event_type, count in event_counts.items():
                report += f"- {event_type}: {count}\n"
        else:
            report += "- Nenhum evento detectado\n"
        
        report += f"""
## 📈 QUALIDADE DOS DADOS

- Total de amostras: {stats['data_quality']['total_samples']:,}
- Valores faltantes: {stats['data_quality']['missing_values']}
- Valores zero: {stats['data_quality']['zero_values']}
- Taxa de amostragem: {stats['data_quality']['sampling_rate']:.2f} Hz

## 📋 CONCLUSÕES

1. Dataset coletado da ESP32 com {len(self.power_data)} amostras
2. Consumo médio de {stats['consumption_stats']['mean_power']:.1f}W
3. {len(events)} eventos de aparelhos detectados
4. Dados adequados para análise NILM avançada

---
Análise gerada pelo sistema ESP32-NILMTK
"""
        
        # Salva relatório
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        print(f"📄 Relatório salvo: {output_file}")
        return output_file

def analyze_esp32_nilmtk_data(hdf5_file: str, 
                             output_dir: str = ".") -> Dict:
    """
    Função utilitária para análise completa de dados ESP32-NILMTK.
    
    Parameters:
    -----------
    hdf5_file : str
        Caminho do arquivo HDF5 NILMTK
    output_dir : str
        Diretório para salvar resultados
        
    Returns:
    --------
    Dict
        Resultados da análise
    """
    print("🔬 Iniciando análise completa ESP32-NILMTK")
    print("-" * 50)
    
    # Cria analisador
    analyzer = NILMTKAnalyzer(hdf5_file)
    
    # Carrega dataset
    if not analyzer.load_dataset():
        raise ValueError("Falha ao carregar dataset")
    
    # Análise de padrões
    stats = analyzer.analyze_consumption_patterns()
    
    # Detecção de eventos
    events = analyzer.detect_appliance_events()
    
    # Visualizações
    print("📈 Gerando visualizações...")
    analyzer.plot_power_consumption()
    
    if not events.empty:
        analyzer.plot_event_detection(events)
    
    # Relatório
    report_file = os.path.join(output_dir, "esp32_nilm_analysis_report.md")
    analyzer.export_analysis_report(report_file)
    
    results = {
        'statistics': stats,
        'events': events,
        'report_file': report_file,
        'analyzer': analyzer
    }
    
    print("\n🎉 Análise completa concluída!")
    return results

if __name__ == "__main__":
    # Exemplo de uso
    hdf5_file = "esp32_nilmtk_dataset.h5"
    
    if os.path.exists(hdf5_file):
        results = analyze_esp32_nilmtk_data(hdf5_file)
        print("✅ Análise concluída com sucesso!")
    else:
        print(f"❌ Arquivo não encontrado: {hdf5_file}")
        print("Execute esp32_to_nilmtk.py primeiro para gerar o dataset.")
