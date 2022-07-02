import paho.mqtt.client as mqtt
import json
from PyQt5 import QtCore, QtWidgets

broker_address = "203.251.78.135"
port = 1883
topic = "device_1/+"
root_topic = "device_1/"

class SUB_MQTT(QtCore.QObject):

    # messageSignal = QtCore.pyqtSignal(float)
    messageSignal = QtCore.pyqtSignal(str, str)

    # def __init__(self, _on_message, broker_addr = broker_address, _port = port, _topic = topic):
    def __init__(self, broker_addr = broker_address, _port = port, _topic = topic):
        super().__init__()
        self.topic = _topic
        self.broker_address = broker_addr
        print("class init")
        self.client1 = mqtt.Client("client1")
        self.pub_client = mqtt.Client("pub client")

        self.client1.on_message = self.on_message
        # self.client1.on_message = _on_message()
        self.client1.on_log = self.on_log
        # self.client1.on_disconnect = self.on_disconnect
        self.client1.on_connect = self.on_connect

        self.pub_client.on_publish = self.on_publish

        self.client1.connect(broker_addr)
        # client1.subscribe(topic, qos=2)    # => moved to on_connect() callback function

        # self.client1.loop_forever()
        # self.client1.loop_start()

    def on_publish(self, client, userdata, result):             #create function for callback
        print("data published \n")
        pass

    def send_msg(self, topic, msg):
        # self.pub_client.connect(self.broker_address)
        ret = self.client1.publish(topic, msg)

    def loop_start_func(self):
        # self.client1.loop_forever()
        self.client1.loop_start()

    # subscriber callback
    def on_message(self, client, userdata, message):
        rcvData = message.payload.decode("utf-8")
        # rcvData = str(message.payload.decode("utf-8"))
        # print("message received ", rcvData)
        print("message topic=", message.topic)
        print("message qos=", message.qos)
        print("message retain flag=", message.retain)

        # if message.topic == root_topic + 'CMD':
        #     print("CMD: ", str(jsonData['CH1']))

        jsonData = json.loads(rcvData) 
        road_temp = jsonData['road_temp']
        # self.messageSignal.emit(road_temp)

        self.messageSignal.emit(rcvData, message.topic)

    def on_log(self, client, userdata, level, buf):
        print("log: ", buf)

    def on_connect(self, client, userdata, flags, rc):
        if rc==0:
            # self.client1.subscribe(topic, qos=2)
            self.client1.subscribe(self.topic, qos=2)
            print("connected OK Returned code=",rc)
            print(client)
        else:
            print("Bad connection Returned code=",rc)

if __name__ == "__main__":
    print("main start")
    sub = SUB_MQTT()