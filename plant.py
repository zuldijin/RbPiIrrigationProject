import busio
import digitalio
import board
import pigpio
from datetime import datetime
import time
import adafruit_mcp3xxx.mcp3008 as MCP
from enum import Enum
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
        self.status=Status()
        
    def calculateMoisture(self):
        return round((((self.saturatedVoltage-self.channel.voltage)/(self.dryVoltage-self.saturatedVoltage))*100)+100,0)
    
        
    def printValues(self):
        print(self.name+' Status: '+str(self.status))
        print(self.name+' Moisture: '+ str(self.calculateMoisture())+'%')
        print(self.name+' Minutes at state: '+str(self.status.getTimeElapsed()))
        
    def now(self):
        return datetime.now()
        
    def logMoistureChange(self):
        if(abs(self.calculateMoisture()-self.previousMoisture)>=2):
            file1 = open('/home/zuldijin/Desktop/plant_'+self.name+'.log', 'a+')
            file1.write(str(self.now())+'\tPlant: '+self.name
            +'\tStatus: '+str(self.status)
            +'\tADC Voltage: '+ str(self.channel.voltage)
            +'V\tMoisture: '+ str(self.calculateMoisture())+'%\n')
            file1.close()
            self.previousMoisture=self.calculateMoisture()
            
    def irrigate(self):
        if self.status.state==State.Absorbing and self.status.getTimeElapsed()<=5:
            pass
        elif self.calculateMoisture()<self.wetLevel:
            self.output.write(self.gpioOutputPort,True)
            print('Irrigating for 4 seconds')  
            irrigationTime=0
            self.status.changeStatus(State.Irrigating)
            while irrigationTime<4:
                self.logMoistureChange()
                self.printValues()
                time.sleep(1)
                irrigationTime=irrigationTime+1
            self.output.write(self.gpioOutputPort,False)
            self.status.changeStatus(State.Absorbing)
        else:
            self.status.changeStatus(State.Reading)
                
    def wait(self):
            plant.output.write(16,True)
            time.sleep(1)
            plant.output.write(16,False)
            time.sleep(1)
            
    def run(self):
            self.printValues()
            self.logMoistureChange()
            if self.calculateMoisture()<=self.dryLevel or self.status.state==State.Absorbing:
                self.irrigate()
                
class Status():
    def __init__(self):
        self.state=State.Reading
        self.time=datetime.now()
    def changeStatus(self, state):
        self.state=state
        self.time=datetime.now()
    def getTimeElapsed(self):
        return int((datetime.now()-self.time).total_seconds() / 60)
    def __str__(self):
        return self.state.name
        
class State(Enum):
    Reading = 1
    Absorbing = 2
    Irrigating = 3
        
if __name__ == "__main__":
    plants=[plant("Mint",MCP.P0,18,30,80), 
            plant("Bamboo",MCP.P1,23,30,80),
            plant("sequoia",MCP.P2,24,20,80),
            plant("Delonix Regia",MCP.P3,25,30,80)]
    while True:
        for plant in plants:
            plant.run()
            plant.wait()
            
    
