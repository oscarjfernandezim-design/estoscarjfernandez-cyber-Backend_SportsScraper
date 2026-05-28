from psycopg2 import errors
from backend.database.db import get_connection
from werkzeug.security import generate_password_hash, check_password_hash


class DuplicateEmailError(Exception):
    pass


def get_all_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, full_name, email, created_at FROM users ORDER BY id ASC"
            )
            return cur.fetchall()


def get_user_by_id(user_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, full_name, email, password, created_at FROM users WHERE id = %s",
                (user_id,),
            )
            return cur.fetchone()


def create_user(full_name: str, email: str, password: str | None = None):
    try:
        clean_email = (email or "").strip().lower()
        pwd_hash = generate_password_hash(password) if password else None
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (full_name, email, password) VALUES (%s, %s, %s) RETURNING id, full_name, email, created_at",
                    (full_name, clean_email, pwd_hash),
                )
                result = cur.fetchone()
                conn.commit()
                return result
    except errors.UniqueViolation as exc:
        raise DuplicateEmailError("email already exists") from exc


def update_user(user_id: int, full_name: str, email: str):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET full_name = %s, email = %s WHERE id = %s RETURNING id, full_name, email, created_at",
                    (full_name, email, user_id),
                )
                result = cur.fetchone()
                conn.commit()
                return result
    except errors.UniqueViolation as exc:
        raise DuplicateEmailError("email already exists") from exc


def delete_user(user_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
            result = cur.fetchone() is not None
            conn.commit()
            return result


def update_password(user_id: int, password: str):
    password_hash = generate_password_hash(password)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password = %s WHERE id = %s RETURNING id, full_name, email, created_at",
                (password_hash, user_id),
            )
            result = cur.fetchone()
            conn.commit()
            return result


def authenticate_user(email: str, password: str):
    clean_email = (email or "").strip().lower()
    query = "SELECT id, full_name, email, password FROM users WHERE lower(email) = %s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (clean_email,))
            row = cur.fetchone()
    if not row:
        return None
    stored = row.get('password') if isinstance(row, dict) else row[3]
    if not stored:
        return None
    if check_password_hash(stored, password):
        return { 'id': row.get('id') if isinstance(row, dict) else row[0], 'full_name': row.get('full_name') if isinstance(row, dict) else row[1], 'email': row.get('email') if isinstance(row, dict) else row[2] }
    return None
