#ifndef CONFIG_H
#define CONFIG_H
#include "errors.h"
#include "types.h"

typedef struct 
{
    float **pat_rec_M;
    uint32_t pat_rec_M_size_1;
    uint32_t pat_rec_M_size_2;
    float **pat_rec_S;
    uint32_t pat_rec_S_size_1;
    uint32_t pat_rec_S_size_2;
    uint8_t pat_rec_features;
    uint8_t pat_rec_classes;
    Running_mode_t running_mode;
    uint8_t num_electrodes;
    Electrode_type_t type_electrodes;
    uint32_t direct_buf_size;
    Algorithm_t direct_algorithm;
    Log_level_t log_level;
    uint32_t log_max_bytes;
    uint32_t idle_time;
    float dac_gain;
    Hand_type_t hand_type;
} ConfigFile;

ReturnCode Config_init();
ReturnCode Config_get_configuration(ConfigFile *config);
ReturnCode Config_set_configuration(ConfigFile *config);
ReturnCode Config_clear_configuration();
ReturnCode Config_update_config();
void Config_print_configuration(ConfigFile *config);

#endif // CONFIG_H