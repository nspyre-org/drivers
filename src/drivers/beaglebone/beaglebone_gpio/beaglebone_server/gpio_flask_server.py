# pip install Adafruit_BBIO
import Adafruit_BBIO.GPIO as GPIO
from flask import Flask
from markupsafe import escape
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return '<p>Example of terminal is P8_10. To output high use /gpio/output/high/terminal. To output low use /gpio/output/low/terminal</p>'

@app.route('/restart')
def restart():
    GPIO.cleanup()
    os._exit(0)

@app.route('/gpio/output/high/<string:terminal>')
def output_high(terminal):
    GPIO.setup(terminal, GPIO.OUT)
    GPIO.output(terminal, GPIO.HIGH)
    return f'{escape(terminal)} is high'

@app.route('/gpio/output/low/<string:terminal>')
def output_low(terminal):
    GPIO.setup(terminal, GPIO.OUT)
    GPIO.output(terminal, GPIO.LOW)
    return f'{escape(terminal)} is low'

if __name__ == '__main__':
    app.run(host='0.0.0.0')
