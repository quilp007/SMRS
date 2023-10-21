#
#   python3
#   sudo apt-get install python3-pip
#   pip3 install pyzmq
#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

import time, datetime
import zmq

time_format = '[%Y.%m.%d]_%H:%M:%S'

context = zmq.Context()
# socket = context.socket(zmq.REP)

# socket = context.socket(zmq.PULL)
# socket.bind("tcp://*:5555")

socket = context.socket(zmq.SUB)
# socket.connect("tcp://localhost:5555")
socket.connect("tcp://211.57.90.83:5555")
socket.subscribe("")

while True:
    dictData = socket.recv_json()
    _time = datetime.datetime.now()
    _time = _time.strftime(time_format)
    print('>>> received DATA: ' + _time)
    print('source:                     0x{:02X}'.format(dictData['source']))
    print('destination:                0x{:02X}'.format(dictData['destination']))
    print('pahse:                      0x{:02X}'.format(dictData['phase']))
    print('gun_barrel_elevation_angle: {:0.2f}'.format(dictData['gun_barrel_elevation_angle']))
    print('gun_azimuth_angle:          {:0.2f}'.format(dictData['gun_azimuth_angle']))
    print('scope_elevation_angle:      {:0.2f}'.format(dictData['scope_elevation_angle']))
    print('scope_azimuth_angle:        {:0.2f}'.format(dictData['scope_azimuth_angle']))
    print('trigger:                    {}'.format(dictData['trigger']))
    print('shot_motor:                 {}'.format(dictData['shot_motor']))
    print('gun_barrel_speed_up_down:   {}'.format(dictData['gun_barrel_speed_up_down']))
    print('gun_barrel_speed_left_right:{}'.format(dictData['gun_barrel_speed_left_right']))

while True:
    event = socket.poll(timeout = 5000) # wait 5 seconds
    if event == 0:
        print(datetime.datetime.now().time(), 'Pi gets stuck!!!!!!!!!!!!!!!!!!!!!!!!')
        # timeout reached before any events were queued
        pass
    else:
        msg = socket.recv_json()
        # print(msg)
        print('angle:  ', msg['angle'])
        print('height: ', msg['height'])
        print('width:  ', msg['width'])
        print('time:   ', msg['time'])

        print('local:  ', datetime.datetime.now().time())
        # if msg == b'working':
        #     print(datetime.datetime.now().time(), msg)


"""
while True:
    #  Wait for next request from client
    try:
        message = socket.recv(flags = zmq.NOBLOCK)
        # message = socket.recv()

        if message == b'working':
            fault_count = 0
        else:
            fault_count += 1


        if fault_count > 10:
            print("ERROR------------------------")
    except Exception as e:
        print(str(e))
        pass
"""