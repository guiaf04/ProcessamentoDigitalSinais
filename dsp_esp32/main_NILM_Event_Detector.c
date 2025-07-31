#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <sys/unistd.h>
#include "driver/adc_types_legacy.h"
#include "esp_err.h"
#include "freertos/FreeRTOSConfig_arch.h"
#include "freertos/idf_additions.h"
#include "freertos/projdefs.h"
#include "hal/adc_types.h"
#include "portmacro.h"
#include "sdkconfig.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_adc/adc_continuous.h"
#include "soc/soc_caps.h"

// Tag para logs
static const char* TAG = "NILM_DETECTOR";

// Configurações do sistema
#define SAMPLE_RATE_HZ          10.0f       // Taxa de amostragem para NILM (10 Hz)
#define ADC_SAMPLE_RATE_HZ      20000       // Taxa de amostragem do ADC (20 kHz)
#define DECIMATION_FACTOR       2000        // 20000/10 = 2000
#define EVENT_THRESHOLD         50.0f       // Limiar de detecção de eventos (W)
#define DEBOUNCE_TIME_MS        2000        // Tempo de debounce (2 segundos)

// Configurações do ADC
adc_channel_t channels[2] = {ADC1_CHANNEL_4, ADC1_CHANNEL_5};
int ADC_DATA[2];
float voltage[2];
static uint32_t decimation_counter = 0;
static float voltage_sum[2] = {0, 0};

adc_continuous_handle_t adc_handle;
TaskHandle_t cb_task;
TaskHandle_t nilm_task;

bool New_ADC_data = pdFALSE;

// Estrutura para armazenar estados do filtro IIR
typedef struct {
    float x[3];  // Entradas anteriores [x[n], x[n-1], x[n-2]]
    float y[3];  // Saídas anteriores [y[n], y[n-1], y[n-2]]
} biquad_state_t;

// Estados dos filtros para cada seção biquad
static biquad_state_t filter_states[3];

// Coeficientes do filtro Butterworth 6ª ordem passa-alta (fc = 0.002 Hz, fs = 10 Hz)
// Decomposto em 3 seções biquad (Segunda Ordem)
static const float filter_coeffs[3][6] = {
    // Seção 1: [b0, b1, b2, a0, a1, a2]
    {0.999001949317, -1.998003898634, 0.999001949317, 1.0, -1.998001949634, 0.998005898268},
    // Seção 2:
    {1.000000000000, -2.000000000000, 1.000000000000, 1.0, -1.997003947368, 0.997005896736},
    // Seção 3:
    {1.000000000000, -2.000000000000, 1.000000000000, 1.0, -1.996007894737, 0.996009844211}
};

// Buffers para processamento
#define POWER_BUFFER_SIZE       100
static float power_buffer[POWER_BUFFER_SIZE];
static uint32_t power_index = 0;
static bool power_buffer_full = false;

// Variáveis para detecção de eventos
static uint32_t last_event_time = 0;
static float baseline_power = 0.0f;

// Função para aplicar uma seção biquad do filtro
static float apply_biquad(float input, int section) {
    biquad_state_t *state = &filter_states[section];
    const float *coeffs = filter_coeffs[section];
    
    // Atualizar entradas
    state->x[2] = state->x[1];
    state->x[1] = state->x[0];
    state->x[0] = input;
    
    // Calcular saída usando Direct Form II Transposed
    float output = coeffs[0] * state->x[0] + 
                   coeffs[1] * state->x[1] + 
                   coeffs[2] * state->x[2] - 
                   coeffs[4] * state->y[1] - 
                   coeffs[5] * state->y[2];
    
    // Atualizar saídas
    state->y[2] = state->y[1];
    state->y[1] = state->y[0];
    state->y[0] = output;
    
    return output;
}

