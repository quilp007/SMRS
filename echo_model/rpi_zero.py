import time
import zmq
import RPi.GPIO as GPIO
import threading as th

ON  = True
OFF = False

# GPIO Setting
print(GPIO.RPI_INFO)
GPIO.setmode(GPIO.BOARD)

AUTO_MODE_PIN = 3
MANUAL_MODE_PIN = 7

GPIO.setup(AUTO_MODE_PIN, GPIO.OUT)
GPIO.setup(MANUAL_MODE_PIN, GPIO.OUT)

context = zmq.Context()
# socket = context.socket(zmq.REP)
# socket.bind("tcp://*:5555")
socket = context.socket(zmq.PAIR)
# socket.connect("tcp://192.168.0.26:5555")
socket.connect("tcp://192.168.0.26:5500")

command_dict = {
    'alive':        False,
    'auto_mode':    OFF,
    'manual_mode':  OFF
}

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
        GPIO.output(AUTO_MODE_PIN, GPIO.HIGH)
        command_dict['auto_mode'] = ON
    else:
        GPIO.output(AUTO_MODE_PIN, GPIO.LOW)
        command_dict['auto_mode'] = OFF

        if message['manual_mode']:
            GPIO.output(MANUAL_MODE_PIN, GPIO.HIGH)
            command_dict['manual_mode'] = ON
        else:
            GPIO.output(MANUAL_MODE_PIN, GPIO.LOW)
            command_dict['manual_mode'] = OFF

    #  Send reply back to client
    socket.send_json(command_dict)
    print('send command', command_dict)
