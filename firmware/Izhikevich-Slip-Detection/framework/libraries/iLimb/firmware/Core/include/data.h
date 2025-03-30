#ifndef DATA_H
#define DATA_H
#include "errors.h"
#include "types.h"

#define BUFF_SIZE 200

ReturnCode Data_init(int index, Running_mode_t mode);
ReturnCode Data_add_data(int index, int in_data);
ReturnCode Data_get_envelop(int index, int *envelop);

#endif // DATA_H