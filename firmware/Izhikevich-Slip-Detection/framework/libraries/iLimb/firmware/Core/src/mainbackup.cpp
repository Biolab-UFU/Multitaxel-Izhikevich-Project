#include "mbed.h"
#include "rtos.h"
#include "SOFBlock.h"
#include "config.h"
#include "errors.h"
#include "filter.h"
#include "data.h"
#include "ads1291.h"
#include "electrode.h"
#include "h_bridge.h"
#include "types.h"
#include "log.h"
#include "robocan.h"

#define VERSION_MAJOR 0.0
#define VERSION_MINOR 1.0
#define VERSION_REV 1.0
#define VERSION (((VERSION_MAJOR * 100.0) + (VERSION_MINOR * 10.0) + (VERSION_REV)) / 100.0)

//#define WRITE_NEW_CONFIG 1

#define TEMP_CLASSES 5  // Temporary number used because of size of default M&S matrices
#define PD_0 ((PinName)0x30)
#define PD_1 ((PinName)0x31)
#define PE_0 ((PinName)0x40)
#define PE_1 ((PinName)0x41)
#define PE_2 ((PinName)0x42)
#define PE_3 ((PinName)0x43)
#define PE_4 ((PinName)0x44)
#define PE_5 ((PinName)0x45)
#define PE_6 ((PinName)0x46)
#define PE_7 ((PinName)0x47)
#define PE_8 ((PinName)0x48)
#define PE_9  ((PinName)0x49) //right button
#define PE_10 ((PinName)0x4A) // left button 
#define PE_11 ((PinName)0x4B) //middle button 
#define PE_12 ((PinName)0x4C)
#define PE_13 ((PinName)0x4D)
#define PE_14 ((PinName)0x4E)
#define BIT_RETRY_MAX 1
// Running states for state machine
typedef enum
{
    Init,
    Bit,
    Config,
    Idle,
    Run,
    Error
} RunningState;

// Devices
Serial *pcserial = new Serial(PA_9, PA_10);

SPI spi_device(PA_7, PA_6, PA_5);

//armband 1 order
PinName electrode_cs[8] = 
{
	PA_12, //cs8
	PC_12, //cs3
	PC_5, //cs6
	PC_11, //cs2
	PA_0, //cs1
	PA_4, //cs4
	PA_8, //cs5
	PC_13 //cs7
	//PD_5
};

//armband 2 order 
/* PinName electrode_cs[8] = 
  {
	PA_0, //cs1
	PC_11, //cs2
	PC_12, //cs3
	PA_4, //cs4
	PA_8, //cs5
	PC_5, //cs6
	PC_13, //cs7
	PA_12 //cs8
	//PD_5
}; */

DigitalOut pwr_FM(PE_2);
DigitalOut pwr_BT(PE_1);
DigitalOut pwr_AC(PE_0);
DigitalOut pwr_CAN(PE_3);

//Serial bluetooth(PA_9, PA_10);

SPI spi_device2(PA_1, PA_11, PB_13);

// Debug LEDS
DigitalOut D_LED1(PE_4);
DigitalOut D_LED2(PE_5);
DigitalOut D_LED3(PE_6);
DigitalOut D_LED4(PE_7);
DigitalOut D_LED5(PE_8);

//Hand control switch
DigitalOut handout_sel(PC_10);

Ticker read_sensor_data_ticker;
Ticker usecond_ticker;

// Global variables
RunningState state = Config;
//RunningState state = Init;
ConfigFile confignew;

static bool process = 0;
static bool done = 0;
volatile static int useconds = 0;

//keyboard commands
bool new_cmd = 0;
char key_cmd = '0';
char last_can_grip = '0';
int current_el = 0;


// protected accessor for process signal
int get_process()
{
    bool tempprocess = 0;

    tempprocess = process;
    
    return tempprocess;
}

// protected assignment for process signal
void set_process()
{
    process = 1;
}

// protected reset for process signal
void reset_process()
{
    process = 0;
}

int data[MAX_ELECTRODES];

// interrupt fires at 1ms
// function to read sensor data and fill circular buffer
// sends a signal to process the data every 10 iterations
void read_sensor_data()
{
    ReturnCode rc = LDA_OK;
    static unsigned int counter = 0;
    if((Run == state) || (Idle == state))
    {
        for(int i = 0; i < confignew.num_electrodes; i++)
        {
            rc = Electrode_read_data(i, &data[i]);
            if(rc != LDA_OK)
            {
                Log_entry(LOG_TYPE_ERROR, sizeof(rc), (uint8_t*)&rc);
                state = Error;
            }
//            pcserial->printf("Data%d = %d\t\t%X\r\n", i, data[i], data[i]);

            Data_add_data(i, Filter_process_sensor_input(i, data[i]));
           // data[i] = Filter_process_sensor_input(i, data[i]);

        }
        // capture an integer data point for the filter method
        counter++;
        if(0 == (counter % 1))
        {
            set_process();
        }
    }
}

