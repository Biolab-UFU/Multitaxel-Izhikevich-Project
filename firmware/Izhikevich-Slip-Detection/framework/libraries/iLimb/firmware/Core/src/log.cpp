/***************************************************************************************************
* This file is used to log information to the on board flash memory when there are event triggers. *
* More event triggers can be added to the code; currently, only the ERROR event trigger is used.   *
* When the trigger happens, the log saves the event type, the number of data bytes and the data.   *
* Modify log.h and main to record other logs to fit needs										   *
* 																								   *
* December 4, 2015																				   *
***************************************************************************************************/

#include "mbed.h"
#include "log.h"
#include "SOFBlock.h"
#include "stm32f4xx_hal_flash.h"

#define LOG_SECTOR1 7
#define LOG_SECTOR2 5
#define LOG_HEADER_SECTOR 4

// Use SOFBlock as data header keeping track of how many log entries, which sector is in use, if the other sector is full
typedef struct 
{
	uint32_t log_address;
	uint8_t sector_in_use;
	uint8_t sectors_full;
} Log_Header_t;

Log_Header_t log_header;

// Data
static SOFWriter writer;
static SOFReader reader;

static uint32_t log_reader_address = 0;
static uint32_t log_reader_sector = 0;

ReturnCode update_log_header();
ReturnCode erase_log_header();
ReturnCode read_log_header();

ReturnCode update_log_header()
{
    ReturnCode rc = LDA_OK;
    SOF_Error_t sof_rc = kSOF_ErrNone;
    SOF_Statics_t stats;
    uint32_t bytes_written = 0;

    // Make sure theres enough room to make another entry into the log header
    if(SOFBlock::get_stat(LOG_HEADER_SECTOR, stats) && (stats.free_size >= sizeof(Log_Header_t)))
    {
	    sof_rc = writer.open(LOG_HEADER_SECTOR);
	    if(kSOF_ErrNone == sof_rc)
	    {
	        bytes_written = writer.write_data((uint8_t*)&log_header, sizeof(Log_Header_t));
		    if(bytes_written != sizeof(Log_Header_t))
		    {    
		    	rc = LDA_FLASH_WRITE_ERROR;
		    }
	    	writer.close();
	    }
	    else
	    {
	        rc = LDA_FLASH_WRITE_ERROR;
	    }
	}
	else
	{
        rc = erase_log_header();
        if(LDA_OK == rc)
        {
	        rc = update_log_header();		
	    }
	}

    return rc;
}

ReturnCode erase_log_header()
{
    ReturnCode rc = LDA_OK;

    if(!SOFBlock::format(LOG_HEADER_SECTOR))
    {
        rc = LDA_FLASH_ERASE_ERROR;
    }

    return rc;
}


ReturnCode read_log_header()
{
    ReturnCode rc = LDA_OK;
    SOF_Error_t sof_rc = kSOF_ErrNone;
    int bytes_read = 0;

    sof_rc = reader.open(LOG_HEADER_SECTOR);
    if(kSOF_ErrNone == sof_rc)
    {
    	bytes_read = reader.read_data((uint8_t*)&log_header, sizeof(Log_Header_t));
	    if(bytes_read != sizeof(log_header))
	    {    
	    	rc = LDA_FLASH_READ_ERROR;
	    }
    	reader.close();
    }
    else
    {
        rc = erase_log_header();
        log_header.sectors_full = 0;
        log_header.sector_in_use = LOG_SECTOR1;
		const SOF_SectorSpec_t *spec = SOF_dev_info_by_index(log_header.sector_in_use);
        log_header.log_address = 0;
    }

    return rc;
}

ReturnCode Log_init()
{
    ReturnCode rc = LDA_OK;
    SOF_Statics_t statics;

    if (!SOFBlock::get_stat(LOG_HEADER_SECTOR, statics))
    { 
        log_header.sectors_full = 0;
        log_header.sector_in_use = LOG_SECTOR1;
		const SOF_SectorSpec_t *spec = SOF_dev_info_by_index(log_header.sector_in_use);
        log_header.log_address = 0;
    }
    else
    {
    	rc = read_log_header();
    }

    return rc;
}

