# import os

# basedir = os.path.abspath(os.path.dirname(__file__))


###############################################################################
class Config(object):
    """ Base configuration for default configuration """

    # Flask settings
    CSRF_ENABLED = True
    DEBUG = False
    TESTING = False
    # DO NOT use Unsecure Secrets in production environments
    # Generate a safe one with:
    #     python -c "import os; print repr(os.urandom(24));"
    SECRET_KEY = 'This is an UNSECURE Secret. CHANGE THIS for production environments.'
    # We're using PBKDF2 with salt.
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    # Replace this with your own salt.
    SECURITY_PASSWORD_SALT = '<changeme : xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx>'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test.db'

    # Flask-Mail settings
    # For smtp.gmail.com to work, you MUST set "Allow less secure apps" to ON in Google Accounts.
    # Change it in https://myaccount.google.com/security#connectedapps (near the bottom).
    MAIL_DEFAULT_SENDER = 'luonbin@hotmail.com',
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025
    MAIL_USE_SSL = False
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'mailhog'
    MAIL_PASSWORD = 'mailhog'

    # Flask-Security optionally sends email notification to users upon registration, password reset, etc.
    # It uses Flask-Mail behind the scenes.
    # Set mail-related config values.
    # Replace this with your own "from" address
    SECURITY_EMAIL_SENDER = 'luonbin@hotmail.com'

    # Flask-User settings
    USER_APP_NAME = 'Flask-User starter app'
    USER_ENABLE_CHANGE_PASSWORD = True  # Allow users to change their password
    USER_ENABLE_CHANGE_USERNAME = False  # Allow users to change their username
    USER_ENABLE_CONFIRM_EMAIL = True  # Force users to confirm their email
    USER_ENABLE_FORGOT_PASSWORD = True  # Allow users to reset their passwords
    USER_ENABLE_EMAIL = True  # Register with Email
    USER_ENABLE_REGISTRATION = True  # Allow new users to register
    USER_REQUIRE_RETYPE_PASSWORD = True  # Prompt for `retype password` in:
    USER_ENABLE_USERNAME = False  # Register and Login with username
    USER_AFTER_LOGIN_ENDPOINT = 'main.member_page'
    USER_AFTER_LOGOUT_ENDPOINT = 'main.home_page'

    # Application settings
    APP_NAME = 'Flask-User starter app'
    APP_SYSTEM_ERROR_SUBJECT_LINE = APP_NAME + " system error"

    # Sendgrid settings
    SENDGRID_API_KEY = 'place-your-sendgrid-api-key-here'

    # Flask-User settings
    USER_APP_NAME = 'Flask-User starter app'
    USER_EMAIL_SENDER_NAME = 'Your name'
    USER_EMAIL_SENDER_EMAIL = 'yourname@gmail.com'

    ADMINS = [
        '"Admin One" <admin1@gmail.com>',
    ]


class ProductionConfig(Config):
    """ specified configuration for production environment """

    DEBUG = False


class StagingConfig(Config):
    """ specified configuration for staging environment """

    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    """ specified configuration for development environment """

    DEVELOPMENT = True
    DEBUG = True
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """ specified configuration for testing environment """

    TESTING = True
    SQLALCHEMY_ECHO = True


###############################################################################
config_by_name = dict(
    production=ProductionConfig,
    staging=StagingConfig,
    development=DevelopmentConfig,
    testing=TestingConfig,
)
