from typing import Any, List, Optional
from backend.database.db import get_connection
import json
from psycopg2.extras import Json


def ensure_table():
    ddl = """
    CREATE TABLE IF NOT EXISTS alerts (
        id SERIAL PRIMARY KEY,
        user_id INT,
        product_id INT NOT NULL,
        target_price NUMERIC(12,2) NOT NULL,
        stores JSONB,
        enabled BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
    )
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            conn.commit()


def create_alert(product_id: int, target_price: float, stores: Optional[list] = None, user_id: Optional[int] = None) -> dict[str, Any]:
    ensure_table()
    query = "INSERT INTO alerts (user_id, product_id, target_price, stores) VALUES (%s, %s, %s, %s) RETURNING id, user_id, product_id, target_price, stores, enabled, created_at"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id, product_id, target_price, Json(stores)))
                row = cur.fetchone()
                conn.commit()
        return dict(row) if row else {}
    except Exception as e:
        print(f"Error creating alert: {e}")
        raise


def list_alerts(user_id: Optional[int] = None) -> List[dict[str, Any]]:
    ensure_table()
    if user_id:
        query = "SELECT id, user_id, product_id, target_price, stores, enabled, created_at FROM alerts WHERE user_id = %s ORDER BY created_at DESC"
        params = (user_id,)
    else:
        query = "SELECT id, user_id, product_id, target_price, stores, enabled, created_at FROM alerts ORDER BY created_at DESC"
        params = None
    with get_connection() as conn:
        with conn.cursor() as cur:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def toggle_alert(alert_id: int, enabled: bool, user_id: Optional[int] = None) -> bool:
    ensure_table()
    try:
        if user_id:
            query = "UPDATE alerts SET enabled = %s WHERE id = %s AND user_id = %s"
            params = (enabled, alert_id, user_id)
        else:
            query = "UPDATE alerts SET enabled = %s WHERE id = %s"
            params = (enabled, alert_id)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                changed = cur.rowcount
                conn.commit()
        return changed > 0
    except Exception as e:
        print(f"Error toggling alert: {e}")
        return False


def delete_alert(alert_id: int, user_id: Optional[int] = None) -> bool:
    ensure_table()
    try:
        if user_id:
            query = "DELETE FROM alerts WHERE id = %s AND user_id = %s"
            params = (alert_id, user_id)
        else:
            query = "DELETE FROM alerts WHERE id = %s"
            params = (alert_id,)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                deleted = cur.rowcount
                conn.commit()
        return deleted > 0
    except Exception as e:
        print(f"Error deleting alert: {e}")
        return False
