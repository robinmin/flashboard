from sqlalchemy.exc import SQLAlchemyError

from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash
from flask_login import current_user, login_required, login_url
from flask_babel import gettext as _

from config.config import all_urls
from .forms import LoginForm, SignupForm
from .services import UserService
from .app import login_manager, send_email, allow_inactive_login
from .rbac import rbac_module

bp = Blueprint('flashboard', __name__, template_folder='templates')
###############################################################################


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
            flash(_('Invalid username or password or inactive user'), 'error')
            # return redirect(next or url_for(all_urls['login']))
    return render_template(
        'login.html',
        title=_('Sign In'),
        form=form,
        url_login=url_for(all_urls['login']),
        url_signup=url_for(all_urls['signup']),
        next=request.args.get('next'),
    )


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
                subject = _('Please confirm your email')
                send_email(current_app, user.email, subject, html)

                flash(
                    _('Activation email has been sent to your email box. Please confirm your email first.'),
                    'info'
                )
                return redirect(request.args.get('next') or url_for(all_urls['login']))
            else:
                flash(error or _('Unknown error in user registration'), 'error')
        else:
            flash(_('Both passwords must be the same.'), 'error')
    return render_template(
        'signup.html',
        title=_('Sign Up'),
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
            flash(error or _('Unknown error in comfirm user.'), 'danger')
        else:
            user = usvc.load_user(current_user.email)
            if user and user.confirmed_at:
                flash(_('Account already confirmed. Please login.'), 'info')
            else:
                flash(_('Something goes wrong when comfirming your account.'), 'danger')
    except SQLAlchemyError:
        flash(_('The confirmation link is invalid or has expired.'), 'danger')

    if current_user.is_authenticated:
        UserService().logout_user(current_user)

    return redirect(url_for(all_urls['login']))


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
        if current_app.config.get('ENV', None) == 'development':
            url_admin = url_for(
                all_urls['admin']) if current_app.config.get('ENABLE_ADMIN', False) else ''

        return render_template(
            'home.html',
            title=_('Home'),
            url_logout=url_for(all_urls['logout']),
            url_admin=url_admin
        )
    return redirect(url_for(all_urls['login']))

###############################################################################
