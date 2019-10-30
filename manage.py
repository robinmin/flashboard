#!/usr/bin/env python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell

from flashboard.app import create_app, enable_celery
from flashboard.database import create_all_tables
from flashboard.utils import get_all_routes

from tests.conftest import add_metadata_for_app
###############################################################################

app = create_app()
celery = enable_celery(app)
manager = Manager(app)

app.app_context().push()

if app.config['ENV'] == 'development':
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)

    def make_shell_context():
        return dict(app=app, db=db)

    manager.add_command('shell', Shell(make_context=make_shell_context))
    manager.add_command('db', MigrateCommand)

    @manager.command
    def list_routes():
        output = get_all_routes(app)
        for line in sorted(output):
            print(line)

    @manager.command
    def recreate_db():
        if input("Are you sure you want drop existing tables and re-create all of them? (y/N)\n").lower() == "y":
            # import all models
            import flashboard.models  # noqa: F401

            # create them
            create_all_tables(app)

            # add meta data & test data
            add_metadata_for_app(app)


@celery.task()
def add_together(a, b):
    return a + b


@celery.task()
def print_hello():
    print('Hello World!')


###############################################################################
if __name__ == '__main__':
    manager.run()
