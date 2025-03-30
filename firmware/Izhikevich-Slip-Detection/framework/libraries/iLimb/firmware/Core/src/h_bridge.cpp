#include "h_bridge.h"
#include "mbed.h"
#include "errors.h"
#include "types.h"

PwmOut HB1in1(PC_6);
PwmOut HB1in2(PC_7);
DigitalOut HB1nsleep(PB_5);

PwmOut HB2in1(PC_8);
PwmOut HB2in2(PC_9);
DigitalOut HB2nsleep(PB_8);

typedef struct
{
	PwmOut *in1;
	PwmOut *in2;
	DigitalOut *nsleep;
} H_Bridge_t;

H_Bridge_t HB[MAX_HB];

ReturnCode HB_init(int index, PinName in1, PinName in2, PinName nsleep)
{
	ReturnCode rc = LDA_OK;

	if((0 <= index) || (MAX_HB > index))
	{
		HB[index].in1 = new PwmOut(in1);
		HB[index].in2 = new PwmOut(in2);
		HB[index].nsleep = new DigitalOut(nsleep);
		HB[index].nsleep->write(1);				// add 1 for default state of coast
		HB[index].in1->period_ms(10);
		HB[index].in1->pulsewidth_ms(1);
		HB[index].in1->write(0);
		HB[index].in2->period_ms(10);
		HB[index].in2->pulsewidth_ms(1);
		HB[index].in2->write(0);
	}
	else
	{
		rc = LDA_INDEX_BOUNDS_ERROR;
	}

	return rc;
}

ReturnCode HB_coast(int index)
{
	ReturnCode ret = LDA_OK;

	if((0 <= index) || (MAX_HB > index))
	{
		HB[index].nsleep->write(1);
		HB[index].in1->write(0);
		HB[index].in2->write(0);
	}
	else
	{
		ret = LDA_INDEX_BOUNDS_ERROR;
	}

	return ret;
}

ReturnCode HB_reverse(int index, float speed) //speed should be between 0 and 1 (i.e. 0.5 = 50% duty cycle)
{
	ReturnCode ret = LDA_OK;

	if((0 <= index) || (MAX_HB > index))
	{
		HB[index].nsleep->write(1);
		HB[index].in1->write(0);
		HB[index].in2->write(speed);	}
	else
	{
		ret = LDA_INDEX_BOUNDS_ERROR;
	}
	pcserial->printf("send reverse");

	return ret;

}

ReturnCode HB_forward(int index, float speed) //speed should be between 0 and 1 (i.e. 0.5 = 50% duty cycle)
{
	ReturnCode ret = LDA_OK;

	if((0 <= index) || (MAX_HB > index))
	{
		HB[index].nsleep->write(1);
		HB[index].in1->write(speed);
		HB[index].in2->write(0);
	}
	else
	{
		ret = LDA_INDEX_BOUNDS_ERROR;
	}
	pcserial->printf("send forward");

	return ret;

}

ReturnCode HB_brake(int index)
{
	ReturnCode ret = LDA_OK;

	if((0 <= index) || (MAX_HB > index))
	{
		HB[index].nsleep->write(1);
		HB[index].in1->write(.8);
		HB[index].in2->write(.8);
	}
	else
	{
		ret = LDA_INDEX_BOUNDS_ERROR;
	}
	pcserial->printf("send brake");

	return ret;

}

ReturnCode HB_BIT(int index)
{
	ReturnCode rc = LDA_OK;

	HB_forward(1,1);
	wait_ms(500);
	HB_reverse(1,1);
	wait_ms(500);
	HB_brake(1);

	return rc;
}

//clockwise motion by a given angle
ReturnCode HB_ClockWise(uint16_t angle) {

	uint16_t wait_time;
	ReturnCode rc = LDA_OK;
	//wait_time =  (float)(angle/180)*1300;
	wait_time = 1000;
	HB_forward(1,1);
	wait_ms(int(1350*((float)angle/180.0) )) ;
	HB_brake(1);
}

//anticlockwise motion by a given angle
ReturnCode HB_AntiClockWise(uint16_t angle) {

	uint16_t wait_time;
	ReturnCode rc = LDA_OK;
	//wait_time =  (float)(angle/180)*1300;
	wait_time  = 1000;
	HB_reverse(1,1);
	wait_ms(int(1350*(float(angle)/180.0) )) ;
	HB_brake(1);
}
