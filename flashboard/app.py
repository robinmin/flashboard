# import system packages
import os
import json
import time
import logging
import logging.config

# import flask and extension packages
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask, redirect, request, url_for, g, flash
from flask_login import LoginManager, current_user
from flask_mail import Mail, Message

# from flask_migrate import Migrate, MigrateCommand
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask_babel import Babel, gettext as _

# import application packages
from config.config import config_factory, all_urls
from .database import init_db, create_session
from .services import UserService

# current working folder
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Instance of Flask extensions
cors = CORS()
login_manager = LoginManager()
mail = Mail()
# migrate = Migrate()
csrf_protect = CSRFProtect()

babel = Babel()

# global instance
log = None
celery = None

###############################################################################


def load_json_config(conf_file):
    """ load configuration information in json format """

    # conf_file = os.path.join(basedir, 'config/config.json')
    if not os.path.isfile(conf_file):
        print('Config file is not exist : ' + conf_file)
        return dict()

    data = ''
    today = time.strftime('%Y%m%d')
    with open(conf_file, 'r') as file:
        data = file.read()
    config = json.loads(data.replace('{today}', today), encoding='UTF-8')
    return config


def create_app(extra_config_settings={}):
    """ Create a Flask application """

    # load configuration information
    log_config = load_json_config(os.path.join(basedir, 'config/logging.json'))
    logging.config.dictConfig(log_config)

    global log
    log = logging.getLogger(__name__)

    # Instantiate Flask
    app = Flask(__name__)

    # Load configuration settings
    app.config.from_object(config_factory(
        os.getenv('FLASK_ENV', 'production')
    ))

    # Load extra settings from extra_config_settings param
    if extra_config_settings is not None and len(extra_config_settings) > 0:
        app.config.update(extra_config_settings)

    init_app(app)

    # enable sentry
    if app.config.get('ENABLE_SENTRY', False):
        enable_sentry(app)

    # enable admin
    if app.config.get('ENABLE_ADMIN', False):
        enable_admin(app)

    # enable debug tool bar
    if app.config.get('ENABLE_DEBUG_TOOLBAR', False):
        from flask_debugtoolbar import DebugToolbarExtension
        DebugToolbarExtension(app)

    # enable celery
    if app.config.get('ENABLE_CELERY', False):
        enable_celery(app)

    # register all relevant blueprints
    with app.app_context():
        if app.config.get('ENABLE_BUILDIN_API', False):
            from .apis import auth_ns, api, bp as bp_api

            # avoid to check CSRF on APIs
            csrf_protect.exempt(bp_api)

            # add namespaces for API
            api.add_namespace(auth_ns, path='/user')

            app.register_blueprint(bp_api, url_prefix='/api')
        if app.config.get('ENABLE_BUILDIN_VIEW', False):
            from .views import bp as bp_sys

            app.register_blueprint(bp_sys, url_prefix='/sys')

            # add default page
            # TODO: how to use APP_URL_WELCOME to call add_url_rule
            from .views import login
            app.add_url_rule('/',      view_func=login)
            app.add_url_rule('/index', view_func=login)

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
    host = app.config.get('MAIL_SERVER', 'localhost')
    port = app.config.get('MAIL_PORT', None)
    from_addr = app.config.get('MAIL_DEFAULT_SENDER', None)
    username = app.config.get('MAIL_USERNAME', None)
    password = app.config.get('MAIL_PASSWORD', None)
    secure = () if app.config.get('MAIL_USE_TLS') else None

    # Retrieve app settings from app.config
    to_addr_list = app.config.get('ADMINS', None)
    subject = app.config.get(
        'APP_SYSTEM_ERROR_SUBJECT_LINE', _('System Error'))

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
    login_manager.login_view = app.config.get('APP_URL_WELCOME', '')
    login_manager.login_message = _('Unauthorized User')
    login_manager.login_message_category = 'info'

    # enable i18n
    babel.init_app(app)


