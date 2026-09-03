from __future__ import annotations

import re


SKILLS: dict[str, list[str]] = {
    "Java": [
        "java",
    ],

    "Kotlin": [
        "kotlin",
    ],

    "REST Assured": [
        "rest assured",
        "restassured",
    ],

    "Selenide": [
        "selenide",
    ],

    "Selenium": [
        "selenium",
        "selenium webdriver",
    ],

    "Appium": [
        "appium",
    ],

    "JUnit": [
        "junit",
        "junit 5",
    ],

    "TestNG": [
        "testng",
    ],

    "Kafka": [
        "kafka",
        "apache kafka",
    ],

    "PostgreSQL": [
        "postgresql",
        "postgres",
    ],

    "SQL": [
        "sql",
    ],

    "gRPC": [
        "grpc",
    ],

    "MockServer": [
        "mockserver",
    ],

    "GitLab CI/CD": [
        "gitlab ci",
        "gitlab ci/cd",
        "gitlab",
    ],

    "Jenkins": [
        "jenkins",
    ],

    "Docker": [
        "docker",
    ],

    "Kubernetes": [
        "kubernetes",
        "k8s",
    ],

    "Terraform": [
        "terraform",
    ],

    "Linux": [
        "linux",
    ],

    "Grafana": [
        "grafana",
    ],

    "Kibana": [
        "kibana",
    ],

    "Prometheus": [
        "prometheus",
    ],

    "Allure": [
        "allure",
        "allure testops",
    ],

    "Spring": [
        "spring",
        "spring boot",
    ],

    "Maven": [
        "maven",
    ],

    "Gradle": [
        "gradle",
    ],

    "Git": [
        "git",
    ],

    "CI/CD": [
        "ci/cd",
        "continuous integration",
    ],

    "REST API": [
        "rest api",
        "restful",
    ],

    "Microservices": [
        "microservices",
        "микросервис",
        "микросервисы",
    ],
}


def normalize(text: str) -> str:
    return (
        text.lower()
        .replace("ё", "е")
    )


def contains_alias(
    text: str,
    alias: str,
) -> bool:
    pattern = (
        r"(?<![\w])"
        + re.escape(alias.lower())
        + r"(?![\w])"
    )

    return bool(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
    )


def extract_skills(
    text: str,
) -> set[str]:

    normalized = normalize(text)

    result: set[str] = set()

    for skill, aliases in SKILLS.items():

        if any(
            contains_alias(
                normalized,
                alias,
            )
            for alias in aliases
        ):
            result.add(skill)

    return result