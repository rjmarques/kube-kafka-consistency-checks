from confluent_kafka import Consumer, KafkaError, KafkaException
from utils.time import millis_to_datetime

def print_assignment(consumer, partitions):
    for p in partitions:
        print(f'Assigned: topic {p.topic} partition {p.partition} offset {p.offset}')

def consume_loop(consumer, topic):
    try:
        consumer.subscribe(topics=[topic], on_assign=print_assignment)

        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None: continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    print.write('%% %s [%d] reached end at offset %d\n' % (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                print(f"Message received: {msg.topic()} @ {msg.partition()} ({msg.offset()}) - {millis_to_datetime(msg.timestamp()[1])}")
                consumer.commit(asynchronous=False)
                # TODO msg process

    finally:
        # Close down consumer to commit final offsets.
        consumer.close()

def main():
    conf = {
        'bootstrap.servers': 'localhost:29092',
        'enable.auto.commit': 'false',
        'group.id': 'consistency-worker',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    topic = 'consistency-checks-in'
    
    # start the production
    consume_loop(consumer, topic)

if __name__ == "__main__":
    main()