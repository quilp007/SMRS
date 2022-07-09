# bash
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic, QtTest, QtGui, QtCore

from pymongo import MongoClient
from datetime import datetime
import time
import json
import numpy as np

import mqtt.pub_class as pc
import mqtt.sub_class as sc


server_ip = '203.251.78.135'

#mqtt
port = 1883
topic = "device_1/+"
# root_topic = "device_1/"
pub_root_topic = "R_PI/"
sub_root_topic = "APP/"

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

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setupUi(self)

        """
        MQTT init
        """
        # pub_mqtt = pc.PUB_MQTT(_broker_address = ip)
        self.sub_mqtt = sc.SUB_MQTT(_broker_address=ip, _topic=sub_root_topic+'CMD', _client='client_r_pi')
        # self.sub_mqtt.messageSignal.connect(self.on_message_callback)

        self.temp_data = {}

        self.idx = 0

        self.x_size = 720
        self.sine_x_data = np.linspace(-np.pi, np.pi, self.x_size)
        self.sine_y_data = np.zeros(self.x_size)


        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000) # 100ms 
        self.timer.timeout.connect(self.send_msg_loop_timer)

        # start loop for drawing graph #################
        self.timer.start()
        ################################################

    @QtCore.pyqtSlot(str, str)
    def on_message_callback(self, msg, topic):
        jsonData = json.loads(msg) 
        if topic == sub_root_topic + 'CMD':
            print('received CMD!!!')
            print("CMD: ", "CH1: ", str(jsonData['CH1']))
            print("CMD: ", "CH2: ", str(jsonData['CH2']))


    def send_msg_loop_timer(self):
        sine_value = np.sin(self.sine_x_data[self.idx%self.x_size])
        # temp_data['_id'] = idx
        self.temp_data['road_temp'] = sine_value
        self.temp_data['road_humidity'] = sine_value * 5 
        self.temp_data['air_temp'] = sine_value * 10 
        self.temp_data['timestamp'] = datetime.now()
        self.temp_data['metadata'] = {"sensorId": self.idx, "type": "sensor data"}

        result = coll_device.insert_one(self.temp_data)

        print("inserted data", self.temp_data['timestamp'])

        del self.temp_data['_id']
        # del temp_data['timestamp']
        self.temp_data['timestamp'] = str(self.temp_data['timestamp'])
        # pub_mqtt.send_msg(root_topic+"DATA", json.dumps(temp_data))
        self.sub_mqtt.send_msg(pub_root_topic+"DATA", json.dumps(self.temp_data))

        self.idx += 1


    def send_msg_loop(self):
        while True:
            sine_value = np.sin(self.sine_x_data[self.idx%self.x_size])
            # temp_data['_id'] = idx
            self.temp_data['road_temp'] = sine_value
            self.temp_data['road_humidity'] = sine_value * 5 
            self.temp_data['air_temp'] = sine_value * 10 
            self.temp_data['timestamp'] = datetime.now()
            self.temp_data['metadata'] = {"sensorId": self.idx, "type": "sensor data"}

            result = coll_device.insert_one(self.temp_data)

            print("inserted data", self.temp_data['timestamp'])

            del self.temp_data['_id']
            # del temp_data['timestamp']
            self.temp_data['timestamp'] = str(self.temp_data['timestamp'])
            # pub_mqtt.send_msg(root_topic+"DATA", json.dumps(temp_data))
            self.sub_mqtt.send_msg(pub_root_topic+"DATA", json.dumps(self.temp_data))

            self.idx += 1

            time.sleep(1)


    def loop_start_func(self):
        self.sub_mqtt.messageSignal.connect(self.on_message_callback)
        self.sub_mqtt.loop_start_func()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()

    ex.loop_start_func()

    # ex.send_msg_loop()

    sys.exit(app.exec_())