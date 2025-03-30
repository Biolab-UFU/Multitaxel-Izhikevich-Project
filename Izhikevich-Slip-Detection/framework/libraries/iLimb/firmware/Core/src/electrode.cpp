#include "electrode.h"
#include "ads1291.h"
#include "types.h"
#include "errors.h"
#include "log.h"

#define MAX_RETRY 5000
#define FREQUENCY 1000000
#define WIDTH 8
#define MODE 1
#define STATUS_OK 0xC00000
#define SIGN_EXT 0xFFFFFF00

typedef struct 
{
    SPI *device;
    DigitalOut *cs[MAX_ELECTRODES];
} Electrode_t;

Electrode_t Electrodes;

unsigned int send_command(uint8_t index, uint16_t command, uint8_t *data, uint8_t datalen)
{
    unsigned int ret = 0;
    Electrodes.device->frequency(FREQUENCY);//1000000
    Electrodes.device->format(WIDTH, MODE);
    Electrodes.cs[index]->write(0);
    Electrodes.device->write(command);
    if((command & ADS_CMD_WRITEREG) || (command & ADS_CMD_READREG))
    {
        Electrodes.device->write(datalen - 1);
        for(uint8_t i = 0; i < datalen; i++)
        {
            if(NULL != data)
            {
                ret = (ret << (8 * i)) | Electrodes.device->write(data[i]);
            }
            else
            {
                ret = (ret << (8 * i)) | Electrodes.device->write(0);
            }
            wait(.01);
        }
    }
    else
    {
        wait(.01);
    }
    Electrodes.cs[index]->write(1);
    return ret;
}

ReturnCode Electrode_read_data(unsigned char index, int *retdata)
{
    ReturnCode rc = LDA_OK;
    int ret1 = 0;
    int ret2 = 0;
    int ret3 = 0;
    int status = 0;

    if(NULL != retdata)
    {
        if(index < MAX_ELECTRODES)
        {
            Electrodes.device->frequency(FREQUENCY);//1000000
            Electrodes.device->format(WIDTH, MODE);

            Electrodes.cs[index]->write(0);
            Electrodes.device->write(ADS_CMD_RDATAS);

            // Channel 1 - 24 Status Bits
            status = (Electrodes.device->write(0x00) << 16);
            status |= (Electrodes.device->write(0x00) << 8);
            status |= Electrodes.device->write(0x00);
//            pcserial->printf("Status 1 = %X\r\n", status);

            // Channel 1 Data
            ret1 = Electrodes.device->write(0x00);
            ret2 = Electrodes.device->write(0x00);
            ret3 = Electrodes.device->write(0x00);

            Electrodes.cs[index]->write(1);

            if(STATUS_OK != status)
            {
                rc = LDA_ELECTRODE_ERROR;
            }

            ret1 = (0x80 & ret1) ? (SIGN_EXT | ret1) : ret1;
            *retdata = (ret1 << 16) | 
                  (ret2 << 8) | 
                  ret3;

        //    pcserial->printf("Data1 = %d\t\t%X\r\n", *retdata, *retdata);
        }
        else
        {
            rc = LDA_INDEX_BOUNDS_ERROR;
        }
    }
    else
    {
        rc = LDA_ERROR_NULL_PTR;
    }
    return rc;
}

ReturnCode Electrode_read_ID(int index, int *ID)
{
    ReturnCode rc = LDA_OK;

    if(NULL != ID)
    {
        if(index < MAX_ELECTRODES)
        {
            send_command(index, ADS_CMD_START_CONV, 0, 1);
            *ID = send_command(index, (ADS_CMD_READREG | ADS_REG_ID), 0, 1);
        }
        else
        {
            rc = LDA_INDEX_BOUNDS_ERROR;
        }
    }
    else
    {
        rc = LDA_ERROR_NULL_PTR;
    }

    return rc;
}