// Função para aplicar o filtro completo (cascata de 3 seções biquad)
static float apply_highpass_filter(float input) {
    float output = input;
    
    // Aplicar cada seção biquad em cascata
    for (int i = 0; i < 3; i++) {
        output = apply_biquad(output, i);
    }
    
    return output;
}

// Função para calcular potência a partir das tensões
static float calculate_power(float v1, float v2) {
    // Para sensores de corrente: P = V * I
    // Assumindo que v1 é tensão e v2 é proporcional à corrente
    // Ajustar conforme a configuração real dos sensores
    return fabsf(v1 * v2 * 100.0f);  // Fator de escala para converter para Watts
}

// Função para detectar eventos
static void detect_events(float current_power, float filtered_power) {
    uint32_t current_time = xTaskGetTickCount() * portTICK_PERIOD_MS;
    
    // Verificar debounce
    if (current_time - last_event_time < DEBOUNCE_TIME_MS) {
        return;
    }
    
    // Verificar se há um evento significativo
    if (fabsf(filtered_power) > EVENT_THRESHOLD) {
        last_event_time = current_time;
        
        // Classificar o tipo de evento
        const char* event_type = "unknown";
        const char* device_type = "unknown";
        
        if (filtered_power > 0) {
            event_type = "ON";
            // Classificar dispositivo baseado na potência
            if (current_power > 2000) {
                device_type = "heating";
            } else if (current_power > 500) {
                device_type = "appliance";
            } else if (current_power > 100) {
                device_type = "lighting";
            } else {
                device_type = "small_load";
            }
        } else {
            event_type = "OFF";
        }
        
        ESP_LOGI(TAG, "EVENT DETECTED: %s | Device: %s | Power: %.1fW | Delta: %.1fW", 
                 event_type, device_type, current_power, filtered_power);
    }
}

// Callback do ADC
static bool IRAM_ATTR callback(adc_continuous_handle_t handle, const adc_continuous_evt_data_t *edata, void *user_data) {
    BaseType_t mustYield = pdFALSE;
    vTaskNotifyGiveFromISR(cb_task, &mustYield);
    return (mustYield == pdTRUE);
}

// Task para processar dados do ADC
void cbTask(void *parameters) {
    uint8_t buf[256];  // Buffer maior para dados do ADC
    uint32_t rxLen = 0;
    
    for (;;) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        
        esp_err_t ret = adc_continuous_read(adc_handle, buf, sizeof(buf), &rxLen, 0);
        if (ret == ESP_OK) {
            for (int i = 0; i < rxLen; i += SOC_ADC_DIGI_RESULT_BYTES) {
                adc_digi_output_data_t *p = (adc_digi_output_data_t *)&buf[i];
                uint16_t channel = p->type2.channel;
                uint16_t data = p->type2.data;
                
                if (channel == ADC1_CHANNEL_4) {
                    voltage_sum[0] += data * 3.3f / 4095.0f;
                } else if (channel == ADC1_CHANNEL_5) {
                    voltage_sum[1] += data * 3.3f / 4095.0f;
                }
                
                decimation_counter++;
                
                // Decimação para obter 10 Hz
                if (decimation_counter >= DECIMATION_FACTOR) {
                    voltage[0] = voltage_sum[0] / DECIMATION_FACTOR;
                    voltage[1] = voltage_sum[1] / DECIMATION_FACTOR;
                    
                    // Reset dos acumuladores
                    voltage_sum[0] = 0;
                    voltage_sum[1] = 0;
                    decimation_counter = 0;
                    
                    New_ADC_data = pdTRUE;
                    
                    // Notificar a task NILM
                    xTaskNotifyGive(nilm_task);
                }
            }
        }
    }
}

