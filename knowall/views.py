from flask import Blueprint, render_template, flash, redirect, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from flask_babel import gettext as _

from flashboard.app import get_menu_list
from .services import ProjectService, TableService, ColumnService
###############################################################################


# def register_api(bp, view, endpoint, url, pk='id', pk_type='int'):
#     view_func = view.as_view(endpoint)
#
#     bp.add_url_rule(url, defaults={pk: None}, view_func=view_func, methods=['GET', ])
#     bp.add_url_rule(url, view_func=view_func, methods=['POST', ])
#     bp.add_url_rule('%s<%s:%s>' % (url, pk_type, pk), view_func=view_func,
#                      methods=['GET', 'PUT', 'DELETE'])


# register_api(UserAPI, 'user_api', '/users/', pk='user_id')

def init_view(app, url_prefix):
    bp = Blueprint('knowall', __name__, template_folder='templates')

    # defin all view class
    class ProjectListView(MethodView):
        decorators = [login_required]

        def get(self):
            projects = ProjectService().get_list(current_user.id)
            return render_template(
                'proj_list.html',
                menu_list=get_menu_list(),
                projects=projects
            )

    class ProjectDetailView(MethodView):
        decorators = [login_required]

        def get(self, proj_id):
            proj_info = ProjectService().get_detail(current_user.id, proj_id)
            print(proj_info)
            return render_template(
                'proj_detail.html',
                menu_list=get_menu_list(),
                proj_info=proj_info
            )

    class TableListView(MethodView):
        decorators = [login_required]

        def get(self):
            tables = TableService().get_list(current_user.id)
            return render_template(
                'table_list.html',
                menu_list=get_menu_list(),
                tables=tables
            )

    class TableDetailView(MethodView):
        decorators = [login_required]

        def get(self, table_name):
            table_info = TableService().get_detail(current_user.id, table_name)
            return render_template(
                'table_detail.html',
                menu_list=get_menu_list(),
                table_info=table_info
            )

    class ColumnListView(MethodView):
        decorators = [login_required]

        def get(self, table_name=''):
            columns = False
            if table_name:
                columns = ColumnService().get_list(table_name)
            if not columns:
                flash(_('Failed to load column list for ') + table_name, 'error')
                return redirect(url_for('.index'))

            return render_template(
                'column_list.html',
                menu_list=get_menu_list(),
                table_name=table_name,
                columns=columns
            )

    # --------------------------------------------------------------------------
    # add URL rule
    # bp.add_url_rule('/', view_func=ProjectListView.as_view('index'))
    # bp.add_url_rule('/detail/<int:proj_id>',
    #                 view_func=ProjectDetailView.as_view('detail'))

    bp.add_url_rule('/', view_func=TableListView.as_view('index'))
    bp.add_url_rule('/tables/<table_name>',
                    view_func=TableDetailView.as_view('detail'))
    bp.add_url_rule('/columns/<table_name>',
                    view_func=ColumnListView.as_view('column_list'))

    # register blueprint
    app.register_blueprint(bp, url_prefix=url_prefix)
