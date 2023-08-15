import sqlalchemy as db

#
# metadata = db.MetaData()
#
# Job = db.Table(
#     "jobs",
#     metadata,
#     db.Column("job_id", db.UUID, primary_key=True),
#     db.Column("map_editor_user", db.String),
#     db.Column("status", db.String, nullable=False),
#     db.Column("input_config", db.String),
#     db.Column("input_esdl", db.String, nullable=False),
#     db.Column("output_esdl", db.String),
#     db.Column("added_at", db.DateTime(timezone=True), nullable=False),
#     db.Column("running_at", db.DateTime(timezone=True)),
#     db.Column("stopped_at", db.DateTime(timezone=True)),
#     db.Column("error_logs", db.DateTime(timezone=True)),
# )

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

    job_id = db.Column(db.UUID, primary_key=True)
    job_name = db.Column(db.String, nullable=False)
    map_editor_user = db.Column(db.String)
    status = db.Column(db.String, nullable=False)
    input_config = db.Column(db.String)
    input_esdl = db.Column(db.String, nullable=False)
    output_esdl = db.Column(db.String)
    added_at = db.Column(db.DateTime(timezone=True), nullable=False)
    running_at = db.Column(db.DateTime(timezone=True))
    stopped_at = db.Column(db.DateTime(timezone=True))
    error_logs = db.Column(db.DateTime(timezone=True))
