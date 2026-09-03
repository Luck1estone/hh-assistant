from __future__ import annotations

from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(
    title="HH Job Assistant API",
    version="0.1.0",
)


# Для локального MVP.
# Позже ограничим доступ только расширением.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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


class SkillMatch(BaseModel):
    name: str

    status: Literal[
        "matched",
        "missing",
        "neutral",
    ]


class VacancyAnalysis(BaseModel):
    vacancy_id: str | None

    score: int = Field(
        ge=0,
        le=100,
    )

    decision: Literal[
        "good",
        "review",
        "skip",
    ]

    recommended_resume: str

    matched_skills: list[str]
    missing_skills: list[str]

    auto_manual_ratio: str

    bonuses: str

    comment: str


JAVA_SKILLS = {
    "java": 15,
    "rest assured": 15,
    "selenide": 10,
    "selenium": 8,
    "junit": 8,
    "kafka": 8,
    "postgresql": 7,
    "sql": 5,
    "gitlab": 5,
    "ci/cd": 5,
    "docker": 5,
    "grpc": 5,
    "appium": 5,
}


def normalize(text: str) -> str:
    return (
        text
        .lower()
        .replace("ё", "е")
    )


def analyze_vacancy(
    vacancy: VacancyRequest,
) -> VacancyAnalysis:

    text = normalize(
        " ".join(
            [
                vacancy.title,
                vacancy.description,
            ]
        )
    )

    score = 0
    matched = []

    for skill, points in JAVA_SKILLS.items():

        if skill in text:
            score += points
            matched.append(skill)

    score = min(
        score,
        100,
    )


    # ---------------------------------------------------------
    # Выбор резюме
    # ---------------------------------------------------------

    if any(
        word in text
        for word in [
            "appium",
            "android",
            "ios",
            "mobile",
            "мобильн",
        ]
    ):
        resume = "03_Mobile_QA_Automation"

    elif any(
        word in text
        for word in [
            "infrastructure",
            "инфраструктур",
            "kubernetes",
            "terraform",
            "platform engineer",
        ]
    ):
        resume = "04_QA_Platform_Test_Infrastructure"

    elif any(
        word in text
        for word in [
            "backend",
            "kafka",
            "grpc",
            "микросервис",
        ]
    ):
        resume = "05_Backend_QA"

    elif any(
        word in text
        for word in [
            "fullstack",
            "full-stack",
        ]
    ):
        resume = "02_Fullstack_QA_Java_API_Web_Mobile"

    else:
        resume = "01_QA_Automation_SDET_Java"


    # ---------------------------------------------------------
    # Решение
    # ---------------------------------------------------------

    if score >= 60:
        decision = "good"

    elif score >= 30:
        decision = "review"

    else:
        decision = "skip"


    # ---------------------------------------------------------
    # Что у нас потенциально отсутствует
    # ---------------------------------------------------------

    important_skills = [
        "java",
        "rest assured",
        "kafka",
        "postgresql",
        "docker",
    ]

    missing = [
        skill
        for skill in important_skills
        if skill not in text
    ]


    return VacancyAnalysis(
        vacancy_id=vacancy.vacancyId,

        score=score,

        decision=decision,

        recommended_resume=resume,

        matched_skills=matched,

        missing_skills=missing,

        auto_manual_ratio="Пока не определено",

        bonuses="Пока не определены",

        comment=(
            f"Автоматический анализ v0.1. "
            f"Найдено совпадений: {len(matched)}."
        ),
    )


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "HH Job Assistant",
    }


@app.post(
    "/api/vacancy/analyze",
    response_model=VacancyAnalysis,
)
def analyze(
    vacancy: VacancyRequest,
) -> VacancyAnalysis:

    return analyze_vacancy(
        vacancy
    )