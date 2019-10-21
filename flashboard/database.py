import sys

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

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

    def exit_on_error(self, msg):
        """ raise exception to report error msg """
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
    except:
        exp = sys.exc_info()
        if not __mannual_on:
            db_session.rollback()
        rst = False

        from flask import current_app
        current_app.logger.error(exp)

    return rst


def init_db(app, db_uri=None):
    """ initialize database session """

    global engine, db_session
    if db_uri is None:
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']

    if engine is None:
        engine = create_engine(db_uri, convert_unicode=True)
    if db_session is None:
        db_session = scoped_session(sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        ))

    # add query engine
    BaseModel.query = db_session.query_property()

    # add handler to teardown
    @app.teardown_request
    def shutdown_session(exception=None):
        if exception:
            app.logger.error(exception)

        try:
            db_session.commit()
        except:
            db_session.rollback()
        finally:
            db_session.close()
            db_session.remove()


def create_all_tables(app, drop_all=False):
    """ create all tables(import all modules before call this function) """

    global engine
    if engine is None:
        engine = create_engine(
            app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True
        )

    if drop_all:
        BaseModel.metadata.drop_all(bind=engine)

    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    # import .models

    BaseModel.metadata.create_all(bind=engine)
