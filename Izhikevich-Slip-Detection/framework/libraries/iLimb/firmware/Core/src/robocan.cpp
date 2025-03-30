/******************************************************************************
* This file contains functions to control the robolimb CAN hand. Currently,   *
* only functions to send information to the hand (TX) are working. The 		  *
* functions to receive data back (RX) are not. A firmware update will include *
* this functionality. Functions that are not useable are commented below, and *
* will be useable after firmware update.									  *
*																			  *
* December 4, 2015															  *
******************************************************************************/
/*
finger position control algorithm described by the end of this source file
*/

#include "robocan.h"
#include "MCP2515.h"
#include "CircularBuffer.h"
#include "types.h"
#define BAUDRATE 1000
#define COMMAND_LENGTH 4
#define GRIP_COMMAND 0x301
#define DIGIT_COMMAND 0x100
#define GET_GRIP_COMMAND 0x302
#define GET_SERIAL_NUMBER_COMMAND 0x402
#define READ_0 0x80
#define READ_1 0x40


InterruptIn read_can(PB_0);    // CAN RX interrupt pin, to be tested


MCP2515 *robocan = NULL;
typedef struct
{
	uint8_t length;
	uint8_t data[8];
	uint16_t id;
} RoboMessage_t;

uint8_t readRequestReceived = 0;
uint32_t dataReceived = 0xFFFFFFFF;
uint32_t ROBOStatus[6] = {0xFFFFFFFF};

// shows the active fingers for each grip, in order specified in "grip_translate"
// 0 = inactive, 1 = active
// Finger indicators are in the order Thumb, Index, Middle, Ring, Little, Th Rotator (left to right)
bool active_finger[NUM_RC_GRIPS][6] =
{
	{1,1,1,1,1,1},
	{1,1,0,0,0,1},
	{1,1,1,0,0,1},
	{1,0,0,0,0,1},
	{1,0,0,0,0,1},
	{0,1,0,0,0,1},
	{1,1,0,0,0,1},
	{0,1,0,0,0,0},
	{0,1,0,0,0,0},
	{0,1,1,0,0,0},
	{1,1,1,0,0,1},
	{0,1,1,0,0,0},
	{0,0,0,0,0,0}
};

 ROBO_GRIP grip_translate[NUM_RC_GRIPS] =
{
	ROBO_GRIP_NORMAL,
	ROBO_GRIP_STD_PRECISION_PINCH_CLOSED,
	ROBO_GRIP_STD_3JAW_CHUCK_CLOSED,
	ROBO_GRIP_THUMB_PARK_CONTINUOUS,
	ROBO_GRIP_LATERAL,
	ROBO_GRIP_INDEX_POINT,
	ROBO_GRIP_STD_PRECISION_PINCH_OPENED,
	ROBO_GRIP_THUMB_PRECISION_PINCH_CLOSED,
	ROBO_GRIP_THUMB_PRECISION_PINCH_OPENED,
	ROBO_GRIP_THUMB_3JAW_CHUCK_CLOSED,
	ROBO_GRIP_STD_3JAW_CHUCK_OPENED,
	ROBO_GRIP_THUMB_3JAW_CHUCK_OPENED,
	ROBO_GRIP_DONNING
};

//loop counters
int ctr = 0;
int grip_ctr = 0;

ROBO_DIGIT allDigits[6] = {ROBO_THUMB, ROBO_INDEX, ROBO_MIDDLE, ROBO_RING, ROBO_LITTLE, ROBO_ROTATOR};
ROBO_DIGIT ctrl_digit;
ROBO_GRIP check_grip;
bool finger_dir[6] = {0,0,0,0,0,0}; // specifies the last direction the finger was moving, 0 = open, 1 = close
uint16_t finger_pos[6] = {0,0,0,0,0,0}; // specifies the current position of the finger
uint16_t finger_times[6] = {0,0,0,0,0,0}; // specifies the time to wait until finger gets into position
uint16_t finger_period[6] = {2,2,2,2,2,2}; // specifies the period of each finger
//vector with max positions
uint16_t RC_maxFingerPositions[6] = {500,500,500,500,500,750};
uint32_t finger_timer[6] = {0,0,0,0,0,0};
uint8_t finger_state[6] = {0,0,0,0,0,0};

