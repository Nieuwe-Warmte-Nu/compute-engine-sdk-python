from datetime import datetime
import logging
from typing import List
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm.strategy_options import load_only

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
    def __init__(self, postgres_config: PostgresConfig):
        initialize_db("nwn", postgres_config)

    def send_input(
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

    def retrieve_input_esdl(self, job_id: uuid4) -> str:
        LOGGER.debug("Retrieving esdl for job %s", job_id)
        with session_scope() as session:
            stmnt = select(Job).where(Job.job_id.is_(job_id))
            job: Job = session.scalar(stmnt)
        return job.input_esdl

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
            stmnt = select(Job).options(load_only(Job.status)).where(Job.job_id == job_id)
            job: Job = session.scalar(stmnt)
        return job.status

    def get_job(self, job_id: uuid4) -> Job:
        LOGGER.debug("Retrieving job data for job with id '%s'", job_id)
        with session_scope(do_expunge=True) as session:
            stmnt = select(Job).where(Job.job_id == job_id)
            job: Job = session.scalar(stmnt)
        return job

    def get_jobs(self, job_ids: list[uuid4] = None) -> List[Job]:
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
