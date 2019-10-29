from flask import Blueprint, render_template, abort, jsonify, current_app, request, redirect, url_for, flash, g
from flask_login import current_user, login_required, login_url
from flask_babel import gettext as _

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

    try:
        # get default language
        from flask import current_app
        lang = current_app.config.get('BABEL_DEFAULT_LOCALE', None)

        # user prefference support
        user = UserService().load_user(user_id)
        if hasattr(user, 'language'):
            lang = user.language

        # cache user language prefference into global variable
        if hasattr(g, 'user_info'):
            g.user_info['locale'] = lang
        else:
            g.user_info = {
                'locale': lang
            }

        # cache config information
        if not hasattr(g, 'config'):
            g.config = {
                'BABEL_DEFAULT_LOCALE': current_app.config.get('BABEL_DEFAULT_LOCALE', 'en'),
                'BABEL_DEFAULT_TIMEZONE': current_app.config.get('BABEL_DEFAULT_TIMEZONE', 'UTC'),
                'BABEL_LANGUAGES': current_app.config.get('BABEL_LANGUAGES', {}),
            }

        # special case for confirm_email
        if request.path:
            include_inactive = allow_inactive_login(request.path)
            if include_inactive:
                return user

        return user if user and user.actived else None
    except:
        return None


@login_manager.unauthorized_handler
def unauthorized():
    """ Redirect unauthorized users to Login page """
    flash(_('You must be logged in to view that page.'))
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
    except:
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
        if current_app.config['ENV'] == 'development':
            url_admin = url_for(
                all_urls['admin']) if current_app.config['ENABLE_ADMIN'] else ''

        return render_template(
            'home.html',
            title=_('Home'),
            url_logout=url_for(all_urls['logout']),
            url_admin=url_admin
        )
    return redirect(url_for(all_urls['login']))

###############################################################################
