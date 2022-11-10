// Jacob Feder 10/17/2022
// simple serial interface to make an arduino toggle digital outputs

#include <Adafruit_MCP4728.h>
#include <Wire.h>
#include "limits.h"

// DAC
Adafruit_MCP4728 mcp;
// number of digital output pins
uint16_t npins = 13;

void setup() {
  // set up digital output pins
  // default to low
  uint16_t i;
  for (i = 2; i < npins; i++) {
    pinMode(i, OUTPUT);
    digitalWrite(i, LOW);
  }
  // config serial port for talking to host
  Serial.begin(115200);
  Serial.setTimeout(LONG_MAX);

  // Try to initialize DAC
  if (mcp.begin(0x64)) {
    // use the internal reference
    mcp.setChannelValue(MCP4728_CHANNEL_A, 0, MCP4728_VREF_INTERNAL, MCP4728_GAIN_2X);
    mcp.setChannelValue(MCP4728_CHANNEL_B, 0, MCP4728_VREF_INTERNAL, MCP4728_GAIN_2X);
    mcp.setChannelValue(MCP4728_CHANNEL_C, 0, MCP4728_VREF_INTERNAL, MCP4728_GAIN_2X);
    mcp.setChannelValue(MCP4728_CHANNEL_D, 0, MCP4728_VREF_INTERNAL, MCP4728_GAIN_2X);
  } else {
    Serial.println("error: failed to find MCP4728 chip");
  }
}

// send a string back to the host with a terminating newline
void response(char *msg) {
  Serial.write(msg);
  Serial.write("\n");
}

// send a number of bytes back to the host with a terminating newline
void response_len(char *bytes, int len) {
  Serial.write(bytes, len);
  Serial.write("\n");
}

// set a digital output high/low
void set_pin(uint8_t pin, uint8_t state) {
  if (state != 0) {
    digitalWrite(pin, HIGH);
  }
  else {
    digitalWrite(pin, LOW);
  }
}

// set the dac output
void set_dac(uint8_t ch, uint8_t byte1, uint8_t byte2) {
  bool success = false;
  // construct data packet
  uint32_t data = byte2;
  data = data << 8;
  data = data | (uint32_t)byte1;
  // set DAC output
  switch (ch) {
    case 0:
      success = mcp.setChannelValue(MCP4728_CHANNEL_A, data, MCP4728_VREF_INTERNAL, MCP4728_GAIN_2X);
      break;
    case 1:
      success = mcp.setChannelValue(MCP4728_CHANNEL_B, data, MCP4728_VREF_INTERNAL, MCP4728_GAIN_2X);
      break;
    case 2:
      success = mcp.setChannelValue(MCP4728_CHANNEL_C, data, MCP4728_VREF_INTERNAL, MCP4728_GAIN_2X);
      break;
    case 3:
      success = mcp.setChannelValue(MCP4728_CHANNEL_D, data, MCP4728_VREF_INTERNAL, MCP4728_GAIN_2X);
      break;
    default:
      response("error: invalid DAC channel");
      break;
  }
  if (success == false) {
    response("error: setting DAC voltage failed");
  }
}

// buffer for message received from host
size_t msg_len;
// length of command packet
const uint8_t cmd_len = 4;
char msg[cmd_len];

// host should send commands with the format
// byte 0: 'o'
// byte 1: arduino pin [0 to (npins-1)]
// byte 2: state (0 for LOW, non-zero for HIGH)
void loop() {
  // listen for a command from the host
  msg_len = Serial.readBytes(msg, cmd_len);
  if (msg_len == cmd_len) {
    switch (msg[0]) {
      case 'o':
        set_pin(msg[1], msg[2]);
        break;
      case 'd':
        set_dac(msg[1], msg[2], msg[3]);
        break;
      default:
        response("error: unrecognized command");
        break;
    }
  }
  else {
      response("error: command packet has wrong length");
      response("message:");
      response(msg);
  }
  response("rdy");
}
