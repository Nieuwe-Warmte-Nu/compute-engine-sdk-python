from dataclasses import dataclass
from typing import List
from uuid import uuid4

from nwnsdk.postgres.dbmodels import Job
from nwnsdk.rabbitmq.rabbitmq_client import RabbitmqClient

import logging
from nwnsdk.postgres.postgres_client import PostgresClient
from nwnsdk import PostgresConfig, RabbitmqConfig, WorkFlowType, JobStatus

LOGGER = logging.getLogger("nwnsdk")


class NwnClient:
    rabbitmq_client: RabbitmqClient
    postgres_client: PostgresClient
    logger: logging.Logger

    def __init__(self, postgres_config: PostgresConfig, rabbitmq_config: RabbitmqConfig):
        self.rabbitmq_client = RabbitmqClient(rabbitmq_config)
        self.postgres_client = PostgresClient(postgres_config)

    def start_work_flow(
            self, work_flow_type: WorkFlowType, job_name: str, esdl_str: str, user_name: str, project_name: str
    ) -> uuid4:
        job_id: uuid4 = uuid4()
        self.postgres_client.send_input(
            job_id=job_id,
            job_name=job_name,
            work_flow_type=work_flow_type,
            esdl_str=esdl_str,
            user_name=user_name,
            project_name=project_name,
        )
        self.rabbitmq_client.send_start_work_flow(job_id, work_flow_type)

        return job_id

    def get_job_status(self, job_id: uuid4) -> JobStatus:
        return self.postgres_client.get_job_status(job_id)

    def get_job_input_esdl(self, job_id: uuid4) -> str:
        return self.postgres_client.get_job_input_esdl(job_id)

    def get_job_output_esdl(self, job_id: uuid4) -> str:
        return self.postgres_client.get_job_output_esdl(job_id)

    def get_job_logs(self, job_id: uuid4) -> str:
        return self.postgres_client.get_job_logs(job_id)

    def get_job_details(self, job_id: uuid4) -> Job:
        return self.postgres_client.get_job(job_id)

    def get_all_jobs(self) -> List[Job]:
        return self.postgres_client.get_jobs()

    def get_jobs_from_ids(self, job_ids: List[uuid4]) -> List[Job]:
        return self.postgres_client.get_jobs(job_ids)

    def get_jobs_from_user(self, user_name: str) -> List[Job]:
        return self.postgres_client.get_jobs_from_user(user_name)

    def get_jobs_from_project(self, project_name: str) -> List[Job]:
        return self.postgres_client.get_jobs_from_project(project_name)

    def delete_job(self, job_id: uuid4) -> bool:
        return self.postgres_client.delete_job(job_id)

    @property
    def db_client(self) -> PostgresClient:
        return self.postgres_client

    @property
    def broker_client(self) -> RabbitmqClient:
        return self.rabbitmq_client