// Task principal do algoritmo NILM
void nilmTask(void *parameters) {
    for (;;) {
        // Aguardar nova amostra
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        
        if (New_ADC_data) {
            New_ADC_data = pdFALSE;
            
            // Calcular potência instantânea
            float current_power = calculate_power(voltage[0], voltage[1]);
            
            // Aplicar filtro passa-alta para detectar eventos
            float filtered_power = apply_highpass_filter(current_power);
            
            // Armazenar no buffer circular
            power_buffer[power_index] = current_power;
            power_index = (power_index + 1) % POWER_BUFFER_SIZE;
            if (power_index == 0) power_buffer_full = true;
            
            // Calcular baseline (média móvel)
            if (power_buffer_full) {
                float sum = 0;
                for (int i = 0; i < POWER_BUFFER_SIZE; i++) {
                    sum += power_buffer[i];
                }
                baseline_power = sum / POWER_BUFFER_SIZE;
            }
            
            // Detectar eventos
            detect_events(current_power, filtered_power);
            
            // Log periódico (a cada 10 segundos)
            static uint32_t log_counter = 0;
            if (++log_counter >= 100) {  // 100 amostras * 0.1s = 10s
                log_counter = 0;
                ESP_LOGI(TAG, "Power: %.1fW | Baseline: %.1fW | Filtered: %.1fW", 
                         current_power, baseline_power, filtered_power);
            }
        }
    }
}

// Função para inicializar o ADC
void configure_adc(adc_channel_t *channels, uint8_t numChannels) {
    // Configuração do handle
    adc_continuous_handle_cfg_t handle_config = {
        .conv_frame_size = 256,
        .max_store_buf_size = 1024,
    };
    ESP_ERROR_CHECK(adc_continuous_new_handle(&handle_config, &adc_handle));
    
    // Configuração do ADC
    adc_continuous_config_t adc_config = {
        .pattern_num = numChannels,
        .conv_mode = ADC_CONV_SINGLE_UNIT_1,
        .format = ADC_DIGI_OUTPUT_FORMAT_TYPE2,
        .sample_freq_hz = ADC_SAMPLE_RATE_HZ  // 20 kHz - dentro do range válido
    };
    
    adc_digi_pattern_config_t channel_config[numChannels];
    for (int i = 0; i < numChannels; i++) {
        channel_config[i].channel = channels[i];
        channel_config[i].atten = ADC_ATTEN_DB_12;
        channel_config[i].bit_width = ADC_BITWIDTH_12;
        channel_config[i].unit = ADC_UNIT_1;
    }
    adc_config.adc_pattern = channel_config;
    
    ESP_ERROR_CHECK(adc_continuous_config(adc_handle, &adc_config));
    
    // Configuração do callback
    adc_continuous_evt_cbs_t cb_config = {
        .on_conv_done = callback,
    };
    ESP_ERROR_CHECK(adc_continuous_register_event_callbacks(adc_handle, &cb_config, NULL));
}

// Função principal
void app_main(void) {
    ESP_LOGI(TAG, "=== NILM Event Detector Starting ===");
    ESP_LOGI(TAG, "Filter: Butterworth 6th order High-Pass, fc = 0.002 Hz");
    ESP_LOGI(TAG, "Sample Rate: %.1f Hz", SAMPLE_RATE_HZ);
    ESP_LOGI(TAG, "Event Threshold: %.1f W", EVENT_THRESHOLD);
    
    // Inicializar estados do filtro
    memset(filter_states, 0, sizeof(filter_states));
    
    // Criar tasks
    xTaskCreate(cbTask, "ADC Callback Task", 4096, NULL, 5, &cb_task);
    xTaskCreate(nilmTask, "NILM Processing Task", 8192, NULL, 4, &nilm_task);
    
    // Configurar e iniciar ADC
    configure_adc(channels, 2);
    ESP_ERROR_CHECK(adc_continuous_start(adc_handle));
    
    ESP_LOGI(TAG, "System initialized successfully!");
    
    // Loop principal - monitoramento do sistema
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));  // 10 segundos
        
        // Log de status do sistema
        ESP_LOGI(TAG, "System running... Free heap: %lu bytes", esp_get_free_heap_size());
    }
}