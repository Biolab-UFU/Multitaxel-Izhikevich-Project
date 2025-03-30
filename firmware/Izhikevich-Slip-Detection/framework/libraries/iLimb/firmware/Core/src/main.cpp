/*
*--------------------------------------------------------------------------
* NATIONAL UNIVERSITY OF SINGAPORE - NUS
* SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
* Singapore
* Last update: 14/05/2018
*--------------------------------------------------------------------------
* Authors:   Andrei Nakagawa-Silva
*            Balakrishna Devarokanda
* URL: http://www.sinapseinstitute.org/
*--------------------------------------------------------------------------
* Description: Modified firmware for controlling the iLimb
*--------------------------------------------------------------------------
* Serial protocol: The communication protocol has been altered to improve
* the control of the fingers. Now, it is possible to control several fingers
* at once using a single serial package
* The designed protocol follows the pattern:
* [HEADER][NUMBYTES]-NUMBYTES-[END]
* where NUMBYTES corresponds to the number of bytes that are actual data
* and should be read
* actual data has the following pattern:
* [FINGERID][ACTION][VMSB][VLSB] or [WRIST][ACTION][PMSB][PLSB]
* where:
*      FINGERID: id of the finger that should be controlled
*      ACTION: which action should be performed: 0=stop, 1=close, 2=open, 3=position
*      VMSB: msb of the pwm value for actions 0-2 or position msb for action 3
*      VLSB: lsb of the pwm value for actions 0-2 or position msb for action 3
*-------------------------------------------------------------------------------
*      WRIST: id for representing the wrist, it will be 0x07
*      ACTION: 0x0 indicates clockwise, 0x01 indicates anticlockwise
*      PMSB: msb of the position value (should be between 0 and 360)
*      PLSB: lsb of the position value (should be between 0 and 360)
*-------------------------------------------------------------------------------
* Therefore, this data will be contained inside the serial package and NUMBYTES will
* depend on the number of fingers that will be controlled at once.
* Example: If NUMBYTES is equal to 4, then one finger will be controlled and 4 bytes
* will follow and the full package will have 7 bytes. if NUMBYTES is equal to 12,
* then three fingers will be controlled and 12 bytes will follow and the full
* package will have 15 bytes.
* Finally, if all fingers are going to be controlled at once, then the maximum
* size the package might have is 27 bytes.
* If all the fingers are going to be controlled at once and the wrist as well
* then the package might have a total of 31 bytes
* header+numbytes+(4*7=28)+end = 28+3 = 31
*--------------------------------------------------------------------------
* Acknowledgements: IBT
*--------------------------------------------------------------------------
*--------------------------------------------------------------------------
*/
//-------------------------------------------------------------------------
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
//-------------------------------------------------------------------------
#define VERSION_MAJOR 0.0
#define VERSION_MINOR 1.0
#define VERSION_REV 1.0
#define VERSION (((VERSION_MAJOR * 100.0) + (VERSION_MINOR * 10.0) + (VERSION_REV)) / 100.0)
//-------------------------------------------------------------------------
//#define WRITE_NEW_CONFIG 1
//-------------------------------------------------------------------------
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
Ticker timerControl;

//Thread
//Thread threadControl;
Mutex mutex;

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
        //pcserial->attach(&read_key);

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


void setupError()
{
    D_LED1.write(0);
    D_LED2.write(0);
    D_LED3.write(0);
    D_LED4.write(0);
    D_LED5.write(0);
    // Capture errors
    pcserial->printf("ERROR!!!");
}


ReturnCode setupInit()
{
    uint8_t ok = 0;
    ReturnCode rc;
    rc = Config_init();

    rc = Config_get_configuration(&confignew);
    confignew.type_electrodes = IBT;
    confignew.num_electrodes = 8;
    confignew.running_mode = KEYBOARD;
    rc = Config_set_configuration(&confignew);
    if(rc == LDA_OK)
        D_LED2.write(1);

    // Initialize any IO
    rc = initialize_hardware();

    //If ok
    if(rc == LDA_OK)
    {
        //debugging
        //pcserial->printf("Init Complete!\r\n");
        D_LED3.write(1);

    }
    else //error
    {
        setupError();
    }
    return rc;
}

//read a package from the serial
void readPackage(uint8_t* package)
{
    //uint8_t package[6] = {0,0,0,0,0,0};
    //uint8_t* package = (uint8_t*)malloc(6*sizeof(uint8_t));
    uint8_t incByte = 0;
    //checks if there are any byte available to read
    if(pcserial->readable())
    {
        uint8_t inbyte = pcserial->getc();
        if(inbyte == 36)
        {
            package[0] = 36;
            //debugging
            //package format
            //[HEADER][NUMBYTES][FINGERID[ACTION][MSB][LSB]...[END]
            //FINGERID,ACTION,MSB,LSB will repeat N times where N = number of fingers
            //to be controlled
            //NUMBYTES will indicate how many bytes should be read which means
            //how many finger actions are being given
            uint8_t numBytes = pcserial->getc();
            package[1] = numBytes;
            //read actual data from the package
            for(int i=2; i<2+numBytes; i++)
            {
                package[i] = pcserial->getc();
            }
            //read end of package
            package[2+numBytes] = pcserial->getc();
            if(package[2+numBytes] == 33)
            {
                //debugging
                //pcserial->printf("Package OK!\r\n"); //debugging
                //pcserial->printf("%d\r\n",package[1]); //debugging
                //pcserial->printf("%d\r\n",package[2]); //debugging
                //pcserial->printf("%d\r\n",package[3]); //debugging
                //pcserial->printf("%d\r\n",package[4]); //debugging
                //pcserial->printf("%d\r\n",package[5]); //debugging
            }
            else
                package[0] = 0;
        }
        else
            package[0] = 0;
    }
    else
        package[0] = 0;
    //package error
    //pcserial->printf("Package error!\r\n"); //debugging
}

