from uuid import uuid4

from nwnsdk.rabbitmq.rabbitmq_client import RabbitmqClient

from dotenv import load_dotenv
import logging
from .app_logging import setup_logging, LogLevel
from src.nwnsdk.postgres.postgres_client import PostgresClient

LOGGER = logging.getLogger(__name__)

load_dotenv()  # take environment variables from .env


class NwnClient:
    rabbitmq_client: RabbitmqClient
    postgres_client: PostgresClient

    def __init__(self, host: str, user_loglevel: str = "info"):
        setup_logging(LogLevel.parse(user_loglevel))
        self.rabbitmq_client = RabbitmqClient(host)
        self.postgres_client = PostgresClient(host)

    def start_work_flow(self, work_flow_name: str, job_name: str, esdl_str: str, user_name: str):
        job_id: uuid4 = uuid4()
        self.rabbitmq_client.send_start_work_flow(job_id, work_flow_name)
        self.postgres_client.send_input(job_id, job_name, user_name, esdl_str)
