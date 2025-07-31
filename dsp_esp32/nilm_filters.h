/**
 * @file nilm_filters.h
 * @brief Definições e estruturas para filtros IIR no detector NILM
 * 
 * Este arquivo contém as definições dos filtros IIR Butterworth
 * para detecção de eventos em sistemas NILM (Non-Intrusive Load Monitoring)
 */

#ifndef NILM_FILTERS_H
#define NILM_FILTERS_H

#include <stdint.h>

// Configurações do sistema NILM
#define NILM_SAMPLE_RATE_HZ     10      // Taxa de amostragem adequada para NILM
#define NILM_BUFFER_SIZE        1024    // Tamanho do buffer de amostras
#define NILM_EVENT_THRESHOLD    50.0f   // Limiar de detecção de eventos (Watts)
#define NILM_DEBOUNCE_TIME_MS   5000    // Tempo de debounce entre eventos (ms)

// Configurações do filtro passa-alta (detector de eventos)
#define HP_FILTER_ORDER         6       // Ordem do filtro passa-alta
#define HP_FILTER_SECTIONS      3       // Número de seções biquad (ordem/2)
#define HP_CUTOFF_FREQ_HZ       0.002f  // Frequência de corte (Hz)

// Configurações do filtro passa-baixa (caracterizador de potência)
#define LP_FILTER_ORDER         2       // Ordem do filtro passa-baixa
#define LP_CUTOFF_FREQ_HZ       0.01f   // Frequência de corte (Hz)

/**
 * @brief Estrutura de uma seção biquad (2ª ordem)
 * 
 * Implementa a forma direta II transposta:
 * H(z) = (b0 + b1*z^-1 + b2*z^-2) / (1 + a1*z^-1 + a2*z^-2)
 */
typedef struct {
    // Coeficientes do numerador
    float b0, b1, b2;
    
    // Coeficientes do denominador (a0 = 1.0 implícito)
    float a1, a2;
    
    // Estados internos (linha de atraso)
    float w1, w2;
} biquad_section_t;

/**
 * @brief Estrutura para classificação de eventos
 */
typedef struct {
    uint32_t timestamp_ms;      // Timestamp do evento
    float delta_power;          // Variação de potência (W)
    uint8_t device_type;        // Tipo de dispositivo classificado
    char device_name[32];       // Nome do dispositivo
} nilm_event_t;

/**
 * @brief Tipos de dispositivos para classificação
 */
typedef enum {
    DEVICE_UNKNOWN = 0,
    DEVICE_LIGHT,           // Lâmpada/iluminação
    DEVICE_MICROWAVE,       // Forno microondas
    DEVICE_WASHING_MACHINE, // Máquina de lavar
    DEVICE_DISHWASHER,      // Lava-louças
    DEVICE_REFRIGERATOR,    // Geladeira
    DEVICE_AIR_CONDITIONER, // Ar condicionado
    DEVICE_WATER_HEATER,    // Aquecedor elétrico
    DEVICE_TV,              // Televisão
    DEVICE_COMPUTER,        // Computador
    DEVICE_OTHER            // Outros dispositivos
} device_type_t;

/**
 * @brief Faixas de potência para classificação de dispositivos
 */
typedef struct {
    device_type_t type;
    const char* name;
    float min_power;    // Potência mínima (W)
    float max_power;    // Potência máxima (W)
} device_power_range_t;

// Tabela de classificação de dispositivos por potência
static const device_power_range_t device_table[] = {
    {DEVICE_LIGHT,           "Light",            5.0f,    100.0f},
    {DEVICE_TV,              "Television",       50.0f,   200.0f},
    {DEVICE_COMPUTER,        "Computer",         100.0f,  400.0f},
    {DEVICE_MICROWAVE,       "Microwave",        800.0f,  1500.0f},
    {DEVICE_DISHWASHER,      "Dishwasher",       1200.0f, 2000.0f},
    {DEVICE_WASHING_MACHINE, "Washing Machine",  500.0f,  2500.0f},
    {DEVICE_AIR_CONDITIONER, "Air Conditioner",  1000.0f, 3000.0f},
    {DEVICE_WATER_HEATER,    "Water Heater",     1500.0f, 4000.0f},
    {DEVICE_REFRIGERATOR,    "Refrigerator",     100.0f,  300.0f}
};

#define DEVICE_TABLE_SIZE (sizeof(device_table) / sizeof(device_power_range_t))

/**
 * @brief Coeficientes pré-calculados do filtro Butterworth passa-alta
 * 
 * Filtro de 6ª ordem (3 seções biquad) com fc = 0.002 Hz @ fs = 10 Hz
 * Calculado usando scipy.signal.butter() e convertido para SOS (Second Order Sections)
 */
static const float hp_filter_coeffs[HP_FILTER_SECTIONS][5] = {
    // Seção 1: [b0, b1, b2, a1, a2]
    {0.997575307740f, -1.988312337657f, 0.990752632414f, -1.991046493047f, 0.991071281177f},
    
    // Seção 2: [b0, b1, b2, a1, a2]
    {1.000000000000f, -2.006874965307f, 1.006890743483f, -2.005708281949f, 1.005721304286f},
    
    // Seção 3: [b0, b1, b2, a1, a2]
    {1.000000000000f, -1.999979933536f, 0.999995642535f, -1.998389952299f, 0.998409811440f}
};

/**
 * @brief Coeficientes do filtro Butterworth passa-baixa
 * 
 * Filtro de 2ª ordem com fc = 0.01 Hz @ fs = 10 Hz
 * Para suavização e caracterização de potência
 */
static const float lp_filter_coeffs[5] = {
    // [b0, b1, b2, a1, a2]
    0.000009446918f, 0.000018893836f, 0.000009446918f, -1.999924093655f, 0.999961880327f
};

// Protótipos de funções
float apply_biquad_section(float input, biquad_section_t *section);
float apply_highpass_filter(float input, biquad_section_t sections[HP_FILTER_SECTIONS]);
float apply_lowpass_filter(float input, biquad_section_t *section);
void init_filter_sections(biquad_section_t sections[HP_FILTER_SECTIONS], biquad_section_t *lp_section);
device_type_t classify_device_by_power(float delta_power);
const char* get_device_name(device_type_t type);

#endif // NILM_FILTERS_H
