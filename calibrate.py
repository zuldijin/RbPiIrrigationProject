import busio
import digitalio
import board
import sys
import pigpio
from datetime import datetime
import time
import matplotlib.pyplot as plt
import math
import adafruit_mcp3xxx.mcp3008 as MCP
from enum import Enum
from adafruit_mcp3xxx.analog_in import AnalogIn

if __name__ == "__main__":
    adc_channel=MCP.P0
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    cs = digitalio.DigitalInOut(board.D5)
    mcp = MCP.MCP3008(spi, cs)
    channel = AnalogIn(mcp, adc_channel)    
    
    def wait_animation(time_to_wait):
        animation = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        idx = 0
        start_time=datetime.now()
        while (datetime.now()-start_time).total_seconds()<time_to_wait:
            print(f"\r{animation[idx%len(animation)]}", flush=True, end="")
            time.sleep(0.1)
            idx += 1
        
    def time_in_seconds(start_time):
        return int((datetime.now()-start_time).total_seconds())
   
    def voltage_average(time):
        voltages=[]
        sum_voltages=0
        start_time=datetime.now()
        while(time_in_seconds(start_time)<time):
            print(f"\r{time_in_seconds(start_time)} s\tvoltage: {channel.voltage}", flush=True, end="")
            voltages.append(channel.voltage)
        for i in voltages:
            sum_voltages+=i
        print("")
        return sum_voltages/(len(voltages)+1)
    answer='n'
    soil_volume = int(input("Enter Soil Volume in ml:"))
    if soil_volume==0:
        raise Exception("soil cannot be 0 , you need soil to meassure soil.... just saying")
    voltages=[]
    water_added=[]
    soil_saturation=[]
    while(answer!='y'):
        water = input("Enter water Volume added in ml:")
        water_added.append(int(water))
        print('will absorb for a minute:')
        wait_animation(60)
        v=voltage_average(60)
        voltages.append(v)
        print(f"Average voltage is: {v}")
        answer=input("is soil saturated?(last average voltages are very close and soil is draining)(y/n): ")
    water_sum=0
    for wtr in water_added:
        water_sum+=wtr
        soil_saturation.append(water_sum/soil_volume)
    plt.scatter(soil_saturation, voltages) 
    plt.show()

    
    
        
        
        
        
    
        
    
    

    