// RX command to decode new messages: NOT USED CURRENTLY 4 DEC 2015
void RC_decode_messages(RoboMessage_t *message)
{
    //decode reply
	if (message->id > 0x200 && message->id < 0x207)
	{
	    ROBOStatus[(message->id - 1)&0x0FF] = message->data[2];
	}
	else if (message->id == 0x303 || message->id == 0x403) //Grip number request - Serial Number
	{
	    dataReceived = message->data[2];
	    readRequestReceived = 1;
	}
}

// RX command to receive new messages upon interrupt pin activation: NOT USED CURRENTLY 4 DEC 2015
void RC_service_interrupt()
{
	RoboMessage_t message_received;

	//(readStatus() & 0x80) == 0x80 means frame in buffer 0
	//(readStatus() & 0x40) == 0x40 means frame in buffer 1
	pcserial->printf("interrupt pin");
	uint8_t status = robocan->readStatus();
	uint8_t test_val;
	if(status & READ_0)
	{
		robocan->readDATA_ff_0(&(message_received.length), message_received.data, &(message_received.id));
		RC_decode_messages(&message_received);
		//robocan->bitModify(0x2C, 0x01, 0x00);
		//wait_ms(10);
	}

	if(status & READ_1)
	{
		robocan->readDATA_ff_1(&(message_received.length), message_received.data, &(message_received.id));
		RC_decode_messages(&message_received);

		//robocan->bitModify(0x2C, 0x02, 0x00);
		//wait_ms(10);
	}
	/* robocan->readRegister(0x2C, &test_val);

	wait_ms(500);

		robocan->writeRegister(0x2C, 0x00);
		wait_ms(500);

		robocan->readRegister(0x2C, &test_val); */
}

ReturnCode RC_init(SPI *can_spi, PinName cs)
{
	ReturnCode rc = LDA_OK;
	robocan = new MCP2515(*can_spi, cs);

	robocan->baudConfig(BAUDRATE);
	robocan->setMode(NORMAL);

    // Set MCP2515 interrupt to call RC function to service it
    //read_can.fall(&RC_service_interrupt);

	return rc;
}

ReturnCode RC_send_grip_command(ROBO_GRIP grip)
{
	ReturnCode rc = LDA_OK;
	uint8_t data[4] = {0x00, 0x00, 0x00, grip};

	robocan->load_ff_0(COMMAND_LENGTH, GRIP_COMMAND, data);
	robocan->send_0();
	wait_ms(10);

	return rc;
}

ReturnCode RC_send_digit_command(ROBO_DIGIT digit, ROBO_DIGIT_COMMAND cmd, int pwm)
{
	ReturnCode rc = LDA_OK;
	uint8_t pwm1 = ((pwm >> 8) & 0xff);
	uint8_t pwm2 = (pwm & 0xff);
	uint8_t data[4] = {0x00, cmd, pwm1, pwm2};

	if((pwm > 10) || (pwm <= 150))
	{
		robocan->load_ff_1(COMMAND_LENGTH, (digit | DIGIT_COMMAND), data);
		robocan->send_1();
	}
	else
	{
		rc = LDA_BOUNDS_ERROR;
	}
	return rc;
}

// RX command to get status of specified finger: NOT USED CURRENTLY 4 DEC 2015
ReturnCode RC_get_status(ROBO_STATUS *status, ROBO_DIGIT digit)
{
	ReturnCode rc = LDA_OK;

    uint8_t* statusBytes;
    int statusInt;

    statusInt = ROBOStatus[digit - 1];
    statusBytes = (uint8_t*)(&statusInt);

    status->digitStatus = (ROBO_DIGIT_STATUS)statusBytes[1];        //low byte of high word
    status->rotatorStatus = (ROBO_ROTATOR_STATUS)statusBytes[0];      //high byte of high word
    status->motorCurrent = ((statusInt >> 12) | (statusInt >> 28)) & 0xFFF;      //low word, 12 bits left aligned


	return rc;
}

// RX command to get current hand grip: NOT USED CURRENTLY 4 DEC 2015
ReturnCode RC_get_current_grip(ROBO_GRIP *grip)
{
	ReturnCode rc = LDA_OK;
	uint32_t waiter = 0;
	uint8_t data[4] = {0x00, 0x00, 0x00, 0x00};

	robocan->load_ff_2(COMMAND_LENGTH, GET_GRIP_COMMAND, data);
	robocan->send_2();

	while(!readRequestReceived && (waiter < 0xFFFF))
	{
		waiter++;
	}
	if(0xFFFF <= waiter)
	{
		rc = LDA_ERROR;	// TODO: define real error
	}
	else
	{
		readRequestReceived = 0;
		*grip = (ROBO_GRIP)dataReceived;
	}

	return rc;
}

