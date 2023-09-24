import busio
import digitalio
import board
import pigpio
from datetime import datetime
import time
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn


class plant():
    def __init__(self,name,adcChannel,gpioOutputPort,dryLevel,wetLevel):
        self.name=name
        self.dryLevel=dryLevel
        self.wetLevel=wetLevel
        self.adcChannel=adcChannel
        self.gpioOutputPort=gpioOutputPort
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs=digitalio.DigitalInOut(board.D5)
        mcp = MCP.MCP3008(spi, cs)
        #create a channel
        self.channel=AnalogIn(mcp,adcChannel)
        #SET GPIO
        self.output = pigpio.pi()
        self.output.set_mode(gpioOutputPort, pigpio.OUTPUT)
        self.output.write(gpioOutputPort,False)
        self.dryVoltage=2.85
        self.saturatedVoltage=1.3
        self.previousMoisture=0
        self.state='Start'
        
    def calculateMoisture(self):
        return round((((self.saturatedVoltage-self.channel.voltage)/(self.dryVoltage-self.saturatedVoltage))*100)+100,0)
    
        
    def printValues(self):
        print(self.name+' Status: '+self.status)
        print(self.name+' Moisture: '+ str(self.calculateMoisture())+'%')
        
    def now(self):
        return datetime.now()
        
    def logStatusChange(self):
        if(abs(self.calculateMoisture()-self.previousMoisture)>=2):
            file1 = open('/home/zuldijin/Desktop/plant_'+self.name+'.log', 'a+')
            file1.write(str(self.now())+'\tPlant: '+self.name
            +'\tStatus: '+self.status
            +'\tADC Voltage: '+ str(self.channel.voltage)
            +'V\tMoisture: '+ str(self.calculateMoisture())+'%\n')
            file1.close()
            self.previousMoisture=self.calculateMoisture()
            
    def irrigate(self):
        if self.calculateMoisture()<self.wetLevel:
            self.output.write(self.gpioOutputPort,True)
            print('Irrigating for 4 seconds')  
            irrigationTime=0
            while irrigationTime<4:
                self.status='Irrigating'
                self.logStatusChange()
                self.printValues()
                time.sleep(1)
                irrigationTime=irrigationTime+1
            self.output.write(self.gpioOutputPort,False)
            absorbWaterTime=0
            while absorbWaterTime<10:
                self.status='Absorbing'
                self.logStatusChange()
                self.printValues()
                time.sleep(1)
                absorbWaterTime=absorbWaterTime+1
                
    def run(self):
            self.status='Reading'
            self.printValues()
            self.logStatusChange()
            if self.calculateMoisture()<self.dryLevel:
                self.irrigate()
    
        
if __name__ == "__main__":
    plants=[plant("Mint",MCP.P0,18,30,80), 
            plant("Bamboo",MCP.P1,23,30,80),
            plant("sequoia",MCP.P2,24,20,80),
            plant("Delonix Regia",MCP.P3,25,30,80)]
    while True:
        for plant in plants:
            plant.run()
    
