from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
import os, sys, argparse, uuid, logging, time, random, threading

logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.INFO)

def delivery_report(err, msg):
    if err:
        logging.info(f'message delivery failed ({msg.topic()} [{str(msg.partition())}]): {err}')
    else:
        logging.info(f"message delivered: {msg.topic()} @ {msg.partition()} ({msg.offset()}) -> {msg.value().decode()}")

uncommited_count = 0
graceful_exit = True

def on_assign(consumer, partitions):        
    for p in partitions:
        logging.info(f'assigned: topic {p.topic} partition {p.partition} offset {p.offset}')


def handle_revokation(producer):
    def on_revoke(consumer, partitions):
        # if the error was raised on pupose
        # don't gracefuly terminate the transaction
        if not graceful_exit:
            return

        for p in partitions:
            logging.info(f'revoking: topic {p.topic} partition {p.partition} offset {p.offset}')

        if uncommited_count > 0:
            try:
                commit_transaction(producer, consumer)
            except:
                abort_transaction(producer)

    return on_revoke

def commit_transaction(producer, consumer):
    # serve delivery reports from previous produce()
    producer.poll(0)

    logging.info('committing transaction....')

    # add the commit of the consumed offsets to the transaction
    producer.send_offsets_to_transaction(
        consumer.position(consumer.assignment()),
        consumer.consumer_group_metadata()
    )

    # commit the transaction
    producer.commit_transaction()

    # new transaction for further commits
    begin_transaction(producer)

def abort_transaction(producer):
    producer.abort_transaction()
    
    begin_transaction(producer)

def begin_transaction(producer):
    global uncommited_count

    # begin new transaction
    producer.begin_transaction()

    # reset the counter
    uncommited_count = 0

def transform(in_msg) -> str:
    return in_msg.value().decode()

# returns true 0.1% of the time
def should_raise() -> bool:
    return random.random() < 0.001

def transform_loop(consumer, input_topic, producer, output_topic):
    global uncommited_count, graceful_exit

    try:
        # init the transaction, clears out any other ones for the given transaction.id
        producer.init_transactions()

        consumer.subscribe(topics=[input_topic], on_assign=on_assign, on_revoke=handle_revokation(producer))
                
        begin_transaction(producer)

        logging.info("starting Consume-Transform-Process loop")
        while True:
            msg = consumer.poll(timeout=0.5)
            if msg is None: continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    logging.info.write('%% %s [%d] reached end at offset %d\n' % (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                logging.info(f"message received: {msg.topic()} @ {msg.partition()} ({msg.offset()}) -> {msg.value().decode()}")

                # synthetic random error to force some transactions to fail sporadically
                if should_raise():
                    logging.info("random error! Boom!")
                    graceful_exit = False
                    sys.exit() 

                out_msg = transform(msg)
                producer.produce(output_topic, value=out_msg, on_delivery=delivery_report)

                # keep track of how many messages need to be commited in the transaction
                uncommited_count += 1                           
            
            if uncommited_count >= 10:
                commit_transaction(producer, consumer)

    finally:
        # close down consumer to commit final offsets.
        logging.info("closing consumer")
        consumer.close()

def parse_config():
    cfg = {}
    cfg['bootstrap_servers'] = os.getenv('BOOTSTRAP_SERVERS', default=None)
    return cfg

def main():
    cfg = parse_config()
    if 'bootstrap_servers' not in cfg:
        logging.error("BOOTSTRAP_SERVERS env var is not define or is empty")
        sys.exit()

    consumer = Consumer({
        'bootstrap.servers': cfg['bootstrap_servers'],
        'enable.auto.commit': False,
        'group.id': 'consistency-worker',
        'auto.offset.reset': 'earliest',
        'isolation.level': 'read_committed'
    })

    producer = Producer({
        'bootstrap.servers': cfg['bootstrap_servers'],
        'transactional.id': f'eos-consistency-{str(uuid.uuid4())}' # exactly-once-semantics
    })

    input_topic = 'consistency-checks-in'
    output_topic = 'consistency-checks-out'
    
    # start the production
    transform_loop(consumer, input_topic, producer, output_topic)

if __name__ == "__main__":
    main()