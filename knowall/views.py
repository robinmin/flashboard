from flask import Blueprint, render_template
from flask.views import MethodView

###############################################################################

# class UserAPI(MethodView):
#    decorators = [user_required]
#     def get(self, user_id):
#         if user_id is None:
#             # 返回一个包含所有用户的列表
#             pass
#         else:
#             # 显示一个用户
#             pass

#     def post(self):
#         # 创建一个新用户
#         pass

#     def delete(self, user_id):
#         # 删除一个用户
#         pass

#     def put(self, user_id):
#         # update a single user
#         pass

# def register_api(bp, view, endpoint, url, pk='id', pk_type='int'):
#     view_func = view.as_view(endpoint)
#
#     bp.add_url_rule(url, defaults={pk: None}, view_func=view_func, methods=['GET', ])
#     bp.add_url_rule(url, view_func=view_func, methods=['POST', ])
#     bp.add_url_rule('%s<%s:%s>' % (url, pk_type, pk), view_func=view_func,
#                      methods=['GET', 'PUT', 'DELETE'])


# register_api(UserAPI, 'user_api', '/users/', pk='user_id')

def init_view(app, url_prefix):
    # defin all view class
    class ProjectListView(MethodView):
        def get(self):
            return render_template('proj_list_index.html')

    # --------------------------------------------------------------------------
    # add URL rule
    bp = Blueprint('knowall', __name__, template_folder='templates')
    bp.add_url_rule('/', view_func=ProjectListView.as_view('index'))

    # register blueprint
    app.register_blueprint(bp, url_prefix=url_prefix)
