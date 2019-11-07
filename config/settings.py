from datetime import timedelta  # noqa F401


class Settings(dict):
    """ class settings should contain all informations of application that will
     never be changed after the development no mater in which mode. That means
     will can import this class directly if necessary:
    ```python
        import config.settings import Settings
        Settings().XXXXXX
    ```
     instead of:
    ```python
        current_app.config.get('xxxxxx', None)
    ```
    """

    # --------------------------------------------------------------------------
    #  Application settings
    # --------------------------------------------------------------------------
    APP_TITLE = 'System'
    APP_URL_WELCOME = 'flashboard.login'
    APP_NAME = 'Flask-User starter app'
    APP_SYSTEM_ERROR_SUBJECT_LINE = APP_NAME + " system error"

    # --------------------------------------------------------------------------
    #  Application settings -- i18n
    # --------------------------------------------------------------------------
    BABEL_DEFAULT_LOCALE = 'zh_Hans_CN'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    # available languages
    BABEL_LANGUAGES = {
        # 'en': 'English',
        'zh_Hans_CN': 'Simplified Chinese',
    }

    # --------------------------------------------------------------------------
    #  Application settings -- RBAC
    # --------------------------------------------------------------------------
    # Define all roles
    RBAC_ROLES = {
        'anonymous': 'Anonymous User',
        'user':    'Normal User',
        'operator':  'Operator',
        'admin':     'Administrator',
    }

    # define default role for registered users
    DEFAULT_ROLE = 'user'

    # define common role sets
    ALL_VALID_ROLES = RBAC_ROLES.keys()
    ALL_ROLES = ['user', 'operator', 'admin']

    # This is the core of RBAC which defined the mapping between RBAC module and
    # roles. The module of current view will be defined via decorator @rbac_module
    RBAC_CONTROL = {
        'sys': ALL_VALID_ROLES,
        'home': ALL_ROLES,
    }

    CELERYBEAT_SCHEDULE = {
        # 'run-every-1-minute': {
        #     'task': 'worker.print_hello',
        #     'schedule': timedelta(seconds=60)
        # },
    }
