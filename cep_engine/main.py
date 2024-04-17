#!/usr/bin/env python
import json
import sys
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from datetime import datetime
from pprint import pprint

from confluent_kafka import Consumer, Producer, OFFSET_BEGINNING


def setup_producer(config):
    producer_config = {key: val for key, val in config.items() if key.startswith('bootstrap.servers')}
    return Producer(producer_config)


def format_timestamp(ts_millis):
    return datetime.fromtimestamp(ts_millis / 1000.0).strftime("%d-%m-%Y %H:%M:%S.%f")[:-3]


def generate_alerts(data, producer, threshold):
    if data['average_pred_acc'] < threshold:
        alert_message = (f"{data['server_id']} : [WARNING] : {data['model']}'s accuracy at {data['client_id']} is "
                         f"{round(data['average_pred_acc'], 3)} on {data['timestamp']}")

        producer.produce('accuracy-alerts', key=data['server_id'], value=alert_message)
        producer.poll(0)  # Serve delivery callback


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()

    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])
    config.update(config_parser['consumer'])
    settings = dict(config_parser['settings'])

    # Convert threshold to float
    threshold = float(settings['threshold'])
    consumer = Consumer(config)
    producer = setup_producer(config)


    def reset_offset(consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            consumer.assign(partitions)


    consumer.subscribe(["accuracy-agg"], on_assign=reset_offset)
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            elif msg.error():
                print(f"ERROR: {msg.error()}")
            else:
                message_data = json.loads(msg.value().decode('utf-8'))
                message_data['timestamp'] = format_timestamp(message_data['timestamp'])
                generate_alerts(message_data, producer, threshold)
                print('\nConsumed Topic:', msg.topic())
                pprint(message_data)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        producer.flush()
