#!/usr/bin/env python
import json
import time as tm
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from datetime import datetime
from pprint import pprint
from random import uniform, randint
import matplotlib.pyplot as plt
from confluent_kafka import Producer

if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    args = parser.parse_args()

    # Parse the configuration.
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])

    # Create Producer instance
    producer = Producer(config)


    # Optional per-message delivery callback (triggered by poll() or flush())
    # when a message has been successfully delivered or permanently
    # failed delivery (after retries).
    def delivery_callback(err, msg):
        if err:
            print('ERROR: Message failed delivery: {}'.format(err))
        else:
            print('\nProduced Topic: {}'.format(msg.topic()))
            pprint(data)


    topic = "accuracy-raw"
    data_entries = []
    mean_accuracies = [0.7, 0.3, 0.5, 0.8, 0.2]

    start_time = tm.time()
    while tm.time() - start_time < 100:
        current_time = tm.time() - start_time
        cycle_index = int(current_time // 10) % len(mean_accuracies)  # Calculate the current cycle index
        mean_acc = mean_accuracies[cycle_index]

        # Adjust accuracy to fluctuate around the mean (mean_acc)
        pred_accuracy = uniform(mean_acc - 0.1, mean_acc + 0.1)
        added_time = datetime.now()
        data_entries.append((pred_accuracy, added_time))

        data = {
            'server_id': 'server-1',
            'service_id': "animal_classification",
            'client_id': "raspi-1",
            'prediction': randint(0, 1),
            'compute_time': tm.time() - current_time,
            'pred_accuracy': pred_accuracy,
            'total_qoe': uniform(0.7, 0.9),
            'accuracy_qoe': uniform(0.3, 0.5),
            'delay_qoe': uniform(0.3, 0.5),
            'req_acc': uniform(0.7, 0.9),
            'req_delay': uniform(0.2, 0.4),
            'model': 'GoogleNet',
            'added_time': added_time.strftime("%d-%m-%Y %H:%M:%S.%f")[:-3]
        }

        producer.produce(topic, json.dumps(data), data['server_id'], callback=delivery_callback)
        producer.poll(0)  # Serve delivery callback
        tm.sleep(0.1)  # Adjust sleep time as needed to simulate production rate

    # Block until all messages are sent
    producer.poll(10000)
    producer.flush()

    times = [entry[1] for entry in data_entries]
    accuracies = [entry[0] for entry in data_entries]
    plt.figure(figsize=(12, 6))
    plt.plot(times, accuracies, marker='o', linestyle='-', color='b')
    plt.title('Prediction Accuracy Over Time')
    plt.xlabel('Time')
    plt.ylabel('Prediction Accuracy')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(True)
    plt.show()
