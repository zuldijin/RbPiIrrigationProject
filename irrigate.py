#!/usr/bin/python3
import busio
import digitalio
import board
import RPi.GPIO as GPIO
import time
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs=digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)
#create a channel
channel=AnalogIn(mcp,MCP.P0)
#SET GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18,GPIO.OUT)
GPIO.output(18,GPIO.LOW)
#1.6V is 100% wet 2.8V is dry
dryVoltage=2.85
saturatedVoltage=1.3 
def calculateMoisture(voltage):
    return round((((saturatedVoltage-voltage)/(dryVoltage-saturatedVoltage))*100)+100,0)
def printValues(status):
    print('Status: '+status)
    print('Raw ADC Value: ',channel.value)
    print('ADC Voltage: '+ str(channel.voltage)+'V')
    print('Moisture: '+ str(calculateMoisture(channel.voltage))+'%')

def irrigatePlant():
    while calculateMoisture(channel.voltage)<80:
        GPIO.output(18,GPIO.HIGH)
        print('Irrigating for 4 seconds')  
        irrigationTime=0
        while irrigationTime<4:
            printValues('Irrigating')
            time.sleep(1)
            irrigationTime=irrigationTime+1
        GPIO.output(18,GPIO.LOW)
        absorbWaterTime=0
        while absorbWaterTime<60:
            printValues('Absorbing')
            time.sleep(1)
            absorbWaterTime=absorbWaterTime+1
        
#Print raw voltage
while True:
    printValues('Reading')
    if calculateMoisture(channel.voltage)<30:
        irrigatePlant()
    time.sleep(5)