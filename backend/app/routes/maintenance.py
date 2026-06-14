from datetime import datetime

from flask import Blueprint, request

from ..database import get_connection, rows_to_dicts

maintenance_bp = Blueprint("maintenance", __name__)


@maintenance_bp.get("/orders", strict_slashes=False)
def list_orders():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM maintenance_orders ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return {"items": rows_to_dicts(rows)}


@maintenance_bp.post("/orders", strict_slashes=False)
def create_order():
    data = request.get_json() or {}
    space_id = data.get("space_id")
    title = data.get("title")
    description = data.get("description")

    if not space_id or not title:
        return {"message": "车位ID和标题不能为空"}, 400

    with get_connection() as conn:
        space = conn.execute("SELECT * FROM spaces WHERE id = ?", (space_id,)).fetchone()
        if not space:
            return {"message": "车位不存在"}, 404
        if space["status"] == "maintenance":
            return {"message": "该车位已在维护中"}, 409

        created_at = datetime.now().isoformat(timespec="minutes")
        cur = conn.execute(
            """
            INSERT INTO maintenance_orders (space_id, space_code, title, description, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
            """,
            (space_id, space["code"], title, description, created_at),
        )

        conn.execute(
            """
            UPDATE spaces
            SET status = 'maintenance', plate_number = NULL, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (space_id,),
        )

        row = conn.execute(
            "SELECT * FROM maintenance_orders WHERE id = ?", (cur.lastrowid,)
        ).fetchone()

    return dict(row), 201


@maintenance_bp.post("/orders/<int:order_id>/close", strict_slashes=False)
def close_order(order_id):
    data = request.get_json() or {}
    remark = data.get("remark")

    with get_connection() as conn:
        order = conn.execute(
            "SELECT * FROM maintenance_orders WHERE id = ?", (order_id,)
        ).fetchone()
        if not order:
            return {"message": "工单不存在"}, 404
        if order["status"] == "closed":
            return {"message": "工单已关闭"}, 409

        closed_at = datetime.now().isoformat(timespec="minutes")
        conn.execute(
            """
            UPDATE maintenance_orders
            SET status = 'closed', closed_at = ?, remark = ?
            WHERE id = ?
            """,
            (closed_at, remark, order_id),
        )

        conn.execute(
            """
            UPDATE spaces
            SET status = 'free', plate_number = NULL, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (order["space_id"],),
        )

        row = conn.execute(
            "SELECT * FROM maintenance_orders WHERE id = ?", (order_id,)
        ).fetchone()

    return dict(row)
