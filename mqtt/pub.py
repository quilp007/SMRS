import paho.mqtt.client as paho

broker_address = "203.251.78.135"
port=1883

def on_publish(client,userdata,result):             #create function for callback
    print("data published \n")
    pass

client1= paho.Client("control1")                           #create client object
client1.on_publish = on_publish                          #assign function to callback
client1.connect(broker_address,port)                                 #establish connection
ret = client1.publish("house/bulb1","on")                   #publish