ReturnCode Log_entry(Log_Event_t event_type, uint8_t num_data_bytes, uint8_t *data)
{
	ReturnCode rc = LDA_OK;
	SOF_DevHandle_t handle = 0;
	const SOF_SectorSpec_t *spec = SOF_dev_info_by_index(log_header.sector_in_use);
	Log_Entry_t log_entry;
	uint32_t bytes_written = 0;

	log_entry.event_time = time(NULL);
	log_entry.event_type = event_type;
	log_entry.num_data_bytes = num_data_bytes;
	if(num_data_bytes > 0)
	{
		log_entry.data = (uint8_t*)malloc(log_entry.num_data_bytes*sizeof(uint8_t));
		for(uint8_t i = 0; i < num_data_bytes; i++)
		{
			log_entry.data[i] = data[i];
		}
	}

	if(SOF_dev_is_valid_sector(log_header.sector_in_use))
	{
		handle = SOF_dev_open(log_header.sector_in_use);
		if(0 != handle)
		{
			uint32_t offset_addr = log_header.log_address;
			if(offset_addr < (spec->sec_size - (sizeof(Log_Entry_t) + 256)))
			{
				uint8_t *ptr = (uint8_t*)&(log_entry.event_time);
				for(uint8_t i = 0; i < sizeof(time_t); i++)
				{
					bytes_written = SOF_dev_write_byte(handle, (offset_addr + i), ptr[i]);
					if(bytes_written != 0)
					{
						rc = LDA_FLASH_WRITE_ERROR;
					}
				}
				offset_addr = offset_addr + sizeof(time_t);
				ptr = (uint8_t*)&(log_entry.event_type);
				for(uint8_t i = 0; i < sizeof(Log_Event_t); i++)
				{
					bytes_written = SOF_dev_write_byte(handle, (offset_addr + i), ptr[i]);
					if(bytes_written != 0)
					{
						rc = LDA_FLASH_WRITE_ERROR;
					}
				}
				offset_addr = offset_addr + sizeof(Log_Event_t);
				ptr = (uint8_t*)&(log_entry.num_data_bytes);
				for(uint8_t i = 0; i < sizeof(log_entry.num_data_bytes); i++)
				{
					bytes_written = SOF_dev_write_byte(handle, (offset_addr + i), ptr[i]);
					if(bytes_written != 0)
					{
						rc = LDA_FLASH_WRITE_ERROR;
					}
				}
				if(log_entry.num_data_bytes > 0)
				{
					offset_addr = offset_addr + sizeof(log_entry.num_data_bytes);
					ptr = (uint8_t*)&(log_entry.data);
					for(uint8_t i = 0; i < log_entry.num_data_bytes; i++)
					{
						bytes_written = SOF_dev_write_byte(handle, (offset_addr + i), ptr[i]);
						if(bytes_written != 0)
						{
							rc = LDA_FLASH_WRITE_ERROR;
						}
					}
					log_header.log_address = offset_addr + log_entry.num_data_bytes;
				}
				else
				{
					log_header.log_address = offset_addr + sizeof(log_entry.num_data_bytes);
				}
				SOF_dev_close(handle);
				if(LDA_OK == rc)
				{
					rc = update_log_header();
				}
			}
			else
			{
				log_header.sector_in_use = (log_header.sector_in_use == LOG_SECTOR1) ? LOG_SECTOR2 : LOG_SECTOR1;
				SOF_dev_erase(log_header.sector_in_use);
				log_header.sectors_full = 1;
				const SOF_SectorSpec_t *tspec = SOF_dev_info_by_index(log_header.sector_in_use);
		        log_header.log_address = 0;
				rc = Log_entry(event_type, num_data_bytes, data);
			}
		}
		else
		{
			rc = LDA_FLASH_WRITE_ERROR;
		}
	}
	else
	{
		rc = LDA_FLASH_WRITE_ERROR;
	}

	free(log_entry.data);

	return rc;
}

