import os

from flask import Flask

from flashboard.app import create_app
from flashboard.views import login

###############################################################################
app = create_app()

app.app_context().push()
app.add_url_rule('/',      view_func=login)
app.add_url_rule('/index', view_func=login)

###############################################################################

if __name__ == '__main__':
    app.run()
