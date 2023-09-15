#!/usr/bin/env python

import logging
import threading
from enum import Enum
from typing import Callable, Dict
from uuid import uuid4

import pika
import pika.exceptions
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


class RabbitmqClient(threading.Thread):
    rabbitmq_is_running: bool
    rabbitmq_config: RabbitmqConfig
    rabbitmq_exchange: str
    connection: pika.BlockingConnection
    channel: BlockingChannel
    queue: str

    def __init__(self, config: RabbitmqConfig):
        super().__init__()
        self.rabbitmq_is_running = False
        self.rabbitmq_config = config
        self.rabbitmq_exchange = config.exchange_name

    def _connect_rabbitmq(self):
        # initialize rabbitmq connection
        LOGGER.info(
            "Connecting to RabbitMQ at %s:%s as user %s",
            self.rabbitmq_config.host,
            self.rabbitmq_config.port,
            self.rabbitmq_config.user_name,
        )
        credentials = pika.PlainCredentials(self.rabbitmq_config.user_name, self.rabbitmq_config.password)
        parameters = pika.ConnectionParameters(
            self.rabbitmq_config.host,
            self.rabbitmq_config.port,
            "/",
            credentials,
            heartbeat=60,
            blocked_connection_timeout=3600,
            connection_attempts=10,
        )

        self.connection = pika.BlockingConnection(parameters)

        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_size=0, prefetch_count=1)
        self.channel.exchange_declare(exchange=self.rabbitmq_exchange, exchange_type="topic")
        self.queue = self.channel.queue_declare(Queue.StartWorkflowOptimizer.value, exclusive=False).method.queue
        self.channel.queue_bind(self.queue, self.rabbitmq_exchange, routing_key=Queue.StartWorkflowOptimizer.value)
        LOGGER.info("Connected to RabbitMQ")

    def _start_rabbitmq(self):
        self._connect_rabbitmq()
        self.start()

    def set_callbacks(self, callbacks: Dict[Queue, PikaCallback]):
        for queue, callback in callbacks.items():
            self.connection.add_callback_threadsafe(lambda: self.channel.basic_consume(queue=queue.value,
                                                                                       on_message_callback=callback,
                                                                                       auto_ack=False))

    def run(self):
        self.rabbitmq_is_running = True

        while self.rabbitmq_is_running:
            try:
                LOGGER.info("Waiting for input...")
                while self.rabbitmq_is_running:
                    self.connection.process_data_events(time_limit=1)
            except pika.exceptions.ConnectionClosedByBroker as exc:
                LOGGER.info('Connection was closed by broker. Reason: "%s". Shutting down...', exc.reply_text)
            except pika.exceptions.AMQPConnectionError:
                LOGGER.info("Connection was lost, retrying...")
                self._connect_rabbitmq()

    def _send_start_work_flow(self, job_id: uuid4, work_flow_type: WorkFlowType):
        # TODO convert to protobuf
        # TODO job_id converted to string for json
        body = json.dumps({"job_id": str(job_id)})
        self._send_output(Queue.from_workflow_type(work_flow_type), body)

    def _send_output(self, queue: Queue, message: str):
        body: bytes = message.encode("utf-8")
        self.connection.add_callback_threadsafe(lambda: self.channel.basic_publish(exchange=self.rabbitmq_exchange,
                                                                                   routing_key=queue.value,
                                                                                   body=body))

    def _stop_rabbitmq(self):
        self.rabbitmq_is_running = False
        if self.connection:
            self.connection.add_callback_threadsafe(lambda: self.connection.close())
