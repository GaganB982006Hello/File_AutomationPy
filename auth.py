from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from db import create_user, verify_user, get_user_by_email, create_oauth_user
from extensions import oauth

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = verify_user(email, password)
        
        if user_data:
            from app import User
            user_obj = User(user_data)
            login_user(user_obj)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        # Check if this is the FIRST user, make them ADMIN
        import db
        is_first_user = len(db.get_all_users()) == 0
        role = 'admin' if is_first_user else 'user'
        
        user_id, message = create_user(email, name, password, role)
        
        if user_id:
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'error')
            
    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# --- Google OAuth ---
# --- Google OAuth ---
@auth_bp.route('/login/google')
def google_login():
    google = getattr(oauth, 'google', None)
    if not google:
        flash('Google Login is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.', 'error')
        return redirect(url_for('auth.login'))
        
    redirect_uri = url_for('auth.google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/google/callback')
def google_auth():
    google = getattr(oauth, 'google', None)
    if not google:
        flash('Google Login configuration missing.', 'error')
        return redirect(url_for('auth.login'))
        
    try:
        token = google.authorize_access_token()
        user_info = google.userinfo()
        
        # user_info contains 'email', 'name', 'picture', etc.
        email = user_info['email']
        name = user_info['name']
        
        # Check if user exists, if not create them
        user_data = create_oauth_user(email, name, 'google')
        
        # Login
        from app import User
        user_obj = User(user_data)
        login_user(user_obj)
        
        flash('Successfully logged in with Google.', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Google login failed: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

# --- GitHub OAuth ---
@auth_bp.route('/login/github')
def github_login():
    github = getattr(oauth, 'github', None)
    if not github:
        flash('GitHub Login is not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables.', 'error')
        return redirect(url_for('auth.login'))
        
    redirect_uri = url_for('auth.github_auth', _external=True)
    return github.authorize_redirect(redirect_uri)

@auth_bp.route('/github/callback')
def github_auth():
    github = getattr(oauth, 'github', None)
    if not github:
        flash('GitHub Login configuration missing.', 'error')
        return redirect(url_for('auth.login'))
        
    try:
        token = github.authorize_access_token()
        # GitHub user info is a separate call or part of token depending on config
        resp = github.get('user', token=token)
        user_info = resp.json()
        
        email = user_info.get('email')
        name = user_info.get('name') or user_info.get('login')
        
        if not email:
            # Sometimes email is private, need another call
            resp_emails = github.get('user/emails', token=token)
            emails = resp_emails.json()
            for e in emails:
                if e['primary'] and e['verified']:
                    email = e['email']
                    break
        
        if not email:
            flash('Could not retrieve email from GitHub.', 'error')
            return redirect(url_for('auth.login'))

        user_data = create_oauth_user(email, name, 'github')
        
        from app import User
        user_obj = User(user_data)
        login_user(user_obj)
        
        flash('Successfully logged in with GitHub.', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'GitHub login failed: {str(e)}', 'error')
        return redirect(url_for('auth.login'))
