(() => {
    "use strict";

    const runtime =
        typeof browser !== "undefined"
            ? browser.runtime
            : chrome.runtime;


    runtime.onMessage.addListener(
        async message => {

            if (
                message?.type !==
                "OPEN_RESUME_MANAGER"
            ) {
                return;
            }


            try {

                await runtime.openOptionsPage();

                return {
                    success: true
                };

            } catch (error) {

                console.error(
                    "[HH Job Assistant] " +
                    "Failed to open options page:",
                    error
                );

                return {
                    success: false,
                    error: String(error)
                };
            }
        }
    );

})();