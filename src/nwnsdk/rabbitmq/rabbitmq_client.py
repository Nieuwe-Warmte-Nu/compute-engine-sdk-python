#!/usr/bin/env python

import os
import logging
from uuid import uuid4

import pika
import json
import traceback
from json import JSONDecodeError

LOGGER = logging.getLogger(__name__)


class RabbitmqClient:
    def __init__(self, host: str):
        self.rabbitmq_exchange = os.getenv("RABBITMQ_EXCHANGE")

        # initialize rabbitmq connection
        credentials = pika.PlainCredentials(os.getenv("RABBITMQ_ROOT_USER"), os.getenv("RABBITMQ_ROOT_PASSWORD"))
        parameters = pika.ConnectionParameters(host, 5672, "/", credentials)
        connection = pika.BlockingConnection(parameters)

        self.channel = connection.channel()
        self.channel.exchange_declare(exchange=self.rabbitmq_exchange, exchange_type="topic")
        self.queue = self.channel.queue_declare("", exclusive=True).method.queue
        LOGGER.info("Connected to RabbitMQ")

    # def wait_for_data(self):
    #     self.bind_lifecycle_topics()
    #
    #     def callback(ch, method, properties, body):
    #         topic = method.routing_key
    #
    #         message = body.decode("utf-8")
    #         LOGGER.info(" [received] {}: {}".format(topic, message))
    #
    #     self.channel.basic_consume(queue=self.queue, on_message_callback=callback, auto_ack=True)
    #
    #     LOGGER.info("Waiting for input...")
    #     self.channel.start_consuming()

    def send_start_work_flow(self, job_id: uuid4, work_flow_name: str):
        # TODO convert to protobuf
        # TODO job_id converted to string for json
        body = json.dumps({"job_id": str(job_id), "work_flow_name": work_flow_name})
        self.send_output(f"nwn.start_work_flow", body)

    def send_output(self, topic: str, message: str):
        body: bytes = message.encode("utf-8")
        topic += "." + "model_id"
        self.channel.basic_publish(exchange=self.rabbitmq_exchange, routing_key=topic, body=body)
