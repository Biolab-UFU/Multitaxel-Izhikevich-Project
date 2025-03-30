/****************************************************************
* This file must be included in any .cpp or .h file in order to *
* use pcserial (serial output)									*
****************************************************************/

#ifndef TYPES_H
#define TYPES_H

typedef enum 
{
	DIRECT = 1,
	KEYBOARD = 2
}Running_mode_t;

typedef enum
{
	IBT = 1,
}Electrode_type_t;

typedef enum 
{
	APPROX_MEAN,
	RMS,
	MEAN
}Algorithm_t;

typedef enum
{
	LOG_NONE,
	LOG_INFO,
	LOG_CRITICAL,
	LOG_ERROR,
	LOG_DEBUG
}Log_level_t;

typedef enum 
{
	SIMPLE = 1,
	ROBOLIMB = 2,

}Hand_type_t;

#define ADS1291 0x52

extern Serial *pcserial;

#endif // TYPES_H