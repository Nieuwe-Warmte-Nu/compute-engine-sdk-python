import logging
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, orm
from sqlalchemy.engine import URL

LOGGER = logging.getLogger(__name__)

session_factory = orm.sessionmaker()
Session = orm.scoped_session(session_factory)


@contextmanager
def session_scope(bind=None):
    """Provide a transactional scope around a series of operations. Ensures that the session is
    commited and closed. Exceptions raised within the 'with' block using this contextmanager
    should be handled in the with block itself. They will not be caught by the 'except' here."""
    try:
        if bind:
            yield Session(bind=bind)
        yield Session()
        Session.commit()
    except Exception:
        # Only the exceptions raised by session.commit above are caught here
        Session.rollback()
        raise
    finally:
        Session.remove()


def initialize_db(application_name: str, host: str):
    """
    Initialize the database connection by creating the engine and configuring
    the default session maker.
    """
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("POSTGRES_ROOT_USER"),
        password=os.getenv("POSTGRES_ROOT_PASSWORD"),
        host=host,
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DATABASE_NAME"),
    )

    engine = create_engine(
        url,
        pool_size=20,
        max_overflow=5,
        echo=False,
        connect_args={
            "application_name": application_name,
            "options": "-c lock_timeout=30000 -c statement_timeout=300000",  # 5 minutes
        },
    )

    # Bind the global session to the actual engine.
    Session.configure(bind=engine)

    return engine