@login_manager.user_loader
def user_loader(user_id):
    """ Given *user_id*, return the associated User object """

    try:
        # get default language
        from flask import current_app
        lang = current_app.config.get('BABEL_DEFAULT_LOCALE', None)

        # user prefference support
        user = UserService().load_user(user_id)
        if hasattr(user, 'language'):
            lang = user.language

        # cache user language prefference into global variable
        if hasattr(g, 'user_info'):
            g.user_info['locale'] = lang
        else:
            g.user_info = {
                'locale': lang
            }

        # cache config information
        if not hasattr(g, 'config'):
            g.config = {
                'BABEL_DEFAULT_LOCALE': current_app.config.get('BABEL_DEFAULT_LOCALE', 'en'),
                'BABEL_DEFAULT_TIMEZONE': current_app.config.get('BABEL_DEFAULT_TIMEZONE', 'UTC'),
                'BABEL_LANGUAGES': current_app.config.get('BABEL_LANGUAGES', {}),
            }

        # special case for confirm_email
        if request.path:
            include_inactive = allow_inactive_login(request.path)
            if include_inactive:
                return user

        return user if user and user.actived else None
    except SQLAlchemyError:
        return None


@login_manager.unauthorized_handler
def unauthorized():
    """ Redirect unauthorized users to Login page """
    flash(_('You must be logged in to view that page.'))
    return redirect(url_for(all_urls['login']))


def allow_inactive_login(next):
    """ helper function to detect current action is allow inactive user login or not """

    if not next:
        return False

    url_parts = next.split('/')
    if not isinstance(url_parts, list) or len(url_parts) < 3:
        return False

    url_prefix = '/'.join(url_parts[0:3])
    valid_urls = [
        '/sys/confirm_email',
    ]
    return url_prefix in valid_urls


def send_email(app, to, subject, template):
    """ send email message """
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config.get('MAIL_DEFAULT_SENDER', None)
    )
    return mail.send(msg)


def enable_sentry(app):
    """ enable sentry

    Arguments:
        app {object} -- instance of application
    """

    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    # integrate with sentry SDK
    sentry_sdk.init(
        dsn=app.config.get('SENTRY_DSN', ''),
        integrations=[FlaskIntegration(), SqlalchemyIntegration()]
    )


def enable_celery(app=None):
    """
        create instance of celery, then you can customize task as shown below:

            celery = enable_celery(flask_app)

            @celery.task()
            def add_together(a, b):
                return a + b
    """
    global celery
    if celery:
        return celery

    from celery import Celery

    if app is None:
        app = create_app()

    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', ''),
        broker=app.config.get('CELERY_BROKER_URL', '')
    )

    celery.conf.update(app.config)

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery


def enable_admin(app):
    """ initialize admin component """

    from flask_admin import Admin
    from flask_admin.menu import MenuLink
    from flask_admin.contrib.sqla import ModelView
    from sqlalchemy.ext.declarative.api import DeclarativeMeta

    from flashboard import models

    # get wecome URL
    url_welcome = app.config.get('APP_URL_WELCOME', None)

    # define customized class
    class MyModelView(ModelView):

        def is_accessible(self):
            return current_user and current_user.is_authenticated

        def inaccessible_callback(self, name, **kwargs):
            # redirect to login page if user doesn't have access
            return redirect(url_for(url_welcome, next=request.url))

    admin = Admin(app, name='Admin', template_mode='bootstrap3')

    # Add administrative views here
    # get all models defined in `models`
    session = create_session(app)
    all_models = [getattr(models, model) for model in dir(models)
                  if model != 'BaseModel' and isinstance(getattr(models, model), DeclarativeMeta)
                  ]
    for model in all_models:
        admin.add_view(MyModelView(model, session, category='Sys.'))

    # add hyper link to return back to home page
    admin.add_link(MenuLink(name='Back', url='/'))


@babel.localeselector
def get_locale():
    # if a user is logged in, use the locale from the user settings
    user_info = getattr(g, 'user_info', None)
    if user_info is not None and 'locale' in user_info:
        return user_info['locale']

    # otherwise try to guess the language from the user accept
    # header the browser transmits. The best match wins.
    if hasattr(g, 'config'):
        langs = g.config['BABEL_LANGUAGES'] if 'BABEL_LANGUAGES' in g.config else {}
        default_lang = g.config['BABEL_DEFAULT_LOCALE'] if 'BABEL_DEFAULT_LOCALE' in g.config else 'en'
        return request.accept_languages.best_match(
            langs.keys() if len(langs) > 0 else default_lang
        )

    # final default language
    return 'en'

# @babel.timezoneselector
# def get_timezone():
#     user = getattr(g, 'user', None)
#     if user is not None:
#         return user.timezone

###############################################################################
