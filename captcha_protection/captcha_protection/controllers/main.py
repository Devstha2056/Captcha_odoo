import logging

import requests

from odoo import http, _
from odoo.http import request

from odoo.addons.web.controllers.home import Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


class CaptchaMixin:

    def _get_captcha_config(self):
        return request.env["captcha.config"].get_active_config(purpose="auth")

    def _verify_captcha(self, config):
        """Verify the reCAPTCHA response token against Google's API.

        :return: (bool success, str|None error_message)
        """
        response_token = request.params.get("g-recaptcha-response")
        if not response_token:
            return False, _("Please complete the captcha challenge.")

        try:
            resp = requests.post(
                RECAPTCHA_VERIFY_URL,
                data={
                    "secret": config.secret_key,
                    "response": response_token,
                    "remoteip": request.httprequest.remote_addr,
                },
                timeout=5,
            )
            result = resp.json()
        except requests.exceptions.RequestException:
            _logger.exception("reCAPTCHA verification request failed")
            return False, _("Could not verify the captcha, please try again.")

        if not result.get("success"):
            return False, _("Captcha verification failed, please try again.")

        if config.version == "v3" and result.get("score", 0) < config.score_threshold:
            return False, _("Captcha verification failed, please try again.")

        return True, None


class CaptchaHome(CaptchaMixin, Home):

    @http.route()
    def web_login(self, redirect=None, **kw):
        config = self._get_captcha_config()
        captcha_error = None
        if config and request.httprequest.method == "POST":
            ok, captcha_error = self._verify_captcha(config)
            if not ok:
                # Let the normal login flow run (so every other module's
                # web_login override still contributes to the rendered
                # page), but guarantee authentication cannot succeed with
                # the submitted credentials.
                request.params["password"] = "__captcha_rejected__"

        response = super().web_login(redirect=redirect, **kw)
        if config and hasattr(response, "qcontext"):
            response.qcontext["captcha_config"] = config
            if captcha_error:
                response.qcontext["error"] = captcha_error
        return response


class CaptchaAuthSignupHome(CaptchaMixin, AuthSignupHome):

    @http.route()
    def web_auth_signup(self, *args, **kw):
        config = self._get_captcha_config()
        if config and request.httprequest.method == "POST":
            ok, error = self._verify_captcha(config)
            if not ok:
                # 'error' is part of SIGN_UP_REQUEST_PARAMS, so injecting it
                # here makes get_auth_signup_qcontext() pick it up, which in
                # turn makes the base controller skip do_signup() entirely -
                # no account gets created when the captcha check fails.
                request.params["error"] = error

        response = super().web_auth_signup(*args, **kw)
        if config and hasattr(response, "qcontext"):
            response.qcontext["captcha_config"] = config
        return response

    @http.route()
    def web_auth_reset_password(self, *args, **kw):
        config = self._get_captcha_config()
        if config and request.httprequest.method == "POST":
            ok, error = self._verify_captcha(config)
            if not ok:
                request.params["error"] = error

        response = super().web_auth_reset_password(*args, **kw)
        if config and hasattr(response, "qcontext"):
            response.qcontext["captcha_config"] = config
        return response
