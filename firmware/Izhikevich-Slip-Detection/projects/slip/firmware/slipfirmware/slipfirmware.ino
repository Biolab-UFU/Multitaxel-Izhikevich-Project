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
#include "Adafruit_VL53L0X.h"
//--------------------------------------------------------------
#define SAMP_PERIOD 2 //in ms
#define BAUD 115200 //baudrate
#define PKG_SIZE 12 //size of the usb packet
#define ST 0x24 //header
#define ET 0x21 //end of packet
#define analogPin A3 //analog input
//--------------------------------------------------------------
MPU6050 accelgyro;
Adafruit_VL53L0X lox = Adafruit_VL53L0X();
//--------------------------------------------------------------
int16_t ax, ay, az;
int16_t gx, gy, gz;
uint16_t ax_offset = -1593; 
uint16_t ay_offset = -881;
uint16_t az_offset = 988;
uint16_t respAD = 0;
VL53L0X_RangingMeasurementData_t measure;
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
  lox.begin(); 

  accelgyro.setXAccelOffset(ax_offset);
  accelgyro.setYAccelOffset(ay_offset);
  accelgyro.setZAccelOffset(az_offset);
}
//--------------------------------------------------------------
//--------------------------------------------------------------
void loop() { 
  //read the output from mpu6050 --> accelerometer and gyroscope
  accelgyro.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  //read the output from vl530x --> distance
  lox.rangingTest(&measure, false);
  respAD = analogRead(analogPin);  

  usbVector[1] = uint16_t(ax) >> 8;
  usbVector[2] = uint16_t(ax) & 0xff; 
  usbVector[3] = uint16_t(ay) >> 8;
  usbVector[4] = uint16_t(ay) & 0xff;
  usbVector[5] = uint16_t(az) >> 8;
  usbVector[6] = uint16_t(az) & 0xff;
  usbVector[7] = uint16_t(measure.RangeMilliMeter) >> 8;
  usbVector[8] = uint16_t(measure.RangeMilliMeter) & 0xff;
  usbVector[9] = uint16_t(respAD) >> 8;
  usbVector[10] = uint16_t(respAD  ) & 0xff;

  Serial.write(usbVector,PKG_SIZE);
  
//  //debugging
//  Serial.print(ax); Serial.print(" ");
//  Serial.print(ay); Serial.print(" ");
//  Serial.print(az); Serial.print(" ");
//  Serial.print(measure.RangeMilliMeter); Serial.print(" ");
//  Serial.print("\n");

  delay(10);
}
