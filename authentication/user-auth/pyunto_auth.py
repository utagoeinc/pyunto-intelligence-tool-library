"""
User Authentication Sample for Pyunto Intelligence.

This module demonstrates a secure authentication flow for applications 
integrating with Pyunto Intelligence.
"""

import os
import jwt
import time
import uuid
import hashlib
import logging
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pyunto_auth')

class PyuntoAuth:
    """
    Handles authentication with Pyunto Intelligence services.
    
    Features:
    - User login/logout
    - Token management
    - Session handling
    - Permissions and role-based access
    """
    
    def __init__(self, api_url=None, client_id=None, client_secret=None):
        """
        Initialize the PyuntoAuth client.
        
        Args:
            api_url: Base URL for the Pyunto API
            client_id: OAuth client ID
            client_secret: OAuth client secret
        """
        self.api_url = api_url or os.environ.get("PYUNTO_API_URL", "https://a.pyunto.com/api")
        self.client_id = client_id or os.environ.get("PYUNTO_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("PYUNTO_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Client ID and Client Secret are required")
        
        # JWT settings
        self.jwt_secret = os.environ.get("PYUNTO_JWT_SECRET", self.client_secret)
        self.token_expiry = int(os.environ.get("PYUNTO_TOKEN_EXPIRY", 3600))  # 1 hour default
        self.refresh_token_expiry = int(os.environ.get("PYUNTO_REFRESH_TOKEN_EXPIRY", 2592000))  # 30 days default
        
        # Session storage
        self.active_sessions = {}
    
    def _hash_password(self, password, salt=None):
        """
        Hash a password with a salt using PBKDF2.
        
        Args:
            password: Plain text password
            salt: Optional salt, generated if not provided
            
        Returns:
            tuple: (hashed_password, salt)
        """
        if salt is None:
            salt = os.urandom(32)
        
        # Use PBKDF2 with SHA-256, 100,000 iterations
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        # Return the key and salt as hex strings
        return key.hex(), salt.hex()
    
    def _verify_password(self, stored_password_hash, stored_salt, provided_password):
        """
        Verify a password against a stored hash.
        
        Args:
            stored_password_hash: The stored password hash
            stored_salt: The stored salt
            provided_password: The password to check
            
        Returns:
            bool: True if the password matches
        """
        # Convert hex salt back to bytes
        salt = bytes.fromhex(stored_salt)
        
        # Hash the provided password with the same salt
        key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        
        # Compare the hashes
        return key.hex() == stored_password_hash
    
    def _generate_tokens(self, user_id, user_data=None):
        """
        Generate access and refresh tokens for a user.
        
        Args:
            user_id: User ID
            user_data: Additional user data
            
        Returns:
            dict: Access and refresh tokens
        """
        now = int(time.time())
        
        # Access token payload
        access_payload = {
            'sub': user_id,
            'iat': now,
            'exp': now + self.token_expiry,
            'type': 'access',
            'jti': str(uuid.uuid4())
        }
        
        # Refresh token payload
        refresh_payload = {
            'sub': user_id,
            'iat': now,
            'exp': now + self.refresh_token_expiry,
            'type': 'refresh',
            'jti': str(uuid.uuid4())
        }
        
        # Add user data if provided
        if user_data:
            access_payload['user_data'] = user_data
        
        # Generate tokens
        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm='HS256')
        
        # Store session info
        self.active_sessions[refresh_payload['jti']] = {
            'user_id': user_id,
            'expires_at': now + self.refresh_token_expiry,
            'created_at': now,
            'last_used': now
        }
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': self.token_expiry,
            'token_type': 'Bearer'
        }
    
    def login(self, email, password):
        """
        Authenticate a user with Pyunto Intelligence.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            dict: Authentication result including tokens
        """
        try:
            # Make request to Pyunto auth endpoint
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={
                    'email': email,
                    'password': password,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                }
            )
            
            # Check for errors
            response.raise_for_status()
            auth_data = response.json()
            
            if auth_data.get('success'):
                user_id = auth_data.get('user_id')
                user_data = auth_data.get('user', {})
                
                # Generate tokens
                tokens = self._generate_tokens(user_id, user_data)
                
                return {
                    'success': True,
                    'user': user_data,
                    'tokens': tokens
                }
            else:
                return {
                    'success': False,
                    'error': auth_data.get('error', 'Authentication failed')
                }
        
        except requests.RequestException as e:
            logger.error(f"Login error: {str(e)}")
            return {
                'success': False,
                'error': f"Authentication error: {str(e)}"
            }
    
    def refresh_token(self, refresh_token):
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            dict: New tokens or error
        """
        try:
            # Decode and validate the refresh token
            try:
                payload = jwt.decode(refresh_token, self.jwt_secret, algorithms=['HS256'])
            except jwt.PyJWTError as e:
                logger.warning(f"Invalid refresh token: {str(e)}")
                return {
                    'success': False,
                    'error': 'Invalid refresh token'
                }
            
            # Check token type
            if payload.get('type') != 'refresh':
                return {
                    'success': False,
                    'error': 'Invalid token type'
                }
            
            # Check if token is in active sessions
            token_id = payload.get('jti')
            if token_id not in self.active_sessions:
                return {
                    'success': False,
                    'error': 'Token has been revoked'
                }
            
            # Get user info and update last used timestamp
            session = self.active_sessions[token_id]
            session['last_used'] = int(time.time())
            
            # Validate session expiry
            if session['expires_at'] < int(time.time()):
                # Clean up expired session
                del self.active_sessions[token_id]
                return {
                    'success': False,
                    'error': 'Token has expired'
                }
            
            # Get user data from Pyunto
            user_id = payload.get('sub')
            response = requests.get(
                f"{self.api_url}/users/{user_id}",
                headers={
                    'Authorization': f"Bearer {refresh_token}"
                }
            )
            
            response.raise_for_status()
            user_data = response.json().get('user', {})
            
            # Generate new tokens
            tokens = self._generate_tokens(user_id, user_data)
            
            return {
                'success': True,
                'user': user_data,
                'tokens': tokens
            }
            
        except requests.RequestException as e:
            logger.error(f"Refresh token error: {str(e)}")
            return {
                'success': False,
                'error': f"Token refresh error: {str(e)}"
            }
    
    def logout(self, refresh_token):
        """
        Log out a user by invalidating their refresh token.
        
        Args:
            refresh_token: The refresh token to invalidate
            
        Returns:
            dict: Logout result
        """
        try:
            # Decode the token without validation to get the JTI
            try:
                payload = jwt.decode(refresh_token, options={"verify_signature": False})
                token_id = payload.get('jti')
                
                # Remove from active sessions if it exists
                if token_id in self.active_sessions:
                    del self.active_sessions[token_id]
                    
                return {
                    'success': True,
                    'message': 'Successfully logged out'
                }
            except:
                return {
                    'success': False,
                    'error': 'Invalid token format'
                }
                
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_token(self, token):
        """
        Validate an access token.
        
        Args:
            token: The access token to validate
            
        Returns:
            dict: Validation result
        """
        try:
            # Decode and validate the token
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Check token type
            if payload.get('type') != 'access':
                return {
                    'valid': False,
                    'error': 'Invalid token type'
                }
            
            return {
                'valid': True,
                'user_id': payload.get('sub'),
                'user_data': payload.get('user_data', {})
            }
            
        except jwt.ExpiredSignatureError:
            return {
                'valid': False,
                'error': 'Token has expired'
            }
        except jwt.PyJWTError as e:
            return {
                'valid': False,
                'error': f"Invalid token: {str(e)}"
            }


# Example implementation in a Flask application
def flask_example():
    """Example implementation in a Flask application."""
    from flask import Flask, request, jsonify, g
    from functools import wraps
    
    app = Flask(__name__)
    
    # Initialize PyuntoAuth
    auth = PyuntoAuth(
        client_id=os.environ.get("PYUNTO_CLIENT_ID"),
        client_secret=os.environ.get("PYUNTO_CLIENT_SECRET")
    )
    
    # Authentication middleware
    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Get token from header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid Authorization header'}), 401
            
            token = auth_header.split(' ')[1]
            
            # Validate token
            result = auth.validate_token(token)
            if not result.get('valid'):
                return jsonify({'error': result.get('error', 'Invalid token')}), 401
            
            # Set user in flask g object
            g.user_id = result.get('user_id')
            g.user_data = result.get('user_data')
            
            return f(*args, **kwargs)
        return decorated
    
    # Login route
    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        result = auth.login(email, password)
        
        if result.get('success'):
            return jsonify({
                'user': result.get('user'),
                'access_token': result.get('tokens', {}).get('access_token'),
                'refresh_token': result.get('tokens', {}).get('refresh_token'),
                'expires_in': result.get('tokens', {}).get('expires_in')
            })
        else:
            return jsonify({'error': result.get('error', 'Authentication failed')}), 401
    
    # Refresh token route
    @app.route('/refresh', methods=['POST'])
    def refresh():
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        result = auth.refresh_token(refresh_token)
        
        if result.get('success'):
            return jsonify({
                'user': result.get('user'),
                'access_token': result.get('tokens', {}).get('access_token'),
                'refresh_token': result.get('tokens', {}).get('refresh_token'),
                'expires_in': result.get('tokens', {}).get('expires_in')
            })
        else:
            return jsonify({'error': result.get('error', 'Token refresh failed')}), 401
    
    # Logout route
    @app.route('/logout', methods=['POST'])
    def logout():
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        result = auth.logout(refresh_token)
        
        if result.get('success'):
            return jsonify({'message': 'Successfully logged out'})
        else:
            return jsonify({'error': result.get('error', 'Logout failed')}), 400
    
    # Protected route example
    @app.route('/profile', methods=['GET'])
    @require_auth
    def profile():
        # g.user_id and g.user_data are set by the require_auth decorator
        return jsonify({
            'user_id': g.user_id,
            'user_data': g.user_data
        })
    
    # Start the server
    if __name__ == '__main__':
        app.run(debug=True)


# Example implementation in a Node.js Express application
def express_example_code():
    """
    This is not executable Python code, but an example of how to implement
    similar authentication in a Node.js Express application.
    """
    return """
    const express = require('express');
    const jwt = require('jsonwebtoken');
    const axios = require('axios');
    const crypto = require('crypto');
    
    const app = express();
    app.use(express.json());
    
    // Configuration
    const config = {
        apiUrl: process.env.PYUNTO_API_URL || 'https://a.pyunto.com/api',
        clientId: process.env.PYUNTO_CLIENT_ID,
        clientSecret: process.env.PYUNTO_CLIENT_SECRET,
        jwtSecret: process.env.PYUNTO_JWT_SECRET || process.env.PYUNTO_CLIENT_SECRET,
        tokenExpiry: parseInt(process.env.PYUNTO_TOKEN_EXPIRY || '3600'),
        refreshTokenExpiry: parseInt(process.env.PYUNTO_REFRESH_TOKEN_EXPIRY || '2592000')
    };
    
    // Store active sessions
    const activeSessions = {};
    
    // Authentication middleware
    const requireAuth = (req, res, next) => {
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: 'Missing or invalid Authorization header' });
        }
        
        const token = authHeader.split(' ')[1];
        
        try {
            // Verify the token
            const payload = jwt.verify(token, config.jwtSecret);
            
            // Check token type
            if (payload.type !== 'access') {
                return res.status(401).json({ error: 'Invalid token type' });
            }
            
            // Set user info in request
            req.userId = payload.sub;
            req.userData = payload.user_data || {};
            
            next();
        } catch (error) {
            if (error instanceof jwt.TokenExpiredError) {
                return res.status(401).json({ error: 'Token has expired' });
            }
            return res.status(401).json({ error: `Invalid token: ${error.message}` });
        }
    };
    
    // Login route
    app.post('/login', async (req, res) => {
        const { email, password } = req.body;
        
        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password are required' });
        }
        
        try {
            // Make request to Pyunto auth endpoint
            const response = await axios.post(`${config.apiUrl}/auth/login`, {
                email,
                password,
                client_id: config.clientId,
                client_secret: config.clientSecret
            });
            
            const authData = response.data;
            
            if (authData.success) {
                const userId = authData.user_id;
                const userData = authData.user || {};
                
                // Generate tokens
                const tokens = generateTokens(userId, userData);
                
                return res.json({
                    user: userData,
                    access_token: tokens.access_token,
                    refresh_token: tokens.refresh_token,
                    expires_in: tokens.expires_in
                });
            } else {
                return res.status(401).json({ error: authData.error || 'Authentication failed' });
            }
        } catch (error) {
            console.error('Login error:', error.message);
            return res.status(500).json({ error: `Authentication error: ${error.message}` });
        }
    });
    
    // Refresh token route
    app.post('/refresh', async (req, res) => {
        const { refresh_token } = req.body;
        
        if (!refresh_token) {
            return res.status(400).json({ error: 'Refresh token is required' });
        }
        
        try {
            // Decode and validate the refresh token
            const payload = jwt.verify(refresh_token, config.jwtSecret);
            
            // Check token type
            if (payload.type !== 'refresh') {
                return res.status(401).json({ error: 'Invalid token type' });
            }
            
            // Check if token is in active sessions
            const tokenId = payload.jti;
            if (!activeSessions[tokenId]) {
                return res.status(401).json({ error: 'Token has been revoked' });
            }
            
            // Get user info and update last used timestamp
            const session = activeSessions[tokenId];
            session.last_used = Math.floor(Date.now() / 1000);
            
            // Validate session expiry
            if (session.expires_at < Math.floor(Date.now() / 1000)) {
                // Clean up expired session
                delete activeSessions[tokenId];
                return res.status(401).json({ error: 'Token has expired' });
            }
            
            // Get user data from Pyunto
            const userId = payload.sub;
            const userResponse = await axios.get(`${config.apiUrl}/users/${userId}`, {
                headers: {
                    Authorization: `Bearer ${refresh_token}`
                }
            });
            
            const userData = userResponse.data.user || {};
            
            // Generate new tokens
            const tokens = generateTokens(userId, userData);
            
            return res.json({
                user: userData,
                access_token: tokens.access_token,
                refresh_token: tokens.refresh_token,
                expires_in: tokens.expires_in
            });
        } catch (error) {
            if (error instanceof jwt.TokenExpiredError) {
                return res.status(401).json({ error: 'Token has expired' });
            }
            console.error('Refresh token error:', error.message);
            return res.status(401).json({ error: `Token refresh error: ${error.message}` });
        }
    });
    
    // Logout route
    app.post('/logout', (req, res) => {
        const { refresh_token } = req.body;
        
        if (!refresh_token) {
            return res.status(400).json({ error: 'Refresh token is required' });
        }
        
        try {
            // Decode the token without validation to get the JTI
            const payload = jwt.decode(refresh_token);
            if (!payload) {
                return res.status(400).json({ error: 'Invalid token format' });
            }
            
            const tokenId = payload.jti;
            
            // Remove from active sessions if it exists
            if (activeSessions[tokenId]) {
                delete activeSessions[tokenId];
            }
            
            return res.json({ message: 'Successfully logged out' });
        } catch (error) {
            console.error('Logout error:', error.message);
            return res.status(400).json({ error: error.message });
        }
    });
    
    // Protected route example
    app.get('/profile', requireAuth, (req, res) => {
        return res.json({
            user_id: req.userId,
            user_data: req.userData
        });
    });
    
    // Helper function to generate tokens
    function generateTokens(userId, userData = {}) {
        const now = Math.floor(Date.now() / 1000);
        
        // Access token payload
        const accessPayload = {
            sub: userId,
            iat: now,
            exp: now + config.tokenExpiry,
            type: 'access',
            jti: crypto.randomUUID()
        };
        
        // Refresh token payload
        const refreshPayload = {
            sub: userId,
            iat: now,
            exp: now + config.refreshTokenExpiry,
            type: 'refresh',
            jti: crypto.randomUUID()
        };
        
        // Add user data if provided
        if (userData) {
            accessPayload.user_data = userData;
        }
        
        // Generate tokens
        const accessToken = jwt.sign(accessPayload, config.jwtSecret);
        const refreshToken = jwt.sign(refreshPayload, config.jwtSecret);
        
        // Store session info
        activeSessions[refreshPayload.jti] = {
            user_id: userId,
            expires_at: now + config.refreshTokenExpiry,
            created_at: now,
            last_used: now
        };
        
        return {
            access_token: accessToken,
            refresh_token: refreshToken,
            expires_in: config.tokenExpiry,
            token_type: 'Bearer'
        };
    }
    
    // Start the server
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
    });
    """


if __name__ == "__main__":
    # Example usage of PyuntoAuth
    auth = PyuntoAuth(
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
    
    # Example login flow
    print("Testing login...")
    login_result = auth.login("user@example.com", "password123")
    print(f"Login success: {login_result.get('success')}")
    
    if login_result.get('success'):
        tokens = login_result.get('tokens', {})
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        
        print(f"Access token: {access_token[:10]}...")
        print(f"Refresh token: {refresh_token[:10]}...")
        
        # Validate the token
        print("\nValidating token...")
        validation = auth.validate_token(access_token)
        print(f"Token valid: {validation.get('valid')}")
        if validation.get('valid'):
            print(f"User ID: {validation.get('user_id')}")
        
        # Refresh the token
        print("\nRefreshing token...")
        refresh_result = auth.refresh_token(refresh_token)
        print(f"Refresh success: {refresh_result.get('success')}")
        
        if refresh_result.get('success'):
            new_tokens = refresh_result.get('tokens', {})
            new_access_token = new_tokens.get('access_token')
            print(f"New access token: {new_access_token[:10]}...")
        
        # Logout
        print("\nLogging out...")
        logout_result = auth.logout(refresh_token)
        print(f"Logout success: {logout_result.get('success')}")
    else:
        print(f"Login error: {login_result.get('error')}")
