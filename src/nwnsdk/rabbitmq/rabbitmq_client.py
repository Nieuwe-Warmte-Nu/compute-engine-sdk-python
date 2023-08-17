#!/usr/bin/env python

import logging
from enum import Enum
import signal
from typing import Callable, Dict
from uuid import uuid4

import pika
import json

from pika.adapters.blocking_connection import BlockingChannel

from nwnsdk import RabbitmqConfig, WorkFlowType

LOGGER = logging.getLogger("nwnsdk")


PikaCallback = Callable[
    [pika.adapters.blocking_connection.BlockingChannel, pika.spec.Basic.Deliver, pika.spec.BasicProperties, bytes], None
]


class Queue(Enum):
    StartWorkflowOptimizer = "start_work_flow.optimizer"

    @staticmethod
    def from_workflow_type(workflow_type: WorkFlowType) -> "Queue":
        if workflow_type == WorkFlowType.GROWTH_OPTIMIZER:
            return Queue.StartWorkflowOptimizer
        else:
            raise RuntimeError(f"Unimplemented workflow type {workflow_type}. Please implement.")


class RabbitmqClient:
    rabbitmq_exchange: str
    channel: BlockingChannel
    queue: str

    def __init__(self, config: RabbitmqConfig):
        self.rabbitmq_exchange = config.exchange_name

        # initialize rabbitmq connection
        LOGGER.info("Connecting to RabbitMQ at %s:%s as user %s", config.host, config.port, config.user_name)
        credentials = pika.PlainCredentials(config.user_name, config.password)
        parameters = pika.ConnectionParameters(
            config.host, config.port, "/", credentials, heartbeat=3600, blocked_connection_timeout=3600
        )

        connection = pika.BlockingConnection(parameters)

        self.channel = connection.channel()
        self.channel.basic_qos(prefetch_size=0, prefetch_count=1)
        self.channel.exchange_declare(exchange=self.rabbitmq_exchange, exchange_type="topic")
        self.queue = self.channel.queue_declare(Queue.StartWorkflowOptimizer.value, exclusive=False).method.queue
        self.channel.queue_bind(self.queue, self.rabbitmq_exchange, routing_key=Queue.StartWorkflowOptimizer.value)
        LOGGER.info("Connected to RabbitMQ")

    def wait_for_data(self, callbacks: Dict[Queue, PikaCallback]):
        for queue, callback in callbacks.items():
            self.channel.basic_consume(queue=queue.value, on_message_callback=callback, auto_ack=False)

        def stop(signal, frame):
            LOGGER.info("Received signal %s. Stopping..", signal)
            self.channel.stop_consuming()

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)

        LOGGER.info("Waiting for input...")
        self.channel.start_consuming()

    def send_start_work_flow(self, job_id: uuid4, work_flow_type: WorkFlowType):
        # TODO convert to protobuf
        # TODO job_id converted to string for json
        body = json.dumps({"job_id": str(job_id)})
        self.send_output(Queue.from_workflow_type(work_flow_type), body)

    def send_output(self, queue: Queue, message: str):
        body: bytes = message.encode("utf-8")
        self.channel.basic_publish(exchange=self.rabbitmq_exchange, routing_key=queue.value, body=body)