void fingerPosControl()
{
    //D_LED5 = !D_LED5;
    RC_update_finger_counters();
}

#define maxPkgBytes 27
uint8_t inPackage[maxPkgBytes] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};

// main loop
int main()
{
    //Turns on the first LED
    D_LED1.write(1);
    //FM_power.write(0);
    //Initializes the serial port
    pcserial = new Serial(PA_9, PA_10);

    int i = 1;
    int agcounter = 1;
    int *inputdata = NULL;
    ReturnCode rc = LDA_OK;

    //Set UART baud rate
    pcserial->baud(115200);

    //printing the version
    //debugging
    //pcserial->printf("Version = %f\r\n", VERSION);
    //

    rc = setupInit();
    wait_ms(1000);
    if(rc == LDA_OK)
    {
        D_LED4.write(1);
        /*RC_stop_hand();
        RC_stop_digit(0);
        wait_ms(100);
        RC_move_finger_pwm_dir(5,2,100);
        wait_ms(1500);
        RC_stop_digit(0);
        RC_move_finger_pwm_dir(5,1,100);
        wait_ms(1500);
        RC_stop_digit(0);
        RC_move_finger_pwm_dir(5,2,100);*/
    }

    //just for testing, I will begin by always stopping the finger first
    //RC_stop_digit(0);
    //now, send the command
    //int pwm = (package[3]>>8) | package[4];
    //RC_move_finger_pwm_dir(0,1,100);

    //init finger interrupts
    //Thread threadControl(fingerPosControl);

    //timer
    timerControl.attach(&fingerPosControl,0.002);
    D_LED5.write(0);
    //infinite loop
    while(true)
    {
         //reads an incoming serial packet
         readPackage(inPackage);

         //if the first byte of the package is different than zero, then it is a valid
         //package and should be processed
         if(inPackage[0] != 0)
         {
           //processing the package
           for(int i=2; i<2+inPackage[1]; i+=4)
           {
               //first decide whether it is finger or wrist command
               //if id is less than 6, then it is finger control,
               //otherwise it will be wrist control
               if(inPackage[i] < 6)
               {
                 RC_stop_digit(inPackage[i]);
                 wait_us(100); //is it really necessary?
                 if(inPackage[i+1] != 3)
                 {
                   int pwm = inPackage[i+2]<<8 | inPackage[i+3];
                   RC_move_finger_pwm_dir(inPackage[i],inPackage[i+1],pwm);
                   //debugging
                   //pcserial->printf("action: %d %d %d %d\n",inPackage[i],inPackage[i+1],inPackage[i+2],inPackage[i+3]);
                 }
                 else
                 {
                   uint16_t fingerPos = (inPackage[i+2]<<8) | inPackage[i+3];
                   RC_move_finger_position(inPackage[i],fingerPos);
                   //debugging
                   //pcserial->printf("position: %d %d %d %d\n",inPackage[i],inPackage[i+1],inPackage[i+2],inPackage[i+3]);
                 }
                 //wait_us(100); //is it really necessary?
               }
               else
               {
                  D_LED5 = !D_LED5;
                  //retrieve the angle
                  uint16_t angle = (inPackage[i+2]<<8) | inPackage[i+3];
                  //rotate the wrist clockwise
                  if(inPackage[i+1] == HB_ROTATE_CLOCKWISE)
                    HB_ClockWise(angle);
                  //rotate anticlockwise
                  else if(inPackage[i+1] == HB_ROTATE_ANTICLOCKWISE)
                    HB_AntiClockWise(angle);
               }
            }
          }
          else
            D_LED4 = !D_LED4;

        //old implementation
         /*
         //pcserial->printf("%d\r\n",inPackage[0]); //debugging
         //if it is a valid package
         if(inPackage[0] != 0)
         {
            //pcserial->printf("reading package!\r\n"); //debugging
            //control a finger
            //just for testing, I will begin by always stopping the finger first
            RC_stop_digit(inPackage[1]);
            wait_ms(1);
            if(inPackage[1] != 7)
            {
                //now, send the command
                int pwm = (inPackage[3]<<8) | inPackage[4];
                RC_move_finger_pwm_dir(inPackage[1],inPackage[2],pwm);
                //wait_ms(100);
                //RC_stop_digit(inPackage[1]);
            }
            else if(inPackage[1] == 7)
            {
                uint16_t pos = (inPackage[3]<<8) | inPackage[4];
                RC_move_finger_position(inPackage[2],pos);
                //pcserial->printf("moving %d\r\n", pos);
            }
         }
         */
    }

    return 0;
}
