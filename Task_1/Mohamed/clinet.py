
import paho.mqtt.client as mqtt  #to connect to any broker
import time                      # delays
import threading                 # parallel tasks - to be always connected

#1- config
BROKER = "broker.emqx.io"    # Free Public MQTT Broker
PORT = 1883


TOPIC_PUBLISH = "/mido/hello"      
TOPIC_SUBSCRIBE = "/mido/control"  

CLIENT_ID = "Mido_PC_Publisher_Subscriber"  

#2.Fun
def on_connect(client, userdata, flags, rc, properties=None):  # 🔴most used
    print("✅ Connected to the broker!")
    # subsribe to topic and take sensors' read
    client.subscribe(TOPIC_SUBSCRIBE)
    print(f"✅ subscribed to topic: {TOPIC_SUBSCRIBE}")
    print(f"✅ send 'Hello World' every 5seconds on {TOPIC_PUBLISH}\n")

def on_message(client, userdata, msg):
    # if there thing to recive.
    print(f"🟢 get a message on  {msg.topic} → {msg.payload.decode()}")

#3.client-config
client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5) # create with id & version
client.on_connect = on_connect
client.on_message = on_message

print("conneting ....")
client.connect(BROKER, PORT)   #async  .....then call on_connect 

# Thread 2 ...subscribe +.....connect
client.loop_start()

#client.loop() after each line +... it stop the code


def publisher_loop():
    while True:
        message = "Hello World"
        client.publish(TOPIC_PUBLISH, message)
        print(f"🔵I sent: {message} → {TOPIC_PUBLISH}")
        time.sleep(5) 

#Thread 3 ....publish
threading.Thread(target=publisher_loop, daemon=True).start()  #cotain... follwer ... run 


# to Stop 
#Thread ..
try:
    while True:
        time.sleep(1)  
except KeyboardInterrupt:
    print("\n Done")
    client.loop_stop() # end thread (what for recive + check conneting)
    client.disconnect() # 
    print("good")