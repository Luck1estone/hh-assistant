from __future__ import annotations

from dataclasses import dataclass

from backend.app.resumes.skills import extract_skills
from backend.app.storage.resume_repository import list_resumes


# Вес технологий.
# Чем технология характернее для нашей работы,
# тем сильнее она влияет на match score.
SKILL_WEIGHTS: dict[str, float] = {
    "Java": 4.0,
    "Kotlin": 2.5,

    "REST Assured": 4.0,
    "REST API": 2.5,

    "Selenide": 3.5,
    "Selenium": 3.0,
    "Appium": 4.0,

    "JUnit": 2.0,
    "TestNG": 2.0,

    "Kafka": 3.0,
    "PostgreSQL": 2.5,
    "SQL": 2.0,
    "gRPC": 3.0,
    "MockServer": 2.0,

    "GitLab CI/CD": 2.5,
    "Jenkins": 2.0,
    "CI/CD": 2.0,

    "Docker": 2.0,
    "Kubernetes": 3.0,
    "Terraform": 3.0,
    "Linux": 2.0,

    "Grafana": 1.5,
    "Kibana": 1.5,
    "Prometheus": 1.5,

    "Spring": 2.0,
    "Maven": 1.0,
    "Gradle": 1.0,
    "Git": 0.5,

    "Microservices": 2.5,
    "Allure": 1.0,
}


ROLE_KEYWORDS = {
    "fullstack": {
        "title": [
            "fullstack",
            "full-stack",
            "full stack",
            "фуллстек",
        ],
        "description": [
            "web",
            "ui",
            "api",
            "frontend",
            "backend",
            "selenide",
            "selenium",
        ],
    },

    "backend": {
        "title": [
            "backend",
            "back-end",
            "бэкенд",
            "бекенд",
        ],
        "description": [
            "rest api",
            "kafka",
            "grpc",
            "postgresql",
            "microservices",
            "микросервис",
        ],
    },

    "mobile": {
        "title": [
            "mobile",
            "android",
            "ios",
            "мобиль",
        ],
        "description": [
            "appium",
            "android",
            "ios",
            "xcode",
            "android studio",
            "эмулятор",
        ],
    },

    "platform": {
        "title": [
            "platform",
            "infrastructure",
            "инфраструктур",
            "test infrastructure",
            "qa platform",
        ],
        "description": [
            "kubernetes",
            "terraform",
            "docker",
            "jenkins",
            "gitlab ci",
            "linux",
            "infrastructure",
        ],
    },

    "sdet": {
        "title": [
            "sdet",
            "aqa",
            "automation",
            "автоматизатор",
            "автоматизации тестирования",
            "автотест",
        ],
        "description": [
            "rest assured",
            "selenide",
            "selenium",
            "junit",
            "автотест",
            "automation",
        ],
    },
}


# Насколько тип одного резюме подходит типу вакансии.
ROLE_COMPATIBILITY = {
    "sdet": {
        "sdet": 100,
        "backend": 86,
        "fullstack": 86,
        "mobile": 72,
        "platform": 65,
    },

    "backend": {
        "backend": 100,
        "sdet": 88,
        "fullstack": 73,
        "platform": 62,
        "mobile": 42,
    },

    "fullstack": {
        "fullstack": 100,
        "sdet": 88,
        "backend": 74,
        "mobile": 58,
        "platform": 45,
    },

    "mobile": {
        "mobile": 100,
        "sdet": 78,
        "fullstack": 65,
        "backend": 48,
        "platform": 40,
    },

    "platform": {
        "platform": 100,
        "sdet": 72,
        "backend": 65,
        "fullstack": 52,
        "mobile": 38,
    },
}


@dataclass(slots=True)
class ResumeMatch:
    resume_id: str
    resume_name: str
    resume_profile: str

    score: int
    skill_score: int
    role_score: int

    matched_skills: list[str]
    missing_skills: list[str]


