from datetime import datetime
from uuid import uuid4

from nwnsdk.postgres.database import initialize_db, session_scope
from nwnsdk.postgres.dbmodels import Job


class PostgresClient:
    def __init__(self, host: str):
        initialize_db("nwn", host)

    def send_input(self, job_id: uuid4, job_name: str, esdl_str: str, user_name: str):
        with session_scope() as session:
            new_job = Job(
                job_id=job_id,
                job_name=job_name,
                map_editor_user=user_name,
                status="registered",
                input_esdl=esdl_str,
                added_at=datetime.now(),
            )
            session.add(new_job)
