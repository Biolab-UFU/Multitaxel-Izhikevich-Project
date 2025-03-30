/********************************************************************************
* This code is currently used to save the last configuration. Currently used    *
* to save the last configuration (Keyboard vs. Direct Control + num electrodes) *
* in order to avoid that step at the start of the program (change scanf lines   *
* to printf). Code can be modified to save other items as a part of the 	    *
* configuration, but the structure of config.h must also be modified. Some      *
* information currently stored is for future development. 						*
*																			    *
* December 4, 2015															    *
********************************************************************************/

#include "mbed.h"
#include "SOFBlock.h"
#include "errors.h"
#include "input_data.h"
#include "config.h"

#define DATA_SECTOR 6

// Data
static SOFBlock flash_block;
static SOFWriter writer;
static SOFReader reader;

static ConfigFile configuration;
static bool is_initialized = 0;

/*                      */
/*  Private functions   */
/*                      */

ReturnCode erase_config()
{
    ReturnCode rc = LDA_OK;

    if(!SOFBlock::format(DATA_SECTOR))
    {
        rc = LDA_FLASH_ERASE_ERROR;
    }

    return rc;
}


ReturnCode write_config()
{
    ReturnCode rc = LDA_OK;
    SOF_Error_t sof_rc = kSOF_ErrNone;

    erase_config();

    sof_rc = writer.open(DATA_SECTOR);
    if(kSOF_ErrNone == sof_rc)
    {
        writer.write_data((uint8_t*)&configuration, sizeof(ConfigFile));
        if(configuration.pat_rec_M != NULL)
        {
            for(uint32_t i = 0; i < configuration.pat_rec_M_size_1; i++)
            {
                for(uint32_t j = 0; j < configuration.pat_rec_M_size_2; j++)
                {
                    writer.write_data((uint8_t*)&(configuration.pat_rec_M[i][j]), sizeof(float));
                }
            }
        }
        if(configuration.pat_rec_S != NULL)
        {
            for(uint32_t i = 0; i < configuration.pat_rec_S_size_1; i++)
            {
                for(uint32_t j = 0; j < configuration.pat_rec_S_size_2; j++)
                {
                    writer.write_data((uint8_t*)(&configuration.pat_rec_S[i][j]), sizeof(float));
                }
            }
        }
        writer.close();
    }
    else
    {
        rc = LDA_FLASH_WRITE_ERROR;
    }

    return rc;
}

ReturnCode read_config(ConfigFile *config)
{
    ReturnCode rc = LDA_OK;
    SOF_Error_t sof_rc = kSOF_ErrNone;

    sof_rc = reader.open(DATA_SECTOR);
    if(kSOF_ErrNone == sof_rc)
    {
        reader.read_data((uint8_t*)config, sizeof(ConfigFile));
        if(config->pat_rec_M != NULL)
        {
            config->pat_rec_M = (float**)malloc(sizeof(float*)*config->pat_rec_M_size_1);
            for(uint32_t i = 0; i < config->pat_rec_M_size_1; i++)
            {
                config->pat_rec_M[i] = (float*)malloc(sizeof(float)*config->pat_rec_M_size_2);
                for(uint32_t j = 0; j < config->pat_rec_M_size_2; j++)
                {
                    reader.read_data((uint8_t*)(&config->pat_rec_M[i][j]), sizeof(float));
                }
            }
        }
        if(config->pat_rec_S != NULL)
        {
            config->pat_rec_S = (float**)malloc(sizeof(float*)*config->pat_rec_S_size_1);
            for(uint32_t i = 0; i < config->pat_rec_S_size_1; i++)
            {
                config->pat_rec_S[i] = (float*)malloc(sizeof(float)*config->pat_rec_S_size_2);
                for(uint32_t j = 0; j < config->pat_rec_S_size_2; j++)
                {
                    reader.read_data((uint8_t*)(&config->pat_rec_S[i][j]), sizeof(float));
                }
            }
        }
        reader.close();
    }
    else
    {
        rc = LDA_FLASH_READ_ERROR;
    }

    return rc;
}

/*                      */
/*  Public functions    */
/*                      */

ReturnCode Config_init()
{
    ReturnCode rc = LDA_OK;
    SOF_Statics_t statics;

    if (!SOFBlock::get_stat(DATA_SECTOR, statics) || statics.free_size < 11) // check available byte
    { 
        SOFBlock::format(DATA_SECTOR);
    }
    else
    {
        rc = read_config(&configuration);
    }
    is_initialized = 1;

    return rc;
}


