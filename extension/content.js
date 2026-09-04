(() => {
    "use strict";

    const APP_NAME = "HH Job Assistant";
    const HOST_ID = "hh-job-assistant-root";
    const API_URL = "http://127.0.0.1:8000";

    let renderTimer = null;
    let previousUrl = location.href;
    let lastVacancyFingerprint = null;

    // =========================================================
    // Extension runtime
    // =========================================================

    function getExtensionRuntime() {
        if (typeof browser !== "undefined" && browser.runtime) {
            return browser.runtime;
        }

        if (typeof chrome !== "undefined" && chrome.runtime) {
            return chrome.runtime;
        }

        return null;
    }

    function getExtensionVersion() {
        const runtime = getExtensionRuntime();

        try {
            return runtime?.getManifest?.()?.version || "dev";
        } catch (error) {
            console.warn(`[${APP_NAME}] Cannot read extension version`, error);
            return "dev";
        }
    }

    async function openResumeManager() {

        const runtime =
            getExtensionRuntime();


        if (!runtime) {

            console.error(
                "[HH Job Assistant] " +
                "Extension runtime not available"
            );

            alert(
                "Не удалось получить доступ " +
                "к API расширения."
            );

            return;
        }


        try {

            const response =
                await runtime.sendMessage({
                    type:
                        "OPEN_RESUME_MANAGER"
                });


            if (
                response &&
                response.success === false
            ) {
                throw new Error(
                    response.error ||
                    "Unknown background error"
                );
            }


        } catch (error) {

            console.error(
                "[HH Job Assistant] " +
                "Unable to open Resume Manager:",
                error
            );


            alert(
                "Не удалось открыть Resume Manager.\n\n" +
                "Проверь background.js и manifest.json."
            );
        }
    }

    // =========================================================
    // Utils
    // =========================================================

    function cleanText(value) {
        if (!value) {
            return "";
        }

        return value
            .replace(/\u00A0/g, " ")
            .replace(/\s+/g, " ")
            .trim();
    }

    function getText(selector) {
        const element = document.querySelector(selector);
        return element ? cleanText(element.textContent) : "";
    }

    function firstNotEmpty(...values) {
        return values.find((value) => cleanText(value)) || "";
    }

    function stripHtml(html) {
        if (!html) {
            return "";
        }

        const doc = new DOMParser().parseFromString(html, "text/html");
        return cleanText(doc.body?.textContent || "");
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function getVacancyId() {
        const match = location.pathname.match(/\/vacancy\/(\d+)/);
        return match ? match[1] : null;
    }

    function getCanonicalUrl() {
        const canonical = document.querySelector('link[rel="canonical"]');

        if (canonical?.href) {
            return canonical.href;
        }

        const vacancyId = getVacancyId();
        return vacancyId ? `https://hh.ru/vacancy/${vacancyId}` : location.href;
    }

    // =========================================================
    // JSON-LD parser
    // =========================================================

    function findJobPosting(value) {
        if (!value) {
            return null;
        }

        if (Array.isArray(value)) {
            for (const item of value) {
                const found = findJobPosting(item);

                if (found) {
                    return found;
                }
            }

            return null;
        }

        if (typeof value !== "object") {
            return null;
        }

        const type = value["@type"];

        if (
            type === "JobPosting" ||
            (Array.isArray(type) && type.includes("JobPosting"))
        ) {
            return value;
        }

        if (Array.isArray(value["@graph"])) {
            return findJobPosting(value["@graph"]);
        }

        return null;
    }

    function getJobPostingJsonLd() {
        const scripts = document.querySelectorAll(
            'script[type="application/ld+json"]'
        );

        for (const script of scripts) {
            try {
                const parsed = JSON.parse(script.textContent);
                const posting = findJobPosting(parsed);

                if (posting) {
                    return posting;
                }
            } catch (_) {
                // На странице могут быть JSON-LD блоки, которые нас не интересуют.
            }
        }

        return null;
    }

    // =========================================================
    // Salary
    // =========================================================

    function formatMoney(value, currency = "") {
        if (value == null) {
            return "";
        }

        const number = Number(value);

        if (Number.isNaN(number)) {
            return String(value);
        }

        const formatted = new Intl.NumberFormat("ru-RU").format(number);

        if (!currency) {
            return formatted;
        }

        const currencyMap = {
            RUR: "₽",
            RUB: "₽",
            USD: "$",
            EUR: "€",
        };

        return `${formatted} ${currencyMap[currency] || currency}`;
    }

    function formatSalaryFromJsonLd(jobPosting) {
        const baseSalary = jobPosting?.baseSalary;

        if (!baseSalary) {
            return "";
        }

        const currency =
            baseSalary.currency ||
            baseSalary.value?.currency ||
            "";

        const value = baseSalary.value || baseSalary;

        if (typeof value === "number") {
            return formatMoney(value, currency);
        }

        if (typeof value?.value === "number") {
            return formatMoney(value.value, currency);
        }

        const min = value?.minValue ?? value?.min;
        const max = value?.maxValue ?? value?.max;

        if (min != null && max != null) {
            return `${formatMoney(min)} – ${formatMoney(max)} ${currency}`.trim();
        }

        if (min != null) {
            return `от ${formatMoney(min)} ${currency}`.trim();
        }

        if (max != null) {
            return `до ${formatMoney(max)} ${currency}`.trim();
        }

        return "";
    }

    // =========================================================
    // Vacancy parser
    // =========================================================

    function parseVacancy() {
        const jobPosting = getJobPostingJsonLd();
        const vacancyId = getVacancyId();

        const title = firstNotEmpty(
            getText('[data-qa="vacancy-title"]'),
            jobPosting?.title,
            getText("h1")
        );

        const company = firstNotEmpty(
            getText('[data-qa="vacancy-company-name"]'),
            jobPosting?.hiringOrganization?.name
        );

        const salary = firstNotEmpty(
            getText('[data-qa="vacancy-salary"]'),
            getText('[data-qa="vacancy-compensation"]'),
            formatSalaryFromJsonLd(jobPosting)
        );

        const description = firstNotEmpty(
            getText('[data-qa="vacancy-description"]'),
            stripHtml(jobPosting?.description)
        );

        const locationText = firstNotEmpty(
            getText('[data-qa="vacancy-view-location"]'),
            getText('[data-qa="vacancy-view-raw-address"]')
        );

        const jsonLdLocation = Array.isArray(jobPosting?.jobLocation)
            ? jobPosting.jobLocation[0]
            : jobPosting?.jobLocation;

        const vacancyLocation = firstNotEmpty(
            locationText,
            jsonLdLocation?.address?.addressLocality,
            jsonLdLocation?.address?.streetAddress
        );

        return {
            vacancyId,
            source: "HH",
            company,
            title,
            salary,
            location: vacancyLocation,
            description,
            url: getCanonicalUrl(),
            scrapedAt: new Date().toISOString(),
        };
    }

    function makeVacancyFingerprint(vacancy) {
        return [
            vacancy.vacancyId,
            vacancy.title,
            vacancy.company,
            vacancy.salary,
            vacancy.location,
            vacancy.description.length,
        ].join("|");
    }

    // =========================================================
    // Clipboard
    // =========================================================

    async function copyText(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (_) {
            const textarea = document.createElement("textarea");
            textarea.value = text;
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            document.body.appendChild(textarea);
            textarea.select();

            const result = document.execCommand("copy");
            textarea.remove();
            return result;
        }
    }

    // =========================================================
    // Backend API
    // =========================================================

    async function analyzeVacancy(vacancy) {
        const response = await fetch(`${API_URL}/api/vacancy/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(vacancy),
        });

        if (!response.ok) {
            let message = `Backend error ${response.status}`;

            try {
                const body = await response.json();
                message = body.detail || message;
            } catch (_) {
                const text = await response.text();

                if (text) {
                    message = text;
                }
            }

            throw new Error(message);
        }

        return response.json();
    }

    // =========================================================
    // UI
    // =========================================================

    function createRoot() {
        let host = document.getElementById(HOST_ID);

        if (host) {
            return host;
        }

        host = document.createElement("div");
        host.id = HOST_ID;
        host.style.position = "fixed";
        host.style.top = "90px";
        host.style.right = "18px";
        host.style.zIndex = "2147483647";

        document.documentElement.appendChild(host);
        host.attachShadow({ mode: "open" });

        return host;
    }

    function decisionLabel(decision) {
        const labels = {
            good: "Хороший match",
            review: "Стоит проверить",
            skip: "Слабый match",
        };

        return labels[decision] || "Анализ";
    }

    function render(vacancy) {
        const host = createRoot();
        const shadow = host.shadowRoot;

        if (!shadow) {
            return;
        }

        const extensionVersion = getExtensionVersion();
        const descriptionStatus = vacancy.description
            ? `${vacancy.description.length} символов`
            : "не найдено";

        shadow.innerHTML = `
            <style>
                * {
                    box-sizing: border-box;
                }

                .panel {
                    width: 350px;
                    max-height: calc(100vh - 120px);
                    overflow-y: auto;
                    background: #ffffff;
                    color: #151515;
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 16px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.16);
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                }

                .header {
                    position: sticky;
                    top: 0;
                    z-index: 2;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 14px 16px;
                    background: #202020;
                    color: #ffffff;
                }

                .title {
                    font-size: 15px;
                    font-weight: 700;
                }

                .version {
                    font-size: 11px;
                    opacity: 0.65;
                }

                .body {
                    padding: 16px;
                }

                .vacancy-title {
                    margin-bottom: 4px;
                    font-size: 15px;
                    line-height: 1.35;
                    font-weight: 700;
                }

                .company {
                    margin-bottom: 16px;
                    color: #666;
                    font-size: 13px;
                }

                .row {
                    display: grid;
                    grid-template-columns: 105px minmax(0, 1fr);
                    gap: 10px;
                    margin-bottom: 9px;
                    font-size: 12px;
                    line-height: 1.4;
                }

                .label {
                    color: #777;
                }

                .value {
                    font-weight: 500;
                    overflow-wrap: anywhere;
                }

                .ok {
                    color: #16883d;
                }

                .warning {
                    color: #aa6a00;
                }

                .divider {
                    height: 1px;
                    margin: 14px 0;
                    background: rgba(0, 0, 0, 0.08);
                }

                button {
                    width: 100%;
                    border: none;
                    border-radius: 10px;
                    padding: 10px 12px;
                    cursor: pointer;
                    font-size: 13px;
                    font-weight: 600;
                }

                button:disabled {
                    cursor: default;
                    opacity: 0.55;
                }

                #analyze-vacancy,
                #copy-json {
                    background: #202020;
                    color: #ffffff;
                }

                #analyze-vacancy:hover:not(:disabled),
                #copy-json:hover:not(:disabled) {
                    background: #333333;
                }

                #toggle-description,
                #open-resume-manager {
                    margin-top: 8px;
                    background: #f3f3f3;
                    color: #222;
                }

                #toggle-description:hover,
                #open-resume-manager:hover {
                    background: #e8e8e8;
                }

                .description {
                    display: none;
                    max-height: 250px;
                    overflow-y: auto;
                    margin-top: 10px;
                    padding: 10px;
                    background: #f7f7f7;
                    border-radius: 8px;
                    font-size: 11px;
                    line-height: 1.45;
                    white-space: pre-wrap;
                }

                .description.visible {
                    display: block;
                }

                .analysis-result {
                    display: none;
                    margin-top: 12px;
                }

                .analysis-result.visible {
                    display: block;
                }

                .score-line {
                    display: flex;
                    align-items: flex-end;
                    justify-content: space-between;
                    gap: 12px;
                }

                .score {
                    font-size: 28px;
                    font-weight: 800;
                    line-height: 1;
                }

                .decision {
                    padding: 4px 7px;
                    background: #f3f3f3;
                    border-radius: 999px;
                    color: #555;
                    font-size: 10px;
                    font-weight: 600;
                }

                .resume {
                    margin-top: 10px;
                    padding: 10px;
                    background: #f4f4f4;
                    border-radius: 8px;
                    font-size: 12px;
                }

                .resume strong {
                    display: block;
                    margin-top: 3px;
                    overflow-wrap: anywhere;
                }

                .skills {
                    margin-top: 10px;
                    font-size: 11px;
                    line-height: 1.65;
                }

                .skill-ok {
                    color: #16883d;
                }

                .skill-missing {
                    color: #aa6a00;
                }

                .alternatives {
                    margin-top: 12px;
                    padding-top: 10px;
                    border-top: 1px solid rgba(0, 0, 0, 0.08);
                }

                .alternatives-title {
                    margin-bottom: 5px;
                    color: #777;
                    font-size: 10px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.03em;
                }

                .alternative {
                    display: flex;
                    justify-content: space-between;
                    gap: 10px;
                    padding: 3px 0;
                    font-size: 11px;
                }

                .alternative-name {
                    min-width: 0;
                    overflow: hidden;
                    color: #555;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .alternative-score {
                    flex: 0 0 auto;
                    font-weight: 700;
                }

                .backend-error {
                    padding: 10px;
                    background: #fff2f2;
                    color: #b42318;
                    border-radius: 8px;
                    font-size: 11px;
                    line-height: 1.45;
                }

                .footer {
                    margin-top: 12px;
                    color: #999;
                    font-size: 10px;
                    text-align: center;
                }
            </style>

            <div class="panel">
                <div class="header">
                    <div class="title">${APP_NAME}</div>
                    <div class="version">v${escapeHtml(extensionVersion)}</div>
                </div>

                <div class="body">
                    <div class="vacancy-title">
                        ${escapeHtml(vacancy.title || "Название не найдено")}
                    </div>

                    <div class="company">
                        ${escapeHtml(vacancy.company || "Компания не найдена")}
                    </div>

                    <div class="row">
                        <div class="label">Vacancy ID</div>
                        <div class="value">${escapeHtml(vacancy.vacancyId || "—")}</div>
                    </div>

                    <div class="row">
                        <div class="label">Зарплата</div>
                        <div class="value">${escapeHtml(vacancy.salary || "Не указана")}</div>
                    </div>

                    <div class="row">
                        <div class="label">Локация</div>
                        <div class="value">${escapeHtml(vacancy.location || "—")}</div>
                    </div>

                    <div class="row">
                        <div class="label">Описание</div>
                        <div class="value ${vacancy.description ? "ok" : "warning"}">
                            ${escapeHtml(descriptionStatus)}
                        </div>
                    </div>

                    <div class="divider"></div>

                    <button id="analyze-vacancy">Проанализировать вакансию</button>
                    <div id="analysis-result" class="analysis-result"></div>

                    <div class="divider"></div>

                    <button id="copy-json">Скопировать данные вакансии</button>
                    <button id="toggle-description">Показать распознанное описание</button>

                    <div id="description" class="description">
                        ${escapeHtml(vacancy.description || "Описание не найдено")}
                    </div>

                    <button id="open-resume-manager">⚙ Управление резюме</button>

                    <div class="footer">
                        Пока ничего не отправляется и не сохраняется
                    </div>
                </div>
            </div>
        `;

        shadow
            .getElementById("copy-json")
            ?.addEventListener("click", async (event) => {
                const button = event.currentTarget;
                const oldText = button.textContent;
                const success = await copyText(JSON.stringify(vacancy, null, 2));

                button.textContent = success
                    ? "✓ Скопировано"
                    : "Ошибка копирования";

                setTimeout(() => {
                    button.textContent = oldText;
                }, 1200);
            });

        shadow
            .getElementById("toggle-description")
            ?.addEventListener("click", (event) => {
                const description = shadow.getElementById("description");

                if (!description) {
                    return;
                }

                const visible = description.classList.toggle("visible");
                event.currentTarget.textContent = visible
                    ? "Скрыть описание"
                    : "Показать распознанное описание";
            });

        shadow
            .getElementById("open-resume-manager")
            ?.addEventListener("click", openResumeManager);

        shadow
            .getElementById("analyze-vacancy")
            ?.addEventListener("click", async (event) => {
                const button = event.currentTarget;
                const resultElement = shadow.getElementById("analysis-result");

                if (!resultElement) {
                    return;
                }

                button.disabled = true;
                button.textContent = "Анализирую...";

                try {
                    const analysis = await analyzeVacancy(vacancy);

                    const matched = (analysis.matched_skills || [])
                        .map(
                            (skill) =>
                                `<div class="skill-ok">✓ ${escapeHtml(skill)}</div>`
                        )
                        .join("");

                    const missing = (analysis.missing_skills || [])
                        .map(
                            (skill) =>
                                `<div class="skill-missing">△ ${escapeHtml(skill)}</div>`
                        )
                        .join("");

                    const alternatives = (analysis.alternatives || [])
                        .map(
                            (item) => `
                                <div class="alternative">
                                    <div class="alternative-name" title="${escapeHtml(item.resume_name)}">
                                        ${escapeHtml(item.resume_name)}
                                    </div>
                                    <div class="alternative-score">${escapeHtml(item.score)}%</div>
                                </div>
                            `
                        )
                        .join("");

                    resultElement.innerHTML = `
                        <div class="score-line">
                            <div class="score">${escapeHtml(analysis.score)}%</div>
                            <div class="decision">${escapeHtml(decisionLabel(analysis.decision))}</div>
                        </div>

                        <div class="resume">
                            <div class="label">Рекомендуемое резюме</div>
                            <strong>${escapeHtml(analysis.recommended_resume || "—")}</strong>
                        </div>

                        <div class="skills">
                            ${matched || '<div class="label">Совпавшие навыки не найдены</div>'}
                            ${missing}
                        </div>

                        ${
                            alternatives
                                ? `
                                    <div class="alternatives">
                                        <div class="alternatives-title">Сравнение резюме</div>
                                        ${alternatives}
                                    </div>
                                `
                                : ""
                        }
                    `;

                    resultElement.classList.add("visible");
                    button.textContent = "✓ Анализ выполнен";
                } catch (error) {
                    console.error(`[${APP_NAME}] Analyze failed`, error);

                    resultElement.innerHTML = `
                        <div class="backend-error">
                            <strong>Не удалось выполнить анализ.</strong>
                            <br><br>
                            ${escapeHtml(error.message || String(error))}
                            <br><br>
                            Проверь, что backend запущен:
                            <br>
                            <code>uvicorn backend.app.main:app --reload --port 8000</code>
                        </div>
                    `;

                    resultElement.classList.add("visible");
                    button.textContent = "Повторить анализ";
                    button.disabled = false;
                    return;
                }

                setTimeout(() => {
                    button.disabled = false;
                    button.textContent = "Проанализировать снова";
                }, 1500);
            });
    }

    // =========================================================
    // Main
    // =========================================================

    function processVacancy() {
        const vacancyId = getVacancyId();

        if (!vacancyId) {
            return;
        }

        const vacancy = parseVacancy();

        if (!vacancy.title && !vacancy.description) {
            return;
        }

        const fingerprint = makeVacancyFingerprint(vacancy);

        // Не перерисовываем панель при каждой мутации DOM HH,
        // если данные вакансии фактически не изменились.
        if (
            fingerprint === lastVacancyFingerprint &&
            document.getElementById(HOST_ID)
        ) {
            return;
        }

        lastVacancyFingerprint = fingerprint;

        console.groupCollapsed(`[${APP_NAME}] ${vacancy.title}`);
        console.table({
            vacancyId: vacancy.vacancyId,
            title: vacancy.title,
            company: vacancy.company,
            salary: vacancy.salary,
            location: vacancy.location,
            descriptionLength: vacancy.description.length,
            url: vacancy.url,
        });
        console.log("Full vacancy:", vacancy);
        console.groupEnd();

        render(vacancy);
    }

    function scheduleProcess() {
        clearTimeout(renderTimer);
        renderTimer = setTimeout(processVacancy, 300);
    }

    scheduleProcess();

    const observer = new MutationObserver(scheduleProcess);
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
    });

    // HH может переключать вакансии без полного reload страницы.
    setInterval(() => {
        if (location.href !== previousUrl) {
            previousUrl = location.href;
            lastVacancyFingerprint = null;
            scheduleProcess();
        }
    }, 700);
})();