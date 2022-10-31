import paho.mqtt.client as mqtt
import json
from PyQt5 import QtCore, QtWidgets

broker_address = "203.251.78.135"
port = 1883
topic = "device_1/+"
# root_topic = "device_1/"
client = 'client'
MQTT_DEBUG = False

class SUB_MQTT(QtCore.QObject):

    messageSignal = QtCore.pyqtSignal(str, str)

    # def __init__(self, _on_message, broker_addr = broker_address, _port = port, _topic = topic):
    def __init__(self, _broker_address = broker_address, _port = port, _topic = topic, _client = client, _mqtt_debug = False):
        super().__init__()
        self.topic = _topic
        print(_topic, _client)
        self.broker_address = _broker_address
        print("class init")
        self.client1 = mqtt.Client(_client)
        # self.pub_client = mqtt.Client("pub client")

        if _client == 'client_r_pi' or _client == 'client_r_pi_test' or _client == 'client_r_pi_test1':
            self.client1.username_pw_set(username="steve",password="password")

        # self.client1.username_pw_set(username="steve", password="password")

        global MQTT_DEBUG
        MQTT_DEBUG = _mqtt_debug

        self.client1.on_message = self.on_message
        self.client1.on_log = self.on_log
        self.client1.on_disconnect = self.on_disconnect
        self.client1.on_connect = self.on_connect

        # self.pub_client.on_publish = self.on_publish
        self.client1.on_publish = self.on_publish

        self.client1.connect(_broker_address)
        # client1.subscribe(topic, qos=2)    # => moved to on_connect() callback function

        # self.client1.loop_forever()
        # self.client1.loop_start()

        self.login_ok = False

    def on_publish(self, client, userdata, result):             #create function for callback
        if MQTT_DEBUG:
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
        if MQTT_DEBUG:
            print("message topic=", message.topic)
            print("message qos=", message.qos)
            print("message retain flag=", message.retain)

        # jsonData = json.loads(rcvData) 
        # self.messageSignal.emit(road_temp)

        self.messageSignal.emit(rcvData, message.topic)

    def on_log(self, client, userdata, level, buf):
        if MQTT_DEBUG:
            print("log: ", buf)
        else:
            return

    def on_connect(self, client, userdata, flags, rc):
        if rc==0:
            # self.client1.subscribe(topic, qos=2)
            self.client1.subscribe(self.topic, qos=2)
            print("connected OK Returned code=",rc)
            print(client)

            self.login_ok = True
        else:
            print("Bad connection Returned code=",rc)

    def on_disconnect(self, client, userdata, rc):
       self.login_ok = False
       print("Client Got Disconnected")
       if rc != 0:
           print('Unexpected MQTT disconnection. Will auto-reconnect')

       else:
           print('rc value:' + str(rc))

       try:
           print("Trying to Reconnect")
           client.connect(broker_address, port)
           client.subscribe(topic)

           print('tried to subscribe')
       except:
           print("Error in Retrying to Connect with Broker")

if __name__ == "__main__":
    print("main start")
    sub = SUB_MQTT()