ReturnCode Config_get_configuration(ConfigFile *config)
{
    ReturnCode rc = LDA_OK;

    if(NULL != config)
    {
        if(is_initialized)
        {
            config->running_mode = configuration.running_mode;
            config->num_electrodes = configuration.num_electrodes;
            config->type_electrodes = configuration.type_electrodes;
            config->pat_rec_M = (float**)malloc(sizeof(float*)*configuration.pat_rec_M_size_1);
            for(uint32_t i = 0; i < configuration.pat_rec_M_size_1; i++)
            {
                config->pat_rec_M[i] = (float*)malloc(sizeof(float)*configuration.pat_rec_M_size_2);
                for(uint32_t j = 0; j < configuration.pat_rec_M_size_2; j++)
                {
                    config->pat_rec_M[i][j] = configuration.pat_rec_M[i][j];
                }
            }
            config->pat_rec_M_size_1 = configuration.pat_rec_M_size_1;
            config->pat_rec_M_size_2 = configuration.pat_rec_M_size_2;
            config->pat_rec_S = (float**)malloc(sizeof(float*)*configuration.pat_rec_S_size_1);
            for(uint32_t i = 0; i < configuration.pat_rec_S_size_1; i++)
            {
                config->pat_rec_S[i] = (float*)malloc(sizeof(float)*configuration.pat_rec_S_size_2);
                for(uint32_t j = 0; j < configuration.pat_rec_S_size_2; j++)
                {
                    config->pat_rec_S[i][j] = configuration.pat_rec_S[i][j];
                }
            }
            config->pat_rec_S_size_1 = configuration.pat_rec_S_size_1;
            config->pat_rec_S_size_2 = configuration.pat_rec_S_size_2;
            config->pat_rec_features = configuration.pat_rec_features;
            config->pat_rec_classes = configuration.pat_rec_classes;
            config->direct_buf_size = configuration.direct_buf_size;
            config->direct_algorithm = configuration.direct_algorithm;
            config->log_level = configuration.log_level;
            config->log_max_bytes = configuration.log_max_bytes;
            config->idle_time = configuration.idle_time;
            config->dac_gain = configuration.dac_gain;
            config->hand_type = configuration.hand_type;
        }
        else
        {
            rc = LDA_CONFIG_NOT_INITIALIZED;
        }
    }
    else
    {
        rc = LDA_CONFIG_NULL_PTR;
    }

    return rc;
}

ReturnCode Config_set_configuration(ConfigFile *config)
{
    ReturnCode rc = LDA_OK;

    if(NULL != config)
    {
        if(is_initialized)
        {
            configuration.running_mode = config->running_mode;
            configuration.num_electrodes = config->num_electrodes;
            configuration.type_electrodes = config->type_electrodes;
            configuration.pat_rec_M = (float**)malloc(sizeof(float*)*config->pat_rec_M_size_1);
            for(uint32_t i = 0; i < config->pat_rec_M_size_1; i++)
            {
                configuration.pat_rec_M[i] = (float*)malloc(sizeof(float)*config->pat_rec_M_size_2);
                for(uint32_t j = 0; j < config->pat_rec_M_size_2; j++)
                {
                    configuration.pat_rec_M[i][j] = config->pat_rec_M[i][j];
                }
            }
            configuration.pat_rec_M_size_1 = config->pat_rec_M_size_1;
            configuration.pat_rec_M_size_2 = config->pat_rec_M_size_2;
            configuration.pat_rec_S = (float**)malloc(sizeof(float*)*config->pat_rec_S_size_1);
            for(uint32_t i = 0; i < config->pat_rec_S_size_1; i++)
            {
                configuration.pat_rec_S[i] = (float*)malloc(sizeof(float)*config->pat_rec_S_size_2);
                for(uint32_t j = 0; j < config->pat_rec_S_size_2; j++)
                {
                    configuration.pat_rec_S[i][j] = config->pat_rec_S[i][j];
                }
            }
            configuration.pat_rec_S_size_1 = config->pat_rec_S_size_1;
            configuration.pat_rec_S_size_2 = config->pat_rec_S_size_2;
            configuration.pat_rec_features = config->pat_rec_features;
            configuration.pat_rec_classes = config->pat_rec_classes;
            configuration.direct_buf_size = config->direct_buf_size;
            configuration.direct_algorithm = config->direct_algorithm;
            configuration.log_level = config->log_level;
            configuration.log_max_bytes = config->log_max_bytes;
            configuration.idle_time = config->idle_time;
            configuration.dac_gain = config->dac_gain;
            configuration.hand_type = config->hand_type;
            rc = write_config();
        }
        else
        {
            rc = LDA_CONFIG_NOT_INITIALIZED;
        }
    }
    else
    {
        rc = LDA_CONFIG_NULL_PTR;
    }

    return rc;

}

ReturnCode Config_clear_configuration()
{
    return erase_config();
}

