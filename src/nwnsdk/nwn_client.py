from uuid import uuid4

from nwnsdk.rabbitmq.rabbitmq_client import RabbitmqClient

import logging
from nwnsdk.postgres.postgres_client import PostgresClient
from nwnsdk import PostgresConfig, RabbitmqConfig, WorkFlowType

LOGGER = logging.getLogger("nwnsdk")


class NwnClient:
    rabbitmq_client: RabbitmqClient
    postgres_client: PostgresClient
    logger: logging.Logger

    def __init__(self, postgres_config: PostgresConfig, rabbitmq_config: RabbitmqConfig):
        self.rabbitmq_client = RabbitmqClient(rabbitmq_config)
        self.postgres_client = PostgresClient(postgres_config)

    def start_work_flow(self, work_flow_type: WorkFlowType, job_name: str, esdl_str: str, user_name: str) -> uuid4:
        job_id: uuid4 = uuid4()
        self.postgres_client.send_input(
            job_id=job_id, job_name=job_name, work_flow_type=work_flow_type, esdl_str=esdl_str, user_name=user_name
        )
        self.rabbitmq_client.send_start_work_flow(job_id, work_flow_type)

        return job_id

    @property
    def db_client(self) -> PostgresClient:
        return self.postgres_client

    @property
    def broker_client(self) -> RabbitmqClient:
        return self.rabbitmq_client
