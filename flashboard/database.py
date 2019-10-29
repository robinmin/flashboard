import sys

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# database engin
engine = None

# db sessioon
db_session = None

# base class for all models
BaseModel = declarative_base()

# internal control flag for mannual db transaction
__mannual_on = False


class db_trasaction():
    def __enter__(self):
        """ callback function for entering with-block """
        global __mannual_on
        __mannual_on = True
        return self

    def __exit__(self, type, value, traceback):
        """ callback function for entering with-block """
        global __mannual_on
        __mannual_on = False

        # automatic submit the transaction if necessary
        if type is None:
            db_session.commit()
        else:
            # rollback all transaction when exception encountered
            db_session.rollback()

            # report the exception
            from flask import current_app
            current_app.logger.error(value)

    def try_assert(self, condition, msg=None):
        """ try asssert when condition is true """

        if condition:
            raise ValueError(msg or 'Unknown error')

    def save_item(self, obj_item):
        """ Save the item into relevant database table """
        return save_item(obj_item)


def save_item(obj_item):
    """ Save the item into relevant database table """
    rst = True
    try:
        db_session.add(obj_item)
        if not __mannual_on:
            db_session.commit()
        else:
            db_session.flush()
    except SQLAlchemyError:
        exp = sys.exc_info()
        if not __mannual_on:
            db_session.rollback()
        rst = False

        from flask import current_app
        current_app.logger.error(str(exp))

    return rst


def init_db(app, db_uri=None):
    """ initialize database session """

    global db_session
    db_session = create_session(app, db_uri, True)

    # add query engine
    BaseModel.query = db_session.query_property()

    # create all tables
    # BaseModel.metadata.create_all(bind=engine)

    # add handler to teardown
    @app.teardown_request
    def shutdown_session(exception=None):
        if exception:
            app.logger.error(exception)

        try:
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
        finally:
            db_session.close()
            db_session.remove()


def create_all_tables(app, drop_all=False):
    """ create all tables(import all modules before call this function) """

    engine = get_engine(app)

    if drop_all:
        BaseModel.metadata.drop_all(bind=engine)

    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    # import .models

    BaseModel.metadata.create_all(bind=engine)


def get_engine(app, db_uri=None):
    """get db engine

    Arguments:
        app {object} -- instance of flask application

    Keyword Arguments:
        db_uri {string} -- db connection string (default: {None})

    Returns:
        object -- instance of db engine
    """

    if db_uri is None:
        # get default global engine
        global engine
        if engine is None:
            engine = create_engine(
                app.config['SQLALCHEMY_DATABASE_URI']
            )
        return engine

    # get specified database engine
    return create_engine(db_uri)


def create_session(app, db_uri=None, scoped=False):
    """
    Create an sql alchemy session for IO db operations
    :param dbpath: the path to the database, e.g. sqlite:///path_to_my_dbase.sqlite
    :param scoped: boolean (False by default) if the session must be scoped session
    """
    # init the session:
    engine = get_engine(app, db_uri)

    if not scoped:
        # create a configured "Session" class
        session = sessionmaker(bind=engine)
        # create a Session
        return session()
    else:
        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        return scoped_session(session_factory)
