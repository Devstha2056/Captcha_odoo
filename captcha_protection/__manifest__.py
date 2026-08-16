{
    "name": "Google reCAPTCHA (v2 & v3)",  
    "summary": "Protect login, signup, password reset and website forms with Google reCAPTCHA",
    "description": """
Captcha Protection
===================
Adds a `captcha.config` model to store Google reCAPTCHA (v2 or v3) credentials
and enforces verification on:

* /web/login, /web/signup, /web/reset_password (own widget, v2 or v3)
* Contact Us and the Helpdesk ticket form:
  - v3: supplies the key Odoo's own website form builder JS already looks
    for, so it works transparently with no widget of our own
  - v2: our own checkbox widget is inserted directly into those two page
    templates (website.contactus / website_helpdesk.ticket_submit_form),
    since the builder's own JS has no v2 code path at all
""",
    "version": "19.0.1.0.0",
    "category": "Extra Tools",
    "author": "Innovax Solutions Pvt. Ltd.",
    "license": "LGPL-3",
    "depends": ["auth_signup", "google_recaptcha", "website", "website_helpdesk"],
    "price": 10.0,
    "currency": "USD",
    "images": [
        "static/description/screenshot_contact_form.png",
        "static/description/screenshot_login.png",
        "static/description/screenshot_helpdesk_ticket.png",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/captcha_config_views.xml",
        "views/login_templates.xml",
        "views/website_form_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "captcha_protection/static/src/js/captcha_widget.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
