#ifndef ROBOCAN_H
#define ROBOCAN_H
#include "mbed.h"

#include "errors.h"

#define NUM_RC_GRIPS 13

/* Digits identifier for the ROBO limb */
typedef enum
{
    ROBO_THUMB      = 0x01,
    ROBO_INDEX      = 0x02,
    ROBO_MIDDLE     = 0x03,
    ROBO_RING       = 0x04,
    ROBO_LITTLE     = 0x05,
    ROBO_ROTATOR    = 0x06

} ROBO_DIGIT;


/* Command options for the digits of the ROBO limb */
typedef enum 
{
    ROBO_STOP   = 0x0,
    ROBO_CLOSE  = 0x1,
    ROBO_OPEN   = 0x2

} ROBO_DIGIT_COMMAND;


/* Command options for the ROBO limb Grips */
typedef enum 
{
    ROBO_GRIP_NORMAL                            = 0x00,
    ROBO_GRIP_STD_PRECISION_PINCH_CLOSED        = 0x01,
    ROBO_GRIP_STD_3JAW_CHUCK_CLOSED             = 0x02,
    ROBO_GRIP_THUMB_PARK_CONTINUOUS             = 0x03,
    ROBO_GRIP_LATERAL                           = 0x05,
    ROBO_GRIP_INDEX_POINT                       = 0x06,
    ROBO_GRIP_STD_PRECISION_PINCH_OPENED        = 0x07,
    ROBO_GRIP_THUMB_PRECISION_PINCH_CLOSED      = 0x09,
    ROBO_GRIP_THUMB_PRECISION_PINCH_OPENED      = 0x0a,
    ROBO_GRIP_THUMB_3JAW_CHUCK_CLOSED           = 0x0b,
    ROBO_GRIP_STD_3JAW_CHUCK_OPENED             = 0x0d,
    ROBO_GRIP_THUMB_3JAW_CHUCK_OPENED           = 0x0e,
    ROBO_GRIP_DONNING                           = 0x18

} ROBO_GRIP;

/* Digit status for the ROBO limb */
typedef enum 
{
    ROBO_STATUS_DIGIT_STOP = 0,
    ROBO_STATUS_DIGIT_CLOSING,
    ROBO_STATUS_DIGIT_OPENING,
    ROBO_STATUS_DIGIT_STALLED_CLOSED,
    ROBO_STATUS_DIGIT_STALLED_OPENED

} ROBO_DIGIT_STATUS;


/* Rotator status for the ROBO limb - provided with every digit status */
typedef enum 
{
    ROBO_STATUS_ROTATOR_NOT_FULLY_PALMAR = 0,
    ROBO_STATUS_FULLY_PALMAR
            
} ROBO_ROTATOR_STATUS;

/* Complete status provided by the ROBO limb */
typedef struct
{
    ROBO_DIGIT_STATUS digitStatus;
    ROBO_ROTATOR_STATUS rotatorStatus;
    int motorCurrent;
    
} ROBO_STATUS;

ReturnCode RC_init(SPI *can_spi, PinName cs);
ReturnCode RC_send_grip_command(ROBO_GRIP grip);
ReturnCode RC_send_digit_command(ROBO_DIGIT digit, ROBO_DIGIT_COMMAND cmd, int pwm);
ReturnCode RC_get_status(ROBO_STATUS *status, ROBO_DIGIT digit);
ReturnCode RC_get_current_grip(ROBO_GRIP *grip);
ReturnCode RC_get_serial_number(char* serial_number);
ReturnCode RC_BIT();

//Functions added by Megan, 11/20/15
ReturnCode RC_stop_hand();
ReturnCode RC_open_hand();
ReturnCode RC_close_hand();
ReturnCode RC_move_finger(int fing);
ReturnCode RC_increase_torque(int fing);
ReturnCode RC_move_finger_pwm(int fing, int pwm);
ReturnCode RC_stop_digit(int fing);
ReturnCode RC_move_finger_pwm_dir(int fing, int dir, int pwm);

//position-based control of fingers

//control individual finger based on position
ReturnCode RC_move_finger_position(uint8_t fing, uint16_t position);
//function to be called by an interrupt in the main program
//updates the counters of every finger to determine when it should
//stop
void RC_update_finger_counters();

#endif // ROBOCAN_H