// protected accessor for usecond counter
int get_useconds()
{
    int temp = 0;

    temp = useconds;

    return temp;
}

// interrupt fires at 20us
// increments usecond counter by 20 each time.
void tick_usec()
{
    useconds+=20;
}

// function to put the state machine into configure
// interrupt fires when the USER button is pressed
void configure()
{
    state = Config;
}

void read_key()
{
	if(pcserial->readable())
	{
		key_cmd = pcserial->getc();
		new_cmd = 1;
		pcserial->printf("New Key CMD\r\n");
	}
}

void read_el()
{
	if(pcserial->readable())
	{
		key_cmd = pcserial->getc();
		current_el = key_cmd - '1';
		pcserial->printf("Change electrode to: %c\r\n", key_cmd);
	}
}

//Crude way for flushing serial comm
void flushSerialBuffer(Serial *s)
{
	char char1 = 0;
	while (s->readable())
	{
		char1 = s->getc();
	} 
	return; 
}

// function to intialize the hardware interrupts, IO and flash
ReturnCode initialize_hardware()
{
    ReturnCode rc = LDA_OK;

    pcserial->printf("Initializing Hardware!\r\n");
	
	//Control power to different peripheral chips on the board
	pwr_CAN.write(1);
    pwr_AC.write(0);
    pwr_BT.write(0);
    pwr_FM.write(0);

	if(confignew.running_mode == DIRECT)
	{
		reset_process();
		Filter_init();
		
		//Attach function to read sensor data to GPT
		read_sensor_data_ticker.attach(&read_sensor_data, 0.001);

		// Attach function to read sensor data to GPT
		usecond_ticker.attach(&tick_usec, 0.00002);
		
		//Attach interrupt to changing which electrode is output
		pcserial->attach(&read_el);
		
		if(LDA_OK == rc)
		{
			pcserial->printf("initializing %d electrodes\r\n", confignew.num_electrodes);
			for(int i = 0; i < confignew.num_electrodes; i++)
			{
				rc = Electrode_init(i, &spi_device, electrode_cs[i]);
				wait_ms(1);
			}
			pcserial->printf("initialized %d electrodes\r\n", confignew.num_electrodes);
		}
		
		if(LDA_OK == rc)
        {
            for(int i = 0; i < confignew.num_electrodes; i++)
            {
                pcserial->printf("Data Init\r\n");
                Data_init(i, confignew.running_mode);
            }
        }
	}

    
	if(confignew.running_mode == KEYBOARD)
	{
		set_process();
		pcserial->attach(&read_key);
		
		if(LDA_OK == rc)
		{
			//sets switch on connector to output CAN
			handout_sel.write(0);
			//initialize CAN controller 
			rc = RC_init(&spi_device2, PA_15);
	   
		}

		if(LDA_OK == rc)
		{
			//initialize top H-Bridge connector (labeled elbow)
			rc = HB_init(1, PC_8, PC_9, PB_8);   //Init HB2
		}
	}
    

	//initialize logging functions 
    if(LDA_OK == rc)
    {
        rc = Log_init();
        if(LDA_OK != rc)
            pcserial->printf("init ERROR!! %d\r\n", rc);

        char answered = 'n';
        pcserial->printf("Print Logs? (Y/N)\r\n");
    //    pcserial->scanf("%c", &answered);
        pcserial->printf("%c\r\n", answered);
        if(('y' == answered) || ('Y' == answered))
        {
            Log_Entry_t entry;
            uint8_t newdata[256];
            entry.data = newdata;

            Log_get_first_entry(&entry);
            if(entry.event_type != LOG_TYPE_END_OF_LOGS)
                pcserial->printf("%u First Entry = %d %d\r\n", entry.event_time, entry.event_type, entry.num_data_bytes);
            int i = 0;
            while(entry.event_type != LOG_TYPE_END_OF_LOGS)
            {
                for(int j = 0; j < entry.num_data_bytes; j++)
                {
                    pcserial->printf("%X\t", entry.data[j]);
                }
                pcserial->printf("\r\n");
                i++;
                rc = Log_get_next_entry(&entry);
                if(LDA_OK != rc)
                    pcserial->printf("%d read ERROR!!\r\n", rc);
                if(entry.event_type != LOG_TYPE_END_OF_LOGS)
                    pcserial->printf("%u Next Entry = %d %d\r\n", entry.event_time, entry.event_type, entry.num_data_bytes);
            }
        }
        pcserial->printf("Erase Logs? (Y/N)\r\n");
    //    pcserial->scanf("%c", &answered);
        answered = 'y';
        pcserial->printf("%c\r\n", answered);
        if(('y' == answered) || ('Y' == answered))
        {
            rc = Log_erase_entries();
            if(LDA_OK != rc)
                pcserial->printf("erase ERROR!! %d\r\n", rc);
        }
    }

    pcserial->printf("Hardware Initialized!\r\n");

    return rc;
}

