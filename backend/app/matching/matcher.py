from __future__ import annotations

from dataclasses import dataclass

from backend.app.resumes.skills import extract_skills
from backend.app.storage.resume_repository import list_resumes


SKILL_WEIGHTS: dict[str, float] = {
    "Java": 3.0,
    "Kotlin": 2.0,

    "REST Assured": 3.0,
    "REST API": 2.0,

    "Selenide": 2.5,
    "Selenium": 2.0,
    "Appium": 3.0,

    "JUnit": 1.5,
    "TestNG": 1.5,

    "Kafka": 2.5,
    "PostgreSQL": 2.0,
    "SQL": 1.5,
    "gRPC": 2.5,

    "MockServer": 1.5,

    "GitLab CI/CD": 2.0,
    "Jenkins": 1.5,
    "CI/CD": 1.5,

    "Docker": 1.5,
    "Kubernetes": 2.0,
    "Terraform": 2.0,
    "Linux": 1.5,

    "Grafana": 1.0,
    "Kibana": 1.0,
    "Prometheus": 1.0,

    "Spring": 1.5,
    "Maven": 1.0,
    "Gradle": 1.0,
    "Git": 0.5,

    "Microservices": 2.0,
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
        "body": [
            "frontend",
            "backend",
            "web",
            "api",
            "ui",
            "selenide",
            "selenium",
        ],
    },

    "mobile": {
        "title": [
            "mobile",
            "мобиль",
            "android",
            "ios",
        ],
        "body": [
            "appium",
            "android",
            "ios",
            "mobile",
            "xcode",
        ],
    },

    "backend": {
        "title": [
            "backend",
            "back-end",
            "бэкенд",
            "бекенд",
        ],
        "body": [
            "kafka",
            "grpc",
            "rest api",
            "microservice",
            "микросервис",
            "postgresql",
        ],
    },

    "platform": {
        "title": [
            "platform",
            "infrastructure",
            "инфраструктур",
            "qa platform",
            "test infrastructure",
        ],
        "body": [
            "kubernetes",
            "terraform",
            "docker",
            "gitlab ci",
            "jenkins",
            "linux",
            "infrastructure",
        ],
    },

    "sdet": {
        "title": [
            "sdet",
            "aqa",
            "automation",
            "автоматизац",
            "автотест",
        ],
        "body": [
            "rest assured",
            "selenide",
            "selenium",
            "junit",
            "автотест",
            "automation",
        ],
    },
}


ROLE_COMPATIBILITY = {
    "fullstack": {
        "fullstack": 100,
        "sdet": 82,
        "backend": 72,
        "mobile": 55,
        "platform": 40,
    },

    "backend": {
        "backend": 100,
        "sdet": 85,
        "fullstack": 72,
        "platform": 60,
        "mobile": 40,
    },

    "mobile": {
        "mobile": 100,
        "sdet": 75,
        "fullstack": 62,
        "backend": 45,
        "platform": 35,
    },

    "platform": {
        "platform": 100,
        "sdet": 68,
        "backend": 60,
        "fullstack": 48,
        "mobile": 35,
    },

    "sdet": {
        "sdet": 100,
        "backend": 82,
        "fullstack": 82,
        "mobile": 72,
        "platform": 62,
    },
}


@dataclass
class ResumeScore:
    resume_id: str
    resume_name: str

    profile: str

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


def detect_resume_profile(
    resume_name: str,
) -> str:

    name = normalize(resume_name)

    if (
        "mobile" in name
        or "appium" in name
        or "мобиль" in name
    ):
        return "mobile"

    if (
        "platform" in name
        or "infrastructure" in name
        or "инфраструктур" in name
    ):
        return "platform"

    if (
        "backend" in name
        or "back-end" in name
    ):
        return "backend"

    if (
        "fullstack" in name
        or "full-stack" in name
        or "full_stack" in name
    ):
        return "fullstack"

    return "sdet"


def detect_vacancy_profile(
    title: str,
    description: str,
) -> str:

    title_normalized = normalize(title)
    body_normalized = normalize(description)

    scores = {
        role: 0
        for role in ROLE_KEYWORDS
    }

    for role, keywords in ROLE_KEYWORDS.items():

        # Название вакансии весит очень сильно.
        for keyword in keywords["title"]:
            if keyword in title_normalized:
                scores[role] += 10

        for keyword in keywords["body"]:
            if keyword in body_normalized:
                scores[role] += 2

    # Если явного профиля нет,
    # для нашей задачи дефолт — обычный SDET/AQA.
    if max(scores.values()) == 0:
        return "sdet"

    return max(
        scores,
        key=scores.get,
    )


def calculate_skill_score(
    vacancy_skills: set[str],
    resume_skills: set[str],
) -> int:

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

    if total_weight == 0:
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
            "Нет загруженных резюме. "
            "Сначала добавь хотя бы одно PDF."
        )

    vacancy_text = (
        f"{title}\n{description}"
    )

    vacancy_skills = extract_skills(
        vacancy_text
    )

    vacancy_profile = detect_vacancy_profile(
        title,
        description,
    )

    results: list[ResumeScore] = []

    for resume in resumes:

        resume_skills = extract_skills(
            resume["text"]
        )

        resume_profile = detect_resume_profile(
            resume["name"]
        )

        skill_score = calculate_skill_score(
            vacancy_skills,
            resume_skills,
        )

        role_score = (
            ROLE_COMPATIBILITY
            .get(vacancy_profile, {})
            .get(resume_profile, 50)
        )

        # Основную роль играет реальный стек.
        # Но профиль резюме тоже важен.
        final_score = round(
            skill_score * 0.72
            + role_score * 0.28
        )

        matched = sorted(
            vacancy_skills
            & resume_skills
        )

        missing = sorted(
            vacancy_skills
            - resume_skills
        )

        results.append(
            ResumeScore(
                resume_id=resume["id"],
                resume_name=resume["name"],
                profile=resume_profile,

                score=final_score,
                skill_score=skill_score,
                role_score=role_score,

                matched_skills=matched,
                missing_skills=missing,
            )
        )

    results.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    best = results[0]

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

        "alternatives": [
            {
                "resume_id": item.resume_id,
                "resume_name": item.resume_name,

                "profile": item.profile,

                "score": item.score,
                "skill_score": item.skill_score,
                "role_score": item.role_score,
            }
            for item in results
        ],
    }