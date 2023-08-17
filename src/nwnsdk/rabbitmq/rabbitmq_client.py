#!/usr/bin/env python

import logging
from uuid import uuid4

import pika
import json

from pika.adapters.blocking_connection import BlockingChannel

from nwnsdk import RabbitmqConfig

LOGGER = logging.getLogger("nwnsdk")


class RabbitmqClient:
    rabbitmq_exchange: str
    channel: BlockingChannel
    queue: str

    def __init__(self, config: RabbitmqConfig):
        self.rabbitmq_exchange = config.exchange_name

        # initialize rabbitmq connection
        credentials = pika.PlainCredentials(config.user_name, config.password)
        parameters = pika.ConnectionParameters(config.host, config.port, "/", credentials)
        connection = pika.BlockingConnection(parameters)

        self.channel = connection.channel()
        self.channel.exchange_declare(exchange=self.rabbitmq_exchange, exchange_type="topic")
        self.queue = self.channel.queue_declare("", exclusive=True).method.queue
        LOGGER.info("Connected to RabbitMQ")

    def wait_for_data(self):
        # self.bind_lifecycle_topics()

        def callback(ch, method, properties, body):
            topic = method.routing_key

            message = body.decode("utf-8")
            LOGGER.info("[received] {}: {}".format(topic, message))

        self.channel.basic_consume(queue=self.queue, on_message_callback=callback, auto_ack=True)

        LOGGER.info("Waiting for input...")
        self.channel.start_consuming()

    def send_start_work_flow(self, job_id: uuid4, work_flow_type: str):
        # TODO convert to protobuf
        # TODO job_id converted to string for json
        body = json.dumps({"job_id": str(job_id)})
        self.send_output(f"nwn.start_work_flow.{work_flow_type}", body)

    def send_output(self, topic: str, message: str):
        body: bytes = message.encode("utf-8")
        topic += "." + "model_id"
        self.channel.basic_publish(exchange=self.rabbitmq_exchange, routing_key=topic, body=body)