// RX command to get serial number of hand: NOT USED CURRENTLY 4 DEC 2015
ReturnCode RC_get_serial_number(char* serial_number)
{
	ReturnCode rc = LDA_OK;
	uint32_t waiter = 0;
	uint32_t val = 0;
	uint8_t data[4] = {0x00, 0x00, 0x00, 0x00};

	robocan->load_ff_2(COMMAND_LENGTH, GET_SERIAL_NUMBER_COMMAND, data);
	robocan->send_2();

	while(!readRequestReceived && (waiter < 0xFFFF))
	{
		waiter++;
	}
	if(0xFFFF <= waiter)
	{
		rc = LDA_ERROR;	// TODO: define real error
	}
	else
	{
		readRequestReceived = 0;

	    serial_number[0] = (char)(dataReceived & 0xFF);
	    serial_number[1] = (char)((dataReceived >> 8) & 0xFF);

	    val = sprintf(serial_number+2, "%d", (int)(((dataReceived>>8)&0xFF00)|((dataReceived>>24)&0xFF)) );
	    if(0 == val)
	    {
	    	rc = LDA_ERROR; // TODO: define real error
	    }
	}

	return rc;
}

// Check to make sure hand turned on/CAN initialized correctly, all fingers open and close in current grip
ReturnCode RC_BIT()
{
	ReturnCode rc = LDA_OK;
    char serial_number[2] = {0};



  /*
  uint8_t test_val;
  robocan->readRegister(0x2B, &test_val);
   pcserial->printf("%d", test_val);

   wait_ms(500);

   robocan->writeRegister(0x2B, 0x03);
   wait_ms(500);

   robocan->readRegister(0x2B, &test_val);
   pcserial->printf("%d", test_val);
   */

	 for (ctr=0;ctr<6;ctr++)
	{
		ctrl_digit = allDigits[ctr];
		if(active_finger[grip_ctr][ctr]){
			RC_send_digit_command(ctrl_digit, ROBO_OPEN, 150);
			wait_ms(10);
		}
	}

	wait_ms(3000);

	for (ctr=0;ctr<6;ctr++)
	{
		ctrl_digit = allDigits[ctr];
		if(active_finger[grip_ctr][ctr]){
			RC_send_digit_command(ctrl_digit, ROBO_CLOSE, 150);
			wait_ms(10);
		}
	}

    return rc;
}

//Methods added by Megan Hodgson, 11/20/15

// Stop all fingers
ReturnCode RC_stop_hand()
{
	ReturnCode rc = LDA_OK;
	for (ctr=0;ctr<6;ctr++)
	{
		ctrl_digit = allDigits[ctr];
		RC_send_digit_command(ctrl_digit, ROBO_STOP, 150);
		wait_ms(10);
	}

	return rc;
}

// Open all fingers (only opens fingers that are active in current grip)
ReturnCode RC_open_hand()
{
	ReturnCode rc = LDA_OK;

	for (ctr=0;ctr<6;ctr++)
	{
		ctrl_digit = allDigits[ctr];
		RC_send_digit_command(ctrl_digit, ROBO_OPEN, 150);
		finger_dir[ctr] = 0;
		wait_ms(10);
	}

	return rc;
}

// Close all fingers (only closes fingers that are active in current grip)
ReturnCode RC_close_hand()
{
	ReturnCode rc = LDA_OK;

	for (ctr=0;ctr<6;ctr++)
	{
		ctrl_digit = allDigits[ctr];
		RC_send_digit_command(ctrl_digit, ROBO_CLOSE, 150);
		finger_dir[ctr] = 1;
		wait_ms(10);
	}
	return rc;
}

