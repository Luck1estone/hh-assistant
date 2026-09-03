from __future__ import annotations

from pydantic import BaseModel

class ResumeProfileUpdate(BaseModel):
    profile: str

from ..storage.db import (
    DB_PATH,
    get_connection,
)

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from ..resumes.parser import (
    extract_pdf_text,
)

from ..resumes.skills import (
    extract_skills,
)

from ..storage.resume_repository import (
    create_resume,
    delete_resume,
    list_resumes,
)


router = APIRouter(
    prefix="/api/resumes",
    tags=["resumes"],
)

ALLOWED_PROFILES = {
    "sdet",
    "fullstack",
    "mobile",
    "backend",
    "platform",
}


@router.get("")
def get_resumes() -> list[dict]:

    result = []

    for resume in list_resumes():

        result.append(
            {
                "id": resume["id"],
                "name": resume["name"],
                "filename": resume["filename"],
                "profile": resume["profile"],
                "skills": sorted(
                    extract_skills(
                        resume["text"]
                    )
                ),
                "text_length": len(
                    resume["text"]
                ),
            }
        )

    return result


@router.post("")
async def upload_resume(
    name: str = Form(...),
    file: UploadFile = File(...),
) -> dict:

    filename = file.filename or "resume.pdf"

    if not filename.lower().endswith(
        ".pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail="Пока поддерживаются только PDF",
        )

    content = await file.read()

    try:
        text = extract_pdf_text(
            content
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    resume = create_resume(
        name=name.strip(),
        filename=filename,
        text=text,
    )

    return {
        "id": resume["id"],
        "name": resume["name"],
        "filename": filename,

        "skills": sorted(
            extract_skills(text)
        ),

        "text_length": len(text),
    }


@router.delete("/{resume_id}")
def remove_resume(
    resume_id: str,
) -> dict:

    if not delete_resume(
        resume_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    return {
        "deleted": True,
    }

@router.get("/status")
def get_resume_storage_status() -> dict:
    with get_connection() as connection:

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM resumes
            """
        ).fetchone()[0]

        rows = connection.execute(
            """
            SELECT
                id,
                name,
                filename,
                created_at,
                LENGTH(text) AS text_length
            FROM resumes
            ORDER BY created_at DESC
            """
        ).fetchall()

    return {
        "database": str(DB_PATH),
        "resume_count": count,
        "resumes": [
            {
                "id": row["id"],
                "name": row["name"],
                "filename": row["filename"],
                "created_at": row["created_at"],
                "text_length": row["text_length"],
            }
            for row in rows
        ],
    }

@router.get("/{resume_id}/debug")
def debug_resume(
    resume_id: str,
) -> dict:

    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT
                id,
                name,
                filename,
                text,
                created_at
            FROM resumes
            WHERE id = ?
            """,
            (resume_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    text = row["text"]

    return {
        "id": row["id"],
        "name": row["name"],
        "filename": row["filename"],
        "created_at": row["created_at"],

        "text_length": len(text),

        "skills": sorted(
            extract_skills(text)
        ),

        # Не возвращаем всё резюме,
        # только первые 2000 символов для отладки.
        "text_preview": text[:2000],
    }

@router.post("")
async def upload_resume(
    name: str = Form(...),
    profile: str = Form(...),
    file: UploadFile = File(...),
) -> dict:

    profile = profile.strip().lower()

    if profile not in ALLOWED_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid profile. "
                "Allowed: sdet, fullstack, mobile, "
                "backend, platform"
            ),
        )

    filename = file.filename or "resume.pdf"

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Пока поддерживаются только PDF",
        )

    content = await file.read()

    try:
        text = extract_pdf_text(content)

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    resume = create_resume(
        name=name.strip(),
        filename=filename,
        text=text,
        profile=profile,
    )

    return {
        "id": resume["id"],
        "name": resume["name"],
        "profile": resume["profile"],
        "filename": filename,

        "skills": sorted(
            extract_skills(text)
        ),

        "text_length": len(text),
    }

@router.patch("/{resume_id}/profile")
def update_resume_profile(
    resume_id: str,
    request: ResumeProfileUpdate,
) -> dict:

    profile = request.profile.strip().lower()

    if profile not in ALLOWED_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid profile. "
                "Allowed: sdet, fullstack, mobile, "
                "backend, platform"
            ),
        )

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE resumes
            SET profile = ?
            WHERE id = ?
            """,
            (
                profile,
                resume_id,
            ),
        )

    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    return {
        "id": resume_id,
        "profile": profile,
    }