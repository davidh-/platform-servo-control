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

unitsFC = 360
dcMin = 29
dcMax = 971
theta = None

q2min = 90
q3max = 270
turns = 0
thetaP = None
angle = None
diff = None
oldDiff = None


#calculate the duty cycle
def cbf(pin, level, tick):
    global tick_high, duty_cycle, turns, thetaP, theta, angle, diff, oldDiff
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
            # print("about to set duty_cycle")
            # print(duty_scale, tick_high, tick, tick-tick_high, period)
            oldDiff = diff
            diff = pigpio.tickDiff(tick_high, tick)
            if abs(oldDiff - diff) > 100:
                return
            duty_cycle = duty_scale*diff/period
            # print("duty cycle", duty_cycle)
            # print("diff", diff, "oldDiff", oldDiff)

            thetaP = theta
            theta = (unitsFC - 1) - ((duty_cycle - dcMin) * unitsFC) / (dcMax - dcMin + 1);
            # print("theta", theta, "duty_cycle", duty_cycle)
            # In case the pulse measurements are a little too large or small, 
            # let’s clamp the angle in the valid range.
            if theta < 0:
                theta = 0
                # print("new_theta", theta)
            elif theta > (unitsFC - 1):
                theta = unitsFC - 1
                # print("new_theta", theta)
            exit_sig = False
            # print("theta", theta, "q2min", q2min, "thetaP", thetaP, "q3max", q3max)
            if (theta < q2min) and (thetaP > q3max): # If 4th to 1st quadrant
                turns += 1  # Increment turns count
                exit_sig = True
            elif (thetaP < q2min) and (theta > q3max): # If in 1st to 4th quadrant
                turns -= 1 # Decrement turns count
                exit_sig = True
            

            if turns >= 0:
                angle = (turns * unitsFC) + theta
            elif turns < 0:
                angle = ((turns + 1) * unitsFC) - (unitsFC - theta)
            print("theta", round(theta, 2), "turns", turns, "angle", round(angle, 2))


        except Exception:
            print("error")
            pass

    #change to high (a rising edge)
    elif level == 1:
        # print("tick_high", tick_high)
        tick_high = tick



gpio.set_mode(positionCTRL, pigpio.INPUT)
cb = gpio.callback(positionCTRL, pigpio.EITHER_EDGE, cbf)



# Initialize PWM on both pins with a frequency of 330Hz
gpio.set_PWM_frequency(servoPIN1, 330)
gpio.set_PWM_frequency(servoPIN2, 50)


dc1 = 1500
dc2 = 1500

gpio.set_servo_pulsewidth(servoPIN1, dc1)
gpio.set_servo_pulsewidth(servoPIN2, dc2)


pan_max_pw = 1720
pan_min_pw = 1280

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
            dc2 = min(dc2 + step, pan_max_pw)
            gpio.set_servo_pulsewidth(servoPIN2, dc2)
            print(dc2)
        elif key == keyboard.Key.right:
            dc2 = max(dc2 - step, pan_min_pw)
            gpio.set_servo_pulsewidth(servoPIN2, dc2)
            print(dc2)
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
