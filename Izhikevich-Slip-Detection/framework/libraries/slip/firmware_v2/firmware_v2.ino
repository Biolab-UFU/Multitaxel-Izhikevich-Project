/*
 * -------------------------------------------------------------
 * NATIONAL UNIVERSITY OF SINGAPORE - NUS
 * SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
 * Neuromorphic Engineering and Robotics Group
 * Singapore
 * -------------------------------------------------------------
 */
//--------------------------------------------------------------
//--------------------------------------------------------------
#include "I2Cdev.h"
#include "MPU6050.h"
// Arduino Wire library is required if I2Cdev I2CDEV_ARDUINO_WIRE implementation
// is used in I2Cdev.h
#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    #include "Wire.h"
#endif
//--------------------------------------------------------------
#include <VL53L0X.h>
//--------------------------------------------------------------
#define SAMP_PERIOD 2 //in ms
#define BAUD 115200 //baudrate
#define PKG_SIZE 12 //size of the usb packet
#define ST 0x24 //header
#define ET 0x21 //end of packet
#define analogPin A3 //analog input
#define ledPin 13 //led
//--------------------------------------------------------------
//--------------------------------------------------------------
// FUNCTION PROTOTYPES
//--------------------------------------------------------------
void readSensors();
//--------------------------------------------------------------
MPU6050 accelgyro;
VL53L0X sensor;
//--------------------------------------------------------------
uint8_t flagRead = 0;
uint8_t ledStatus = 0;
int16_t ax, ay, az;
int16_t gx, gy, gz;
uint16_t ax_offset = -1593; 
uint16_t ay_offset = -881;
uint16_t az_offset = 988;
uint16_t distance = 0;
uint16_t respAD = 0;
uint8_t usbVector[PKG_SIZE] = {ST,0,0,0,0,0,0,0,0,0,0,ET};
//--------------------------------------------------------------
void setup() {
  // put your setup code here, to run once:
    #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
      Wire.begin();
  #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
      Fastwire::setup(400, true);
  #endif
  
  //initialize serial
  Serial.begin(BAUD);
  
  // initialize mpu5040
  accelgyro.initialize();
  // initialize vl530x
//  lox.begin(); 
  sensor.init();
  sensor.setTimeout(500);
  sensor.setMeasurementTimingBudget(20000); //increase speed -> 20 ms

  //led
  pinMode(ledPin,OUTPUT);
  digitalWrite(ledPin,LOW);

  accelgyro.setXAccelOffset(ax_offset);
  accelgyro.setYAccelOffset(ay_offset);
  accelgyro.setZAccelOffset(az_offset);
}
//--------------------------------------------------------------
//--------------------------------------------------------------
void loop() { 

  if(Serial.available())
  {
    String s = Serial.readStringUntil('\n');
    if(s == "START")
    {
      flagRead = 1;
      //readSensors(1);
      distance = sensor.readRangeSingleMillimeters();
    }
    else if(s == "STOP")
    {
      flagRead = 0;
      //readSensors(1);
      digitalWrite(ledPin,LOW);
      distance = sensor.readRangeSingleMillimeters();
    }
    else if(s == "DIST")
    {
      distance = sensor.readRangeSingleMillimeters();
    }
  }

  if(flagRead)
  {
    readSensors(1);
  }
}

void readSensors(uint8_t flagDistance)
{

    if(ledStatus == 0)
    {
      digitalWrite(ledPin,HIGH);
      ledStatus = 1;
    }
    else
    {
      digitalWrite(ledPin,LOW);
      ledStatus = 0;
    }
    
      //read the output from mpu6050 --> accelerometer and gyroscope
    accelgyro.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    //read the output from vl530x --> distance
    if(flagDistance)
      distance = sensor.readRangeSingleMillimeters();
    //read the analog channel - optic sensor
    respAD = analogRead(analogPin);  
  
    usbVector[1] = uint16_t(ax) >> 8;
    usbVector[2] = uint16_t(ax) & 0xff; 
    usbVector[3] = uint16_t(ay) >> 8;
    usbVector[4] = uint16_t(ay) & 0xff;
    usbVector[5] = uint16_t(az) >> 8;
    usbVector[6] = uint16_t(az) & 0xff;
    usbVector[7] = uint16_t(distance) >> 8;
    usbVector[8] = uint16_t(distance) & 0xff;
    usbVector[9] = uint16_t(respAD) >> 8;
    usbVector[10] = uint16_t(respAD  ) & 0xff;
  
    Serial.write(usbVector,PKG_SIZE);
    
  //  //debugging
  //  Serial.print(ax); Serial.print(" ");
  //  Serial.print(ay); Serial.print(" ");
  //  Serial.print(az); Serial.print(" ");
  //  Serial.print(measure.RangeMilliMeter); Serial.print(" ");
  //  Serial.print("\n");
  
  //  digitalWrite(ledPin,LOW);

    if(flagDistance == 0)
      delay(1); 
}

