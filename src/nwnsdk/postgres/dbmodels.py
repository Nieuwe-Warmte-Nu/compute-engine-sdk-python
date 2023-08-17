from enum import Enum

import sqlalchemy as db

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class JobStatus(Enum):
    REGISTERED = "registered"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"
    STOPPED = "stopped"


class Job(Base):
    __tablename__ = "job"

    job_id = db.Column(db.UUID, primary_key=True)
    job_name = db.Column(db.String, nullable=False)
    work_flow_type = db.Column(db.String, nullable=False)
    map_editor_user = db.Column(db.String)
    status = db.Column(db.String, nullable=False)
    input_config = db.Column(db.String)
    input_esdl = db.Column(db.String, nullable=False)
    output_esdl = db.Column(db.String)
    added_at = db.Column(db.DateTime(timezone=True), nullable=False)
    running_at = db.Column(db.DateTime(timezone=True))
    stopped_at = db.Column(db.DateTime(timezone=True))
    logs = db.Column(db.DateTime(timezone=True))
