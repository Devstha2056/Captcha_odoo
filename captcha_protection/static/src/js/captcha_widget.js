(function () {
    "use strict";

    function waitForGrecaptcha(timeoutMs) {
        return new Promise(function (resolve, reject) {
            var start = Date.now();
            (function check() {
                if (typeof grecaptcha !== "undefined" && grecaptcha.execute) {
                    resolve();
                } else if (Date.now() - start > timeoutMs) {
                    reject(new Error("reCAPTCHA did not load in time"));
                } else {
                    setTimeout(check, 100);
                }
            })();
        });
    }

    function initRecaptchaV3(container) {
        var form = container.closest("form");
        if (!form) {
            return;
        }
        var siteKey = container.getAttribute("data-sitekey");
        var action = container.getAttribute("data-action") || "submit";
        var submitting = false;

        form.addEventListener("submit", function (ev) {
            if (submitting || form.querySelector("input[name='g-recaptcha-response']")) {
                return;
            }
            // Always block the native submit first: if we let it through
            // whenever grecaptcha isn't ready yet, the request goes out with
            // no token at all instead of waiting for one.
            ev.preventDefault();

            function submitWithToken(token) {
                if (token) {
                    var input = document.createElement("input");
                    input.type = "hidden";
                    input.name = "g-recaptcha-response";
                    input.value = token;
                    form.appendChild(input);
                }
                submitting = true;
                form.submit();
            }

            waitForGrecaptcha(10000)
                .then(function () {
                    return new Promise(function (resolve) {
                        grecaptcha.ready(resolve);
                    });
                })
                .then(function () {
                    return grecaptcha.execute(siteKey, {action: action});
                })
                .then(submitWithToken)
                .catch(function () {
                    // reCAPTCHA failed to load/execute in time. Submit
                    // anyway so the user gets the server's captcha error
                    // message instead of a form that silently does nothing.
                    submitWithToken(null);
                });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll(".g-recaptcha-v3").forEach(initRecaptchaV3);
    });
})();
