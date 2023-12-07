
from confluent_kafka import Producer
import threading
import socket
from time import sleep
from utils.time import millis_to_datetime

def acked(err, msg):
    if err is not None:
        print("Failed to deliver message: %s: %s" % (str(msg), str(err)))
    else:
        print(f"Message produced: {msg.topic()} @ {msg.partition()} ({msg.offset()}) - {millis_to_datetime(msg.timestamp()[1])}")

def produce_loop(prd, topic):
    # push one record to each partition
    for i in range(4):
        prd.produce(topic, partition=i, value=f"foo_{i}", on_delivery=acked)
        sleep(1)
    
    prd.flush()
    threading.Timer(1, produce_loop(prd, topic)).start()

def main():
    conf = {
        'bootstrap.servers': 'localhost:29092',
        'client.id': socket.gethostname()
    }

    producer = Producer(conf)
    topic = 'consistency-checks-in'
    
    # start the production
    produce_loop(producer, topic)

if __name__ == "__main__":
    main()
