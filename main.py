import pigpio
import time
from pynput import keyboard

# Assuming the servos are connected to GPIO 12 (PWM0) and GPIO 13 (PWM1)
servoPIN1 = 12 # TILT
servoPIN2 = 13 # PAN


positionCTRL = 19 # PAN-Position GPIO 19 (Hardware PWM) Input

# Setup GPIO
gpio = pigpio.pi()
gpio.set_mode(servoPIN1, pigpio.OUTPUT)
gpio.set_mode(servoPIN2, pigpio.OUTPUT)


period = 1/910*1000000
tick_high = None
duty_cycle = None
duty_scale = 1000

#calculate the duty cycle
def cbf(pin, level, tick):
    global tick_high, duty_cycle
    # print(pin, level, tick)
    #change to low (a falling edge)
    if level == 0:
        # print("level 0")
        #if first edge is a falling one the following code will fail
        #a try first time is faster than an if-statement every time 
        try:
            #http://abyz.me.uk/rpi/pigpio/python.html#callback
            # tick        32 bit    The number of microseconds since boot
            #                       WARNING: this wraps around from
            #                       4294967295 to 0 roughly every 72 minutes
            #Tested: This is handled by the tickDiff function internally, if t1 (earlier tick)
            #is smaller than t2 (later tick), which could happen every 72 min. The result will
            #not be a negative value, the real difference will be properly calculated.
            print("about to set duty_cycle")
            print(duty_scale, tick_high, period)
            duty_cycle = duty_scale*pigpio.tickDiff(tick_high, tick)/period
            print("duty cycle", duty_cycle)
        except Exception:
            pass

    #change to high (a rising edge)
    elif level == 1:
        # print("tick_high", tick_high)
        tick_high = tick



gpio.set_mode(positionCTRL, pigpio.INPUT)
cb = gpio.callback(positionCTRL, pigpio.EITHER_EDGE, cbf)



# Initialize PWM on both pins with a frequency of 330Hz
gpio.set_PWM_frequency(servoPIN1, 330)
gpio.set_PWM_frequency(servoPIN2, 330)


dc1 = 1500
dc2 = 1500

gpio.set_servo_pulsewidth(servoPIN1, dc1)
gpio.set_servo_pulsewidth(servoPIN2, dc2)




def on_press(key):
    global dc1
    global dc2
    step = 50
    try: 
        if key == keyboard.Key.up:
            dc1 = min(dc1 + step, 2500)
            gpio.set_servo_pulsewidth(servoPIN1, dc1)
            print(dc1)
        elif key == keyboard.Key.down:
            dc1 = max(dc1 - step, 500)
            gpio.set_servo_pulsewidth(servoPIN1, dc1)
            print(dc1)
        elif key == keyboard.Key.left:
            dc2 = min(dc2 + step, 2500)
            gpio.set_servo_pulsewidth(servoPIN2, dc2)
            print(dc2)
            # print(duty_cycle)
        elif key == keyboard.Key.right:
            dc2 = max(dc2 - step, 500)
            gpio.set_servo_pulsewidth(servoPIN2, dc2)
            print(dc2)
            # print(duty_cycle)
    except AttributeError:
        pass

listener = keyboard.Listener(
    on_press=on_press)
listener.start()

try:
    while True:
        # Your program continues to do other stuff here
        time.sleep(0.0000001)

except KeyboardInterrupt:
    # User pressed CTRL+C - cleanup GPIO and stop the program
    gpio.set_servo_pulsewidth(servoPIN1, 1500)
    gpio.set_servo_pulsewidth(servoPIN2, 1500)
