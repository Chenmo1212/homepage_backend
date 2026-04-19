"""
Authentication module for Swagger UI protection
Implements HTTP Basic Auth with rate limiting for failed attempts

Note: This implementation uses in-memory storage which works for single-process
deployments. For production multi-process deployments (e.g., gunicorn with multiple
workers), consider using Redis or a database for shared state.

Privacy: IP addresses are hashed before logging to comply with privacy regulations.
"""

from flask import request, Response
from functools import wraps
from datetime import datetime, timedelta
import os
import threading
import hashlib

# Thread-safe lock for modifying failed_attempts
_lock = threading.Lock()

# Store failed login attempts: {ip_hash: {'count': int, 'blocked_until': datetime, 'last_attempt': datetime}}
# Note: For multi-process deployments, replace with Redis/database
failed_attempts = {}

# Configuration - will be loaded from Flask app config
MAX_FAILED_ATTEMPTS = 5
BLOCK_DURATION_HOURS = 2
CLEANUP_INTERVAL_HOURS = 24  # Clean up old entries every 24 hours
MAX_TRACKED_IPS = 10000  # Prevent unbounded growth

def _hash_ip(ip):
    """
    Hash IP address for privacy-compliant logging
    
    Args:
        ip: The IP address to hash
        
    Returns:
        str: SHA256 hash of the IP address (first 16 chars for brevity)
    """
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _cleanup_old_entries():
    """
    Remove old entries from failed_attempts to prevent unbounded memory growth
    Removes entries that haven't had attempts in the last CLEANUP_INTERVAL_HOURS
    """
    with _lock:
        if len(failed_attempts) < MAX_TRACKED_IPS:
            return
            
        cutoff_time = datetime.now() - timedelta(hours=CLEANUP_INTERVAL_HOURS)
        to_remove = []
        
        for ip_hash, data in failed_attempts.items():
            last_attempt = data.get('last_attempt')
            blocked_until = data.get('blocked_until')
            
            # Remove if no recent activity and not currently blocked
            if last_attempt and last_attempt < cutoff_time:
                if not blocked_until or datetime.now() >= blocked_until:
                    to_remove.append(ip_hash)
        
        for ip_hash in to_remove:
            del failed_attempts[ip_hash]
        
        if to_remove:
            print(f"[Auth] Cleaned up {len(to_remove)} old authentication tracking entries")


def get_swagger_credentials():
    """Get Swagger credentials from Flask app config or environment variables"""
    from flask import current_app
    username = current_app.config.get('SWAGGER_USERNAME') or os.getenv('SWAGGER_USERNAME', 'admin')
    password = current_app.config.get('SWAGGER_PASSWORD') or os.getenv('SWAGGER_PASSWORD', 'change-me-in-production')
    return username, password


def check_auth(username, password):
    """
    Verify username and password
    
    Args:
        username: The username to check
        password: The password to check
        
    Returns:
        bool: True if credentials are valid, False otherwise
    """
    expected_username, expected_password = get_swagger_credentials()
    return username == expected_username and password == expected_password


def is_ip_blocked(ip):
    """
    Check if an IP address is currently blocked (thread-safe)
    
    Args:
        ip: The IP address to check
        
    Returns:
        tuple: (is_blocked: bool, blocked_until: datetime or None)
    """
    ip_hash = _hash_ip(ip)
    
    with _lock:
        if ip_hash not in failed_attempts:
            return False, None
        
        attempt_data = failed_attempts[ip_hash]
        blocked_until = attempt_data.get('blocked_until')
        
        if blocked_until and datetime.now() < blocked_until:
            return True, blocked_until
        
        # Block period has expired, reset the counter
        if blocked_until and datetime.now() >= blocked_until:
            failed_attempts[ip_hash] = {
                'count': 0,
                'blocked_until': None,
                'last_attempt': datetime.now()
            }
            return False, None
        
        return False, None