ReturnCode Electrode_init(unsigned char index, SPI *spi_device, PinName spi_cs)
{
    ReturnCode rc = LDA_OK;
    int retry = 0;
    int ID = 0;
    uint8_t data[8] = {0};
    int config = 0;
	pcserial->printf("%d\r\n", index);
    if(NULL != spi_device)
    {
        if(index < MAX_ELECTRODES)
        {
            Electrodes.device = spi_device;
            Electrodes.cs[index] = new DigitalOut(spi_cs);
            Electrodes.device->frequency(FREQUENCY);
            Electrodes.device->format(WIDTH, MODE);
            Electrodes.cs[index]->write(1);
            while((ID != ADS1291) && (retry < MAX_RETRY))   // Add error when MAX_RETRY is hit
            {
                send_command(index, ADS_CMD_RESET, 0, 1);
                send_command(index, ADS_CMD_STOP_CONV, 0, 1);
                send_command(index, ADS_CMD_SDATAC, 0, 1);
				pcserial->printf("check 1\r\n");
                do
                {
                    data[0] = (LEAD_OFF_DISABLED | REF_BUFFER_ENABLED | VREF_2V | OSC_CLK_OFF | INT_TEST_SIG_OFF | INT_TEST_SIG_DC);
                    send_command(index, (ADS_CMD_WRITEREG | ADS_REG_CONFIG2), data, 1);
                    config = send_command(index, (ADS_CMD_READREG | ADS_REG_CONFIG2), 0, 1); 
					//pcserial->printf("%i", config);
                    retry++;
                }while((retry < MAX_RETRY) && (config != data[0]));
				pcserial->printf("check 2\r\n");
                do
                {
                    data[0] = (SINGLE_SHOT_MODE | DATA_RATE_4000);
                    send_command(index, (ADS_CMD_WRITEREG | ADS_REG_CONFIG1), data, 1);
                    config = send_command(index, (ADS_CMD_READREG | ADS_REG_CONFIG1), 0, 1);
                    retry++;
                }while((retry < MAX_RETRY) && (config != data[0]));
				pcserial->printf("check 3\r\n");
                do
                {
                    data[0] = (PWR_UP | GAIN_6 | ELECT_IN);
                    send_command(index, (ADS_CMD_WRITEREG | ADS_REG_CH1SET), data, 1);
                    config = send_command(index, (ADS_CMD_READREG | ADS_REG_CH1SET), 0, 1);
                    retry++;
                }while((retry < MAX_RETRY) && (config != data[0]));
				pcserial->printf("check 4\r\n");
                do
                {
                    data[0] = (PWR_DWN | GAIN_6 | ELECT_IN);
                    send_command(index, (ADS_CMD_WRITEREG | ADS_REG_CH2SET), data, 1);
                    config = send_command(index, (ADS_CMD_READREG | ADS_REG_CH2SET), 0, 1);
                    retry++;
                }while((retry < MAX_RETRY) && (config != data[0]));
				pcserial->printf("check 5\r\n");
                Electrode_read_ID(index, &ID);
                retry++;
            }
			pcserial->printf("check 6\r\n");
            if(retry >= MAX_RETRY)
            {
                rc = LDA_ELECTRODE_MAX_RETRY_ERROR;
            }
        }
        else
        {
            rc = LDA_INDEX_BOUNDS_ERROR;
        }
    }
    else
    {
        rc = LDA_ERROR_NULL_PTR;
    }

    return rc;
}

ReturnCode Electrode_BIT(int index)
{
    ReturnCode rc = LDA_OK;
    int ID = 0;

    rc = Electrode_read_ID(index, &ID);
    if((LDA_OK != rc) || (ADS1291 != ID))
    {
        struct failure_t
        {
            ReturnCode ret;
            int ID;
        } failure;
        failure.ret = rc;
        failure.ID = ID;
        Log_entry(LOG_TYPE_ERROR, sizeof(failure), (uint8_t*)&failure);

        rc = LDA_ELECTRODE_BIT_FAILED;
    }

    return rc;
}