// function to update configuration "file"
// functional but with meaningless data for now
ReturnCode Config_update_config()
{
    ReturnCode rc = LDA_OK;
    ConfigFile confignew;

    confignew.running_mode = MODE;
    confignew.num_electrodes = NUM_ELECTRODES;
    confignew.type_electrodes = ELECTRODE_TYPE;
    confignew.pat_rec_M = (float**)malloc(sizeof(float*)*M_SIZE_1);
    for(uint32_t i = 0; i < M_SIZE_1; i++)
    {
        confignew.pat_rec_M[i] = (float*)malloc(sizeof(float)*M_SIZE_2);            
        for(uint32_t j = 0; j < M_SIZE_2; j++)
        {
            confignew.pat_rec_M[i][j] = M_MATRIX[i][j];
        }
    }
    confignew.pat_rec_M_size_1 = M_SIZE_1;
    confignew.pat_rec_M_size_2 = M_SIZE_2;
    confignew.pat_rec_S = (float**)malloc(sizeof(float*)*S_SIZE_1);
    for(uint32_t i = 0; i < S_SIZE_1; i++)
    {
        confignew.pat_rec_S[i] = (float*)malloc(sizeof(float)*S_SIZE_2);
        for(uint32_t j = 0; j < S_SIZE_2; j++)
        {
            confignew.pat_rec_S[i][j] = S_MATRIX[i][j];
        }
    }
    confignew.pat_rec_S_size_1 = S_SIZE_1;
    confignew.pat_rec_S_size_2 = S_SIZE_2;
    confignew.pat_rec_features = FEATURES;
    confignew.pat_rec_classes = CLASSES;
    confignew.direct_buf_size = BUFFER_SIZE;
    confignew.direct_algorithm = ALGORITHM;
    confignew.log_level = LOG_LEVEL;
    confignew.log_max_bytes = LOG_MAX_SIZE;
    confignew.idle_time = IDLE_TIME;
    confignew.dac_gain = DAC_GAIN;
    confignew.hand_type = HAND_TYPE;

    printf("Writing new configuration\r\n");
    rc = Config_set_configuration(&confignew);
    printf("Wrote new configuration\r\n");

    for(uint32_t i = 0; i < confignew.pat_rec_M_size_1; i++)
    {
        delete [] confignew.pat_rec_M[i];
    }
    delete [] confignew.pat_rec_M;
    for(uint32_t i = 0; i < confignew.pat_rec_S_size_1; i++)
    {
        delete [] confignew.pat_rec_S[i];
    }
    delete [] confignew.pat_rec_S;
    return rc;
}

void Config_print_configuration(ConfigFile *confignew)
{
    printf("%d\r\n", confignew->running_mode);// = MODE;
    printf("%d\r\n", confignew->num_electrodes);// = NUM_ELECTRODES;
    printf("%d\r\n", confignew->type_electrodes);// = ELECTRODE_TYPE;
    printf("%p\r\n", confignew->pat_rec_M);// = (float**)malloc(sizeof(float*)*M_SIZE_1);
    for(uint32_t i = 0; i < M_SIZE_1; i++)
    {
        printf("%p\r\n", confignew->pat_rec_M[i]);// = (float*)malloc(sizeof(float)*M_SIZE_2);            
        for(uint32_t j = 0; j < M_SIZE_2; j++)
        {
//            confignew->pat_rec_M[i][j] = M_MATRIX[i][j];
//            printf("M %d %d %f\r\n", i, j, confignew->pat_rec_M[i][j]);
        }
    }
    printf("%d\r\n", confignew->pat_rec_M_size_1);// = M_SIZE_1;
    printf("%d\r\n", confignew->pat_rec_M_size_2);// = M_SIZE_2;
    printf("%p\r\n", confignew->pat_rec_S);// = (float**)malloc(sizeof(float*)*S_SIZE_1);
    for(uint32_t i = 0; i < S_SIZE_1; i++)
    {
        printf("%p\r\n", confignew->pat_rec_S[i]);// = (float*)malloc(sizeof(float)*S_SIZE_2);
        for(uint32_t j = 0; j < S_SIZE_2; j++)
        {
//            confignew->pat_rec_S[i][j] = S_MATRIX[i][j];
//            printf("S %d %d %f\r\n", i, j, confignew->pat_rec_S[i][j]);
        }
    }
    printf("%d\r\n", confignew->pat_rec_S_size_1);// = S_SIZE_1;
    printf("%d\r\n", confignew->pat_rec_S_size_2);// = S_SIZE_2;
    printf("%d\r\n", confignew->pat_rec_features);// = FEATURES;
    printf("%d\r\n", confignew->pat_rec_classes);// = CLASSES;
    printf("%d\r\n", confignew->direct_buf_size);// = BUFFER_SIZE;
    printf("%d\r\n", confignew->direct_algorithm);// = ALGORITHM;
    printf("%d\r\n", confignew->log_level);// = LOG_LEVEL;
    printf("%d\r\n", confignew->log_max_bytes);// = LOG_MAX_SIZE;
    printf("%d\r\n", confignew->idle_time);// = IDLE_TIME;
    printf("%d\r\n", confignew->dac_gain);// = DAC_GAIN;
    printf("%d\r\n", confignew->hand_type);// = HAND_TYPE;

}




