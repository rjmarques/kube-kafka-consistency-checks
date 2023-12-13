from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
import os, sys, time, threading, socket, uuid, logging

logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.INFO)

# indicates if message production is enabled
stopped = False

# map of inflight messages: { uuid -> epoch seconds timestamp }
inflight_messages = {}

def gen_value() -> str:
    return str(uuid.uuid4())

def acked(err, msg):
    if err is not None:
        logging.info("failed to deliver message: %s: %s" % (str(msg), str(err)))
    else:
        logging.debug(f"message produced: {msg.topic()} @ {msg.partition()} ({msg.offset()}) -> {msg.value().decode()}")

def produce_loop(producer, topic):
    if stopped:
        return # stop the production

    # push one record to each partition
    for i in range(4):
        val = gen_value()
        producer.produce(topic, partition=i, value=val, on_delivery=acked)
        inflight_messages[val] = time.time()
        time.sleep(1)
    
    producer.flush()
    threading.Timer(1, produce_loop, (producer, topic)).start()

def consume_loop(consumer, topic):
    global stopped

    try:
        consumer.subscribe(topics=[topic])

        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None: continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    logging.info.write('%% %s [%d] reached end at offset %d\n' % (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                id = msg.value().decode()
                logging.debug(f"message received: {msg.topic()} @ {msg.partition()} ({msg.offset()}) -> {id}")
                if id in inflight_messages:
                    del inflight_messages[id]    
                else:
                    logging.info(f"{id} not found in map!")
                    
    except RuntimeError as err:
        logging.info("err raised in consume loop:", err)
    
    finally:
        # close down consumer to commit final offsets.
        logging.info("terminating consume loop")
        stopped = True
        consumer.close()

def check_for_stuck():
    if stopped:
        return # stop checking

    logging.info("checking for late/stuck messages")
    
    now = time.time()
    for id, ts in inflight_messages.items():
        age_in_seconds = now - ts
        if age_in_seconds > 60:
            logging.info(f'{id} is stil inflight after {age_in_seconds} seconds!')
    
    threading.Timer(10, check_for_stuck).start()

def parse_config():
    cfg = {}
    cfg['bootstrap_servers'] = os.getenv('BOOTSTRAP_SERVERS', default=None)
    return cfg

def main():
    cfg = parse_config()
    if 'bootstrap_servers' not in cfg:
        logging.error("BOOTSTRAP_SERVERS env var is not define or is empty")
        sys.exit()

    producer = Producer({
        'bootstrap.servers': cfg['bootstrap_servers'],
        'client.id': socket.gethostname()
    })
    input_topic = 'consistency-checks-in'

    consumer = Consumer({
        'bootstrap.servers': cfg['bootstrap_servers'],
        'enable.auto.commit': True,
        'group.id': 'consistency-controller',
        'auto.offset.reset': 'earliest',
        'isolation.level': 'read_committed'
    })
    output_topic = 'consistency-checks-out'

    # start the production
    threading.Timer(1, produce_loop, (producer, input_topic)).start()

    # periodically check for stuck messages
    threading.Timer(10, check_for_stuck).start()

    # start the consumption
    consume_loop(consumer, output_topic)


if __name__ == "__main__":
    main()
