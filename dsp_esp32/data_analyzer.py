#!/usr/bin/env python3
"""
Analisador de dados salvos do Signal Analyzer
Carrega dados do CSV e gera gráficos de análise
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import argparse
import os

def load_data(csv_file):
    """Carrega dados do arquivo CSV"""
    try:
        df = pd.read_csv(csv_file)
        print(f"[INFO] Arquivo carregado: {csv_file}")
        print(f"[INFO] Total de registros: {len(df)}")
        
        # Estatísticas básicas
        print("\n=== ESTATÍSTICAS ===")
        print("Tipos de dados disponíveis:")
        print(df['data_type'].value_counts())
        print(f"\nPacotes únicos: {df['packet_id'].nunique()}")
        print(f"Período: {df['timestamp'].min()} até {df['timestamp'].max()}")
        
        return df
    except Exception as e:
        print(f"[ERRO] Não foi possível carregar {csv_file}: {e}")
        return None

def plot_packet_comparison(df, packet_id):
    """Plota comparação de um pacote específico"""
    packet_data = df[df['packet_id'] == packet_id]
    
    if packet_data.empty:
        print(f"[ERRO] Pacote {packet_id} não encontrado")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f'Análise do Pacote #{packet_id}', fontsize=16)
    
    # Sinal Original
    signal_orig = packet_data[packet_data['data_type'] == 'signal_original']
    if not signal_orig.empty:
        ax1.plot(signal_orig['time_or_freq'], signal_orig['amplitude_or_magnitude'], 'b-', linewidth=1)
        ax1.set_title('Sinal Original')
        ax1.set_xlabel('Tempo (s)')
        ax1.set_ylabel('Amplitude (V)')
        ax1.grid(True)
    
    # Sinal Filtrado
    signal_filt = packet_data[packet_data['data_type'] == 'signal_filtered']
    if not signal_filt.empty:
        ax2.plot(signal_filt['time_or_freq'], signal_filt['amplitude_or_magnitude'], 'r-', linewidth=1)
        ax2.set_title('Sinal Filtrado')
        ax2.set_xlabel('Tempo (s)')
        ax2.set_ylabel('Amplitude (V)')
        ax2.grid(True)
    
    # FFT Original
    fft_orig = packet_data[packet_data['data_type'] == 'fft_original']
    if not fft_orig.empty:
        ax3.semilogx(fft_orig['time_or_freq'], fft_orig['amplitude_or_magnitude'], 'g-', linewidth=1)
        ax3.set_title('FFT do Sinal Original')
        ax3.set_xlabel('Frequência (Hz)')
        ax3.set_ylabel('Magnitude (dB)')
        ax3.grid(True)
    
    # FFT Filtrado
    fft_filt = packet_data[packet_data['data_type'] == 'fft_filtered']
    if not fft_filt.empty:
        ax4.semilogx(fft_filt['time_or_freq'], fft_filt['amplitude_or_magnitude'], 'm-', linewidth=1)
        ax4.set_title('FFT do Sinal Filtrado')
        ax4.set_xlabel('Frequência (Hz)')
        ax4.set_ylabel('Magnitude (dB)')
        ax4.grid(True)
    
    plt.tight_layout()
    return fig

def plot_signal_evolution(df, data_type='signal_original', max_packets=10):
    """Plota evolução temporal de múltiplos pacotes"""
    unique_packets = sorted(df['packet_id'].unique())
    
    if len(unique_packets) > max_packets:
        packets_to_plot = unique_packets[-max_packets:]  # Últimos N pacotes
        print(f"[INFO] Plotando os últimos {max_packets} pacotes de {len(unique_packets)} total")
    else:
        packets_to_plot = unique_packets
    
    plt.figure(figsize=(12, 8))
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(packets_to_plot)))
    
    for i, packet_id in enumerate(packets_to_plot):
        packet_data = df[(df['packet_id'] == packet_id) & (df['data_type'] == data_type)]
        
        if not packet_data.empty:
            label = f'Pacote #{packet_id}'
            if data_type.startswith('fft'):
                plt.semilogx(packet_data['time_or_freq'], packet_data['amplitude_or_magnitude'], 
                           color=colors[i], alpha=0.7, linewidth=1, label=label)
            else:
                plt.plot(packet_data['time_or_freq'], packet_data['amplitude_or_magnitude'], 
                        color=colors[i], alpha=0.7, linewidth=1, label=label)
    
    plt.title(f'Evolução Temporal - {data_type.replace("_", " ").title()}')
    
    if data_type.startswith('signal'):
        plt.xlabel('Tempo (s)')
        plt.ylabel('Amplitude (V)')
    else:
        plt.xlabel('Frequência (Hz)')
        plt.ylabel('Magnitude (dB)')
    
    plt.grid(True)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    return plt.gcf()

def generate_statistics(df):
    """Gera estatísticas detalhadas dos dados"""
    stats = {}
    
    for data_type in df['data_type'].unique():
        type_data = df[df['data_type'] == data_type]
        
        stats[data_type] = {
            'count': len(type_data),
            'mean': type_data['amplitude_or_magnitude'].mean(),
            'std': type_data['amplitude_or_magnitude'].std(),
            'min': type_data['amplitude_or_magnitude'].min(),
            'max': type_data['amplitude_or_magnitude'].max(),
            'packets': type_data['packet_id'].nunique()
        }
    
    return stats

def plot_statistics_summary(df):
    """Plota resumo estatístico"""
    stats = generate_statistics(df)
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Resumo Estatístico dos Dados', fontsize=16)
    
    # Gráfico 1: Médias por tipo
    types = list(stats.keys())
    means = [stats[t]['mean'] for t in types]
    ax1.bar(types, means)
    ax1.set_title('Valores Médios por Tipo')
    ax1.set_ylabel('Amplitude/Magnitude Média')
    ax1.tick_params(axis='x', rotation=45)
    
    # Gráfico 2: Desvios padrão
    stds = [stats[t]['std'] for t in types]
    ax2.bar(types, stds, color='orange')
    ax2.set_title('Desvio Padrão por Tipo')
    ax2.set_ylabel('Desvio Padrão')
    ax2.tick_params(axis='x', rotation=45)
    
    # Gráfico 3: Contagem de amostras
    counts = [stats[t]['count'] for t in types]
    ax3.bar(types, counts, color='green')
    ax3.set_title('Número de Amostras por Tipo')
    ax3.set_ylabel('Contagem')
    ax3.tick_params(axis='x', rotation=45)
    
    # Gráfico 4: Evolução de pacotes no tempo
    packet_times = df.groupby('packet_id')['timestamp'].first().sort_values()
    packet_ids = packet_times.index
    times = pd.to_datetime(packet_times.values)
    
    ax4.plot(times, packet_ids, 'bo-', markersize=4)
    ax4.set_title('Pacotes Recebidos ao Longo do Tempo')
    ax4.set_xlabel('Timestamp')
    ax4.set_ylabel('ID do Pacote')
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

def main():
    parser = argparse.ArgumentParser(description='Analisador de dados do Signal Analyzer')
    parser.add_argument('--csv', default='signal_analysis_data.csv', 
                       help='Arquivo CSV com os dados (padrão: signal_analysis_data.csv)')
    parser.add_argument('--packet', type=int, 
                       help='ID do pacote específico para análise')
    parser.add_argument('--evolution', choices=['signal_original', 'signal_filtered', 'fft_original', 'fft_filtered'],
                       help='Tipo de dado para análise de evolução temporal')
    parser.add_argument('--stats', action='store_true',
                       help='Gerar resumo estatístico')
    parser.add_argument('--save', action='store_true',
                       help='Salvar gráficos em arquivos PNG')
    parser.add_argument('--max-packets', type=int, default=10,
                       help='Máximo de pacotes para plotar na evolução (padrão: 10)')
    
    args = parser.parse_args()
    
    # Verificar se arquivo existe
    if not os.path.exists(args.csv):
        print(f"[ERRO] Arquivo não encontrado: {args.csv}")
        return
    
    # Carregar dados
    df = load_data(args.csv)
    if df is None:
        return
    
    figures = []
    
    # Análise de pacote específico
    if args.packet is not None:
        fig = plot_packet_comparison(df, args.packet)
        if fig:
            figures.append(('packet_analysis', fig))
    
    # Análise de evolução temporal
    if args.evolution:
        fig = plot_signal_evolution(df, args.evolution, args.max_packets)
        figures.append((f'evolution_{args.evolution}', fig))
    
    # Resumo estatístico
    if args.stats:
        fig = plot_statistics_summary(df)
        figures.append(('statistics_summary', fig))
        
        # Imprimir estatísticas textuais
        stats = generate_statistics(df)
        print("\n=== ESTATÍSTICAS DETALHADAS ===")
        for data_type, stat in stats.items():
            print(f"\n{data_type.replace('_', ' ').title()}:")
            print(f"  Amostras: {stat['count']}")
            print(f"  Pacotes: {stat['packets']}")
            print(f"  Média: {stat['mean']:.6f}")
            print(f"  Desvio: {stat['std']:.6f}")
            print(f"  Min/Max: {stat['min']:.6f} / {stat['max']:.6f}")
    
    # Se nenhuma opção específica foi escolhida, mostrar o último pacote
    if not any([args.packet is not None, args.evolution, args.stats]):
        last_packet = df['packet_id'].max()
        print(f"[INFO] Mostrando análise do último pacote: #{last_packet}")
        fig = plot_packet_comparison(df, last_packet)
        if fig:
            figures.append(('last_packet_analysis', fig))
    
    # Salvar gráficos se solicitado
    if args.save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for name, fig in figures:
            filename = f"{name}_{timestamp}.png"
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"[INFO] Gráfico salvo: {filename}")
    
    # Mostrar gráficos
    if figures:
        plt.show()
    else:
        print("[INFO] Nenhum gráfico gerado. Use --help para ver opções disponíveis.")

if __name__ == '__main__':
    main()
