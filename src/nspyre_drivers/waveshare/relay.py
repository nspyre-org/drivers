#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import socket               
import pycrc
import time
 
class Relay():

    def __init__(self, host='192.168.1.200', port=4196, address=0x01):
        self.address = address
        self.sock = socket.socket()         # creat socket 
        self.sock.connect((host, port))     # connect serve

    def _write(self, cmd):
        crc = pycrc.ModbusCRC(cmd)
        cmd.append(crc & 0xFF)
        cmd.append(crc >> 8)
        self.sock.send(bytearray(cmd))

    def on(self, channel):
        assert(channel in [0,1,2,3,4,5,6,7])

        cmd = [self.address, 0x05, 0, channel, 0xFF, 0]     

        self._write(cmd)

        time.sleep(0.2)

        assert(self.sock.recv(8) == bytearray(cmd))


    def off(self, channel):
        assert(channel in [0,1,2,3,4,5,6,7])

        cmd = [self.address, 0x05, 0, channel, 0, 0]     

        self._write(cmd)

        time.sleep(0.2)

        assert(self.sock.recv(8) == bytearray(cmd))

    def all_off(self):
        for i in range(8):
            self.off(i)

    def all_on(self):
        for i in range(8):
            self.on(i)

    def read(self, channel):
        cmd = [0x01, 0x01, 0, 0, 0, 0x08, 0x3D, 0xCC]   
        self.sock.send(bytearray(cmd))

        if self.sock.recv(6)[3] & 2**channel:
            return True
        else:
            return False

    def __del__(self):
        self.close()

    def close(self):
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

if __name__ == '__main__':

    with Relay(host='192.168.1.200', port=4196, address=0x01) as relay:
        relay.all_off()

        channel = 0
        relay.on(channel)
        relay.off(channel)

        relay.on(7)
        relay.on(1)
        print(relay.read(7))
        print(relay.read(1))
        print(relay.read(0))
        relay.all_off()