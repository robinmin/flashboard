# import system packages
import os
import json
import logging
import logging.config
from datetime import datetime

# import flask and extension packages
from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail, Message

# from flask_migrate import Migrate, MigrateCommand
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from celery import Celery

# import application packages
from config.config import config_by_name
from .database import init_db, create_all_tables

# current working folder
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Instance of Flask extensions
cors = CORS()
# db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
# migrate = Migrate()
csrf_protect = CSRFProtect()


###############################################################################
def load_json_config(conf_file):
    """ load configuration information in json format """

    # conf_file = os.path.join(basedir, 'config/config.json')
    if not os.path.isfile(conf_file):
        print('Config file is not exist : ' + conf_file)
        return dict()
    config = json.load(open(conf_file), encoding='UTF-8')
    return config


def create_app(extra_config_settings={}):
    """ Create a Flask application """

    # load configuration information
    log_config = load_json_config(os.path.join(basedir, 'config/logging.json'))
    logging.config.dictConfig(log_config)

    log = logging.getLogger(__name__)

    # Instantiate Flask
    app = Flask(__name__)

    # Load configuration settings
    config_name = os.getenv('FLASK_ENV', 'production')
    if config_name not in config_by_name:
        config_name = 'production'
    app.config.from_object(config_by_name[config_name])

    # Load extra settings from extra_config_settings param
    if extra_config_settings is not None and len(extra_config_settings) > 0:
        app.config.update(extra_config_settings)

    # integrate with sentry SDK
    sentry_sdk.init(
        dsn=app.config['SENTRY_DSN'],
        integrations=[FlaskIntegration(), SqlalchemyIntegration()]
    )

    # Define bootstrap_is_hidden_field for flask-bootstrap's bootstrap_wtf.html
    from wtforms.fields import HiddenField

    def is_hidden_field_filter(field):
        return isinstance(field, HiddenField)

    app.jinja_env.globals['bootstrap_is_hidden_field'] = is_hidden_field_filter

    init_app(app)

    # register all relevant blueprints
    with app.app_context():
        from .views import bp as bp_sys
        from .factories import api, bp as bp_api
        from .apis import auth_ns

        # avoid to check CSRF on APIs
        csrf_protect.exempt(bp_api)

        # add namespaces for API
        api.add_namespace(auth_ns, path='/user')

        app.register_blueprint(bp_sys, url_prefix='/sys')
        app.register_blueprint(bp_api, url_prefix='/api')

        # Initialize Global db and create all tables
        init_db(app)

        return app


def init_email_error_handler(app):
    """
    Initialize a logger to send emails on error-level messages.
    Unhandled exceptions will now send an email message to app.config.ADMINS.
    """
    if app.debug:
        return  # Do not send error emails while developing

    # Retrieve email settings from app.config
    host = app.config['MAIL_SERVER']
    port = app.config['MAIL_PORT']
    from_addr = app.config['MAIL_DEFAULT_SENDER']
    username = app.config['MAIL_USERNAME']
    password = app.config['MAIL_PASSWORD']
    secure = () if app.config.get('MAIL_USE_TLS') else None

    # Retrieve app settings from app.config
    to_addr_list = app.config['ADMINS']
    subject = app.config.get('APP_SYSTEM_ERROR_SUBJECT_LINE', 'System Error')

    # Setup an SMTP mail handler for error-level messages
    import logging
    from logging.handlers import SMTPHandler

    mail_handler = SMTPHandler(
        mailhost=(host, port),  # Mail host and port
        fromaddr=from_addr,  # From address
        toaddrs=to_addr_list,  # To address
        subject=subject,  # Subject line
        credentials=(username, password),  # Credentials
        secure=secure,
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)


def init_app(app):
    """ Initialize application extensions instance """

    # Setup Flask-CORS
    cors.init_app(app)

    # Setup Flask-SQLAlchemy
    # db.init_app(app)

    # Setup Flask-Mail
    mail.init_app(app)
    # Setup an error-logger to send emails to app.config.ADMINS
    # init_email_error_handler(app)

    # Setup Flask-Migrate
    # migrate.init_app(app, db)

    # Setup WTForms CSRFProtect
    csrf_protect.init_app(app)

    # Setup Flask-Login
    login_manager.init_app(app)
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'login'

    if app.config['ENV'] == 'development':
        from flask_debugtoolbar import DebugToolbarExtension

        # disable intercept redirect
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        toolbar = DebugToolbarExtension(app)


def send_email(app, to, subject, template):
    """ send email message """
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    return mail.send(msg)


def int_celery(app):
    """
        create instance of celery, then you can customize task as shown below:

            celery = init_celery(flask_app)

            @celery.task()
            def add_together(a, b):
                return a + b
    """

    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


###############################################################################
