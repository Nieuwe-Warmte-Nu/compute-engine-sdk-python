from dataclasses import dataclass
from typing import List, Callable, Dict
from uuid import uuid4

from nwnsdk.postgres.dbmodels import Job
from nwnsdk.rabbitmq.rabbitmq_client import RabbitmqClient, Queue, PikaCallback

import logging
from nwnsdk.postgres.postgres_client import PostgresClient
from nwnsdk import PostgresConfig, RabbitmqConfig, WorkFlowType, JobStatus

LOGGER = logging.getLogger("nwnsdk")


class NwnClient(PostgresClient, RabbitmqClient):
    rabbitmq_client: RabbitmqClient
    postgres_client: PostgresClient
    logger: logging.Logger

    def __init__(self, postgres_config: PostgresConfig, rabbitmq_config: RabbitmqConfig):
        PostgresClient.__init__(self, postgres_config)
        RabbitmqClient.__init__(self, rabbitmq_config)

    def connect(self):
        PostgresClient._connect_postgres(self)
        RabbitmqClient._start_rabbitmq(self)

    def stop(self):
        PostgresClient._close_postgres(self)
        RabbitmqClient._stop_rabbitmq(self)

    def start_work_flow(
        self, work_flow_type: WorkFlowType, job_name: str, esdl_str: str, user_name: str, project_name: str
    ) -> uuid4:
        job_id: uuid4 = uuid4()
        PostgresClient._send_input(
            self,
            job_id=job_id,
            job_name=job_name,
            work_flow_type=work_flow_type,
            esdl_str=esdl_str,
            user_name=user_name,
            project_name=project_name,
        )
        RabbitmqClient._send_start_work_flow(self, job_id, work_flow_type)

        return job_id

    def get_job_details(self, job_id: uuid4) -> Job:
        return self.get_job(job_id)

    def get_all_jobs(self) -> List[Job]:
        return self.get_jobs()

    def get_jobs_from_ids(self, job_ids: List[uuid4]) -> List[Job]:
        return self.get_jobs(job_ids)
