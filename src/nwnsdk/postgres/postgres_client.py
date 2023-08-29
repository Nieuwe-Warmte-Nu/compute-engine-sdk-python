from datetime import datetime
import logging
from typing import List
from uuid import uuid4

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from sqlalchemy.orm.strategy_options import load_only
from sqlalchemy.engine import Engine

from nwnsdk import PostgresConfig, WorkFlowType
from nwnsdk.postgres.database import initialize_db, session_scope
from nwnsdk.postgres.dbmodels import Job, JobStatus

LOGGER = logging.getLogger("nwnsdk")

ALL_JOBS_STMNT = select(Job).options(
    load_only(
        Job.job_id,
        Job.job_name,
        Job.work_flow_type,
        Job.user_name,
        Job.project_name,
        Job.status,
        Job.added_at,
        Job.running_at,
        Job.stopped_at,
    )
)


class PostgresClient:
    db_config: PostgresConfig
    engine: Engine

    def __init__(self, postgres_config: PostgresConfig):
        self.db_config = postgres_config

    def _connect_postgres(self):
        self.engine = initialize_db("nwn", self.db_config)

    def _close_postgres(self):
        if self.engine:
            self.engine.dispose()

    def _send_input(
        self,
        job_id: uuid4,
        job_name: str,
        work_flow_type: WorkFlowType,
        esdl_str: str,
        user_name: str,
        project_name: str,
    ) -> None:
        with session_scope() as session:
            new_job = Job(
                job_id=job_id,
                job_name=job_name,
                work_flow_type=work_flow_type,
                user_name=user_name,
                project_name=project_name,
                status=JobStatus.REGISTERED,
                input_esdl=esdl_str,
                added_at=datetime.now(),
            )
            session.add(new_job)

    def set_job_running(self, job_id: uuid4) -> None:
        LOGGER.debug("Started job with id '%s'", job_id)
        with session_scope() as session:
            stmnt = update(Job).where(Job.job_id == job_id).values(status=JobStatus.RUNNING, running_at=datetime.now())
            session.execute(stmnt)

    def store_job_result(self, job_id: uuid4, new_logs: str, new_status: JobStatus, output_esdl: str):
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
                .values(status=new_status, logs=new_logs, output_esdl=output_esdl, stopped_at=datetime.now())
            )
            session.execute(stmnt)

    def get_job_status(self, job_id: uuid4) -> JobStatus:
        LOGGER.debug("Retrieving job status for job with id '%s'", job_id)
        with session_scope(do_expunge=True) as session:
            stmnt = select(Job.status).where(Job.job_id == job_id)
            job_status = session.scalar(stmnt)
        return job_status

    def get_job_input_esdl(self, job_id: uuid4) -> str:
        LOGGER.debug("Retrieving input esdl for job %s", job_id)
        with session_scope(do_expunge=True) as session:
            stmnt = select(Job.input_esdl).where(Job.job_id == (job_id))
            job_input_esdl: str = session.scalar(stmnt)
        return job_input_esdl

    def get_job_output_esdl(self, job_id: uuid4) -> str:
        LOGGER.debug("Retrieving job output esdl for job with id '%s'", job_id)
        with session_scope() as session:
            stmnt = select(Job.output_esdl).where(Job.job_id == job_id)
            job_output_esdl: Job = session.scalar(stmnt)
        return job_output_esdl

    def get_job_logs(self, job_id: uuid4) -> str:
        LOGGER.debug("Retrieving job log for job with id '%s'", job_id)
        with session_scope() as session:
            stmnt = select(Job.logs).where(Job.job_id == job_id)
            job_logs: Job = session.scalar(stmnt)
        return job_logs

    def get_job(self, job_id: uuid4) -> Job:
        LOGGER.debug("Retrieving job data for job with id '%s'", job_id)
        session: Session
        with session_scope(do_expunge=True) as session:
            stmnt = select(Job).where(Job.job_id == job_id)
            job = session.scalar(stmnt)
        return job

    def get_jobs(self, job_ids: List[uuid4] = None) -> List[Job]:
        with session_scope(do_expunge=True) as session:
            stmnt = ALL_JOBS_STMNT
            if job_ids:
                LOGGER.debug(f"Retrieving job data for jobs '{','.join([str(job_id) for job_id in job_ids])}'")
                stmnt = stmnt.where(Job.job_id.in_(job_ids))
            else:
                LOGGER.debug(f"Retrieving job data for all jobs")

            jobs = session.scalars(stmnt).all()
        return jobs

    def get_jobs_from_user(self, user_name: str) -> List[Job]:
        LOGGER.debug(f"Retrieving job data for jobs from user '{user_name}'")
        with session_scope(do_expunge=True) as session:
            stmnt = ALL_JOBS_STMNT.where(Job.user_name == user_name)
            jobs = session.scalars(stmnt).all()
        return jobs

    def get_jobs_from_project(self, project_name: str) -> List[Job]:
        LOGGER.debug(f"Retrieving job data for jobs from project '{project_name}'")
        with session_scope(do_expunge=True) as session:
            stmnt = ALL_JOBS_STMNT.where(Job.project_name == project_name)
            jobs = session.scalars(stmnt).all()
        return jobs

    def delete_job(self, job_id: uuid4) -> bool:
        LOGGER.debug("Deleting job with id '%s'", job_id)
        session: Session
        with session_scope() as session:
            stmnt = select(Job).where(Job.job_id == job_id)
            job = session.scalars(stmnt).all()
            if job:
                stmnt = delete(Job).where(Job.job_id == job_id)
                session.execute(stmnt)
                job_deleted = True
            else:
                job_deleted = False
        return job_deleted