ReturnCode Log_get_next_entry(Log_Entry_t *event)
{
	ReturnCode rc = LDA_OK;
	uint8_t *outptr = (uint8_t*)&(event->event_time);
	uint32_t offset_addr = log_reader_address;
	SOF_DevHandle_t handle = 0;
	const SOF_SectorSpec_t *spec = SOF_dev_info_by_index(log_reader_sector);

	if(log_reader_address >= (spec->sec_size - (sizeof(Log_Event_t) + 256)))
	{
		log_reader_sector = (log_reader_sector == LOG_SECTOR1) ? LOG_SECTOR2 : LOG_SECTOR1;
		log_reader_address = 0;
		offset_addr = log_reader_address;
	}

	if((log_reader_sector == log_header.sector_in_use) &&
		(log_reader_address >= log_header.log_address))
	{
		event->event_type = LOG_TYPE_END_OF_LOGS;
	}
	else
	{
		if(SOF_dev_is_valid_sector(log_reader_sector))
		{
			handle = SOF_dev_open(log_reader_sector);
			if(0 != handle)
			{
				for(uint8_t i = 0; i < sizeof(time_t); i++)
				{
					outptr[i] = SOF_dev_read_byte(handle, (offset_addr++));
				}
				outptr = (uint8_t*)&(event->event_type);
				for(uint8_t i = 0; i < sizeof(Log_Event_t); i++)
				{
					outptr[i] = SOF_dev_read_byte(handle, (offset_addr++));
				}
				outptr = (uint8_t*)&(event->num_data_bytes);
				for(uint8_t i = 0; i < sizeof(event->num_data_bytes); i++)
				{
					outptr[i] = SOF_dev_read_byte(handle, (offset_addr++));
				}
				if(event->num_data_bytes > 0)
				{
					if(NULL != event->data)
					{
						outptr = (uint8_t*)&(event->data);
						for(uint8_t i = 0; i < event->num_data_bytes; i++)
						{
							outptr[i] = SOF_dev_read_byte(handle, (offset_addr++));
						}
						log_reader_address = offset_addr;
					}
					else
					{
						log_reader_address = offset_addr + event->num_data_bytes;
						rc = LDA_ERROR_NULL_PTR;
					}
				}
				else
				{
					log_reader_address = offset_addr;
				}
			}
			else
			{
				rc = LDA_FLASH_READ_ERROR;
			}
		}
		else
		{
			rc = LDA_FLASH_READ_ERROR;
		}
	}

	return rc;
}

ReturnCode Log_get_first_entry(Log_Entry_t *event)
{
	ReturnCode rc = LDA_OK;
	uint8_t *offset_addr = NULL;

	if(log_header.sectors_full > 0)
	{
		log_reader_sector = (log_header.sector_in_use == LOG_SECTOR1) ? LOG_SECTOR2 : LOG_SECTOR1;
	}
	else
	{
		log_reader_sector = log_header.sector_in_use;
	}

	log_reader_address = 0;

	Log_get_next_entry(event);

	return rc;
}

ReturnCode Log_erase_entries()
{
	ReturnCode rc = LDA_OK;

	rc = erase_log_header();
	if(LDA_OK == rc)
	{
	    log_header.sectors_full = 0;
	    log_header.sector_in_use = LOG_SECTOR1;
		const SOF_SectorSpec_t *spec = SOF_dev_info_by_index(log_header.sector_in_use);
	    log_header.log_address = 0;
	    rc = update_log_header();

	    if(LDA_OK == rc)
	    {
			if(!SOFBlock::format(LOG_SECTOR1))
		    {
		        rc = LDA_FLASH_ERASE_ERROR;
		    }

		    if(!SOFBlock::format(LOG_SECTOR2))
		    {
		        rc = LDA_FLASH_ERASE_ERROR;
		    }
		}
	}

	return rc;
}