def record_failed_attempt(ip):
    """
    Record a failed login attempt for an IP address (thread-safe)
    
    Args:
        ip: The IP address that failed authentication
    """
    ip_hash = _hash_ip(ip)
    
    with _lock:
        # Periodic cleanup to prevent unbounded growth
        if len(failed_attempts) >= MAX_TRACKED_IPS:
            _cleanup_old_entries()
        
        if ip_hash not in failed_attempts:
            failed_attempts[ip_hash] = {
                'count': 0,
                'blocked_until': None,
                'last_attempt': datetime.now()
            }
        
        failed_attempts[ip_hash]['count'] += 1
        failed_attempts[ip_hash]['last_attempt'] = datetime.now()
        
        # Block the IP if max attempts reached
        if failed_attempts[ip_hash]['count'] >= MAX_FAILED_ATTEMPTS:
            blocked_until = datetime.now() + timedelta(hours=BLOCK_DURATION_HOURS)
            failed_attempts[ip_hash]['blocked_until'] = blocked_until
            print(f"[Auth] IP {ip_hash} (hashed) blocked until {blocked_until} after {MAX_FAILED_ATTEMPTS} failed attempts")


def reset_failed_attempts(ip):
    """
    Reset failed attempts counter for an IP after successful login (thread-safe)
    
    Args:
        ip: The IP address to reset
    """
    ip_hash = _hash_ip(ip)
    
    with _lock:
        if ip_hash in failed_attempts:
            failed_attempts[ip_hash] = {
                'count': 0,
                'blocked_until': None,
                'last_attempt': datetime.now()
            }


def authenticate():
    """
    Send a 401 response that enables basic auth
    
    Returns:
        Response: Flask response with 401 status and WWW-Authenticate header
    """
    return Response(
        'Access denied. Please provide valid credentials.\n'
        'Contact the administrator if you believe this is an error.',
        401,
        {'WWW-Authenticate': 'Basic realm="Swagger UI - Login Required"'}
    )


def authenticate_blocked(blocked_until):
    """
    Send a 403 response for blocked IPs
    
    Args:
        blocked_until: datetime when the block will be lifted
        
    Returns:
        Response: Flask response with 403 status
    """
    time_remaining = blocked_until - datetime.now()
    hours = int(time_remaining.total_seconds() // 3600)
    minutes = int((time_remaining.total_seconds() % 3600) // 60)
    
    return Response(
        f'Access blocked due to too many failed login attempts.\n'
        f'Please try again in {hours} hours and {minutes} minutes.\n'
        f'Block will be lifted at: {blocked_until.strftime("%Y-%m-%d %H:%M:%S")}',
        403,
        {'Content-Type': 'text/plain; charset=utf-8'}
    )


def requires_auth(f):
    """
    Decorator to require HTTP Basic Auth for a route
    Also implements rate limiting for failed attempts
    
    Usage:
        @app.route('/protected')
        @requires_auth
        def protected_route():
            return 'Protected content'
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        client_ip = request.remote_addr
        
        # Check if IP is blocked
        is_blocked, blocked_until = is_ip_blocked(client_ip)
        if is_blocked:
            print(f"[Auth] Blocked IP {_hash_ip(client_ip)} (hashed) attempted access")
            return authenticate_blocked(blocked_until)
        
        # Check authentication
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            # Record failed attempt
            record_failed_attempt(client_ip)
            
            # Get attempts left (thread-safe)
            ip_hash = _hash_ip(client_ip)
            with _lock:
                attempts_left = MAX_FAILED_ATTEMPTS - failed_attempts[ip_hash]['count']
            
            if attempts_left > 0:
                print(f"[Auth] Failed login attempt from {ip_hash} (hashed). Attempts remaining: {attempts_left}")
            
            return authenticate()
        
        # Successful authentication - reset failed attempts
        reset_failed_attempts(client_ip)
        return f(*args, **kwargs)
    
    return decorated


def get_failed_attempts_info():
    """
    Get information about current failed attempts and blocked IPs
    Useful for monitoring and debugging
    
    Returns:
        dict: Information about failed attempts and blocked IPs
    """
    info = {
        'total_tracked_ips': len(failed_attempts),
        'blocked_ips': [],
        'ips_with_failed_attempts': []
    }
    
    with _lock:
        for ip_hash, data in failed_attempts.items():
            if data.get('blocked_until') and datetime.now() < data['blocked_until']:
                info['blocked_ips'].append({
                    'ip_hash': ip_hash,
                    'blocked_until': data['blocked_until'].isoformat(),
                    'attempts': data['count']
                })
            elif data['count'] > 0:
                info['ips_with_failed_attempts'].append({
                    'ip_hash': ip_hash,
                    'attempts': data['count'],
                    'attempts_remaining': MAX_FAILED_ATTEMPTS - data['count']
                })
    
    return info

# Made with Bob
