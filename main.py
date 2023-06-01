import pigpio
import time
from pynput import keyboard

# Assuming the servos are connected to GPIO 12 (PWM0) and GPIO 13 (PWM1)
servoPIN1 = 12
servoPIN2 = 13

# Setup GPIO
pwm = pigpio.pi()
pwm.set_mode(servoPIN1, pigpio.OUTPUT)
pwm.set_mode(servoPIN2, pigpio.OUTPUT)


# Initialize PWM on both pins with a frequency of 330Hz
pwm.set_PWM_frequency(servoPIN1, 100)
pwm.set_PWM_frequency(servoPIN2, 100)


dc1 = 1500
dc2 = 1500

pwm.set_servo_pulsewidth(servoPIN1, dc1)
pwm.set_servo_pulsewidth(servoPIN2, dc2)


def on_press(key):
    global dc1
    global dc2
    step = 100
    try: 
        if key == keyboard.Key.down:
            dc1 = min(dc1 + step, 2500)
            pwm.set_servo_pulsewidth(servoPIN1, dc1)
            print(dc1)
        elif key == keyboard.Key.up:
            dc1 = max(dc1 - step, 500)
            pwm.set_servo_pulsewidth(servoPIN1, dc1)
            print(dc1)
        elif key == keyboard.Key.left:
            dc2 = min(dc2 + step, 2500)
            pwm.set_servo_pulsewidth(servoPIN2, dc2)
            print(dc2)
        elif key == keyboard.Key.right:
            dc2 = max(dc2 - step, 500)
            pwm.set_servo_pulsewidth(servoPIN2, dc2)
            print(dc2)
    except AttributeError:
        pass

listener = keyboard.Listener(
    on_press=on_press)
listener.start()

try:
    while True:
        # Your program continues to do other stuff here
        time.sleep(0.1)

except KeyboardInterrupt:
    # User pressed CTRL+C - cleanup GPIO and stop the program
    pwm.set_servo_pulsewidth(servoPIN1, 1500)
    pwm.set_servo_pulsewidth(servoPIN2, 1500)
