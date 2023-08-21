from dataclasses import dataclass
from enum import Enum

import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID

from nwnsdk import WorkFlowType

Base = declarative_base()


class JobStatus(Enum):
    REGISTERED = "registered"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class Job(Base):
    __tablename__ = "job"

    job_id = db.Column(UUID(as_uuid=True), primary_key=True)
    job_name = db.Column(db.String, nullable=False)
    work_flow_type = db.Column(db.Enum(WorkFlowType), nullable=False)
    user_name = db.Column(db.String)
    project_name = db.Column(db.String)
    status = db.Column(db.Enum(JobStatus), nullable=False)
    input_config = db.Column(db.String)
    input_esdl = db.Column(db.String, nullable=False)
    output_esdl = db.Column(db.String)
    added_at = db.Column(db.DateTime(timezone=True), nullable=False)
    running_at = db.Column(db.DateTime(timezone=True))
    stopped_at = db.Column(db.DateTime(timezone=True))
    logs = db.Column(db.String)
