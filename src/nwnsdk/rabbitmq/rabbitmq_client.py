#!/usr/bin/env python
import functools
import logging
import threading
from enum import Enum
from typing import Callable, Dict, Optional
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
    StartWorkflowGrowSimulator = "start_work_flow.grow_simulator"

    @staticmethod
    def from_workflow_type(workflow_type: WorkFlowType) -> "Queue":
        if workflow_type == WorkFlowType.GROW_OPTIMIZER:
            return Queue.StartWorkflowOptimizer
        elif workflow_type == WorkFlowType.GROW_SIMULATOR:
            return Queue.StartWorkflowGrowSimulator
        else:
            raise RuntimeError(f"Unimplemented workflow type {workflow_type}. Please implement.")


class RabbitmqClient(threading.Thread):
    rabbitmq_callbacks: Dict[Queue, PikaCallback]
    rabbitmq_is_running: bool
    rabbitmq_config: RabbitmqConfig
    rabbitmq_exchange: str
    rabbitmq_connection: Optional[pika.BlockingConnection]
    rabbitmq_channel: Optional[BlockingChannel]

    def __init__(self, config: RabbitmqConfig):
        super().__init__()
        self.rabbitmq_callbacks = {}
        self.rabbitmq_is_running = False
        self.rabbitmq_config = config
        self.rabbitmq_exchange = config.exchange_name
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None

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

        if not self.rabbitmq_connection or self.rabbitmq_connection.is_closed:
            LOGGER.info("Setting up a new connection to RabbitMQ.")
            self.rabbitmq_connection = pika.BlockingConnection(parameters)

        if not self.rabbitmq_channel or self.rabbitmq_channel.is_closed:
            LOGGER.info("Setting up a new channel to RabbitMQ.")
            self.rabbitmq_channel = self.rabbitmq_connection.channel()
            self.rabbitmq_channel.basic_qos(prefetch_size=0, prefetch_count=1)
            self.rabbitmq_channel.exchange_declare(exchange=self.rabbitmq_exchange, exchange_type="topic")
            for queue_item in Queue:
                queue = self.rabbitmq_channel.queue_declare(queue_item.value, exclusive=False).method.queue
                self.rabbitmq_channel.queue_bind(queue, self.rabbitmq_exchange, routing_key=queue_item.value)

            for queue, callback in self.rabbitmq_callbacks.items():
                self.rabbitmq_channel.basic_consume(queue=queue.value, on_message_callback=callback, auto_ack=False)
        LOGGER.info("Connected to RabbitMQ")

    def _start_rabbitmq(self):
        self._connect_rabbitmq()
        self.start()

    def set_callbacks(self, callbacks: Dict[Queue, PikaCallback]):
        self.rabbitmq_callbacks.update(callbacks)
        for queue, callback in callbacks.items():
            self.rabbitmq_connection.add_callback_threadsafe(
                functools.partial(
                    self.rabbitmq_channel.basic_consume, queue=queue.value, on_message_callback=callback, auto_ack=False
                )
            )

    def run(self):
        self.rabbitmq_is_running = True

        while self.rabbitmq_is_running:
            try:
                LOGGER.info("Waiting for input...")
                while self.rabbitmq_is_running:
                    self.rabbitmq_channel._process_data_events(time_limit=1)
            except pika.exceptions.ConnectionClosedByBroker as exc:
                LOGGER.info('Connection was closed by broker. Reason: "%s". Shutting down...', exc.reply_text)
            except pika.exceptions.ChannelClosedByBroker as exc:
                LOGGER.info('Channel was closed by broker. Reason: "%s". retrying...', exc.reply_text)
                self._connect_rabbitmq()
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
        self.rabbitmq_connection.add_callback_threadsafe(
            functools.partial(
                self.rabbitmq_channel.basic_publish, exchange=self.rabbitmq_exchange, routing_key=queue.value, body=body
            )
        )

    def _stop_rabbitmq(self):
        self.rabbitmq_is_running = False
        if self.rabbitmq_connection:
            self.rabbitmq_connection.add_callback_threadsafe(self.rabbitmq_connection.close)
