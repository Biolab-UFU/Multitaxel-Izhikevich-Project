/****************************************************************
* readDATA and readID functions currently not operational. Need *
* functional interrupt structure								*
*																*
* December 4, 2015												*
*****************************************************************/

#include "MCP2515.h"

#define FREQUENCY 10000000
#define WIDTH 8
#define MODE 0

DigitalOut RC_reset(PD_2); //must be activated to put controller into configuration mode

MCP2515::MCP2515(SPI& spi, PinName cs) : spi(spi), cs(cs)
{
    
    RC_reset.write(0);// RESET MCP2515 CONTROLLER
    wait_ms(10);
    RC_reset.write(1);
    wait_ms(100);
    
}

void MCP2515::baudConfig(int bitRate)//sets bitrate for MCP2515 node
{
    spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
	byte config0 = 0x00;
    byte config1 = 0x00;
    byte config2 = 0x00;

    switch (bitRate)
    {
case 10:
        config0 = 0x31;
        config1 = 0xB8;
        config2 = 0x05;
        break;

case 20:
        config0 = 0x18;
        config1 = 0xB8;
        config2 = 0x05;
        break;

case 50:
        config0 = 0x09;
        config1 = 0xB8;
        config2 = 0x05;
        break;

case 100:
        config0 = 0x04;
        config1 = 0xB8;
        config2 = 0x05;
        break;

case 125:
        config0 = 0x03;
        config1 = 0xB8;
        config2 = 0x05;
        break;

case 250:
        config0 = 0x01;
        config1 = 0xB8;
        config2 = 0x05;
        break;

case 500:
        config0 = 0x00;
        config1 = 0xB8;
        config2 = 0x05;
        break;
case 1000:
    //1 megabit mode added by Patrick Cruce(pcruce_at_igpp.ucla.edu)
    //Faster communications enabled by shortening bit timing phases(3 Tq. PS1 & 3 Tq. PS2) Note that this may exacerbate errors due to synchronization or arbitration.
   // config0 = 0x80;
   // config1 = 0x90;
   // config2 = 0x02;
   
   //ONLY VALUES BASED ON THE 20MHz OSCILLATOR ON THE DEV BOARD
		config0 = 0x00;
		config1 = 0xE8;
		config2 = 0x01;
    }
    cs = 0;
    wait_ms(10);
    spi.write(WRITE);
    spi.write(CNF0);
    spi.write(config0);
    wait_ms(10);
    cs = 1;
    wait_ms(10);

    cs = 0;
    wait_ms(10);
    spi.write(WRITE);
    spi.write(CNF1);
    spi.write(config1);
    wait_ms(10);
    cs = 1;
    wait_ms(10);

    cs = 0;
    wait_ms(10);
    spi.write(WRITE);
    spi.write(CNF2);
    spi.write(config2);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
}

//Method added to enable testing in loopback mode.(pcruce_at_igpp.ucla.edu)
void MCP2515::setMode(MCP2515Mode mode) { //put MCP2515 controller in one of five modes

    spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
	//byte writeVal,mask,readVal;
    byte writeVal = 0x00;
    byte mask = 0x00;

    switch(mode) {
      case CONFIGURATION:
            writeVal = 0x80;
            break;
      case NORMAL:
          writeVal = 0x00;
            break;
      case SLEEP:
            writeVal = 0x20;
          break;
    case LISTEN:
            writeVal = 0x60;
          break;
      case LOOPBACK:
            writeVal = 0x40;
          break;
   }

    mask = 0xE0;

    cs = 0;
    spi.write(BIT_MODIFY);
    spi.write(MCP2515CTRL);
    spi.write(mask);
    spi.write(writeVal);
    cs = 1;

}


void MCP2515::send_0()//transmits buffer 0
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    //wait_mss removed from SEND command(pcruce_at_igpp.ucla.edu)
    //In testing we found that any lost data was from PC<->Serial wait_mss,
    //Not MCP2515 Controller/AVR wait_mss.  Thus removing the wait_mss at this level
    //allows maximum flexibility and performance.
    cs = 0;
    spi.write(SEND_TX_BUF_0);
    cs = 1;
}

void MCP2515::send_1()//transmits buffer 1
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    cs = 0;
    spi.write(SEND_TX_BUF_1);
    cs = 1;
}