// Moves individual digit in direction opposite to last moved direction
ReturnCode RC_move_finger(int fing)
{
	ReturnCode rc = LDA_OK;

	ctrl_digit = allDigits[fing];
	if(finger_dir[fing])
	{
		RC_send_digit_command(ctrl_digit, ROBO_OPEN, 80);
		finger_dir[fing] = 0;
	}
	else
	{
		RC_send_digit_command(ctrl_digit, ROBO_CLOSE, 80);
		finger_dir[fing] = 1;
	}

	//debugging
	//pcserial->printf("motors on\r\n");
	wait_ms(100);
	return rc;
}

// Moves individual digit in direction opposite to last moved direction
ReturnCode RC_move_finger_pwm(int fing, int pwm)
{
	ReturnCode rc = LDA_OK;
	if(pwm >= 10 && pwm <= 297)
	{
		ctrl_digit = allDigits[fing];
		if(finger_dir[fing])
		{
			RC_send_digit_command(ctrl_digit, ROBO_OPEN, pwm);
			finger_dir[fing] = 0;
		}
		else
		{
			RC_send_digit_command(ctrl_digit, ROBO_CLOSE, pwm);
			finger_dir[fing] = 1;
		}
	}

	pcserial->printf("motors on\r\n");
	wait_ms(1);
	return rc;
}

ReturnCode RC_move_finger_pwm_dir(int fing, int dir, int pwm)
{
	ReturnCode rc = LDA_OK;
	ctrl_digit = allDigits[fing];
	if(pwm >= 10 && pwm <= 297)
	{
		if(dir == 0)
		{
			RC_send_digit_command(ctrl_digit, ROBO_STOP, pwm);
		}
		else if(dir == 1)
		{
			RC_send_digit_command(ctrl_digit, ROBO_CLOSE, pwm);
		}
		else if(dir == 2)
		{
			RC_send_digit_command(ctrl_digit, ROBO_OPEN, pwm);
		}
	}
	finger_pos[fing] = 0;
	wait_ms(1);
	return rc;
}

// Moves individual digit in direction opposite to last moved direction
ReturnCode RC_increase_torque(int fing)
{
	ReturnCode rc = LDA_OK;

	ctrl_digit = allDigits[fing];
	if(finger_dir[fing])
	{
		RC_send_digit_command(ctrl_digit, ROBO_CLOSE, 297);
	}
	pcserial->printf("torque on\r\n");
	wait_ms(100);
	return rc;
}

ReturnCode RC_stop_digit(int fing)
{
	ReturnCode rc = LDA_OK;
	ctrl_digit = allDigits[fing];
	RC_send_digit_command(ctrl_digit, ROBO_STOP, 297);
	wait_ms(1);
	return rc;
}

