# Captcha Protection for Odoo

Odoo module that protects login, signup, password reset, and website forms using Google reCAPTCHA (v2 or v3).

## Features

- Adds a `captcha.config` model to manage reCAPTCHA credentials
- - Enforces verification on the login, signup, and password reset pages
  - - Adds reCAPTCHA support to the Contact Us and Helpdesk ticket forms
    - - Supports both reCAPTCHA v2 (checkbox widget) and v3 (score-based)
     
      - ## Installation
     
      - 1. Copy the `captcha_protection` folder into your Odoo addons directory.
        2. 2. Update the apps list and install "Captcha Protection" from the Odoo Apps menu.
           3. 3. Configure your reCAPTCHA site/secret keys in the module settings.
             
              4. ## Requirements
             
              5. - Odoo 19.0
                 - - Dependencies: `auth_signup`, `google_recaptcha`, `website`, `website_helpdesk`
                  
                   - ## License
                  
                   - LGPL-3
                  
                   - ## Author
                  
                   - Grantha Network
                   - 
