import paho.mqtt.client as mqtt
import json

broker_address = "203.251.78.135"
port = 1883
topic = "device_1/+"
root_topic = "device_1/"

# subscriber callback
def on_message(client, userdata, message):
    rcvData =  str(message.payload.decode("utf-8"))
    print("message received ", rcvData)
    # print("message received ", str(message.payload.decode("utf-8")))
    print("message topic=", message.topic)
    print("message qos=", message.qos)
    print("message retain flag=", message.retain)

    jsonData = json.loads(rcvData) 

    if message.topic == root_topic + 'CMD':
        print("CMD: ", str(jsonData['CH1']))


def on_log(client, userdata, level, buf):
    print("log: ", buf)

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client1.subscribe(topic, qos=2)
        print("connected OK Returned code=",rc)
        print(client)
    else:
        print("Bad connection Returned code=",rc)

def on_disconnect(client, userdata, rc):
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

client1 = mqtt.Client("client1")

client1.on_message = on_message
client1.on_log = on_log
# client1.on_disconnect = on_disconnect
client1.on_connect = on_connect

client1.connect(broker_address)
# client1.subscribe(topic, qos=2)    # => moved to on_connect() callback function

client1.loop_forever()