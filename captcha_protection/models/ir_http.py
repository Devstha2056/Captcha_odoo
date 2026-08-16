from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

# Login, signup and password-reset are verified independently by this
# module's own controllers (captcha.config, purpose="auth"), using their own
# widget and their own g-recaptcha-response field. Odoo core's web_login()
# unconditionally also calls _verify_request_recaptcha_token('login') (and
# the auth_signup routes declare captcha='signup'/'password_reset'), which
# would otherwise be routed through this override too and fail, since core
# looks for a different field name (recaptcha_token_response) that our own
# widget never sets. These actions are therefore short-circuited to a no-op
# unconditionally - NOT delegated to core's own ir.config_parameter-based
# check, since that would still fire (and still fail) if those parameters
# happen to hold a value from unrelated configuration.
_AUTH_ACTIONS = {"login", "signup", "password_reset"}


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @api.model
    def _add_public_key_to_session_info(self, session_info):
        # Only leak a public key for v3: the website form builder's own JS
        # (Form interaction) always loads it via the v3 render= flow, so
        # handing it a v2 key would make core try to load recaptcha with an
        # incompatible key type and fail. v2 website forms are handled by
        # our own widget (captcha_protection.website_form_v2_widget)
        # instead, which looks up its config directly.
        config = request.env["captcha.config"].sudo().get_active_config(purpose="website_form")
        if config and config.version == "v3":
            session_info["recaptcha_public_key"] = config.site_key
            return session_info
        return super()._add_public_key_to_session_info(session_info)

    @api.model
    def _verify_recaptcha_token(self, ip_addr, token, action=False):
        if action in _AUTH_ACTIONS:
            return "no_secret"
        config = request.env["captcha.config"].sudo().get_active_config(purpose="website_form")
        if not config or config.version != "v3":
            return super()._verify_recaptcha_token(ip_addr, token, action)
        return config.verify_recaptcha_v3(token, ip_addr, action)

    @api.model
    def _verify_request_recaptcha_token(self, action):
        # v2 website forms use Google's own field name (g-recaptcha-response)
        # rather than core's v3-oriented recaptcha_token_response, and their
        # siteverify response has no action/score to check. Handle that case
        # entirely ourselves instead of routing it through
        # _verify_recaptcha_token (which core's outer method feeds the wrong
        # field name into).
        if action not in _AUTH_ACTIONS:
            config = request.env["captcha.config"].sudo().get_active_config(purpose="website_form")
            if config and config.version == "v2":
                token = request.params.pop("g-recaptcha-response", False)
                result = config.verify_recaptcha_v2(token, request.httprequest.remote_addr)
                if result in ("is_human", "no_secret"):
                    return
                if result == "wrong_secret":
                    raise ValidationError(_("The reCaptcha private key is invalid."))
                if result == "wrong_token":
                    raise ValidationError(_("The reCaptcha token is invalid."))
                if result == "timeout":
                    raise UserError(_("Your request has timed out, please retry."))
                raise UserError(_("Suspicious activity detected by reCAPTCHA."))
        return super()._verify_request_recaptcha_token(action)
