#include <stdio.h>
#include <math.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_adc/adc_continuous.h"
#include "hal/adc_types.h"
#include "esp_log.h"
#include "esp_dsp.h"

#define TAG "SIGNAL_ANALYZER"

// Configurações
#define N_SAMPLES 512
#define SAMPLE_FREQ_HZ 10000
#define FILTER_FC 1000  // Frequência de corte do filtro passa-baixas (1kHz)

// ADC
adc_channel_t ADC_CHANNEL[1] = {ADC_CHANNEL_5};
static adc_continuous_handle_t adc_handle = NULL;
static TaskHandle_t cb_task_handle = NULL;
static TaskHandle_t analysis_task_handle = NULL;

// Buffers
static float adc_buffer[N_SAMPLES];
static float filtered_buffer[N_SAMPLES];
static int adc_index = 0;
static volatile bool buffer_full = false;

// FFT buffers
static float window[N_SAMPLES] __attribute__((aligned(16)));
static float fft_input[N_SAMPLES * 2] __attribute__((aligned(16)));
static float mag_db_original[N_SAMPLES / 2];
static float mag_db_filtered[N_SAMPLES / 2];

// Filtro IIR passa-baixas
static float coeffs_lp[5];
static float w_lp[5] = {0};

// Contador para controlar envio de dados
static uint32_t sample_counter = 0;
static const uint32_t SEND_INTERVAL = 100; // Enviar a cada 100 aquisições

/**
 * Callback do ADC
 */
static bool IRAM_ATTR adc_callback(adc_continuous_handle_t handle, 
                                   const adc_continuous_evt_data_t *edata, 
                                   void *user_data) {
    BaseType_t must_yield = pdFALSE;
    vTaskNotifyGiveFromISR(cb_task_handle, &must_yield);
    return (must_yield == pdTRUE);
}

/**
 * Task de callback do ADC - coleta dados
 */
static void cbTask(void *param) {
    uint8_t buf[256];
    uint32_t ret_num = 0;
    
    while (1) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        
        esp_err_t ret = adc_continuous_read(adc_handle, buf, sizeof(buf), &ret_num, 0);
        if (ret == ESP_OK && ret_num > 0) {
            for (int i = 0; i < ret_num; i += SOC_ADC_DIGI_RESULT_BYTES) {
                adc_digi_output_data_t *data = (adc_digi_output_data_t *)&buf[i];
                
                if (data->type2.channel == ADC_CHANNEL[0]) {
                    // Converte para tensão (0-3.3V)
                    float voltage = (float)data->type2.data * 3.3f / 4095.0f;
                    
                    adc_buffer[adc_index++] = voltage;
                    
                    if (adc_index >= N_SAMPLES) {
                        adc_index = 0;
                        buffer_full = true;
                        
                        // Notifica task de análise
                        xTaskNotifyGive(analysis_task_handle);
                    }
                }
            }
        }
    }
}

/**
 * Calcula FFT e retorna magnitude em dB
 */
static void calculate_fft(float *input, float *mag_output) {
    // Prepara entrada da FFT (windowing)
    for (int i = 0; i < N_SAMPLES; i++) {
        fft_input[2 * i] = input[i] * window[i];      // Real
        fft_input[2 * i + 1] = 0.0f;                  // Imaginário
    }
    
    // Executa FFT
    dsps_fft2r_fc32(fft_input, N_SAMPLES);
    dsps_bit_rev_fc32(fft_input, N_SAMPLES);
    dsps_cplx2reC_fc32(fft_input, N_SAMPLES);
    
    // Calcula magnitude em dB
    for (int i = 0; i < N_SAMPLES / 2; i++) {
        float real = fft_input[2 * i];
        float imag = fft_input[2 * i + 1];
        float magnitude = sqrtf(real * real + imag * imag);
        mag_output[i] = 20.0f * log10f(magnitude / N_SAMPLES + 1e-12f);
    }
}

/**
 * Envia dados do sinal original
 */
static void send_original_signal(void) {
    printf("---SIGNAL_ORIGINAL_START---\n");
    for (int i = 0; i < N_SAMPLES; i++) {
        float time = (float)i / SAMPLE_FREQ_HZ;
        printf("%.6f,%.6f\n", time, adc_buffer[i]);
    }
    printf("---SIGNAL_ORIGINAL_END---\n");
}

/**
 * Envia dados do sinal filtrado
 */
static void send_filtered_signal(void) {
    printf("---SIGNAL_FILTERED_START---\n");
    for (int i = 0; i < N_SAMPLES; i++) {
        float time = (float)i / SAMPLE_FREQ_HZ;
        printf("%.6f,%.6f\n", time, filtered_buffer[i]);
    }
    printf("---SIGNAL_FILTERED_END---\n");
}

/**
 * Envia FFT do sinal original
 */
static void send_fft_original(void) {
    printf("---FFT_ORIGINAL_START---\n");
    for (int i = 0; i < N_SAMPLES / 2; i++) {
        float freq = (float)i * SAMPLE_FREQ_HZ / N_SAMPLES;
        printf("%.1f,%.6f\n", freq, mag_db_original[i]);
    }
    printf("---FFT_ORIGINAL_END---\n");
}

/**
 * Envia FFT do sinal filtrado
 */
static void send_fft_filtered(void) {
    printf("---FFT_FILTERED_START---\n");
    for (int i = 0; i < N_SAMPLES / 2; i++) {
        float freq = (float)i * SAMPLE_FREQ_HZ / N_SAMPLES;
        printf("%.1f,%.6f\n", freq, mag_db_filtered[i]);
    }
    printf("---FFT_FILTERED_END---\n");
}

/**
 * Task principal de análise
 */
