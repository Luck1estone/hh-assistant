(() => {
    "use strict";


    const API_URL =
        "http://127.0.0.1:8000";


    const PROFILE_NAMES = {
        sdet:
            "SDET / QA Automation",

        fullstack:
            "Fullstack QA",

        backend:
            "Backend QA",

        mobile:
            "Mobile QA",

        platform:
            "QA Platform"
    };


    const resumeList =
        document.getElementById(
            "resume-list"
        );


    const backendStatus =
        document.getElementById(
            "backend-status"
        );


    const refreshButton =
        document.getElementById(
            "refresh-button"
        );


    const uploadForm =
        document.getElementById(
            "upload-form"
        );


    const uploadButton =
        document.getElementById(
            "upload-button"
        );


    const uploadResult =
        document.getElementById(
            "upload-result"
        );


    // =========================================================
    // Utils
    // =========================================================

    function escapeHtml(value) {
        return String(
            value ?? ""
        )
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }


    function showMessage(
        text,
        type
    ) {
        uploadResult.textContent =
            text;

        uploadResult.className =
            `message visible ${type}`;
    }


    function hideMessage() {
        uploadResult.className =
            "message";

        uploadResult.textContent =
            "";
    }


    // =========================================================
    // Backend
    // =========================================================

    async function request(
        path,
        options = {}
    ) {

        const response = await fetch(
            `${API_URL}${path}`,
            options
        );


        if (!response.ok) {

            let message =
                `HTTP ${response.status}`;

            try {

                const body =
                    await response.json();

                message =
                    body.detail ||
                    message;

            } catch (_) {
                // ignore
            }


            throw new Error(
                message
            );
        }


        return await response.json();
    }


    async function checkBackend() {

        try {

            await request(
                "/health"
            );

            backendStatus.textContent =
                "● Backend online";

            backendStatus.className =
                "backend-status online";

            return true;

        } catch (error) {

            backendStatus.textContent =
                "● Backend offline";

            backendStatus.className =
                "backend-status offline";

            return false;
        }
    }


    // =========================================================
    // Resumes
    // =========================================================

    async function loadResumes() {

        resumeList.innerHTML =
            "Загрузка...";


        try {

            const resumes =
                await request(
                    "/api/resumes"
                );


            renderResumes(
                resumes
            );

        } catch (error) {

            resumeList.innerHTML = `

                <div class="empty-state">

                    Не удалось получить резюме.

                    <br><br>

                    ${escapeHtml(
                        error.message
                    )}

                </div>
            `;
        }
    }


    function renderResumes(
        resumes
    ) {

        if (!resumes.length) {

            resumeList.innerHTML = `

                <div class="empty-state">

                    В базе пока нет резюме.

                </div>
            `;

            return;
        }


        resumeList.innerHTML =
            resumes
                .map(
                    resume =>
                        createResumeHtml(
                            resume
                        )
                )
                .join("");


        document
            .querySelectorAll(
                "[data-delete-resume]"
            )
            .forEach(
                button => {

                    button.addEventListener(
                        "click",
                        async () => {

                            const id =
                                button.dataset
                                    .deleteResume;

                            const name =
                                button.dataset
                                    .resumeName;


                            const confirmed =
                                confirm(
                                    `Удалить резюме "${name}"?`
                                );


                            if (!confirmed) {
                                return;
                            }


                            button.disabled = true;


                            try {

                                await request(
                                    `/api/resumes/${id}`,
                                    {
                                        method:
                                            "DELETE"
                                    }
                                );

                                await loadResumes();

                            } catch (error) {

                                alert(
                                    `Ошибка: ${error.message}`
                                );

                                button.disabled =
                                    false;
                            }
                        }
                    );
                }
            );
    }


    function createResumeHtml(
        resume
    ) {

        const skills =
            (resume.skills || [])
                .map(
                    skill => `
                        <span class="skill">
                            ${escapeHtml(skill)}
                        </span>
                    `
                )
                .join("");


        const profileName =
            PROFILE_NAMES[
                resume.profile
            ]
            ||
            resume.profile
            ||
            "Профиль не назначен";


        return `

            <div class="resume-card">

                <div>

                    <div class="resume-title">

                        ${escapeHtml(
                            resume.name
                        )}

                    </div>


                    <div class="resume-meta">

                        ${escapeHtml(
                            resume.filename
                        )}

                        ·

                        ${Number(
                            resume.text_length || 0
                        ).toLocaleString("ru-RU")}

                        символов

                    </div>


                    <div class="profile-badge">

                        ${escapeHtml(
                            profileName
                        )}

                    </div>


                    <div class="skills">

                        ${skills}

                    </div>

                </div>


                <div class="resume-actions">

                    <button
                        class="button danger"

                        data-delete-resume="${
                            escapeHtml(
                                resume.id
                            )
                        }"

                        data-resume-name="${
                            escapeHtml(
                                resume.name
                            )
                        }"
                    >

                        Удалить

                    </button>

                </div>

            </div>
        `;
    }


    // =========================================================
    // Upload
    // =========================================================

    uploadForm.addEventListener(
        "submit",
        async event => {

            event.preventDefault();

            hideMessage();


            const profile =
                document
                    .getElementById(
                        "profile"
                    )
                    .value;


            const name =
                document
                    .getElementById(
                        "resume-name"
                    )
                    .value
                    .trim();


            const fileInput =
                document
                    .getElementById(
                        "resume-file"
                    );


            const file =
                fileInput.files[0];


            if (
                !profile ||
                !name ||
                !file
            ) {
                showMessage(
                    "Заполни все поля.",
                    "error"
                );

                return;
            }


            const formData =
                new FormData();


            formData.append(
                "name",
                name
            );


            formData.append(
                "profile",
                profile
            );


            formData.append(
                "file",
                file
            );


            uploadButton.disabled =
                true;

            uploadButton.textContent =
                "Загружаю...";


            try {

                const response =
                    await fetch(
                        `${API_URL}/api/resumes`,
                        {
                            method:
                                "POST",

                            body:
                                formData
                        }
                    );


                if (!response.ok) {

                    const body =
                        await response.json();

                    throw new Error(
                        body.detail ||
                        `HTTP ${response.status}`
                    );
                }


                const resume =
                    await response.json();


                showMessage(
                    `✓ Загружено: ${resume.name}`,
                    "success"
                );


                uploadForm.reset();


                await loadResumes();

            } catch (error) {

                showMessage(
                    error.message,
                    "error"
                );

            } finally {

                uploadButton.disabled =
                    false;

                uploadButton.textContent =
                    "Загрузить PDF";
            }
        }
    );


    refreshButton.addEventListener(
        "click",
        async () => {

            await checkBackend();
            await loadResumes();
        }
    );


    // =========================================================
    // Startup
    // =========================================================

    async function init() {

        const online =
            await checkBackend();


        if (online) {
            await loadResumes();
        }
    }


    init();

})();