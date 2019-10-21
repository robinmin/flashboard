from flask import Blueprint, render_template, abort, jsonify, current_app, request, redirect, url_for, flash
from flask_login import current_user, login_required

from .forms import LoginForm, SignupForm
from .services import UserService
from .app import login_manager
from .rbac import rbac_module

bp = Blueprint('flashboard', __name__, template_folder='templates')
###############################################################################

# all build-in urls here
all_urls = {
    'login': 'flashboard.login',
    'logout': 'flashboard.logout',
    'signup': 'flashboard.signup',
    'home': 'flashboard.home',
}


@login_manager.user_loader
def user_loader(user_id):
    """ Given *user_id*, return the associated User object """
    return UserService().load_user(user_id)


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
    if request.method == 'POST' and form.validate_on_submit():
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        remember_me = 'remember_me' in request.form

        usvc = UserService()
        user = usvc.load_valid_user(email, password)
        if user:
            usvc.login_user(user, remember=remember_me, login_ip=request.environ.get(
                'HTTP_X_REAL_IP', request.remote_addr
            ))
            # flash('Logged in successfully')
            return redirect(request.args.get('next') or url_for(all_urls['home']))
        else:
            flash('Invalid username or password or inactive user', 'error')
    return render_template(
        'login.html',
        title='Sign In',
        form=form,
        url_login=url_for(all_urls['login']),
        url_signup=url_for(all_urls['signup'])
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
            user, error = usvc.register_user(name, email, password)
            if user:
                flash('Sign up successfully', 'info')
                return redirect(request.args.get('next') or url_for(all_urls['login']))
            else:
                flash(error or 'Unknown error in Sign Up', 'error')
        else:
            flash('Both passwords must be the same.', 'error')
    return render_template(
        'signup.html',
        title='Sign Up',
        form=form,
        url_login=url_for(all_urls['login']),
        url_signup=url_for(all_urls['signup'])
    )


@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if current_user.is_authenticated:
        UserService().logout_user(current_user)
        flash('Logout successfully', 'info')

    return redirect(url_for(all_urls['login']))


@bp.route('/home', methods=['GET'])
@rbac_module('home')
def home():
    if current_user.is_authenticated:
        return render_template(
            'home.html',
            title='Home',
            url_logout=url_for(all_urls['logout'])
        )
    return redirect(url_for(all_urls['login']))
###############################################################################
