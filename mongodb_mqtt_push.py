# bash
from pymongo import MongoClient
from datetime import datetime
import time
import json
import numpy as np

import mqtt.pub_class as pc
import mqtt.sub_class as sc


ip = '203.251.78.135'

#mqtt
port = 1883
topic = "device_1/+"
root_topic = "device_1/"

userid = 'smrs_1'
passwd = 'smrs2580_1!'

# client = MongoClient(host='localhost', port=27017)
# client = MongoClient(host=ip, port=27017)
client = MongoClient('mongodb://' + ip,
                    username = userid,
                    password =  passwd,
                    authSource = 'road_1')

print(client.list_database_names())

db_test = client['road_1']
print(db_test.list_collection_names())

coll_device = db_test['device_1']
# print(coll_weather.list_document_names())

def on_message_callback(msg, topic):
    jsonData = json.loads(msg) 
    if topic == root_topic + 'CMD':
        print('received CMD!!!')
        print("CMD: ", "CH1: ", str(jsonData['CH1']))
        print("CMD: ", "CH2: ", str(jsonData['CH2']))


"""
MQTT init
"""
# pub_mqtt = pc.PUB_MQTT(_broker_address = ip)
sub_mqtt = sc.SUB_MQTT(_broker_address = ip, _topic = 'device_1/CMD')
sub_mqtt.messageSignal.connect(on_message_callback)
sub_mqtt.loop_start_func()

temp_data = {}

idx = 0

x_size = 720
sine_x_data = np.linspace(-np.pi, np.pi, x_size)
sine_y_data = np.zeros(x_size)



while True:
    sine_value = np.sin(sine_x_data[idx%x_size])
    # temp_data['_id'] = idx
    temp_data['road_temp'] = sine_value
    temp_data['road_humidity'] = sine_value * 5 
    temp_data['air_temp'] = sine_value * 10 
    temp_data['timestamp'] = datetime.now()
    temp_data['metadata'] = {"sensorId": idx, "type": "sensor data"}

    result = coll_device.insert_one(temp_data)

    print("inserted data", temp_data['timestamp'])

    del temp_data['_id']
    # del temp_data['timestamp']
    temp_data['timestamp'] = str(temp_data['timestamp'])
    # pub_mqtt.send_msg(root_topic+"DATA", json.dumps(temp_data))
    sub_mqtt.send_msg(root_topic+"DATA", json.dumps(temp_data))

    idx += 1

    time.sleep(1)
