from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import BaseModel

from backend.app.matching.matcher import (
    analyze_against_resumes,
)


router = APIRouter(
    prefix="/api/vacancy",
    tags=["vacancy"],
)


class VacancyRequest(BaseModel):
    vacancyId: str | None = None

    source: str = "HH"

    company: str = ""
    title: str = ""
    salary: str = ""
    location: str = ""

    description: str = ""
    url: str = ""

    scrapedAt: str | None = None


@router.post("/analyze")
def analyze_vacancy(
    vacancy: VacancyRequest,
) -> dict:

    try:
        result = analyze_against_resumes(
            title=vacancy.title,
            description=vacancy.description,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    return {
        "vacancy_id": vacancy.vacancyId,

        **result,

        "auto_manual_ratio":
            "Пока не определено",

        "bonuses":
            "Пока не определены",

        "comment":
            "Анализ выполнен по загруженным резюме.",
    }