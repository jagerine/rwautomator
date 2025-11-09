from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from flask import request, redirect, url_for, session, make_response, Blueprint
from datetime import datetime, timedelta
from saml_settings import SAML_SETTINGS
import os

# Create a blueprint for SAML routes
saml_bp = Blueprint('saml', __name__, url_prefix='/saml')

def init_saml_auth(req):
    """Initialize SAML authentication"""
    auth = OneLogin_Saml2_Auth(req, SAML_SETTINGS)
    return auth

def prepare_flask_request(request):
    """Prepare Flask request for SAML processing"""
    # If server is behind reverse proxy, use x-forwarded-* headers
    url_data = request.environ['werkzeug.request'].url.split('?')
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.headers.get('Host'),
        'server_port': request.environ['SERVER_PORT'],
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy(),
        'query_string': request.query_string.decode('utf-8')
    }

@saml_bp.route('/sso')
def sso():
    """Initiate SAML SSO login"""
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    return redirect(auth.login())

@saml_bp.route('/acs', methods=['POST'])
def acs():
    """Assertion Consumer Service - handles SAML response from IdP"""
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_response()
    
    errors = auth.get_errors()
    
    if len(errors) == 0:
        attributes = auth.get_attributes()
        
        username = None
        
        if 'urn:oid:0.9.2342.19200300.100.1.1' in attributes:
            username = attributes['urn:oid:0.9.2342.19200300.100.1.1'][0]
        elif 'urn:oid:0.9.2342.19200300.100.1.3' in attributes:
            email = attributes['urn:oid:0.9.2342.19200300.100.1.3'][0]
            username = email.split('@')[0]  
        elif 'uid' in attributes:
            username = attributes['uid'][0]
        elif 'mail' in attributes:
            email = attributes['mail'][0]
            username = email.split('@')[0]
        
        if not username:
            return "Could not extract username from SAML response", 400
        
        print(f"Extracted username: {username}")
        
        user_data = {
            'username': username,
            'nameid': auth.get_nameid(),
            'attributes': attributes,
        }
        
        username = user_data['username'].lower()
        
        allowed_users = os.getenv('ACCESS_USERS', '').split(',')
        allowed_users = [u.strip().lower() for u in allowed_users if u.strip()]
        if allowed_users and username not in allowed_users:
            return f"Access denied: {username} not authorized", 403

        # Set session data
        session['authenticated_user'] = user_data['username']
        session['auth_expires'] = datetime.now() + timedelta(hours=4)
        session['user_id'] = user_data['nameid']
        
        # Redirect to originally requested URL or home
        # Changed from 'main.home' to just 'home' since you don't have a main blueprint
        relay_state = session.pop('RelayState', None)
        if relay_state:
            return redirect(relay_state)
        else:
            return redirect('/')
    else:
        return f"SAML authentication failed: {', '.join(errors)}", 400

@saml_bp.route('/sls', methods=['GET', 'POST'])
def sls():
    """Single Logout Service"""
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    url = auth.process_slo(delete_session_cb=lambda: session.clear())
    errors = auth.get_errors()
    
    if len(errors) == 0:
        if url is not None:
            return redirect(url)
        else:
            session.clear()
            return redirect('/')
    else:
        return f"SLO failed: {', '.join(errors)}", 400

@saml_bp.route('/metadata')
def metadata():
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    
    try:
        # Initialize settings object
        saml_settings = OneLogin_Saml2_Settings(SAML_SETTINGS)
        
        # Get metadata
        metadata = saml_settings.get_sp_metadata()
        
        # Return metadata without validation for now
        resp = make_response(metadata, 200)
        resp.headers['Content-Type'] = 'text/xml'
        return resp
        
    except Exception as e:
        return f"Error generating metadata: {str(e)}", 500

@saml_bp.route('/logout')
def logout():
    """Initiate SAML logout"""
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    
    # Get session index if available
    session_index = session.get('saml_session_index')
    
    return redirect(auth.logout(
        name_id_format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        session_index=session_index
    ))