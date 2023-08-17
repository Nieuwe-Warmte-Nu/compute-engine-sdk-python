from datetime import datetime
import logging
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from nwnsdk import PostgresConfig, WorkFlowType
from nwnsdk.postgres.database import initialize_db, session_scope
from nwnsdk.postgres.dbmodels import Job, JobStatus

LOGGER = logging.getLogger("nwnsdk")


class PostgresClient:
    def __init__(self, postgres_config: PostgresConfig):
        initialize_db("nwn", postgres_config)

    def send_input(
        self, job_id: uuid4, job_name: str, work_flow_type: WorkFlowType, esdl_str: str, user_name: str
    ) -> None:
        with session_scope() as session:
            new_job = Job(
                job_id=job_id,
                job_name=job_name,
                work_flow_type=work_flow_type.value,
                map_editor_user=user_name,
                status="registered",
                input_esdl=esdl_str,
                added_at=datetime.now(),
            )
            session.add(new_job)

    def retrieve_input_esdl(self, job_id: uuid4) -> str:
        session: Session
        LOGGER.debug("Retrieving esdl for job %s", job_id)
        with session_scope() as session:
            stmnt = select(Job.input_esdl).where(Job.job_id == job_id)
            input_esdl: str = session.scalar(stmnt)
        return input_esdl

    def set_job_running(self, job_id: uuid4) -> None:
        session: Session
        LOGGER.debug("Started job %s", job_id)
        with session_scope() as session:
            stmnt = (
                update(Job)
                .where(Job.job_id == job_id)
                .values(status=JobStatus.RUNNING.value, running_at=datetime.now())
            )
            session.execute(stmnt)

    def store_job_result(self, job_id: uuid4, new_logs: str, new_status: JobStatus, output_esdl: str):
        session: Session
        LOGGER.debug(
            "Stored job result %s with exit code %s, status %s and %s characters of log",
            job_id,
            new_status,
            len(new_logs),
        )
        with session_scope() as session:
            stmnt = (
                update(Job)
                .where(Job.job_id == job_id)
                .values(status=new_status.value, logs=new_logs, output_esdl=output_esdl, stopped_at=datetime.now())
            )
            session.execute(stmnt)

    def get_job(self, job_id: uuid4) -> Job:
        session: Session
        LOGGER.debug("Retrieving job data for job %s", job_id)
        with session_scope() as session:
            stmnt = select(Job).where(Job.job_id == job_id)
            job: Job = session.scalar(stmnt)
        return job
