
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
def on_connect(client, userdata, flags, rc, properties=None):  #
    print("✅ Connected to the broker!")
    # نشترك في التوبيك اللي هنستقبل منه
    client.subscribe(TOPIC_SUBSCRIBE)
    print(f"✅ subscribed to topic: {TOPIC_SUBSCRIBE}")
    print(f"✅ send 'Hello World' every 5seconds on {TOPIC_PUBLISH}\n")

def on_message(client, userdata, msg):
    # دي بتتنفذ كل ما يجيلك رسالة على التوبيك اللي مشترك فيه
    print(f"🟢 get a message on  {msg.topic} → {msg.payload.decode()}")

#3.client-config
client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message

print("conneting ....")
client.connect(BROKER, PORT)   #async

# Thread 1
client.loop_start()


def publisher_loop():
    while True:
        message = "Hello World"
        client.publish(TOPIC_PUBLISH, message)
        print(f"🔵I sent: {message} → {TOPIC_PUBLISH}")
        time.sleep(5) 

#Thread 2
threading.Thread(target=publisher_loop, daemon=True).start()


# to Stop 
#Thread 3
try:
    while True:
        time.sleep(1)  # خلي البرنامج كله كله شغال إلى ما لا نهاية
except KeyboardInterrupt:
    print("\n Done")
    client.loop_stop()
    client.disconnect()
    print("good")