static void analysisTask(void *param) {
    ESP_LOGI(TAG, "Analysis Task Started");
    
    while (1) {
        // Aguarda buffer cheio
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        
        if (buffer_full) {
            buffer_full = false;
            sample_counter++;
            
            // Copia dados para processamento local (evita sobreposição)
            float local_buffer[N_SAMPLES];
            memcpy(local_buffer, adc_buffer, sizeof(adc_buffer));
            
            // Aplica filtro passa-baixas
            memcpy(filtered_buffer, local_buffer, sizeof(local_buffer));
            dsps_biquad_f32(filtered_buffer, filtered_buffer, N_SAMPLES, coeffs_lp, w_lp);
            
            // Calcula FFT de ambos os sinais
            calculate_fft(local_buffer, mag_db_original);
            calculate_fft(filtered_buffer, mag_db_filtered);
            
            // Envia dados periodicamente
            if (sample_counter % SEND_INTERVAL == 0) {
                ESP_LOGI(TAG, "Sending data packet #%lu", sample_counter / SEND_INTERVAL);
                
                // Envia dados na sequência
                send_original_signal();
                vTaskDelay(pdMS_TO_TICKS(50));  // Pequena pausa entre envios
                
                send_filtered_signal();
                vTaskDelay(pdMS_TO_TICKS(50));
                
                send_fft_original();
                vTaskDelay(pdMS_TO_TICKS(50));
                
                send_fft_filtered();
                vTaskDelay(pdMS_TO_TICKS(50));
                
                printf("---DATA_COMPLETE---\n");
            }
            
            // Log estatísticas básicas
            float avg_original = 0.0f, avg_filtered = 0.0f;
            for (int i = 0; i < N_SAMPLES; i++) {
                avg_original += local_buffer[i];
                avg_filtered += filtered_buffer[i];
            }
            avg_original /= N_SAMPLES;
            avg_filtered /= N_SAMPLES;
            
            if (sample_counter % 50 == 0) {  // Log a cada 50 amostras
                ESP_LOGI(TAG, "Avg Original: %.3fV, Avg Filtered: %.3fV", avg_original, avg_filtered);
            }
        }
    }
}

/**
 * Configuração inicial do ADC
 */
static void configure_adc(void) {
    // Configuração do handle ADC
    adc_continuous_handle_cfg_t handle_cfg = {
        .conv_frame_size = 256,
        .max_store_buf_size = 1024,
    };
    ESP_ERROR_CHECK(adc_continuous_new_handle(&handle_cfg, &adc_handle));
    
    // Configuração do ADC
    adc_continuous_config_t adc_config = {
        .pattern_num = 1,
        .conv_mode = ADC_CONV_SINGLE_UNIT_1,
        .format = ADC_DIGI_OUTPUT_FORMAT_TYPE2,
        .sample_freq_hz = SAMPLE_FREQ_HZ,
    };
    
    // Padrão de conversão
    adc_digi_pattern_config_t pattern = {
        .atten = ADC_ATTEN_DB_12,
        .channel = ADC_CHANNEL[0],
        .bit_width = ADC_BITWIDTH_12,
        .unit = ADC_UNIT_1,
    };
    adc_config.adc_pattern = &pattern;
    
    ESP_ERROR_CHECK(adc_continuous_config(adc_handle, &adc_config));
    
    // Configuração de callbacks
    adc_continuous_evt_cbs_t cbs = {
        .on_conv_done = adc_callback,
    };
    ESP_ERROR_CHECK(adc_continuous_register_event_callbacks(adc_handle, &cbs, NULL));
}

/**
 * Função principal
 */
void app_main(void) {
    ESP_LOGI(TAG, "=== Signal Analyzer Starting ===");
    ESP_LOGI(TAG, "Sample Rate: %d Hz", SAMPLE_FREQ_HZ);
    ESP_LOGI(TAG, "Filter FC: %d Hz", FILTER_FC);
    ESP_LOGI(TAG, "FFT Size: %d points", N_SAMPLES);
    
    // Inicializa DSP
    esp_err_t ret = dsps_fft2r_init_fc32(NULL, N_SAMPLES);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "FFT initialization failed!");
        return;
    }
    
    // Gera janela de Hann
    dsps_wind_hann_f32(window, N_SAMPLES);
    
    // Configura filtro passa-baixas (Butterworth, fc normalizada, Q=0.707)
    float fc_normalized = (float)FILTER_FC / SAMPLE_FREQ_HZ;
    dsps_biquad_gen_lpf_f32(coeffs_lp, fc_normalized, 0.707f);
    
    ESP_LOGI(TAG, "Filter coefficients: b0=%.6f, b1=%.6f, b2=%.6f, a1=%.6f, a2=%.6f", 
             coeffs_lp[0], coeffs_lp[1], coeffs_lp[2], coeffs_lp[3], coeffs_lp[4]);
    
    // Configura ADC
    configure_adc();
    
    // Cria tasks
    xTaskCreate(cbTask, "ADC Callback Task", 4096, NULL, 5, &cb_task_handle);
    xTaskCreate(analysisTask, "Analysis Task", 8192, NULL, 4, &analysis_task_handle);
    
    // Inicia ADC
    ESP_ERROR_CHECK(adc_continuous_start(adc_handle));
    
    ESP_LOGI(TAG, "=== Signal Analyzer Ready ===");
    ESP_LOGI(TAG, "Waiting for ADC data...");
    
    // Task principal apenas monitora o sistema
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000)); // 10 segundos
        ESP_LOGI(TAG, "System running... Free heap: %lu bytes", esp_get_free_heap_size());
        ESP_LOGI(TAG, "Total samples processed: %lu", sample_counter);
    }
}
