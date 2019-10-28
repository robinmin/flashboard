from flask import Blueprint, render_template, abort, jsonify, current_app, request, redirect, url_for, flash
from flask_login import current_user, login_required, login_url

from .forms import LoginForm, SignupForm
from .services import UserService
from .app import login_manager, send_email
from .rbac import rbac_module

bp = Blueprint('flashboard', __name__, template_folder='templates')
###############################################################################

# all build-in urls here
all_urls = {
    'login': 'flashboard.login',
    'logout': 'flashboard.logout',
    'signup': 'flashboard.signup',
    'confirm_email': 'flashboard.confirm_email',
    'home': 'flashboard.home',

    'admin': 'admin.index',
}


@login_manager.user_loader
def user_loader(user_id):
    """ Given *user_id*, return the associated User object """
    user = UserService().load_user(user_id)
    return user if user and user.actived else None


@login_manager.unauthorized_handler
def unauthorized():
    """ Redirect unauthorized users to Login page """
    flash('You must be logged in to view that page.')
    return redirect(url_for(all_urls['login']))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Bypass Login screen if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for(all_urls['home']))

    form = LoginForm()
    next = request.form.get('next', None)
    if request.method == 'POST' and form.validate_on_submit():
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        remember_me = 'remember_me' in request.form

        usvc = UserService()

        # special process for confirm_email
        include_inactive = allow_inactive_login(next)
        user = usvc.load_valid_user(email, password, include_inactive)
        login_ip = request.environ.get(
            'HTTP_X_REAL_IP', request.remote_addr
        )

        # update user login information
        if user and usvc.login_user(user, remember=remember_me, login_ip=login_ip, force=include_inactive):
            return redirect(next or url_for(all_urls['home']))
        else:
            flash('Invalid username or password or inactive user', 'error')
            # return redirect(next or url_for(all_urls['login']))
    return render_template(
        'login.html',
        title='Sign In',
        form=form,
        url_login=url_for(all_urls['login']),
        url_signup=url_for(all_urls['signup']),
        next=request.args.get('next'),
    )


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


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    # Bypass Login screen if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for(all_urls['home']))

    form = SignupForm()
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form.get('name', None)
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        password2 = request.form.get('password2', None)

        if password and password2 and password == password2:
            usvc = UserService()
            user, token, error = usvc.register_user(name, email, password)
            if user and token:
                # triger activation email
                confirm_url = login_url(
                    login_view=url_for(
                        all_urls['login'],
                        _external=True
                    ),
                    next_url=url_for(
                        all_urls['confirm_email'],
                        token=token.token
                    ))
                html = render_template(
                    'activate.html', confirm_url=confirm_url
                )
                subject = 'Please confirm your email'
                send_email(current_app, user.email, subject, html)

                flash(
                    'Activation email has been sent to your email box. Please confirm your email first.',
                    'info'
                )
                return redirect(request.args.get('next') or url_for(all_urls['login']))
            else:
                flash(error or 'Unknown error in user registration', 'error')
        else:
            flash('Both passwords must be the same.', 'error')
    return render_template(
        'signup.html',
        title='Sign Up',
        form=form,
        url_login=url_for(all_urls['login']),
        url_signup=url_for(all_urls['signup'])
    )


@bp.route('/confirm_email/<token>', methods=['GET'])
@login_required
def confirm_email(token):
    if not current_user.is_authenticated:
        return login_manager.unauthorized()

    usvc = UserService()
    try:
        result, error = usvc.confirm_user(current_user, token)
        if not result:
            flash(error or 'Unknown error in comfirm user.', 'danger')
        else:
            user = usvc.load_user(current_user.email)
            if user and user.confirmed_at:
                flash('Account already confirmed. Please login.', 'info')
            else:
                flash('Something goes wrong when comfirming your account.', 'danger')
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    return redirect(url_for(all_urls['logout']))


@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if current_user.is_authenticated:
        UserService().logout_user(current_user)
        # flash('Logout successfully', 'info')

    return redirect(url_for(all_urls['login']))


@bp.route('/home', methods=['GET'])
@rbac_module('home')
def home():
    if current_user.is_authenticated:
        url_admin = ''
        if current_app.config['ENV'] == 'development':
            url_admin = url_for(
                all_urls['admin']) if current_app.config['ENABLE_ADMIN'] else ''

        return render_template(
            'home.html',
            title='Home',
            url_logout=url_for(all_urls['logout']),
            url_admin=url_admin
        )
    return redirect(url_for(all_urls['login']))

###############################################################################