// function to run built in test, currently stubbed out
ReturnCode run_bit()
{
    ReturnCode rc = LDA_OK;
    int retry = 0;
    pcserial->printf("Built In Test.\r\n");


	if(confignew.running_mode == DIRECT)
	{
		// IBT Electrodes
		if((LDA_OK == rc) && (confignew.type_electrodes == IBT))
		{
			for(int i = 0; (i < confignew.num_electrodes) && (LDA_OK == rc); i++)
			{
				rc = Electrode_BIT(i);
			}
		}
	}


	if(confignew.running_mode == KEYBOARD)
    {
		// H-Bridge
		if(LDA_OK == rc)
		{
			for(int i = 0; (i < MAX_HB) && (LDA_OK == rc); i++)
			{
				//rc = HB_BIT(i);  // should rotate wrist both directions for short time
			}
		}

		// RoboCAN Hand
		if(LDA_OK == rc)
		{
			rc = RC_BIT();  // should fully open and fully close hand in both current grip
		}
	}

    if(LDA_OK == rc)
    {
        pcserial->printf("Passed.\r\n");
    }

    return rc;
}


// main loop
int main() 
{
    D_LED1.write(1);
//    FM_power.write(0);
    pcserial = new Serial(PA_9, PA_10);
    int i = 1;
    int agcounter = 1;
    int *inputdata = NULL;
    ReturnCode rc = LDA_OK;

    // Set UART baud rate
    pcserial->baud(115200);

    pcserial->printf("Version = %f\r\n", VERSION);


    while(!done) 
    { 
        switch(state)
        {
            case Init:
                // Initialize any IO
                rc = initialize_hardware();

                if(LDA_OK == rc)
                {
                    pcserial->printf("Init Complete!\r\n");
                    state = Bit;
					D_LED3.write(1);
                }
                else
                {
                    state = Error;
                }
                break;
            
            case Bit:
                // Test anything we can
                rc = run_bit();
                if(LDA_OK == rc)
                {
                    state = Idle;
					D_LED4.write(1);					
										
                }
                else
                {
                    state = Error;
                }
                break;
            
            case Idle:
                // Wait for IO to become steady state
                pcserial->printf("Waiting for a few seconds.\r\n", i++);
                wait(1);
                state = Run;
                break;
            
            case Config:
                {
                    char answer = 'n';
                    // Read configuration and apply
                    pcserial->printf("Reading Config...\r\n", i++);
                    // Initialize the flash for configuration settings
                    rc = Config_init();
#ifdef WRITE_NEW_CONFIG
                    rc = Config_update_config();
#endif
                    rc = Config_get_configuration(&confignew);
                    pcserial->printf("New Configuration? (Y/N)\r\n");
                    pcserial->scanf("%c", &answer);
                    //pcserial->printf("%c\r\n", answer); //in order to use last configuration automatically, uncomment this line and comment out the one above

                    if(('y' == answer) || ('Y' == answer))
                    {
                        // Config Menu for Testing
                        pcserial->printf("Select Mode:\r\n");
                        pcserial->printf("1. Direct\r\n");
						pcserial->printf("2. Keyboard control\r\n");
                        pcserial->scanf("%d", &confignew.running_mode);
                        //pcserial->printf("%d\r\n", confignew.running_mode);

                        confignew.type_electrodes = IBT;


                        switch(confignew.running_mode)
                        {
                            case 1:
								confignew.num_electrodes = 8;
								key_cmd = 'a'; //sets default serial output to stream all 8 electrodes at the same time.
								pcserial->printf("Configured Direct Mode!\r\n");
                                break;
								
							case 2:
								pcserial->printf("Configured Keyboard Mode!\r\n");
								break;

                            default:
                                pcserial->printf("Not an available Run Mode \r\n");
								// Error!
                                break;
                        }
                        rc = Config_set_configuration(&confignew);

                        Log_entry(LOG_TYPE_CONFIG_CHANGE, sizeof(confignew), (uint8_t*)&confignew);
                    }
                    state = Init;
					D_LED2.write(1);

                }
                break;
            
            case Run:
                // Execute realtime running code
				D_LED5.write(1);
                if(get_process())
                {
                    switch(confignew.running_mode)
                    {                    	                    	
                        default:
                        case DIRECT:
                            agcounter++;
                            reset_process();
                            if(0 == (agcounter % 1))
                            {
								switch(key_cmd)
                                {                                	
									//outputs all electrodes at the same time as integers
									default:
									case 'a':
									for(int i = 0; i < confignew.num_electrodes; i++)
									{
										int envelop = 0;

										rc = Data_get_envelop(i, &envelop);
									
									
										// Debug ouput!
										if(0 == (agcounter % 10))
										{
											pcserial->printf("%9d\t", (int)(envelop));
										}
									
										if(LDA_OK != rc)
										{
											state = Error;
										}
									}
									if(0 == (agcounter % 10))
										pcserial->printf("\r\n");
									break;
									
									//if keys 1-8 are hit, the system will only output data for that electrode in a method compatible with the C# Signal Viewer 
									//(Protocol: #, High Data Byte, Middle Data Byte, Low Data Byte, $)
									case '1':
									case '2':
									case '3':
									case '4':
									case '5':
									case '6':
									case '7':
									case '8':
									int envelop = 0;
									rc = Data_get_envelop(current_el, &envelop);
									int data_hi = envelop>>16;
									int data_mid = envelop>>8;
									int data_low = envelop;
									
									pcserial->putc(35);
									pcserial->putc(data_hi);
									pcserial->putc(data_mid);
									pcserial->putc(data_low);
									pcserial->putc(36);
									break;

								}
                            }
                            break;
							
						case KEYBOARD:
							//to declare: last_grip,  flag for hand (hand_ctrl), flag for wrist (wrist_ctrl)
							//flushSerialBuffer(pcserial);
							//pcserial->printf("flushing!\r\n");
							if(new_cmd)
							{								
								pcserial->printf("newcmd\r\n");
								pcserial->printf("%c\r\n",key_cmd);								

								switch (key_cmd)
								{	
									HB_brake(1);
									RC_stop_hand();
									case 's':
										HB_brake(1);
										RC_stop_hand();
										new_cmd = 0;
										pcserial->printf("stop\r\n");
										break;
									
									case '0':
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_NORMAL);
											pcserial->printf("normal\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("normal\r\n");
										break;
									
									case '1':
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_STD_PRECISION_PINCH_CLOSED);
											pcserial->printf("std pinch closed\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("std pinch closed\r\n");
										break;
									
									case '2': 
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_STD_3JAW_CHUCK_CLOSED);
											pcserial->printf("std tripod closed\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("std tripod closed\r\n");
										break;
									
									case '3': 
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_THUMB_PARK_CONTINUOUS);
											pcserial->printf("thumb park continuous\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("thumb park continuous\r\n");
										break;
									
									case '5': 
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_LATERAL);
											pcserial->printf("lateral\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("lateral\r\n");
										break;
										
									case '6': 
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_INDEX_POINT);
											pcserial->printf("index\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("index\r\n");
										break;
										
									case '7': 
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_STD_PRECISION_PINCH_OPENED);
											pcserial->printf("std pinch open\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("std pinch open\r\n");
										break;
										
									case '9': 
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_THUMB_PRECISION_PINCH_CLOSED);
											pcserial->printf("thumb pinch closed\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("thumb pinch closed\r\n");
										break;
										
									case 'a': 
										//HB_brake(1);
										//RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											wait_ms(40);
											RC_send_grip_command(ROBO_GRIP_THUMB_PRECISION_PINCH_OPENED);
											wait_ms(40);
											pcserial->printf("thumb pinch open\r\n");
										} 
										new_cmd = 0;
										//pcserial->printf("thumb pinch open\r\n");
										break;
										
									case 'b': 
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_THUMB_3JAW_CHUCK_CLOSED);
											pcserial->printf("thumb tripod closed\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("thumb tripod closed\r\n");
										break;
										
									case 'd': 
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_STD_3JAW_CHUCK_OPENED);
											pcserial->printf("std tripod open\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("std tripod open\r\n");
										break;
										
									case 'e': 
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_THUMB_3JAW_CHUCK_OPENED);
											pcserial->printf("thumb tripod open\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("thumb tripod open\r\n");
										break;
										
									case 'f': 
										HB_brake(1);
										RC_stop_hand();
										if (last_can_grip == key_cmd)
										{
											//do nothing
										}
										else
										{
											last_can_grip = key_cmd;
											RC_send_grip_command(ROBO_GRIP_DONNING);
											pcserial->printf("donning\r\n");
										} 
										new_cmd = 0;
										pcserial->printf("donning\r\n");
										break;
										
									case 'o': //open all fingers
										
										HB_brake(1);
										RC_stop_hand();
										wait_ms(10);
										RC_open_hand();
										new_cmd = 0;
										pcserial->printf("open\r\n");
										break;
										
									case 'c': //close all fingers
										HB_brake(1);
										RC_close_hand();
										new_cmd = 0;
										pcserial->printf("close\r\n");
										break;
										
									case 't':
										//thumb
										HB_brake(1);
										RC_move_finger(0);
										new_cmd = 0;
										break;
										
									case 'i':
										//index
										HB_brake(1);
										RC_move_finger(1);
										new_cmd = 0;
										break;
										
									case 'm':
										//middle
										HB_brake(1);
										RC_move_finger(2);
										new_cmd = 0;
										break;
										
									case 'r':
										//ring
										HB_brake(1);
										RC_move_finger(3);
										new_cmd = 0;
										break;
										
									case 'p':
										//pinky
										HB_brake(1);
										RC_move_finger(4);
										new_cmd = 0;
										break;
										
									case 'w':
										//rotator
										HB_brake(1);
										RC_move_finger(5);
										new_cmd = 0;
										break;
										
									case 'x':
										//brake wrist
										HB_brake(1);
										pcserial->printf("wrist brake");
										new_cmd = 0;
										break;
										
									case 'y':
										//pronate
										RC_stop_hand();
										HB_reverse(1,1);
										pcserial->printf("wrist reverse");
										new_cmd = 0;
										break;
										
									case 'z':
										//supinate
										RC_stop_hand();
										HB_forward(1,1);
										pcserial->printf("wrist forward");
										new_cmd = 0;
										break;
										
									case 'j':
										HB_brake(1);
										RC_stop_hand();
										wait_ms(1);
										RC_move_finger_pwm(5,80);
										wait_ms(1);
										RC_move_finger_pwm(1,80);
										new_cmd = 0;
										break;
										
									case 'k':
										//HB_brake(1);
										//RC_stop_hand();
										//wait_ms(1);
										RC_increase_torque(1);
										wait_ms(1);
										new_cmd = 0;
										break;
										
																			
									case 'l':
										HB_brake(1);
										RC_stop_hand();
										wait_ms(1);
										RC_move_finger_pwm(5,297);
										wait_ms(1500);
										RC_stop_digit(5);
										wait_ms(1);
										RC_move_finger_pwm(0,297);
										//wait_ms(1);
										RC_move_finger_pwm(1,297);
										wait_ms(900);
										RC_stop_digit(1);
										//wait_ms(1);
										new_cmd = 0;
										break;
										
									case 'n':
										HB_brake(1);
										RC_stop_hand();
										wait_ms(1);
										RC_move_finger_pwm_dir(1,1,297);
										wait_ms(500);
										RC_move_finger_pwm_dir(1,1,40);
										new_cmd = 0;
										break;
										
									case 'g':
										HB_brake(1);
										RC_stop_hand();
										wait_ms(1);
										RC_move_finger_pwm_dir(5,1,297);
										wait_ms(900);
										RC_stop_digit(5);
										wait_ms(1);
										RC_move_finger_pwm_dir(1,1,90);
										RC_move_finger_pwm_dir(2,1,90);
										RC_move_finger_pwm_dir(3,1,90);
										wait_ms(1);
										RC_move_finger_pwm_dir(4,1,90);
										wait_ms(100);
										RC_move_finger_pwm_dir(0,1,90);
										new_cmd = 0;
										break;
										
									default:
										new_cmd = 0;
										pcserial->printf("default\r\n");
										break;
								}
							}
								
							break;

                    }
                }
                break;
            
            default:
            case Error:
				D_LED1.write(0);
				D_LED2.write(0);
				D_LED3.write(0);
				D_LED4.write(0);
				D_LED5.write(0);
                // Capture errors
                pcserial->printf("ERROR!!! %d\r\n", rc);
                if(LDA_OK != rc)
                {
                    Log_entry(LOG_TYPE_ERROR, sizeof(rc), (uint8_t*)&rc);
                }
                wait(10);
                state = Bit;
                break;
        }
    }
}
 