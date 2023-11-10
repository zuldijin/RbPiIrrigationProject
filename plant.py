import busio
import digitalio
import board
import RPi.GPIO as GPIO
from datetime import datetime
import time
import math
import adafruit_mcp3xxx.mcp3008 as MCP
from enum import Enum
from adafruit_mcp3xxx.analog_in import AnalogIn

GPIO.cleanup()
RPI_Pin = 18                        # define the RPI GPIO Pin we will use with PWM (PWM)
RPI_Freq = 100                      # define the frequency in Hz (500Hz)
GPIO.setmode(GPIO.BCM)              # set actual GPIO BCM Numbers
GPIO.setup(RPI_Pin, GPIO.OUT)       # set RPI_PIN as OUTPUT mode
GPIO.output(RPI_Pin, GPIO.LOW)          # set RPI_PIN LOW to at the start
global pwmobj

class Plant:
    def __init__(self, name, adc_channel, gpio_output_port,dry_level,wet_level,soil,pump_duty):
        self.name = name
        self.dry_level = dry_level
        self.wet_level = wet_level
        self.adc_channel = adc_channel
        self.gpio_output_port = gpio_output_port
        self.duty=pump_duty
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(board.D5)
        mcp = MCP.MCP3008(spi, cs)
        self.channel = AnalogIn(mcp, adc_channel)
        GPIO.setup(gpio_output_port,GPIO.OUT)
        GPIO.output(gpio_output_port,GPIO.LOW)
        GPIO.setup(16,GPIO.OUT)
        self.soil=soil
        self.previous_moisture = [0,0,0]
        self.previous_moisture_index=0
        self.status = Status()
        self.last_log_time = datetime.now()

    def calculate_moisture(self):
        average_voltage=self.get_volatge_avarage_for_x_seconds(1)
        return int(str(math.trunc((((self.soil.get_saturated_voltage() - round(average_voltage, 2)) / (self.soil.get_dry_voltage() - self.soil.get_saturated_voltage())) * 100) + 100)))

    def print_values(self):
        print(f"{self.name} Voltage: {self.channel.voltage}v")
        print(f"{self.name}\t{self.status}")

    def get_time_elapsed_in_seconds(self,start_time):
        return int((datetime.now() - start_time).total_seconds())
    
    def get_volatge_avarage_for_x_seconds(self,time):
        GPIO.output(16,GPIO.HIGH)
        voltages=[]
        sum_voltages=0
        start_time=datetime.now()
        while(self.get_time_elapsed_in_seconds(start_time)<time):
            voltages.append(self.channel.voltage)
        for i in voltages:
            sum_voltages+=i
        GPIO.output(16,GPIO.LOW)
        return sum_voltages/(len(voltages))
        
    def log_moisture_change(self):
        current_moisture=self.calculate_moisture() 
        if ((current_moisture not in self.previous_moisture
            and self.get_time_elapsed_in_seconds(self.last_log_time) >= 60)
            or sum(self.previous_moisture) == 0
            or self.status.has_changed()
        ):
            with open(f"/home/zuldijin/Desktop/plant_{self.name}.log", "a+") as file:
                file.write(
                    f"{datetime.now()}\tPlant: {self.name}\t{self.status}\tADC Voltage: {self.channel.voltage}V\tMoisture: {current_moisture}%\n"
                )
            self.previous_moisture[self.previous_moisture_index]=current_moisture
            self.previous_moisture_index+=1
            if(self.previous_moisture_index==3):
                self.previous_moisture_index=0
            self.last_log_time = datetime.now()
        print(self.previous_moisture)

    def pump(self,pump_time):
        GPIO.output(self.gpio_output_port,GPIO.HIGH)
        pwmobj.ChangeDutyCycle(100)
        time.sleep(0.3)
        irrigation_time=0
        while irrigation_time < pump_time:
                pwmobj.ChangeDutyCycle(self.duty) 
                self.log_moisture_change()
                self.print_values()
                irrigation_time += 1
        GPIO.output(self.gpio_output_port,GPIO.LOW)
        
    def irrigate(self):
        if self.status.state == State.Absorbing and self.status.get_time_elapsed() < 10:
            pass
        elif self.calculate_moisture() < self.wet_level:
            print("Irrigating for 4 seconds")
            irrigation_time = 0
            self.status.change_status(State.Irrigating)
            self.pump(4)
            self.status.change_status(State.Absorbing)
        else:
            self.status.change_status(State.Reading)

    def run(self):
        self.print_values()
        self.log_moisture_change()
        if self.calculate_moisture() <= self.dry_level or self.status.state == State.Absorbing:
            self.irrigate()

class Status:
    def __init__(self):
        self.state = State.Reading
        self.previous_state = State.Reading
        self.time = datetime.now()

    def has_changed(self):
        is_changed=self.previous_state != self.state
        if is_changed:
            self.previous_state=self.state
        return is_changed

    def change_status(self, state):
        self.previous_state = self.state
        self.state = state
        self.time = datetime.now()

    def get_time_elapsed(self):
        return int((datetime.now() - self.time).total_seconds() / 60)

    def __str__(self):
        return f"Status: {self.state.name}, for: {self.get_time_elapsed()} minutes"

class State(Enum):
    Reading = 1
    Absorbing = 2
    Irrigating = 3
    
class Soil():
    def __init__(self, name, dry_voltage, saturated_voltage):
        self.name=name
        self.dry_voltage=dry_voltage
        self.saturated_voltage=saturated_voltage
    
    def get_dry_voltage(self):
        return self.dry_voltage
    
    def get_saturated_voltage(self):
        return self.saturated_voltage

if __name__ == "__main__":
    pwmobj = GPIO.PWM(RPI_Pin, RPI_Freq)# Initialise instance and set Frequency
    pwmobj.start(0)
    flower_soil=Soil("Flower Soil",2.15,1.15)
    gravel=Soil("Gravel",2.75,1.50)
    flower_gravel=Soil("50 flower-50 gravelblend",2.80,1.38)
    plants = [
        Plant("Mint", MCP.P0, 6, 60, 80,flower_soil,70),
        Plant("Bamboo", MCP.P1, 13, 50, 80,flower_soil,70),
        Plant("Sequoia", MCP.P2, 19, 50, 80,gravel,50),
        Plant("Delonix Regia", MCP.P3, 26, 50, 70,flower_gravel,50),
    ]

    while True:
        for plant in plants:
            plant.run()
            time.sleep(1)