void MCP2515::send_2()//transmits buffer 2
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    cs = 0;
    spi.write(SEND_TX_BUF_2);
    cs = 1;
}

char MCP2515::readID_0()//reads ID in recieve buffer 0
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    char retVal;
    cs = 0;
    wait_ms(10);
    spi.write(READ_RX_BUF_0_ID);
    retVal = spi.write(0xFF);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
    return retVal;
}

char MCP2515::readID_1()//reads ID in reciever buffer 1
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    char retVal;
    cs = 0;
    wait_ms(10);
    spi.write(READ_RX_BUF_1_ID);
    retVal = spi.write(0xFF);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
    return retVal;
}

char MCP2515::readDATA_0()//reads DATA in recieve buffer 0
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    char retVal;
    cs = 0;
    wait_ms(10);
    spi.write( READ_RX_BUF_0_DATA);
    retVal = spi.write(0xFF);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
    return retVal;
}

char MCP2515::readDATA_1()//reads data in recieve buffer 1
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    char retVal;
    cs = 0;
    wait_ms(10);
    spi.write( READ_RX_BUF_1_DATA);
    retVal = spi.write(0xFF);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
    return retVal;
}

    //extending MCP2515 data read to full frames(pcruce_at_igpp.ucla.edu)
    //It is the responsibility of the user to allocate memory for output.
    //If you don't know what length the bus frames will be, data_out should be 8-bytes
void MCP2515::readDATA_ff_0(byte* length_out,byte *data_out,unsigned short *id_out)
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    byte len,i;
    unsigned short id_h,id_l;

    cs = 0;
    spi.write(READ_RX_BUF_0_ID);
    id_h = (unsigned short) spi.write(0xFF); //id high
    id_l = (unsigned short) spi.write(0xFF); //id low
    spi.write(0xFF); //extended id high(unused)
    spi.write(0xFF); //extended id low(unused)
    len = (spi.write(0xFF) & 0x0F); //data length code
    for (i = 0;i<len;i++) {
        data_out[i] = spi.write(0xFF);
    }
    cs = 1;
    (*length_out) = len;
    (*id_out) = ((id_h << 3) + ((id_l & 0xE0) >> 5)); //repack identifier
    
}

void MCP2515::readDATA_ff_1(byte* length_out,byte *data_out,unsigned short *id_out)
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    byte id_h,id_l,len,i;

    cs = 0;
    spi.write(READ_RX_BUF_1_ID);
    id_h = spi.write(0xFF); //id high
    id_l = spi.write(0xFF); //id low
    spi.write(0xFF); //extended id high(unused)
    spi.write(0xFF); //extended id low(unused)
    len = (spi.write(0xFF) & 0x0F); //data length code
    for (i = 0;i<len;i++) {
        data_out[i] = spi.write(0xFF);
    }
    cs = 1;

    (*length_out) = len;
    (*id_out) = ((((unsigned short) id_h) << 3) + ((id_l & 0xE0) >> 5)); //repack identifier
}

    //Adding method to read status register
    //MCP2515 be used to determine whether a frame was received.
    //(readStatus() & 0x80) == 0x80 means frame in buffer 0
    //(readStatus() & 0x40) == 0x40 means frame in buffer 1
byte MCP2515::readStatus() 
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    byte retVal;
    cs = 0;
    spi.write(READ_STATUS);
    retVal = spi.write(0xFF);
    cs = 1;
    return retVal;

}

void MCP2515::load_0(byte identifier, byte data)//loads ID and DATA into transmit buffer 0
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    cs = 0;
    wait_ms(10);
    spi.write(LOAD_TX_BUF_0_ID);
    spi.write(identifier);
    wait_ms(10);
    cs = 1;
    wait_ms(10);

    cs = 0;
    wait_ms(10);
    spi.write(LOAD_TX_BUF_0_DATA);
    spi.write(data);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
}

void MCP2515::load_1(byte identifier, byte data)//loads ID and DATA into transmit buffer 1
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    cs = 0;
    wait_ms(10);
    spi.write(LOAD_TX_BUF_1_ID);
    spi.write(identifier);
    wait_ms(10);
    cs = 1;
    wait_ms(10);

    cs = 0;
    wait_ms(10);
    spi.write(LOAD_TX_BUF_1_DATA);
    spi.write(data);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
}

