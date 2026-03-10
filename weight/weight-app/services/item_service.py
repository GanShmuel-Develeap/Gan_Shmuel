from datetime import datetime
from db import get_conn


def parse_item_time_range(t1_str=None, t2_str=None):
    now = datetime.now()
    default_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if t1_str is None:
        t1_str = default_from.strftime("%Y%m%d%H%M%S")
    if t2_str is None:
        t2_str = now.strftime("%Y%m%d%H%M%S")

    t1 = datetime.strptime(t1_str, "%Y%m%d%H%M%S")
    t2 = datetime.strptime(t2_str, "%Y%m%d%H%M%S")

    return t1, t2


def truck_exists(cur, item_id):
    cur.execute(
        """
        SELECT 1
        FROM transactions
        WHERE truck = %s
        LIMIT 1
        """,
        (item_id,)
    )
    return cur.fetchone() is not None


def container_exists(cur, item_id):
    cur.execute(
        """
        SELECT 1
        FROM transactions
        WHERE FIND_IN_SET(%s, containers)
        LIMIT 1
        """,
        (item_id,)
    )
    return cur.fetchone() is not None


def get_truck_item_data(cur, item_id, t1, t2):
    cur.execute(
        """
        SELECT DISTINCT session_id
        FROM transactions
        WHERE truck = %s
          AND datetime BETWEEN %s AND %s
        ORDER BY session_id
        """,
        (item_id, t1, t2)
    )
    sessions = [row["session_id"] for row in cur.fetchall()]

    cur.execute(
        """
        SELECT truckTara
        FROM transactions
        WHERE truck = %s
          AND datetime BETWEEN %s AND %s
          AND truckTara IS NOT NULL
        ORDER BY datetime DESC
        LIMIT 1
        """,
        (item_id, t1, t2)
    )
    row = cur.fetchone()
    tara = row["truckTara"] if row else "na"

    return {
        "id": item_id,
        "tara": tara,
        "sessions": sessions
    }


def get_container_item_data(cur, item_id, t1, t2):
    cur.execute(
        """
        SELECT DISTINCT session_id
        FROM transactions
        WHERE FIND_IN_SET(%s, containers)
          AND datetime BETWEEN %s AND %s
        ORDER BY session_id
        """,
        (item_id, t1, t2)
    )
    sessions = [row["session_id"] for row in cur.fetchall()]

    return {
        "id": item_id,
        "tara": "na",
        "sessions": sessions
    }


def get_item_data(item_id, t1_str=None, t2_str=None):
    t1, t2 = parse_item_time_range(t1_str, t2_str)

    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    try:
        if truck_exists(cur, item_id):
            return get_truck_item_data(cur, item_id, t1, t2)

        if container_exists(cur, item_id):
            return get_container_item_data(cur, item_id, t1, t2)

        return None
    finally:
        cur.close()
        conn.close()