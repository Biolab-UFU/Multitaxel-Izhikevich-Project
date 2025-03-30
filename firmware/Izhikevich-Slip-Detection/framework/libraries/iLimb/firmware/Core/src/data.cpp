#include "mbed.h"
#include "rtos.h"
#include "electrode.h"
#include "data.h"

#define NUM_SENSORS MAX_ELECTRODES
#define MAX_VAL (25000)
#define MIN_VAL (-25000)
#define BASELINETHRESH 250
#define DAC_MAX 4095
#define ENVELOP_PEAK 10000
#define ZETA 10

typedef struct 
{
	int c_buffer[BUFF_SIZE];
	int data_pointer;
	int num_samples;
	int rms;
} Data;

Data sensor[NUM_SENSORS];
Running_mode_t fmode = DIRECT;

ReturnCode Data_init(int index, Running_mode_t mode)
{
	ReturnCode rc = LDA_OK;

	if(index < NUM_SENSORS)
	{
		memset(sensor[index].c_buffer, 0, BUFF_SIZE);
		sensor[index].data_pointer = 0;
		sensor[index].num_samples = 0;
		sensor[index].rms = 0;
		fmode = mode;
	}
	else
	{
		rc = LDA_INDEX_BOUNDS_ERROR;
	}

	return rc;
}

ReturnCode Data_add_data(int index, int in_data)
{	
	ReturnCode rc = LDA_OK;

	if(index < NUM_SENSORS)
	{
		if(0 != sensor[index].num_samples)
		{
			// DIRECT
			sensor[index].rms -= sensor[index].c_buffer[sensor[index].data_pointer] * sensor[index].c_buffer[sensor[index].data_pointer] / BUFF_SIZE;

		}


		// DIRECT
		in_data = (in_data < MAX_VAL) ? ((in_data > MIN_VAL) ? in_data : MIN_VAL) : MAX_VAL; //limits range of raw outputs to +/-25k
		sensor[index].c_buffer[sensor[index].data_pointer] = in_data;
			
		sensor[index].rms += sensor[index].c_buffer[sensor[index].data_pointer] * sensor[index].c_buffer[sensor[index].data_pointer] / BUFF_SIZE;
		sensor[index].data_pointer = (sensor[index].data_pointer + 1) % BUFF_SIZE;

		if(sensor[index].num_samples <= BUFF_SIZE)
		{
			sensor[index].num_samples++;
		}
	}
	else
	{
		rc = LDA_INDEX_BOUNDS_ERROR;
	}

	return rc;
}

ReturnCode Data_get_envelop(int index, int *envelop)
{
	ReturnCode rc = LDA_OK;

	if(NULL != envelop)
	{
		if(index < NUM_SENSORS)
		{
			*envelop = sqrt(sensor[index].rms);

			////////////////////////////////////////////////////
		    //   Shift Down and Cut Negative Part of Envelop  //
		    //            By Hai Tang, 2015.9.2               //
		    ////////////////////////////////////////////////////
		    *envelop -= BASELINETHRESH;

		    *envelop = (*envelop < 0) ? 0 : *envelop;
		    
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
