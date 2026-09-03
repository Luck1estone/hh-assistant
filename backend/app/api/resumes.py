from __future__ import annotations

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


@router.get("")
def get_resumes() -> list[dict]:

    result = []

    for resume in list_resumes():

        result.append(
            {
                "id": resume["id"],
                "name": resume["name"],
                "filename": resume["filename"],
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