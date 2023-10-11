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
        self.lastLogTime=datetime.now()
        
    def calculateMoisture(self):
        return round((((self.saturatedVoltage-self.channel.voltage)/(self.dryVoltage-self.saturatedVoltage))*100)+100,0)
    
        
    def printValues(self):
        print(self.name+' Moisture: '+ str(self.calculateMoisture())+'%')
        print(self.name+'\t'+str(self.status))
        
    def now(self):
        return datetime.now()
    
    def getTimeElapsedInsecods(self):
        return int((datetime.now()-self.lastLogTime).total_seconds())
    
    def logMoistureChange(self):
        currentMoisture=self.calculateMoisture()
        if((abs(currentMoisture-self.previousMoisture)>=1 and self.getTimeElapsedInsecods()>=60)
            or self.previousMoisture==0
            or self.status.hasChanged()):
            file1 = open('/home/zuldijin/Desktop/plant_'+self.name+'.log', 'a+')
            file1.write(str(self.now())+'\tPlant: '+self.name
            +'\t'+str(self.status)
            +'\tADC Voltage: '+ str(self.channel.voltage)
            +'V\tMoisture: '+ str(currentMoisture)+'%\n')
            file1.close()
            self.previousMoisture=currentMoisture
            self.lastLogTime=datetime.now()
            
    def irrigate(self):
        if self.status.state==State.Absorbing and self.status.getTimeElapsed()<5:
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
        self.previousState=State.Reading
        self.time=datetime.now()
    def hasChanged(self):
        return self.previousState!=self.state
    def changeStatus(self, state):
        self.previousState=self.state
        self.state=state
        self.time=datetime.now()
    def getTimeElapsed(self):
        return int((datetime.now()-self.time).total_seconds() / 60)
    def __str__(self):
        return 'Status: '+self.state.name+', for: '+str(self.getTimeElapsed())+' minutes'
        
class State(Enum):
    Reading = 1
    Absorbing = 2
    Irrigating = 3
        
if __name__ == "__main__":
    plants=[plant("Mint",MCP.P0,18,40,80), 
            plant("Bamboo",MCP.P1,23,30,80),
            plant("sequoia",MCP.P2,24,50,70),
            plant("Delonix Regia",MCP.P3,25,50,70)]
    while True:
        for plant in plants:
            plant.run()
            plant.wait()
            
    