/*
* FINGER CONTROL ALGORITHM
* The position of a finger is controlled in a feedforward manner by adjusting
* the time duration for a giving action (opening or closing the finger). By
* empirical analysis. I found that all the fingers (for pwm=297) it takes about
* one second for it to fully close when opened, while the thumb rotator takes
* about 1.5 seconds. Therefore, I divided these periods in 500 segments for the
* fingers and 750 segments for the thumb rotator, which means that the period
* of time for each position is equal to 2 ms.
* Position is controlled based on the number of timesteps that has passed
* since the function 'RC_move_finger_position' has been called.
* For example: If the index finger is at position 0 (zero) and the desired
* position is equal to 300, then it is necessary to wait 600 ms before
* stopping the movement of the finger, which means that 300 steps of 2 ms are
* required.
* Therefore, in the main loop there is a timer with a 2 ms interval. Whenever
* the interrupt is called, it will update the time left for a given finger
* to stop moving. This is made by using the RTC of the microcontroller.
* When the function is first called, 'HAL_GetTick()' provides the current
* tick and this variable is stored. When the interrupt is called, another
* 'HAL_GetTick()' is called, and the time difference between both of them
* is calculated to decide whether the finger should keep moving or if it
* should stop. The decision is made by comparing the amount of time that has
* passed with the total time that should be waited before stopping the finger.
* The 'RC_move_finger_position' function decides what is the direction of the
* movement and the amount of time that should be waited to stop the movement.
* The 'RC_update_finger_counters' function is called from the timer created
* in the main loop. It will update the time counters of every finger and decide
* when to stop them based on the time difference between the current tick and
* the tick measured when the 'RC_move_finger_position' was first called.
*
*/
//This function operates on four variables:
//finger_times: array containing the amount of time before stopping movement for
//each finger
//finger_timer: array containing the tick value ('HAL_GetTick()') when the move
//finger position was called for each finger
//finger_state: array containing the state of each finger. 0: still, 1: closing
//2: opening
//finger_dir: finger_dir is used here to maintain the firmware coherent since
//every action of closing or opening updates this array
ReturnCode RC_move_finger_position(uint8_t fing, uint16_t position)
{
	//first, stop the desired finger from moving
	//probably necessary for avoiding problems
	//while moving the fingers
	//just like it is done when closing or opening a finger
	//RC_stop_digit(fing);
	//wait_us(100);

	ReturnCode rc = LDA_OK;
	//retrieves the finger Id for internal control
	ctrl_digit = allDigits[fing];
	//Calculates the amount of time that should pass before stopping the movement
	//of the finger. Example: If the finger is at position 120 and should be moved
	//to 330, then: abs(330-120) = 210 steps. Since each step takes 2ms, then the
	//total time is 210*2 = 420 ms.
	//The difference is absolute because the amount of time waiting is independent
	//of the direction of the movement itself.
	uint32_t diff = abs(position - finger_pos[fing]);
	//Decides what is the direction of the movement
	//if the desired position is higher than the current position
	//then the finger should close
	if(position > finger_pos[fing])
	{
		//closes the finger
		RC_send_digit_command(ctrl_digit, ROBO_CLOSE, 297);
		//calculates the amount of time to wait
		finger_times[fing] = diff*finger_period[fing];
		finger_timer[fing] = HAL_GetTick(); //get current tick
		finger_dir[fing] = 1; //direction = closing -> increasing values
		finger_state[fing] = 1; //state = closing

		//debugging
		//pcserial->printf("closing: %d  %d  %d  %d\r\n",position,finger_pos[fing],finger_timer[fing],finger_times[fing]);

		//previous approach, innacuracies with timer and so on caused strange and
		//inconsistent behavior
		//finger_pos[fing] = position;
		//wait_ms(diff * finger_period[fing]);
		//RC_stop_digit(fing);
	}
	//otherwise, the finger should open
	else if(position < finger_pos[fing])
	{
		//opens the finger
		RC_send_digit_command(ctrl_digit, ROBO_OPEN, 297);
		//calculates the amount of time to wait
		finger_times[fing] = diff*finger_period[fing];
		finger_timer[fing] = HAL_GetTick(); //get current tick
		finger_dir[fing] = 0; //direction = opening -> decreasing values
		finger_state[fing] = 2; //state = opening

		//debugging
		//pcserial->printf("opening: %d  %d  %d  %d\r\n",position,finger_pos[fing],finger_timer[fing],finger_times[fing]);

		//previous approach, innacuracies with timer and so on caused strange and
		//inconsistent behavior
		//finger_pos[fing] = position;
		//wait_ms(diff * finger_period[fing]);
		//RC_stop_digit(fing);
	}
	return rc;
}
//this function updates the counters to decide whether it is time to stop the
//movement of the finger or not
//it is called by an interrupt created in 'main.cpp'
//gets the current tick and check if the difference between the current tick
//and the tick measured when 'RC_move_finger_position' was called is equal or
//greater than the amount of time specified in 'finger_times'
//if it is, the finger stops. otherwise, current positions in incremented or
//decremented depending on the direction of the movement
void RC_update_finger_counters()
{
	int k=0;
	//pcserial->printf("%d\r\n",finger_times[1]); //debugging
	uint32_t currentTick = HAL_GetTick();
	for(k=0; k<6; k++)
	{
		//if the finger is moving, update its counter
		if(finger_state[k] != 0)
		{
			//compares the current tick with the tick measured when the function was
			//called
			if(currentTick-finger_timer[k] < finger_times[k])
			{
				//if the finger is closing
				if(finger_state[k] == 1)
				{
					//if it is not the maximum position, increment current position
					if(finger_pos[k] < RC_maxFingerPositions[k])
						finger_pos[k]++; //increment
				}
				//if the finger is opening
				else if(finger_state[k] == 2)
				{
					//if the finger is not fully opened, decrement the position
					if(finger_pos[k]> 0)
						finger_pos[k]--; //decrement
				}
			}
			//if the difference between the ticks is greater or equal than the
			//specified time, then stops the movement
			else
			{
				RC_stop_digit(k); //stop the finger
				finger_state[k] = 0; //state = still or stopped
			}
		}
	}
}
