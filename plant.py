import busio
import digitalio
import board
import pigpio
from datetime import datetime
import time
import math
import adafruit_mcp3xxx.mcp3008 as MCP
from enum import Enum
from adafruit_mcp3xxx.analog_in import AnalogIn

class Plant:
    def __init__(self, name, adc_channel, gpio_output_port,dry_level,wet_level,soil):
        self.name = name
        self.dry_level = dry_level
        self.wet_level = wet_level
        self.adc_channel = adc_channel
        self.gpio_output_port = gpio_output_port
        
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(board.D5)
        mcp = MCP.MCP3008(spi, cs)
        self.channel = AnalogIn(mcp, adc_channel)
        
        self.output = pigpio.pi()
        self.output.set_mode(gpio_output_port, pigpio.OUTPUT)
        self.output.write(gpio_output_port, False)
        
        #self.dry_voltage = 2.85
        #self.saturated_voltage = 1.3
        self.soil=soil
        self.previous_voltage = 0
        self.status = Status()
        self.last_log_time = datetime.now()

    def calculate_moisture(self):
        return math.trunc((((self.soil.get_saturated_voltage() - round(self.channel.voltage, 2)) / (self.soil.get_dry_voltage() - self.soil.get_saturated_voltage())) * 100) + 100)

    def print_values(self):
        print(f"{self.name} Moisture: {self.calculate_moisture()}%")
        print(f"{self.name}\t{self.status}")

    def get_time_elapsed_in_seconds(self):
        return int((datetime.now() - self.last_log_time).total_seconds())

    def log_moisture_change(self):
        current_voltage = round(self.channel.voltage, 2)
        if (
            (round(abs(self.channel.voltage - self.previous_voltage), 2) > 0.02
            and self.get_time_elapsed_in_seconds() >= 60)
            or self.previous_voltage == 0
            or self.status.has_changed()
        ):
            with open(f"/home/zuldijin/Desktop/plant_{self.name}.log", "a+") as file:
                file.write(
                    f"{datetime.now()}\tPlant: {self.name}\t{self.status}\tADC Voltage: {self.channel.voltage}V\tMoisture: {self.calculate_moisture()}%\n"
                )
            self.previous_voltage = current_voltage
            self.last_log_time = datetime.now()

    def irrigate(self):
        if self.status.state == State.Absorbing and self.status.get_time_elapsed() < 5:
            pass
        elif self.calculate_moisture() < self.wet_level:
            self.output.write(self.gpio_output_port, True)
            print("Irrigating for 4 seconds")
            irrigation_time = 0
            self.status.change_status(State.Irrigating)
            while irrigation_time < 4:
                self.log_moisture_change()
                self.print_values()
                time.sleep(1)
                irrigation_time += 1
            self.output.write(self.gpio_output_port, False)
            self.status.change_status(State.Absorbing)
        else:
            self.status.change_status(State.Reading)

    def wait(self):
        self.output.write(16, True)
        time.sleep(1)
        self.output.write(16, False)
        time.sleep(1)

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
        return self.previous_state != self.state

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
    regular_soil=Soil("Regular",2.85,1.3)
    gravel=Soil("Gravel",2.75,1.8)
    plants = [
        Plant("Mint", MCP.P0, 18, 40, 80,regular_soil),
        Plant("Bamboo", MCP.P1, 23, 30, 80,regular_soil),
        Plant("Sequoia", MCP.P2, 24, 40, 80,gravel),
        Plant("Delonix Regia", MCP.P3, 25, 50, 70,regular_soil),
    ]

    while True:
        for plant in plants:
            plant.run()
            plant.wait()