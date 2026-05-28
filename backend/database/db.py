import os

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    conn.set_session(autocommit=True)  # Enable autocommit for auto-persistence
    return conn
