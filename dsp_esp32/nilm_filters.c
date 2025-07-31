/**
 * @file nilm_filters.c
 * @brief Implementação das funções de filtros IIR para NILM
 */

#include "nilm_filters.h"
#include <math.h>
#include <string.h>

/**
 * @brief Aplica uma seção biquad usando Direct Form II Transposed
 * 
 * Esta implementação é numericamente estável e eficiente para ponto fixo
 * 
 * @param input Amostra de entrada
 * @param section Ponteiro para a estrutura da seção biquad
 * @return Amostra filtrada de saída
 */
float apply_biquad_section(float input, biquad_section_t *section) {
    // Direct Form II Transposed
    float output = section->b0 * input + section->w1;
    
    // Atualiza estados internos
    section->w1 = section->b1 * input - section->a1 * output + section->w2;
    section->w2 = section->b2 * input - section->a2 * output;
    
    return output;
}

/**
 * @brief Aplica o filtro passa-alta completo (cascata de seções biquad)
 * 
 * @param input Amostra de entrada
 * @param sections Array de seções biquad
 * @return Amostra filtrada de saída
 */
float apply_highpass_filter(float input, biquad_section_t sections[HP_FILTER_SECTIONS]) {
    float output = input;
    
    // Aplica cada seção em cascata
    for (int i = 0; i < HP_FILTER_SECTIONS; i++) {
        output = apply_biquad_section(output, &sections[i]);
    }
    
    return output;
}

/**
 * @brief Aplica o filtro passa-baixa para suavização
 * 
 * @param input Amostra de entrada
 * @param section Ponteiro para a seção biquad do filtro passa-baixa
 * @return Amostra filtrada de saída
 */
float apply_lowpass_filter(float input, biquad_section_t *section) {
    return apply_biquad_section(input, section);
}

/**
 * @brief Inicializa as seções de filtro com os coeficientes pré-calculados
 * 
 * @param sections Array de seções para o filtro passa-alta
 * @param lp_section Ponteiro para a seção do filtro passa-baixa
 */
void init_filter_sections(biquad_section_t sections[HP_FILTER_SECTIONS], biquad_section_t *lp_section) {
    // Inicializa seções do filtro passa-alta
    for (int i = 0; i < HP_FILTER_SECTIONS; i++) {
        sections[i].b0 = hp_filter_coeffs[i][0];
        sections[i].b1 = hp_filter_coeffs[i][1];
        sections[i].b2 = hp_filter_coeffs[i][2];
        sections[i].a1 = hp_filter_coeffs[i][3];
        sections[i].a2 = hp_filter_coeffs[i][4];
        sections[i].w1 = 0.0f;
        sections[i].w2 = 0.0f;
    }
    
    // Inicializa seção do filtro passa-baixa
    if (lp_section != NULL) {
        lp_section->b0 = lp_filter_coeffs[0];
        lp_section->b1 = lp_filter_coeffs[1];
        lp_section->b2 = lp_filter_coeffs[2];
        lp_section->a1 = lp_filter_coeffs[3];
        lp_section->a2 = lp_filter_coeffs[4];
        lp_section->w1 = 0.0f;
        lp_section->w2 = 0.0f;
    }
}

/**
 * @brief Classifica o tipo de dispositivo baseado na variação de potência
 * 
 * @param delta_power Variação de potência em Watts
 * @return Tipo de dispositivo classificado
 */
device_type_t classify_device_by_power(float delta_power) {
    float abs_power = fabsf(delta_power);
    
    // Busca na tabela de dispositivos
    for (int i = 0; i < DEVICE_TABLE_SIZE; i++) {
        if (abs_power >= device_table[i].min_power && 
            abs_power <= device_table[i].max_power) {
            return device_table[i].type;
        }
    }
    
    // Se não encontrou correspondência
    if (abs_power > 50.0f) {
        return DEVICE_OTHER;
    } else {
        return DEVICE_UNKNOWN;
    }
}

/**
 * @brief Retorna o nome do dispositivo baseado no tipo
 * 
 * @param type Tipo do dispositivo
 * @return String com o nome do dispositivo
 */
const char* get_device_name(device_type_t type) {
    for (int i = 0; i < DEVICE_TABLE_SIZE; i++) {
        if (device_table[i].type == type) {
            return device_table[i].name;
        }
    }
    
    switch (type) {
        case DEVICE_OTHER: return "Other Device";
        case DEVICE_UNKNOWN: return "Unknown";
        default: return "Undefined";
    }
}

/**
 * @brief Reset dos estados internos do filtro (útil para reinicialização)
 * 
 * @param sections Array de seções do filtro passa-alta
 * @param lp_section Seção do filtro passa-baixa
 */
void reset_filter_states(biquad_section_t sections[HP_FILTER_SECTIONS], biquad_section_t *lp_section) {
    // Reset estados do filtro passa-alta
    for (int i = 0; i < HP_FILTER_SECTIONS; i++) {
        sections[i].w1 = 0.0f;
        sections[i].w2 = 0.0f;
    }
    
    // Reset estado do filtro passa-baixa
    if (lp_section != NULL) {
        lp_section->w1 = 0.0f;
        lp_section->w2 = 0.0f;
    }
}

/**
 * @brief Calcula a resposta em frequência de uma seção biquad
 * 
 * Útil para verificação e debug dos filtros
 * 
 * @param section Seção biquad
 * @param frequency Frequência em Hz
 * @param sample_rate Taxa de amostragem em Hz
 * @return Magnitude da resposta (linear, não em dB)
 */
float biquad_frequency_response(const biquad_section_t *section, float frequency, float sample_rate) {
    float omega = 2.0f * M_PI * frequency / sample_rate;
    float cos_omega = cosf(omega);
    float sin_omega = sinf(omega);
    float cos_2omega = cosf(2.0f * omega);
    float sin_2omega = sinf(2.0f * omega);
    
    // Numerador: |b0 + b1*e^(-jω) + b2*e^(-j2ω)|²
    float num_real = section->b0 + section->b1 * cos_omega + section->b2 * cos_2omega;
    float num_imag = -section->b1 * sin_omega - section->b2 * sin_2omega;
    float num_mag_sq = num_real * num_real + num_imag * num_imag;
    
    // Denominador: |1 + a1*e^(-jω) + a2*e^(-j2ω)|²
    float den_real = 1.0f + section->a1 * cos_omega + section->a2 * cos_2omega;
    float den_imag = -section->a1 * sin_omega - section->a2 * sin_2omega;
    float den_mag_sq = den_real * den_real + den_imag * den_imag;
    
    // |H(ω)| = |Numerador| / |Denominador|
    return sqrtf(num_mag_sq / den_mag_sq);
}