void MCP2515::load_2(byte identifier, byte data)//loads ID and DATA into transmit buffer 2
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    cs = 0;
    wait_ms(10);
    spi.write(LOAD_TX_BUF_2_ID);
    spi.write(identifier);
    wait_ms(10);
    cs = 1;
    wait_ms(10);

    cs = 0;
    wait_ms(10);
    spi.write(LOAD_TX_BUF_2_DATA);
    spi.write(data);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
}

void MCP2515::load_ff_0(byte length,unsigned short identifier,byte *data)
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
    
    byte i,id_high,id_low;

    //generate id bytes before spi write
    id_high = (byte) (identifier >> 3);
    id_low = (byte) ((identifier << 5) & 0x00E0);

    cs = 0;
    spi.write(LOAD_TX_BUF_0_ID);
    spi.write(id_high); //identifier high bits
    spi.write(id_low); //identifier low bits
    spi.write(0x00); //extended identifier registers(unused)
    spi.write(0x00);
    spi.write(length);
    for (i=0;i<length;i++) { //load data buffer
        spi.write(data[i]);
    }

    cs = 1;

}

void MCP2515::load_ff_1(byte length,unsigned short identifier,byte *data)
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
    
    byte i,id_high,id_low;

    //generate id bytes before spi write
    id_high = (byte) (identifier >> 3);
    id_low = (byte) ((identifier << 5) & 0x00E0);

    cs = 0;
    spi.write(LOAD_TX_BUF_1_ID);
    spi.write(id_high); //identifier high bits
    spi.write(id_low); //identifier low bits
    spi.write(0x00); //extended identifier registers(unused)
    spi.write(0x00);
    spi.write(length);
    for (i=0;i<length;i++) { //load data buffer
        spi.write(data[i]);
    }

    cs = 1;


}

void MCP2515::load_ff_2(byte length,unsigned short identifier,byte *data)
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
    
    byte i,id_high,id_low;

    //generate id bytes before spi write
    id_high = (byte) (identifier >> 3);
    id_low = (byte) ((identifier << 5) & 0x00E0);

    cs = 0;

    spi.write(LOAD_TX_BUF_2_ID);
    spi.write(id_high); //identifier high bits
    spi.write(id_low); //identifier low bits
    spi.write(0x00); //extended identifier registers(unused)
    spi.write(0x00);
    spi.write(length); //data length code
    for (i=0;i<length;i++) { //load data buffer
        spi.write(data[i]);
    }

    cs = 1;

}

//------------------------------------------------------------------------------
//Added for ram
void MCP2515::writeRegister(byte address, byte data)
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    cs = 0;
    wait_ms(10);
    spi.write(WRITE);
    spi.write(address);
    spi.write(data);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
}
void MCP2515::readRegister(byte address, byte *data_out)
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    cs = 0;
    wait_ms(10);
    spi.write(READ);
    spi.write(address);
    *data_out = spi.write(0xFF);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
}

void MCP2515::reset()
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    cs = 0;
    wait_ms(10);
    spi.write(RESET_REG);
    wait_ms(10);
    cs = 1;
    wait_ms(10);
}

byte MCP2515::readRXStatus()
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    byte retVal;
    cs = 0;
    spi.write(RX_STATUS);
    retVal = spi.write(0xFF);
    cs = 1;
    return retVal;
}

void MCP2515::bitModify(byte address, byte mask, byte data)
{
	spi.frequency(FREQUENCY);
    spi.format(WIDTH, MODE);
	
    cs = 0;
    spi.write(BIT_MODIFY);
    spi.write(address);
    spi.write(mask);
    spi.write(data);
    cs = 1;
}

void MCP2515::setMask(unsigned short identifier)
{
    setMask_0(identifier);
    setMask_1(identifier);
}

void MCP2515::setMask_0(unsigned short identifier)
{
    writeRegister(RXM0SIDH, (byte)(identifier>>3));
    writeRegister(RXM0SIDL, (byte)(identifier<<5));
}

void MCP2515::setMask_1(unsigned short identifier)
{
    writeRegister(RXM1SIDH, (byte)(identifier>>3));
    writeRegister(RXM1SIDL, (byte)(identifier<<5));
}

