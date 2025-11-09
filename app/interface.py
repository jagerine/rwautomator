import re
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from functools import wraps
import time
import uuid
import sys
sys.path.insert(0, '/app')
from lib.db import create_job_record, get_job_status, get_job_history, get_pending_jobs

# Import SAML blueprint
from saml_auth import saml_bp

app = Flask(__name__)
app.secret_key = 'san8xebx9n8h2rrb782x9nn749tn7q8oqrxlh3rq'  # IMPORTANT: Change this to a random secret key
app.config['SESSION_COOKIE_SECURE'] = False  # Set to False for local development
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Register SAML blueprint
app.register_blueprint(saml_bp)

# Authentication decorator
def require_auth(f):
    """Decorator to require SAML authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated_user' not in session:
            # Store the original URL to redirect back after login
            session['RelayState'] = request.url
            return redirect(url_for('saml.sso'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@require_auth
def home():

    user_data = {
        'username': session.get('authenticated_user', 'guest'),
        'user_id': session.get('user_id', ''),
        'authenticated': 'authenticated_user' in session
    }
    return render_template('dashboard.html', user_data=user_data)

@app.route('/status/<job_id>', methods=['GET'])
def check_status(job_id):
    # This route is public - no authentication required
    job_status = get_job_status(job_id)
    if job_status:
        return jsonify(job_status)
    return jsonify({'status': 'error', 'message': 'Job not found'}), 404

# Protected routes - require authentication
@app.route('/api/history', methods=['GET'])
@require_auth
def history():
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 100)  # Cap at 100 records per page
        
        # Filter parameters
        order_number = request.args.get('order_number', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        status = request.args.get('status', '').strip()
        
        result = get_job_history(
            page=page,
            per_page=per_page,
            order_number=order_number,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        return jsonify({
            'status': 'success',
            **result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500

@app.route('/api/currentjobs', methods=['GET'])
@require_auth
def current_jobs():
    try:
        jobs = get_pending_jobs()
        return jsonify({
            'status': 'success',
            'jobs': jobs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500
        
@app.route('/api/jobstatus/<job_id>', methods=['GET'])
@require_auth
def job_status(job_id):
    job_status = get_job_status(job_id)
    if job_status:
        return jsonify({
            'status': 'success',
            'job_status': job_status
        })
    return jsonify({
        'status': 'error',
        'message': 'Job not found'
    }), 404
    
@app.route('/api/jobstatuses', methods=['POST'])
@require_auth
def job_statuses():
    job_ids = request.json.get('job_ids', [])
    statuses = {}
    for job_id in job_ids:
        job_status = get_job_status(job_id)
        if job_status:
            statuses[job_id] = job_status
        else:
            statuses[job_id] = {'status': 'error', 'message': 'Job not found'}
    return jsonify({
        'status': 'success',
        'job_statuses': statuses
    })  

@app.route('/api/reset', methods=['POST'])
@require_auth  # Require authentication for reset operations
def reset():
    order_number = request.json.get('order_number')
    dc = request.json.get('distribution_center', '00')
    
    # Get username from session instead of request
    username = session.get('authenticated_user', 'unknown')
    
    job_type = request.json.get('job_type', 'reset_order')
    ticket_number = request.json.get('ticket_number', '')

    # check if job_type has keyword "Batch"
    if "Batch" in job_type:
        # split order numbers by space, line breaks, or commas
        order_numbers = re.split(r'[\s,]+', order_number.strip())
        for order_num in order_numbers:
            if order_num:
                # trim whitespace from order_num
                order_num = order_num.strip()
                job_id = str(uuid.uuid4())
                try:
                    create_job_record(job_id, job_type, order_num, dc, username, ticket_number)
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': f'Database error: {str(e)}'
                    }), 500
        return jsonify({
            'status': 'pending',
            'message': f'Batch reset job created for {len(order_numbers)} orders'
        })

    if not order_number:
        return jsonify({
            'status': 'error',
            'message': 'order_number is required'
        }), 400
    
    # Create job record in database
    job_id = str(uuid.uuid4())
    try:
        create_job_record(job_id, job_type, order_number, dc, username, ticket_number)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500
        
    return jsonify({
        'status': 'pending',
        'message': f'Order {order_number} reset job created'
    })

# Optional: Add a user info endpoint
@app.route('/api/userinfo', methods=['GET'])
@require_auth
def user_info():
    """Return current user information"""
    return jsonify({
        'status': 'success',
        'user': {
            'username': session.get('authenticated_user'),
            'role': session.get('user_role'),
            'user_id': session.get('user_id'),
            'reports': session.get('user_reports', [])
        }
    })

# Optional: Add a logout endpoint
@app.route('/logout')
def logout():
    """Logout endpoint - redirects to SAML logout"""
    return redirect(url_for('saml.logout'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)