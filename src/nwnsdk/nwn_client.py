from uuid import uuid4

from nwnsdk.rabbitmq.rabbitmq_client import RabbitmqClient

from dotenv import load_dotenv
import logging
from nwnsdk.app_logging import setup_logging, LogLevel
from nwnsdk.postgres.postgres_client import PostgresClient

LOGGER = logging.getLogger('nwnsdk')

load_dotenv()  # take environment variables from .env

class PostgresConfig:
    username: str
    password: str


class NwnClient:
    rabbitmq_client: RabbitmqClient
    postgres_client: PostgresClient
    logger: logging.Logger

    def __init__(self,
                 postgres_config: PostgresConfig,
                 host: str, user_loglevel: str = "info"):
        self.logger = setup_logging(LogLevel.parse(user_loglevel))
        self.rabbitmq_client = RabbitmqClient(host)
        self.postgres_client = PostgresClient(host)

    def start_work_flow(self, work_flow_type: str, job_name: str, esdl_str: str, user_name: str) -> uuid4:
        job_id: uuid4 = uuid4()
        self.postgres_client.send_input(job_id, job_name, work_flow_type, user_name, esdl_str)
        self.rabbitmq_client.send_start_work_flow(job_id, work_flow_type)

        return job_id

    @property
    def db_client(self):
        return self.postgres_client
