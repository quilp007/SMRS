import time
import zmq
import RPi.GPIO as GPIO
import threading as th
import atexit

ON  = True
OFF = False

# GPIO Setting
print(GPIO.RPI_INFO)
GPIO.setmode(GPIO.BOARD)

# I2C pin for ADC [TODO]
ADC_SDA                 = 3
ADC_SCL                 = 5

# RELEAY CONTROL
AUTO_MODE_RELAY_PIN     = 11
MANUAL_MODE_RELAY_PIN   = 13

# LED ON/OFF
LED_AUTO_MODE_ON        = 16
LED_MANUAL_MODE_ON      = 18
LED_MANUAL_OUT_ON       = 22
LED_MANUAL_OUT_OFF      = 29
LED_WIFI_LINK           = 31

# CONFIG ADDR
ADDR_0_PIN              = 15
ADDR_1_PIN              = 36
ADDR_2_PIN              = 37


GPIO.setup(AUTO_MODE_RELAY_PIN, GPIO.OUT)
GPIO.setup(MANUAL_MODE_RELAY_PIN, GPIO.OUT)

GPIO.setup(LED_AUTO_MODE_ON  , GPIO.OUT)
GPIO.setup(LED_MANUAL_MODE_ON, GPIO.OUT)
GPIO.setup(LED_MANUAL_OUT_ON , GPIO.OUT)
GPIO.setup(LED_MANUAL_OUT_OFF, GPIO.OUT)
GPIO.setup(LED_WIFI_LINK     , GPIO.OUT)

GPIO.setup(ADDR_0_PIN, GPIO.IN)
GPIO.setup(ADDR_1_PIN, GPIO.IN)
GPIO.setup(ADDR_2_PIN, GPIO.IN)

addr = 0
if GPIO.input(ADDR_2_PIN):
    addr += 1 << 2
if GPIO.input(ADDR_1_PIN):
    addr += 1 << 1
if GPIO.input(ADDR_0_PIN):
    addr += 1

context = zmq.Context()
# socket = context.socket(zmq.REP)
# socket.bind("tcp://*:5555")
socket = context.socket(zmq.PAIR)
# socket.connect("tcp://192.168.0.26:5555")
socket.connect(f"tcp://192.168.0.26:550{addr}")

command_dict = {
    'alive':        False,
    'auto_mode':    OFF,
    'manual_mode':  OFF
}
def cleanup_gpio():
    GPIO.cleanup()

atexit.register(cleanup_gpio)

def alive_function():
    global command_dict
    command_dict['alive'] = True 
    socket.send_json(command_dict)
    print('send alive', command_dict)

def start_periodic_task(interval_seconds):
    # 주기적인 작업 실행
    alive_function()

    # 타이머를 설정하여 일정 시간(초) 후에 함수를 다시 호출
    timer = th.Timer(interval_seconds, start_periodic_task, args=(interval_seconds,))
    timer.start()

start_periodic_task(1)

while True:
    message = socket.recv_json()
    print(message)
    # print('auto mode: ', message['auto_mode'])
    # print('manual mode: ', message['manual_mode'])

    if message['alive'] == False:
        command_dict['alive'] = True
        # socket.send_json(command_dict)
        # continue

    if message['auto_mode']:
        # AUTO MODE -> relay on, led on
        GPIO.output(AUTO_MODE_RELAY_PIN, GPIO.HIGH)
        GPIO.output(LED_AUTO_MODE_ON, GPIO.HIGH)
        # MANUAL MODE -> relay off, led off 
        GPIO.output(MANUAL_MODE_RELAY_PIN, GPIO.LOW)
        GPIO.output(LED_MANUAL_MODE_ON, GPIO.LOW)
        command_dict['auto_mode'] = ON
    else:
        # MANUAL MODE -> relay off, led off 
        GPIO.output(AUTO_MODE_RELAY_PIN, GPIO.LOW)
        GPIO.output(LED_AUTO_MODE_ON, GPIO.LOW)
        GPIO.output(LED_MANUAL_MODE_ON, GPIO.HIGH)
        command_dict['auto_mode'] = OFF

        if message['manual_mode']:
            GPIO.output(MANUAL_MODE_RELAY_PIN, GPIO.HIGH)
            GPIO.output(LED_MANUAL_OUT_ON, GPIO.HIGH)
            GPIO.output(LED_MANUAL_OUT_OFF, GPIO.LOW)
            command_dict['manual_mode'] = ON
        else:
            GPIO.output(MANUAL_MODE_RELAY_PIN, GPIO.LOW)
            GPIO.output(LED_MANUAL_OUT_ON, GPIO.LOW)
            GPIO.output(LED_MANUAL_OUT_OFF, GPIO.HIGH)
            command_dict['manual_mode'] = OFF

    #  Send reply back to client
    socket.send_json(command_dict)
    print('send command', command_dict)
