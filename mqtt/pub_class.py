import paho.mqtt.client as mqtt
import json

broker_address = "203.251.78.135"
port = 1883
topic = "device_1/+"
root_topic = "device_1/"

class PUB_MQTT:
    def __init__(self, _broker_address = broker_address, _port = port, _topic = topic ):
        self.topic = _topic
        self.broker_address = _broker_address
        print("class init")
        self.client1 = mqtt.Client("control1")
        self.client1.on_publish = self.on_publish
        # self.client1.connect(self.broker_ress)
        self.client1.loop_start()

    def on_publish(self, client, userdata, result):             #create function for callback
        print("data published \n")
        pass

    def send_msg(self, topic, msg):
        self.client1.connect(self.broker_address)
        ret = self.client1.publish(topic, msg)

if __name__ == "__main__":
    print("main start")
    sub = PUB_MQTT()
