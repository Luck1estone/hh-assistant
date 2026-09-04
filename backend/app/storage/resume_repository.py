from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .db import get_connection


def create_resume(
    name: str,
    filename: str,
    text: str,
    profile: str,
) -> dict:

    resume_id = str(uuid4())

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO resumes (
                id,
                name,
                filename,
                text,
                profile,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                resume_id,
                name,
                filename,
                text,
                profile,
                created_at,
            ),
        )

    return {
        "id": resume_id,
        "name": name,
        "filename": filename,
        "text": text,
        "profile": profile,
        "created_at": created_at,
    }


def list_resumes() -> list[dict]:
    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                id,
                name,
                filename,
                text,
                profile,
                created_at
            FROM resumes
            ORDER BY created_at
            """
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def delete_resume(
    resume_id: str,
) -> bool:

    with get_connection() as connection:

        cursor = connection.execute(
            """
            DELETE FROM resumes
            WHERE id = ?
            """,
            (resume_id,),
        )

        return cursor.rowcount > 0


def update_resume_metadata(
    resume_id: str,
    *,
    name: str,
    profile: str,
) -> bool:

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE resumes
            SET
                name = ?,
                profile = ?
            WHERE id = ?
            """,
            (
                name,
                profile,
                resume_id,
            ),
        )

        return cursor.rowcount > 0


def replace_resume_content(
    resume_id: str,
    *,
    filename: str,
    text: str,
) -> bool:

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE resumes
            SET
                filename = ?,
                text = ?
            WHERE id = ?
            """,
            (
                filename,
                text,
                resume_id,
            ),
        )

        return cursor.rowcount > 0