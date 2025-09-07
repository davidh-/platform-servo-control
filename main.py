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

dc2_angle = 0


#calculate the duty cycle
def cbf(pin, level, tick):
    global tick_high, duty_cycle, turns, thetaP, theta, angle, diff, oldDiff, dc2_angle
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
            dc2_angle = theta

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
            # print("theta", round(theta, 2), "turns", turns, "angle", round(angle, 2))


        except Exception:
            print("math error")
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

targetAngle = None


def goToAngle(targetAngle):
    Kp = 2
    offset = None
    timeout = 0
    boost = 25
    while (True):
        errorAngle = targetAngle - angle;
        # print("errorAngle", errorAngle)

        output = errorAngle * Kp;

        if output > 200:
            output = 200
        if output < -200: 
            output = -200

        if errorAngle > 0:
            offset = 30
        elif errorAngle < 0:
            offset = -30
        else:
            offset = 0

        newPW = output + offset
        # print("output + offset", newPW)
        timeout += 1
        if timeout > 1000:
            print("boost")
            boost = 50
            if errorAngle > 0:
                newPW += boost
            elif errorAngle < 0:
                newPW -= boost
            # if timeout > 5000:
            #     break

        newPW_final = dc2 + newPW
        # if newPW_final > pan_max_pw:
        #     newPW_final = pan_max_pw
        # elif newPW_final < pan_min_pw:
        #     newPW_final = pan_min_pw
        gpio.set_servo_pulsewidth(servoPIN2, newPW_final)
        print("theta", theta)
        # time.sleep(10/1000)
        # Exit the loop when the error is close to zero (desired angle reached)
        if abs(errorAngle) < 1:
            gpio.set_servo_pulsewidth(servoPIN2, dc2)
            break
    # print("targetAngle", targetAngle, "confirmed")

def on_press(key):
    global dc1, dc2, targetAngle, dc2_angle
    step = 50
    step_angle = 5
    try: 
        if isinstance(key, keyboard.KeyCode):
            # Capture numerical keys to build the targetAngle value
            try:
                num = int(key.char)
                if targetAngle is None:
                    targetAngle = num
                else:
                    targetAngle = targetAngle * 10 + num
                print(f"\rAngle entered: {targetAngle}", end='', flush=True)  # Use \r to overwrite the current line
            except ValueError:
                pass
        elif key == keyboard.Key.enter:  # Handle the Enter key separately
            # When Enter key is pressed, check if the targetAngle is set and in valid range (0-359)
            # print(targetAngle)
            if targetAngle is not None and 0 <= targetAngle <= 359:
                # Perform your actions based on the targetAngle value
                goToAngle(targetAngle)
                # Reset the targetAngle variable for the next input
                targetAngle = None
            else:
                print("Invalid degree. Please enter a value between 0 and 359.")
                targetAngle = None
        elif key == keyboard.Key.up:
            dc1 = min(dc1 + step, 2500)
            gpio.set_servo_pulsewidth(servoPIN1, dc1)
            print(dc1)
        elif key == keyboard.Key.down:
            dc1 = max(dc1 - step, 500)
            gpio.set_servo_pulsewidth(servoPIN1, dc1)
            print(dc1)
        elif key == keyboard.Key.left:
            dc2_angle = min(dc2_angle + step_angle, 359)
            goToAngle(dc2_angle)
            # dc2 = min(dc2 + step, pan_max_pw)
            # gpio.set_servo_pulsewidth(servoPIN2, dc2)
            print(dc2)
        elif key == keyboard.Key.right:
            dc2_angle = max(dc2_angle - step_angle, 0)
            goToAngle(dc2_angle)
            # dc2 = max(dc2 - step, pan_min_pw)
            # gpio.set_servo_pulsewidth(servoPIN2, dc2)
            print(dc2)
    except AttributeError:
        print("keyboard error")
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
    goToAngle(140) # 140 front, 320 back
    gpio.set_servo_pulsewidth(servoPIN2, 1500)
    gpio.set_servo_pulsewidth(servoPIN1, 550)

