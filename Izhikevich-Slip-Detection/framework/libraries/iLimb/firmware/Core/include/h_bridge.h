#ifndef H_BRIDGE_H
#define H_BRIDGE_H
#include "errors.h"
#include "mbed.h"

#define MAX_HB 2
#define HB_ROTATE_CLOCKWISE 0x04
#define HB_ROTATE_ANTICLOCKWISE 0x05

ReturnCode HB_init(int index, PinName in1, PinName in2, PinName nsleep);
ReturnCode HB_coast(int index);
ReturnCode HB_reverse(int index, float speed);
ReturnCode HB_forward(int index, float speed);
ReturnCode HB_brake(int index);
ReturnCode HB_BIT(int index);
//functions created by Nipun, SINAPSE-NUS
//clockwise motion by a given angle
ReturnCode HB_ClockWise(uint16_t angle);
//anticlockwise motion by a given angle
ReturnCode HB_AntiClockWise(uint16_t angle);

#endif // H_BRIDGE_H
