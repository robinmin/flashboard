#!/usr/bin/env python
import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell
from flask_admin import Admin

# from redis import Redis
# from rq import Connection, Queue, Worker

from flashboard.app import create_app
from flashboard.views import login
from flashboard.database import create_all_tables, db_trasaction
from flashboard.rbac import create_all_roles
from flashboard.services import UserService, TokenService, TOKEN_USER_ACTIVATION


###############################################################################
app = create_app()
manager = Manager(app)

app.app_context().push()
app.add_url_rule('/',      view_func=login)
app.add_url_rule('/index', view_func=login)

if app.config['ENV'] == 'development':
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)

    def make_shell_context():
        return dict(app=app, db=db)

    manager.add_command('shell', Shell(make_context=make_shell_context))
    manager.add_command('db', MigrateCommand)

    @manager.command
    def list_routes():
        import urllib

        output = []
        for rule in app.url_map.iter_rules():
            methods = ', '.join(rule.methods)
            line = urllib.parse.unquote("{:40s} {:24s}\t{}".format(
                rule.endpoint, methods, rule))
            output.append(line)

        for line in sorted(output):
            print(line)

    @manager.command
    def recreate_db():
        if input("Are you sure you want drop existing tables and re-create all of them? (y/N)\n").lower() == "y":
            # import all models
            import flashboard.models

            # create them
            create_all_tables(app)

            # add meta data
            add_metadata_for_app(app)


def add_metadata_for_app(app):
    # Add meta data for user-role
    create_all_roles()
    # with db_trasaction() as txn:
    #     txn.save_item(RoleModel('anonymous', 'Anonymous User'))
    #     txn.save_item(RoleModel('user',    'Normal User'))
    #     txn.save_item(RoleModel('operator',  'Operator'))
    #     txn.save_item(RoleModel('admin',     'Administrator'))

    with db_trasaction() as txn:
        # add test user
        usvc = UserService()

        user, error = usvc.register_user(
            'robin', 'luonbin@hotmail.com', 'Test001')
        if user is None:
            app.logger.error(error or 'Unknown error in Sign Up')
        else:
            # retrieve activation token for user confirmation
            tsvc = TokenService()
            act_token = tsvc.get_last_one(TOKEN_USER_ACTIVATION, user.id)

            result, error = usvc.confirm_user(user, act_token)
            if not result:
                app.logger.error(error or 'Unknown error in comfirm user.')


###############################################################################
if __name__ == '__main__':
    manager.run()
