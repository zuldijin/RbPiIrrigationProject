import RPi.GPIO as GPIO
import time
#####################################################################################
# Define the Variables Needed and the GPIO initialisation
#####################################################################################
global pwmobj                    # declare the pmwobj as a global variable
RPI_Pin = 18                     # define the RPI GPIO Pin we will use with PWM (PWM)
RPI_DutyCycle = 10               # define the Duty Cycle in percentage  (50%)
RPI_Freq = 100                  # define the frequency in Hz (500Hz)
RPI_LEDTime = 0.2			            # the time you want the LED to stay lit for (secs)
GPIO.setmode(GPIO.BCM)              # set actual GPIO BCM Numbers
GPIO.setup(RPI_Pin, GPIO.OUT)         # set RPI_PIN as OUTPUT mode
GPIO.output(RPI_Pin, GPIO.LOW)        # set RPI_PIN LOW to at the start
pwmobj = GPIO.PWM(RPI_Pin, RPI_Freq)  # Initialise instance and set Frequency
pwmobj.start(0)                       # set initial Duty cycle to 0 & turn on PWM
gpio_output_port=17
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.OUT)
#####################################################################################
# Define our main task
#####################################################################################
def pump():
    RPI_DutyCycle = 100
    pwmobj.ChangeDutyCycle(RPI_DutyCycle)
    GPIO.output(gpio_output_port,GPIO.HIGH)
    time.sleep(.1)
    duty=100
    while(duty>0):
        print(f"{duty}",flush=True, end="")
        pwmobj.ChangeDutyCycle(duty)      
        time.sleep(1)
        duty=duty-10
    GPIO.output(gpio_output_port,GPIO.LOW)
#####################################################################################
# Define our DESTROY Function
#####################################################################################
def destroy():
    print('Im dead now!')
    pwmobj.stop()
    GPIO.output(gpio_output_port,GPIO.LOW)
    GPIO.cleanup()
    # stop PWM
#####################################################################################
# Finally the code for the MAIN program
#####################################################################################
if __name__ == '__main__':                                      # Program entry point
    print ('LED Turned on with Duty Cycle of ', RPI_DutyCycle)  # Print duty cycle
    try:
        pump()                                                 # call light function
    except KeyboardInterrupt:                                   # Watches for Ctrl-C
        destroy()                                               # call destroy funct
    finally:
        destroy()                                               # call destroy funct