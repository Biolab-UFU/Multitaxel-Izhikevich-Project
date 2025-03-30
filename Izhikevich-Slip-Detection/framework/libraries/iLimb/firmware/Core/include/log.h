#ifndef LOG_H
#define LOG_H
#include "errors.h"

typedef enum 
{
	LOG_TYPE_ERROR = 0,
	LOG_TYPE_CONFIG_CHANGE = 1,
	LOG_TYPE_END_OF_LOGS = 5
} Log_Event_t;

// User SOF_dev read/write commands to write logs to sectors controlled by data in SOFBlock data header defined above
/*
Log  = configuration changes, counter for # of tag swipes (Morph), errors, pattern rec classifier triggers, cumulative use
*/
typedef struct 
{
	time_t event_time;
	Log_Event_t event_type;
	uint8_t num_data_bytes;
	uint8_t *data;
} Log_Entry_t;

ReturnCode Log_init();
ReturnCode Log_entry(Log_Event_t event_type, uint8_t num_data_bytes, uint8_t *data);
ReturnCode Log_get_next_entry(Log_Entry_t *event);
ReturnCode Log_get_first_entry(Log_Entry_t *event);
ReturnCode Log_erase_entries();

#endif // LOG_H