def normalize(text: str) -> str:
    return (
        text.lower()
        .replace("ё", "е")
    )


def detect_vacancy_profile(
    title: str,
    description: str,
) -> tuple[str, dict[str, int]]:
    title = normalize(title)
    description = normalize(description)

    scores = {
        role: 0
        for role in ROLE_KEYWORDS
    }

    for role, keywords in ROLE_KEYWORDS.items():

        # Название вакансии очень важное.
        for keyword in keywords["title"]:
            if keyword in title:
                scores[role] += 12

        # Описание тоже учитываем,
        # но оно не должно перетянуть очевидный title.
        for keyword in keywords["description"]:
            if keyword in description:
                scores[role] += 2

    if max(scores.values()) == 0:
        return "sdet", scores

    best_role = max(
        scores,
        key=scores.get,
    )

    return best_role, scores


def calculate_skill_score(
    vacancy_skills: set[str],
    resume_skills: set[str],
) -> int:

    # Если наш extractor вообще не смог найти технологий,
    # не будем изображать точность.
    if not vacancy_skills:
        return 50

    total_weight = sum(
        SKILL_WEIGHTS.get(skill, 1.0)
        for skill in vacancy_skills
    )

    matched_weight = sum(
        SKILL_WEIGHTS.get(skill, 1.0)
        for skill in vacancy_skills
        if skill in resume_skills
    )

    if total_weight <= 0:
        return 50

    return round(
        matched_weight
        / total_weight
        * 100
    )


def analyze_against_resumes(
    title: str,
    description: str,
) -> dict:

    resumes = list_resumes()

    if not resumes:
        raise ValueError(
            "В базе нет резюме."
        )

    vacancy_text = (
        f"{title}\n\n{description}"
    )

    vacancy_skills = extract_skills(
        vacancy_text
    )

    vacancy_profile, role_debug = (
        detect_vacancy_profile(
            title=title,
            description=description,
        )
    )

    matches: list[ResumeMatch] = []

    for resume in resumes:

        resume_skills = extract_skills(
            resume["text"]
        )

        resume_profile = resume["profile"]

        skill_score = calculate_skill_score(
            vacancy_skills=vacancy_skills,
            resume_skills=resume_skills,
        )

        role_score = (
            ROLE_COMPATIBILITY
            .get(vacancy_profile, {})
            .get(resume_profile, 50)
        )

        # Стек важнее названия резюме.
        final_score = round(
            skill_score * 0.75
            + role_score * 0.25
        )

        matched_skills = sorted(
            vacancy_skills
            & resume_skills
        )

        missing_skills = sorted(
            vacancy_skills
            - resume_skills
        )

        matches.append(
            ResumeMatch(
                resume_id=resume["id"],
                resume_name=resume["name"],
                resume_profile=resume_profile,

                score=final_score,
                skill_score=skill_score,
                role_score=role_score,

                matched_skills=matched_skills,
                missing_skills=missing_skills,
            )
        )

    matches.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    best = matches[0]

    if best.score >= 75:
        decision = "good"

    elif best.score >= 50:
        decision = "review"

    else:
        decision = "skip"

    return {
        "score": best.score,
        "decision": decision,

        "vacancy_profile": vacancy_profile,

        "recommended_resume": best.resume_name,
        "recommended_resume_id": best.resume_id,

        "matched_skills": best.matched_skills,
        "missing_skills": best.missing_skills,

        "vacancy_skills": sorted(
            vacancy_skills
        ),

        "alternatives": [
            {
                "resume_id": match.resume_id,
                "resume_name": match.resume_name,

                "profile": match.resume_profile,

                "score": match.score,
                "skill_score": match.skill_score,
                "role_score": match.role_score,
            }
            for match in matches
        ],

        # Пока оставим для разработки.
        # Позже можно удалить.
        "debug": {
            "role_scores": role_debug,
        },
    }