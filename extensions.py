from authlib.integrations.flask_client import OAuth
import os

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)
    
    # Register Google
    # We use env vars for client_id and client_secret
    # If they are not set, these will handle it gracefully or error when called
    if os.environ.get('GOOGLE_CLIENT_ID'):
        oauth.register(
            name='google',
            client_id=os.environ.get('GOOGLE_CLIENT_ID'),
            client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
    
    # Register GitHub
    if os.environ.get('GITHUB_CLIENT_ID'):
        oauth.register(
            name='github',
            client_id=os.environ.get('GITHUB_CLIENT_ID'),
            client_secret=os.environ.get('GITHUB_CLIENT_SECRET'),
            access_token_url='https://github.com/login/oauth/access_token',
            access_token_params=None,
            authorize_url='https://github.com/login/oauth/authorize',
            authorize_params=None,
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email'},
        )
