import logging

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

RECAPTCHA_VERIFY_URL = "https://www.recaptcha.net/recaptcha/api/siteverify"


class CaptchaConfig(models.Model):
    _name = "captcha.config"
    _description = "Google reCAPTCHA Configuration"

    name = fields.Char(default="reCAPTCHA Settings", required=True)
    active = fields.Boolean(
        default=True,
        help="Only the first active configuration found for a given purpose is used.",
    )
    purpose = fields.Selection(
        [
            ("auth", "Login / Signup / Password Reset"),
            ("website_form", "Website Forms (Contact Us, Helpdesk, ...)"),
            ("both", "Both"),
        ],
        string="Used For",
        default="auth",
        required=True,
        help="Login/signup/password reset and website forms (Contact Us, Helpdesk "
             "ticket form) both support either reCAPTCHA version. 'Both' reuses the "
             "same key/secret everywhere.",
    )
    version = fields.Selection(
        [
            ("v2", "reCAPTCHA v2 (\"I'm not a robot\" checkbox)"),
            ("v3", "reCAPTCHA v3 (score-based, invisible)"),
        ],
        string="Version",
        default="v2",
        required=True,
    )
    site_key = fields.Char(string="Site Key", required=True)
    secret_key = fields.Char(string="Secret Key", required=True)
    score_threshold = fields.Float(
        string="Minimum Score",
        default=0.5,
        help="reCAPTCHA v3 only: minimum score (0.0 to 1.0) required to consider "
             "the request as coming from a human.",
    )

    _sql_constraints = [
        (
            "score_threshold_range",
            "CHECK (score_threshold >= 0 AND score_threshold <= 1)",
            "The minimum score must be between 0 and 1.",
        ),
    ]

    @api.model
    def get_active_config(self, purpose=None):
        domain = [("active", "=", True)]
        if purpose:
            domain += ["|", ("purpose", "=", purpose), ("purpose", "=", "both")]
        return self.sudo().search(domain, limit=1)

    def verify_recaptcha_v3(self, token, ip_addr, action=False):
        """Verify a reCAPTCHA v3 token, mirroring the result codes used by
        Odoo's own ir.http._verify_recaptcha_token so it can be dropped in
        as a replacement for it.
        """
        self.ensure_one()
        try:
            resp = requests.post(
                RECAPTCHA_VERIFY_URL,
                data={
                    "secret": self.secret_key,
                    "response": token,
                    "remoteip": ip_addr,
                },
                timeout=5,
            )
            result = resp.json()
            res_success = result.get("success")
            res_action = res_success and action and result.get("action")
        except requests.exceptions.Timeout:
            _logger.warning("reCAPTCHA verification timed out for ip address %s", ip_addr)
            return "timeout"
        except Exception:
            _logger.exception("reCAPTCHA verification request failed")
            return "bad_request"

        if res_success:
            score = result.get("score", 0)
            if score < self.score_threshold:
                return "is_bot"
            if res_action and res_action != action:
                return "wrong_action"
            return "is_human"

        for error in result.get("error-codes", []):
            if error in ("missing-input-secret", "invalid-input-secret"):
                return "wrong_secret"
            if error in ("missing-input-response", "invalid-input-response"):
                return "wrong_token"
            if error == "timeout-or-duplicate":
                return "timeout"
            if error == "bad-request":
                return "bad_request"
        return "is_bot"

    def verify_recaptcha_v2(self, token, ip_addr):
        """Verify a reCAPTCHA v2 (checkbox) response, mirroring the same
        result codes as verify_recaptcha_v3 (v2's siteverify response has no
        score/action, just success/failure).
        """
        self.ensure_one()
        if not token:
            return "wrong_token"
        try:
            resp = requests.post(
                RECAPTCHA_VERIFY_URL,
                data={
                    "secret": self.secret_key,
                    "response": token,
                    "remoteip": ip_addr,
                },
                timeout=5,
            )
            result = resp.json()
        except requests.exceptions.Timeout:
            _logger.warning("reCAPTCHA verification timed out for ip address %s", ip_addr)
            return "timeout"
        except Exception:
            _logger.exception("reCAPTCHA verification request failed")
            return "bad_request"

        if result.get("success"):
            return "is_human"

        for error in result.get("error-codes", []):
            if error in ("missing-input-secret", "invalid-input-secret"):
                return "wrong_secret"
            if error in ("missing-input-response", "invalid-input-response"):
                return "wrong_token"
            if error == "timeout-or-duplicate":
                return "timeout"
            if error == "bad-request":
                return "bad_request"
        return "wrong_token"
